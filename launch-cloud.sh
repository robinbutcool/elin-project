#!/bin/bash
KEY_FILE="$HOME/elin-project/.groq_key"
if [ ! -f "$KEY_FILE" ]; then
    echo "Please log into console.groq.com and copy your API key."
    read -p "API Key: " GROQ_KEY
    echo "$GROQ_KEY" > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
else
    GROQ_KEY=$(cat "$KEY_FILE")
fi
cd ~/elin-project/searxng-docker && docker compose up -d
cd ~/elin-project
echo "starting elin in cloud mode..."
GROQ_API_KEY="$GROQ_KEY" ELIN_MODE="cloud" python elin.py "$@"
cd ~/elin-project/searxng-docker && docker compose down
