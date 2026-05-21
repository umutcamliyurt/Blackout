#!/bin/bash

LOG_FILE="./shutdown_log.txt"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] Heartbeat lost. custom.sh triggered before shutdown." >> "$LOG_FILE"