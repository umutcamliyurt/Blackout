# Blackout

## A network-wide encrypted killswitch for emergency situations

<img src="background.png" width="900">

> ## ⚠️ **Warning:** Broadcast server must be on the same network as clients and should be a Tor hidden service, as there is currently no authentication mechanism for trigger.

<!-- DESCRIPTION -->
## Description:

This tool consists of a broadcast server that securely transmits encrypted heartbeat messages over the local network, along with a client that listens for these messages. Client devices equipped with the correct key can recognize these heartbeat signals. Triggering the killswitch stops the broadcasts, which causes the clients to execute emergency commands and shutdown.

<!-- FEATURES -->
## Features:

- Broadcasts encrypted heartbeats to clients using different encryption keys
- Client computers shutdown when killswitch is triggered or when connectivity with broadcast server is lost
- Client computers run custom emergency script before shutdown
- Docker support
- Written in Python

<!-- INSTALLATION -->
## Setup:

    git clone https://github.com/umutcamliyurt/Blackout.git
    cd Blackout/
    sudo apt-get install python3 python3-pip
    sudo pip3 install -r requirements.txt

### Client usage:

```
sudo python3 client.py --test
[*] Enter 64-character hex-encoded AES key (or press Enter to generate one):
>> 
[*] No key entered. Generated a new AES-256 key.
============================================================
                      Blackout Client                       
============================================================

🔑 AES Key in use (hex): 2a14f213aa6d6cd8abbeb5d0e16bd06620886632c0879ab183bf8283813e03b7
[*] Share this key securely with the server.

[*] Waiting for confirmation that the server is broadcasting...
>> Press Enter once the server has been configured with the AES key and is running.

[+] Listening for encrypted heartbeats on UDP port 9999...
⠹ Heartbeats received: 22 from 192.168.1.7 [TEST MODE] Heartbeat lost. System would shut down now.
```

### Server usage with Docker:

    sudo docker build --network=host -t blackout .
    sudo docker run --rm -it blackout:latest

### Server usage:

```
sudo python3 server.py
============================================================
                 Blackout Broadcast Server                  
============================================================

🔐 Enter AES keys (hex, 64 chars each, comma-separated):
>>> c10e2b8b62da3c63aa0fdd6e83d76a05313015b596bad01bb23c7de1a06ad0b4
Enter redirect URL (e.g. https://example.com):
>>> https://example.com

Server will listen on http://127.0.0.1:8080
⚠️  Killswitch is running! Any request to URL will trigger emergency broadcast.

Using interface 'wlan0' with IP 192.168.1.24
🚨 URL accessed! Stopping heartbeat broadcast and clients will shutdown.
```

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.