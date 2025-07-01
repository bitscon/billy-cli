#!/bin/bash
set -e

echo "🔧 Creating Ollama systemd service..."
sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOL'
[Unit]
Description=Ollama AI Model Server
After=network.target

[Service]
Type=simple
User=billybs
ExecStart=/usr/local/bin/ollama serve
Restart=always

[Install]
WantedBy=multi-user.target
EOL

echo "🔧 Creating Billy systemd service..."
sudo tee /etc/systemd/system/billy.service > /dev/null << 'EOL'
[Unit]
Description=Billy AI Assistant Service
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=billybs
WorkingDirectory=/home/billybs/projects/billy
ExecStart=/home/billybs/projects/billy/venv/bin/flask run --host=0.0.0.0 --port=5000
Environment="FLASK_APP=src/billy.py"
Environment="BILLY_DB_PATH=db/billy.db"
Restart=always

[Install]
WantedBy=multi-user.target
EOL

echo "🔧 Reloading systemd..."
sudo systemctl daemon-reload

echo "🔧 Enabling services to start at boot..."
sudo systemctl enable ollama
sudo systemctl enable billy

echo "🔧 Starting services now..."
sudo systemctl start ollama
sleep 2
sudo systemctl start billy

echo "✅ Deployment complete. Checking status..."

sudo systemctl status ollama --no-pager
sudo systemctl status billy --no-pager
