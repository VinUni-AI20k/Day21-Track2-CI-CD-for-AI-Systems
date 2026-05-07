#!/bin/bash
# VM Setup Script for MLOps Pipeline
# Run this script on a fresh Ubuntu 22.04 EC2 instance

set -e

echo "=== MLOps VM Setup Script ==="
echo "This script will set up the ML model serving environment"
echo ""

# Variables - Modify these as needed
S3_BUCKET="${S3_BUCKET:-mlops-wine-quality-dung}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "Configuration:"
echo "  S3_BUCKET: $S3_BUCKET"
echo "  AWS_REGION: $AWS_REGION"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "ERROR: Do not run this script as root. Use 'sudo' for individual commands if needed."
    exit 1
fi

echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "Step 2: Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv curl

echo "Step 3: Creating application directories..."
mkdir -p ~/src ~/models
echo "  Created ~/src and ~/models directories"

echo "Step 4: Installing Python packages..."
pip3 install --user fastapi uvicorn scikit-learn joblib boto3

echo "Step 5: Downloading serve.py..."
cd ~/src
curl -O https://raw.githubusercontent.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/master/src/serve.py

echo "Step 6: Creating systemd service..."
sudo tee /etc/systemd/system/mlops-serve.service > /dev/null <<EOF
[Unit]
Description=MLOps Wine Quality Prediction API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME
Environment="S3_BUCKET=$S3_BUCKET"
Environment="AWS_REGION=$AWS_REGION"
ExecStart=$(which python3) $HOME/src/serve.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Step 7: Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable mlops-serve
sudo systemctl start mlops-serve

echo "Step 8: Checking service status..."
sleep 2
sudo systemctl status mlops-serve --no-pager || true

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Test the health endpoint: curl http://localhost:8000/health"
echo "2. View logs: sudo journalctl -u mlops-serve -f"
echo "3. Configure IAM role for EC2 (recommended) or add AWS credentials to service"
echo ""
