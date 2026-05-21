from scapy.all import sniff, UDP, IP
import subprocess
import platform
import sys
import os
import threading
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from colorama import init, Fore, Style
import binascii

init(autoreset=True)

LISTEN_PORT = 9999
HEARTBEAT_TIMEOUT = 3
TEST_MODE = "--test" in sys.argv

heartbeat_timer = None
heartbeat_lock = threading.Lock()
last_counter = -1
heartbeat_count = 0
spinner_cycle = ['⠋','⠙','⠹','⠸','⠼','⠴','⠦','⠧','⠇','⠏']

def input_aes_key():
    print(Fore.CYAN + "[*] Enter 64-character hex-encoded AES key (or press Enter to generate one):")
    user_input = input(Fore.BLUE + ">> ").strip()
    if user_input:
        try:
            key_bytes = bytes.fromhex(user_input)
            if len(key_bytes) != 32:
                raise ValueError("Invalid key length")
            print(Fore.GREEN + "[+] Using user-provided AES key.")
            return key_bytes
        except ValueError:
            print(Fore.RED + "[!] Invalid key. Must be exactly 64 hex characters (32 bytes).")
            sys.exit(1)
    else:
        generated_key = os.urandom(32)
        print(Fore.YELLOW + "[*] No key entered. Generated a new AES-256 key.")
        return generated_key

AES_KEY = input_aes_key()

def print_header():
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.MAGENTA + Style.BRIGHT + "Blackout Client".center(60))
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print()

def print_footer():
    print()
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)
    print(Fore.GREEN + "Listening terminated gracefully.".center(60))
    print(Fore.CYAN + Style.BRIGHT + "=" * 60)

def run_custom_script():
    system = platform.system()
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if system == "Windows":
        script_name = "custom.bat"
    else:
        script_name = "custom.sh"

    script_path = os.path.join(script_dir, script_name)

    if os.path.isfile(script_path):
        if system != "Windows":
            try:
                os.chmod(script_path, 0o755)
                print(Fore.GREEN + f"[+] Set executable permission for {script_name}")
            except Exception as e:
                print(Fore.RED + f"[ERROR] Failed to set executable permission: {e}")
        print(Fore.YELLOW + f"[*] Running custom shutdown script: {script_name}")
        try:
            subprocess.run([script_path], shell=True, check=True)
            print(Fore.GREEN + f"[+] {script_name} executed successfully.")
        except subprocess.CalledProcessError as e:
            print(Fore.RED + f"[ERROR] {script_name} execution failed: {e}")
    else:
        print(Fore.YELLOW + f"[*] No custom shutdown script ({script_name}) found. Skipping...")

def shutdown_computer():
    if TEST_MODE:
        print(Fore.MAGENTA + "[TEST MODE] Heartbeat lost. System would shut down now.")
        return

    print(Fore.RED + Style.BRIGHT + "❗ Heartbeat lost. Preparing to shut down...")

    run_custom_script()

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
        elif system == "Linux":
            subprocess.run(["systemctl", "poweroff", "-i", "--force"], check=True)
        elif system == "Darwin":
            subprocess.run(["shutdown", "-h", "now"], check=True)
        else:
            print(Fore.YELLOW + "⚠️ Unsupported OS. Please shut down manually.")
    except Exception as e:
        print(Fore.RED + f"[ERROR] Shutdown failed: {e}")

def decrypt_packet(packet):
    if len(packet) < 13:
        return None
    nonce = packet[:12]
    ciphertext = packet[12:]
    aesgcm = AESGCM(AES_KEY)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception:
        return None

def is_valid_counter(counter_bytes):
    global last_counter
    try:
        new_counter = int.from_bytes(counter_bytes, 'big')
    except Exception:
        return False
    if new_counter > last_counter:
        last_counter = new_counter
        return True
    return False

def reset_heartbeat_timer():
    global heartbeat_timer
    with heartbeat_lock:
        if heartbeat_timer:
            heartbeat_timer.cancel()
        heartbeat_timer = threading.Timer(HEARTBEAT_TIMEOUT, shutdown_computer)
        heartbeat_timer.start()

def handle_packet(packet):
    global heartbeat_count
    if UDP in packet and packet[UDP].dport == LISTEN_PORT:
        src_ip = packet[IP].src
        raw_data = bytes(packet[UDP].payload)
        plaintext = decrypt_packet(raw_data)
        if plaintext and is_valid_counter(plaintext):
            heartbeat_count += 1
            spinner = spinner_cycle[heartbeat_count % len(spinner_cycle)]
            print(Fore.GREEN + f"\r{spinner} Heartbeats received: {heartbeat_count} from {src_ip} ", end='', flush=True)
            reset_heartbeat_timer()

def listen_for_heartbeat():
    print(Fore.CYAN + f"[+] Listening for encrypted heartbeats on UDP port {LISTEN_PORT}...")
    reset_heartbeat_timer()
    try:
        sniff(filter=f"udp and port {LISTEN_PORT}", prn=handle_packet, store=0)
    except KeyboardInterrupt:
        print()
        print(Fore.YELLOW + "\nListener stopped by user.")
        print_footer()

if __name__ == "__main__":
    print_header()

    print(Fore.CYAN + Fore.YELLOW + f"🔑 AES Key in use (hex): {AES_KEY.hex()}")
    print(Fore.MAGENTA + "[*] Share this key securely with the server.\n")

    print(Fore.CYAN + "[*] Waiting for confirmation that the server is broadcasting...")
    input(Fore.BLUE + ">> Press Enter once the server has been configured with the AES key and is running.\n")

    listen_for_heartbeat()
