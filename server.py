import warnings
warnings.filterwarnings("ignore", message="'iface' has no effect on L3 I/O send()")

import os
import threading
import time
from flask import Flask, redirect
from waitress import serve
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from colorama import init, Fore, Style
from scapy.all import sendp, sendpfast, Ether, IP, UDP, Raw, get_if_list, get_if_addr, getmacbyip, get_if_hwaddr

init(autoreset=True)

PORT = 8080
BROADCAST_IP = "255.255.255.255"
BROADCAST_PORT = 9999
HEARTBEAT_INTERVAL = 0.5

app = Flask(__name__)
AES_KEYS = []
REDIRECT_URL = None
broadcasting = True
counter = 0

spinner_cycle = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

def print_header():
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.MAGENTA + Style.BRIGHT + "Blackout Broadcast Server".center(60))
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print()

def encrypt_counter(counter_value, aesgcm):
    nonce = os.urandom(12)
    counter_bytes = counter_value.to_bytes(8, 'big')
    ciphertext = aesgcm.encrypt(nonce, counter_bytes, None)
    return nonce + ciphertext

def get_send_interface():
    for iface in get_if_list():
        try:
            ip = get_if_addr(iface)
            if ip and not ip.startswith("127."):
                mac = getmacbyip(ip)
                if mac is None:
                    mac = get_if_hwaddr(iface)
                if mac:
                    return iface, ip, mac
        except Exception:
            continue
    raise RuntimeError("No suitable interface found")

def send_heartbeat_packets(packets, iface):
    try:
        sendpfast(packets, iface=iface, verbose=False)
    except Exception:
        for pkt in packets:
            sendp(pkt, iface=iface, verbose=False)

def send_emergency_packet():
    global broadcasting
    broadcasting = False
    print(Fore.RED + Style.BRIGHT + "🚨 URL accessed! Stopping heartbeat broadcast and clients will shutdown.")

def heartbeat_loop():
    global counter
    spinner_index = 0

    try:
        iface, src_ip, src_mac = get_send_interface()
        print(Fore.GREEN + f"Using interface '{iface}' with IP {src_ip}")
    except RuntimeError as e:
        print(Fore.RED + f"❌ {e}")
        return

    aesgcm_objects = [AESGCM(key) for key in AES_KEYS]

    while broadcasting:
        packets = []
        for aesgcm in aesgcm_objects:
            packet_data = encrypt_counter(counter, aesgcm)
            pkt = (
                Ether(src=src_mac, dst="ff:ff:ff:ff:ff:ff") /
                IP(src=src_ip, dst=BROADCAST_IP) /
                UDP(sport=12345, dport=BROADCAST_PORT) /
                Raw(load=packet_data)
            )
            packets.append(pkt)

        send_heartbeat_packets(packets, iface)

        counter += 1
        if counter % 100 == 0:
            spinner = spinner_cycle[spinner_index % len(spinner_cycle)]
            print(Fore.CYAN + f"\r{spinner} Heartbeat broadcasts sent: {counter} ", end='', flush=True)
            spinner_index += 1

        if HEARTBEAT_INTERVAL > 0:
            time.sleep(HEARTBEAT_INTERVAL)

    print()

@app.before_request
def killswitch():
    send_emergency_packet()
    return redirect(REDIRECT_URL)

def get_keys_from_user():
    keys = []
    print(Fore.CYAN + "🔐 Enter AES keys (hex, 64 chars each, comma-separated):")
    line = input(Fore.YELLOW + ">>> ").strip()
    for k in line.split(","):
        k = k.strip()
        if len(k) == 64:
            try:
                keys.append(bytes.fromhex(k))
            except ValueError:
                print(Fore.RED + f"❌ Invalid hex key skipped: {k}")
        else:
            print(Fore.RED + f"❌ Skipped invalid key length: {k}")
    return keys

def get_redirect_url_from_user():
    print(Fore.CYAN + "Enter redirect URL (e.g. https://example.com):")
    return input(Fore.YELLOW + ">>> ").strip()

if __name__ == "__main__":
    print_header()

    AES_KEYS = get_keys_from_user()
    if not AES_KEYS:
        print(Fore.RED + Style.BRIGHT + "❌ No valid AES keys provided. Exiting.")
        exit(1)

    REDIRECT_URL = get_redirect_url_from_user()
    if not REDIRECT_URL:
        print(Fore.RED + Style.BRIGHT + "❌ No redirect URL provided. Exiting.")
        exit(1)

    print(Fore.GREEN + Style.BRIGHT + f"\nServer will listen on http://127.0.0.1:{PORT}")
    print(Fore.RED + Style.BRIGHT + "⚠️  Killswitch is running! Any request to URL will trigger emergency broadcast.\n")

    threading.Thread(target=heartbeat_loop, daemon=True).start()

    serve(app, host="127.0.0.1", port=PORT)
