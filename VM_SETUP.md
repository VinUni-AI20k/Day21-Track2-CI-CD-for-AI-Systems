# EC2 VM Setup Guide for MLOps Pipeline

## Overview

This guide walks you through setting up an EC2 instance to run the FastAPI model serving application. The instance will host `serve.py` which provides the `/predict` and `/health` endpoints.

---

## Step 1: Create EC2 Instance

### Actions:

1. Go to EC2 Console: https://console.aws.amazon.com/ec2/
2. Click **"Launch instance"**
3. Configure the instance:

   | Setting | Value |
   |---------|-------|
   | **Name** | `mlops-wine-quality-vm` |
   | **OS** | Ubuntu 22.04 LTS (Free tier eligible) |
   | **Instance type** | `t2.small` (1 vCPU, 2 GB RAM - sufficient for this lab) |
   | **Key pair** | Create new or use existing (needed for SSH) |

4. **Network settings**:
   - VPC: Default
   - Subnet: Default
   - Auto-assign public IP: **Enable**
   - **Security Group**: Create new
     - Add Rule 1: SSH (port 22) - My IP
     - Add Rule 2: **Custom TCP (port 8000)** - Anywhere (for FastAPI)
     - Add Rule 3: HTTP (port 80) - Anywhere (optional)

5. Click **"Launch instance"**

### Note Important Values:
After launch, note:
- **Public IPv4 address**: e.g., `54.123.45.67`
- **Instance ID**: e.g., `i-0123456789abcdef0`
- **Key pair file**: The `.pem` file you downloaded

---

## Step 2: Connect to EC2 Instance

### Option A: Using Windows Command Prompt (OpenSSH)

If you have OpenSSH installed on Windows:

```bash
ssh -i "path\to\your\key.pem" ubuntu@54.123.45.67
```

### Option B: Using PuTTY

1. Convert `.pem` to `.ppk` using PuTTYgen
2. Connect with hostname: `ubuntu@54.123.45.67`

### Option C: Using Windows Subsystem for Linux (WSL)

```bash
chmod 400 path/to/your/key.pem
ssh -i path/to/your/key.pem ubuntu@54.123.45.67
```

---

## Step 3: Install Dependencies on VM

Once connected to the EC2 instance, run:

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install -y python3 python3-pip python3-venv

# Create directories
mkdir -p ~/src ~/models

# Install Python packages
pip3 install fastapi uvicorn scikit-learn joblib boto3
```

---

## Step 4: Upload serve.py to VM

### Option A: SCP from Windows

```bash
# In Windows CMD/PowerShell
scp -i "path\to\key.pem" "D:\Project_AI\Day21-Track2-CI-CD-for-AI-Systems\src\serve.py" ubuntu@54.123.45.67:~/src/
```

### Option B: Download from GitHub

On the EC2 instance:

```bash
cd ~/src
curl -O https://raw.githubusercontent.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/master/src/serve.py
```

---

## Step 5: Create Systemd Service

Create a systemd service file to run the FastAPI server:

```bash
sudo nano /etc/systemd/system/mlops-serve.service
```

Paste the following content:

```ini
[Unit]
Description=MLOps Wine Quality Prediction API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="S3_BUCKET=mlops-wine-quality-dung"
Environment="AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY"
Environment="AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY"
Environment="AWS_REGION=us-east-1"
ExecStart=/usr/bin/python3 /home/ubuntu/src/serve.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Important**: Replace the following values:
- `S3_BUCKET`: Your actual bucket name
- `AWS_ACCESS_KEY_ID`: Your IAM user access key
- `AWS_SECRET_ACCESS_KEY`: Your IAM user secret key
- `AWS_REGION`: Your bucket region

Or use a more secure approach with AWS IAM roles (see Section 6).

---

## Step 6: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable mlops-serve

# Start the service
sudo systemctl start mlops-serve

# Check service status
sudo systemctl status mlops-serve

