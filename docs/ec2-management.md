# 💰 EC2 Instance Management - Save Costs Overnight

## Instance Details

| Property | Value |
|----------|-------|
| **Instance ID** | `i-007678f8e80a5b95d` |
| **Instance Type** | `g5.xlarge` |
| **Cost** | ~$1.01/hour = **~$24/day** if running 24/7 |

---

## 🔐 AWS CLI Setup (First Time)

### Install AWS CLI (if not installed)
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Verify installation
aws --version
```

### Configure dfir-dev Profile
```bash
# Create/configure the dfir-dev profile
aws configure --profile dfir-dev

# You'll be prompted for:
# AWS Access Key ID: [your-access-key]
# AWS Secret Access Key: [your-secret-key]
# Default region name: us-east-1
# Default output format: json
```

### Verify Connection
```bash
# Test your credentials
aws --profile dfir-dev sts get-caller-identity

# Should return your account info
```

---

## 🛑 Stop Instance (Before Sleep/Overnight)

```bash
# Using your dfir-dev AWS profile
aws --profile dfir-dev ec2 stop-instances --instance-ids i-007678f8e80a5b95d

# Check status
aws --profile dfir-dev ec2 describe-instances --instance-ids i-007678f8e80a5b95d \
  --query 'Reservations[0].Instances[0].State.Name'
```

**When stopped:** You only pay for EBS storage (~$0.08/GB/month), **NOT compute time**.

---

## ▶️ Start Instance (In the Morning)

```bash
# Start the instance
aws --profile dfir-dev ec2 start-instances --instance-ids i-007678f8e80a5b95d

# Wait for it to be running
aws --profile dfir-dev ec2 wait instance-running --instance-ids i-007678f8e80a5b95d

# Get the NEW public IP (it changes on restart!)
aws --profile dfir-dev ec2 describe-instances --instance-ids i-007678f8e80a5b95d \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
```

⚠️ **Important:** The public IP changes each time you start! Update your SSH config with the new IP.

---

## 🔄 Quick Shell Aliases

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# DFIR EC2 Instance Management Aliases
alias dfir-start='aws --profile dfir-dev ec2 start-instances --instance-ids i-007678f8e80a5b95d && echo "Starting... wait ~30s"'
alias dfir-stop='aws --profile dfir-dev ec2 stop-instances --instance-ids i-007678f8e80a5b95d && echo "Stopping instance"'
alias dfir-status='aws --profile dfir-dev ec2 describe-instances --instance-ids i-007678f8e80a5b95d --query "Reservations[0].Instances[0].[State.Name,PublicIpAddress]" --output text'
alias dfir-ip='aws --profile dfir-dev ec2 describe-instances --instance-ids i-007678f8e80a5b95d --query "Reservations[0].Instances[0].PublicIpAddress" --output text'
```

After adding, reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### Usage

| Command | Description |
|---------|-------------|
| `dfir-stop` | Stop before sleep |
| `dfir-start` | Start in morning |
| `dfir-ip` | Get current IP address |
| `dfir-status` | Check if running |

---

## 🔌 SSH Connection

After getting the new IP, connect via SSH:

```bash
# Get the current IP
dfir-ip

# Connect (replace IP with actual)
ssh -i ~/.ssh/your-key.pem ubuntu@<IP_ADDRESS>

# Or update your SSH config (~/.ssh/config)
Host dfir-dev
    HostName <NEW_IP_ADDRESS>
    User ubuntu
    IdentityFile ~/.ssh/your-key.pem
```

---

## 💡 Pro Tip: Elastic IP (Optional)

To keep a **fixed IP address** that survives restarts:

```bash
# Allocate an Elastic IP (one-time, ~$3.60/month if instance is stopped)
aws --profile dfir-dev ec2 allocate-address --domain vpc

# Note the AllocationId from the output (eipalloc-XXXXX)

# Associate it with your instance
aws --profile dfir-dev ec2 associate-address \
  --instance-id i-007678f8e80a5b95d \
  --allocation-id eipalloc-XXXXX
```

**Note:** Elastic IPs are free while the instance is running, but cost ~$0.005/hour (~$3.60/month) if the instance is stopped.

---

## 📊 Cost Savings Summary

| Usage Pattern | Monthly Cost |
|---------------|--------------|
| Running 24/7 | ~$730/month |
| Running 10h/day weekdays | ~$220/month |
| Running 8h/day weekdays | ~$176/month |

**Savings by stopping overnight:** Up to **$500+/month**!
