# 🐳 Docker Scripts Quick Reference

This directory contains scripts to easily build and run the Telegram Promo Bot using Docker.

## 📁 Files Overview

| File | Platform | Purpose |
|------|----------|---------|
| `build.sh` | Linux/macOS | Build Docker images |
| `build.ps1` | Windows | Build Docker images (PowerShell) |
| `run.sh` | Linux/macOS | Run and manage containers |
| `run.ps1` | Windows | Run and manage containers (PowerShell) |

## 🚀 Quick Start

### Linux/macOS

```bash
# Make scripts executable
chmod +x build.sh run.sh

# Build and run production
./run.sh

# Build and run development
./run.sh -m development

# Show logs
./run.sh logs

# Stop bot
./run.sh stop
```

### Windows (PowerShell)

```powershell
# Build and run production
.\run.ps1

# Build and run development
.\run.ps1 -Mode development

# Show logs
.\run.ps1 logs

# Stop bot
.\run.ps1 stop
```

## 🔧 Build Scripts

### build.sh / build.ps1

**Purpose**: Build Docker images with various options

**Linux/macOS Examples:**
```bash
./build.sh                    # Build production image
./build.sh -t development     # Build development image
./build.sh --no-cache         # Build without cache
./build.sh -T v1.0.0 --push   # Build and push with tag
```

**Windows Examples:**
```powershell
.\build.ps1                     # Build production image
.\build.ps1 -Type development   # Build development image
.\build.ps1 -NoCache           # Build without cache
.\build.ps1 -Tag v1.0.0 -Push  # Build and push with tag
```

## 🏃 Run Scripts

### run.sh / run.ps1

**Purpose**: Manage container lifecycle

**Linux/macOS Examples:**
```bash
./run.sh start                # Start bot (default)
./run.sh -m development       # Start in development mode
./run.sh -f                   # Start in foreground
./run.sh stop                 # Stop bot
./run.sh restart              # Restart bot
./run.sh logs                 # Show logs
./run.sh status               # Show container status
./run.sh -b                   # Build and start
```

**Windows Examples:**
```powershell
.\run.ps1 start               # Start bot (default)
.\run.ps1 -Mode development   # Start in development mode
.\run.ps1 -Foreground         # Start in foreground
.\run.ps1 stop                # Stop bot
.\run.ps1 restart             # Restart bot
.\run.ps1 logs                # Show logs
.\run.ps1 status              # Show container status
.\run.ps1 -Build              # Build and start
```

## 📋 Prerequisites

1. **Docker installed and running**
2. **Docker Compose available**
3. **`.env` file configured** (copy from `config.env.template`)

## 🔍 Common Commands

### Check if everything is working
```bash
# Linux/macOS
./run.sh status

# Windows
.\run.ps1 status
```

### View real-time logs
```bash
# Linux/macOS
./run.sh logs

# Windows
.\run.ps1 logs
```

### Clean restart
```bash
# Linux/macOS
./run.sh stop
./run.sh -b start

# Windows
.\run.ps1 stop
.\run.ps1 -Build start
```

## 🆘 Troubleshooting

### Script won't run (Linux/macOS)
```bash
# Make executable
chmod +x build.sh run.sh
```

### Docker not found
- Install Docker Desktop
- Make sure Docker daemon is running
- Add Docker to system PATH

### Permission denied
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

### Container won't start
1. Check `.env` file exists and has correct API keys
2. Check Docker daemon is running
3. View logs for error details

## 📖 More Information

For detailed documentation, see the main [DOCKER.md](../DOCKER.md) file in the project root. 