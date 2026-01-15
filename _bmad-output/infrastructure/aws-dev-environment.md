# AWS Development Environment
# Windows Internals DFIR Knowledge Assistant

---
created: '2026-01-15'
status: 'active'
purpose: 'Development and testing before air-gap deployment'
---

## Infrastructure Summary

| Resource | Value |
|----------|-------|
| **Instance ID** | i-007678f8e80a5b95d |
| **Instance Type** | g5.xlarge (NVIDIA A10G - 22GB VRAM) |
| **Public IP** | 54.89.177.230 |
| **Region** | us-east-1d |
| **AMI** | Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.7 (Ubuntu 22.04) |
| **Storage** | 100GB gp3 |

## Connection Details

### SSH Access
```bash
ssh -i ~/.ssh/dfir-dev-key.pem ubuntu@54.89.177.230
```

### Gradio UI (when running)
```
http://54.89.177.230:7860
```

## Security Group

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | 0.0.0.0/0 | SSH access |
| 7860 | TCP | 0.0.0.0/0 | Gradio UI |

⚠️ **Security Note:** In production, restrict these to specific IPs.

## GPU Specifications

| Spec | Value |
|------|-------|
| GPU | NVIDIA A10G |
| VRAM | ~22GB |
| Compute | Ampere architecture |
| Comparison | Similar to RTX 4090 (24GB) |

## Initial Setup Commands

After SSH:
```bash
# 1. Verify GPU
nvidia-smi

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 3. Pull models
ollama pull qwen2.5:32b-instruct-q4_K_M
ollama pull nomic-embed-text

# 4. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 5. Clone project (or sync from local)
git clone https://github.com/ohadthenonnavad/windows-dfir-assistant-bmad.git
cd windows-dfir-assistant-bmad

# 6. Initialize project
uv init --name dfir-assistant --python 3.11
uv add gradio qdrant-client instructor httpx marker-pdf pydantic pyyaml rich pynvml
uv sync

# 7. Run VRAM validation
uv run python scripts/validate_vram.py
```

## Cost Estimate

| Instance Type | On-Demand Price | Monthly (730 hrs) |
|---------------|-----------------|-------------------|
| g5.xlarge | ~$1.00/hr | ~$730/month |

**Recommendation:** Stop instance when not in use to reduce costs.

## Instance Management

### Stop Instance (save costs)
```bash
aws --profile dfir-dev ec2 stop-instances --instance-ids i-007678f8e80a5b95d
```

### Start Instance
```bash
aws --profile dfir-dev ec2 start-instances --instance-ids i-007678f8e80a5b95d
# Wait for running
aws --profile dfir-dev ec2 wait instance-running --instance-ids i-007678f8e80a5b95d
# Get new public IP
aws --profile dfir-dev ec2 describe-instances --instance-ids i-007678f8e80a5b95d \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text
```

### Terminate Instance (delete)
```bash
aws --profile dfir-dev ec2 terminate-instances --instance-ids i-007678f8e80a5b95d
```

## Development Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Local Dev      │     │  AWS g5.xlarge  │     │  Air-Gap Target │
│  (Code + BMAD)  │────▶│  (Test + VRAM)  │────▶│  (Production)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                       │                       │
   Code editing           GPU testing            Final deployment
   BMAD workflows         Model inference        No internet
   Planning               VRAM validation        RTX 4090
```

## Quick Reference

```bash
# Add to ~/.ssh/config for easier access
Host dfir-dev
    HostName 54.89.177.230
    User ubuntu
    IdentityFile ~/.ssh/dfir-dev-key.pem
    
# Then connect with:
ssh dfir-dev
```

---

*AWS Development Environment configured for DFIR Assistant Sprint 0*
