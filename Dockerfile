FROM python:3.11-alpine

RUN apk add --no-cache \
      tor \
      netcat-openbsd \
      gcc \
      musl-dev \
      libffi-dev \
      openssl-dev \
      su-exec

WORKDIR /server

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

RUN mkdir -p /var/lib/tor/hidden_service && \
    chown -R tor:tor /var/lib/tor && \
    chmod 700 /var/lib/tor/hidden_service

RUN printf "HiddenServiceDir /var/lib/tor/hidden_service\nHiddenServicePort 80 127.0.0.1:8080\nSocksPort 0\n" > /etc/tor/torrc

EXPOSE 8080

CMD ["sh","-c","su-exec tor tor -f /etc/tor/torrc --quiet > /dev/null 2>&1 & echo \"Starting Tor…\" && for i in $(seq 1 30); do [ -f /var/lib/tor/hidden_service/hostname ] && break; sleep 1; done && if [ ! -f /var/lib/tor/hidden_service/hostname ]; then echo \"❌ Onion hostname file not found. Tor did not start correctly.\" && exit 1; fi && ONION_ADDR=$(cat /var/lib/tor/hidden_service/hostname) && echo \"[+] Onion service available at: http://$ONION_ADDR\" && exec python server.py"]
