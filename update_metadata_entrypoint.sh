#!/bin/bash

# Write cron job to run update_metadata.py daily at 02:00 UTC
echo "0 2 * * * python /app/src/update_metadata.py" > /etc/crontabs/root

# Start the cron service
crond -f -l 2