# View logs
sudo journalctl -u mlops-serve -f
```

---

## Step 7: Configure IAM Role for EC2 (Recommended for Security)

Instead of embedding AWS credentials in the service file, use IAM roles:

### Actions:

1. Go to IAM Console: https://console.aws.amazon.com/iam/
2. Create a new **IAM Role**:
   - Trusted entity: AWS service → EC2
   - Permissions: `AmazonS3FullAccess` (or custom S3 policy)
3. Go to EC2 Console
4. Select your instance → **Actions** → **Security** → **Modify IAM role**
5. Select the role you created and click **Update IAM role**

### Update Service File:

Remove AWS credential lines from the service file:

```ini
[Unit]
Description=MLOps Wine Quality Prediction API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu
Environment="S3_BUCKET=mlops-wine-quality-dung"
ExecStart=/usr/bin/python3 /home/ubuntu/src/serve.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart mlops-serve
```

---

## Step 8: Test the API

From your local machine or any machine with network access:

### Health Check:
```bash
curl http://54.123.45.67:8000/health
```

Expected response:
```json
{"status":"ok"}
```

### Prediction:
```bash
curl -X POST http://54.123.45.67:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [7.0, 0.27, 0.36, 20.7, 0.045, 45.0, 170.0, 1.001, 3.0, 0.45, 8.8, 0]}'
```

Expected response (example):
```json
{"prediction":1,"label":"trung_binh"}
```

---

## Step 9: Set Up SSH Key for GitHub Actions

For the GitHub Actions deploy job to SSH into the VM, you need to:

### 9.1: Generate SSH Key Pair (on local Windows)

```bash
# In PowerShell or CMD
ssh-keygen -t ed25519 -C "github-actions-deploy"
```

Save to: `C:\Users\YourName\.ssh\mlops_deploy_key`

### 9.2: Add Public Key to EC2

On the EC2 instance:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
```

Paste the **public key** (from `C:\Users\YourName\.ssh\mlops_deploy_key.pub`) into this file.

### 9.3: Add Private Key to GitHub Secrets

1. Read the private key content:
   ```bash
   # In PowerShell
   Get-Content C:\Users\YourName\.ssh\mlops_deploy_key
   ```

2. Go to GitHub Secrets: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/settings/secrets/actions
3. Add:
   - **Secret Name**: `VM_SSH_KEY`
   - **Value**: The entire private key content (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

---

## Step 10: Add Remaining GitHub Secrets

Go to: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/settings/secrets/actions

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `VM_HOST` | Your EC2 public IP (e.g., `54.123.45.67`) |
| `VM_USER` | `ubuntu` |
| `VM_SSH_KEY` | Content of your private SSH key |

---

## Service Management Commands

```bash
# View service status
sudo systemctl status mlops-serve

# View live logs
sudo journalctl -u mlops-serve -f

# Restart service
sudo systemctl restart mlops-serve

# Stop service
sudo systemctl stop mlops-serve

# Disable service (prevent auto-start)
sudo systemctl disable mlops-serve
```

---

## Troubleshooting

### Service Won't Start

1. Check logs: `sudo journalctl -u mlops-serve -n 50`
2. Verify Python dependencies: `pip3 list | grep -E "fastapi|uvicorn|sklearn"`
3. Test serve.py manually: `python3 ~/src/serve.py`

### Health Check Fails

1. Verify port 8000 is open in security group
2. Check if service is running: `sudo systemctl is-active mlops-serve`
3. Check if port is listening: `sudo netstat -tlnp | grep 8000`

### Model Download Fails

1. Verify S3 bucket exists and is accessible
2. Check AWS credentials/IAM role permissions
3. Verify bucket name is correct in service file

---

## Next Steps

1. Verify all GitHub Secrets are set
2. Push a commit to GitHub to trigger the pipeline
3. Monitor GitHub Actions at: https://github.com/Dung20225817/Day21-Track2-CI-CD-for-AI-Systems/actions
4. If pipeline succeeds, test the deployed API
