# 🐳 Docker Deployment Guide

This guide covers how to deploy the Telegram Promo Bot using Docker containers for easy deployment, scaling, and management.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Docker Files Overview](#docker-files-overview)
- [Deployment Options](#deployment-options)
- [Management Scripts](#management-scripts)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## 🔧 Prerequisites

### Required Software
- **Docker**: Version 20.10+ recommended
- **Docker Compose**: Version 2.0+ recommended
- **Git**: For cloning the repository

### System Requirements
- **RAM**: Minimum 512MB, recommended 1GB+
- **Storage**: Minimum 2GB free space
- **Network**: Internet connection for API calls

### Installation Commands

**Ubuntu/Debian:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Add user to docker group (optional)
sudo usermod -aG docker $USER
```

**Windows:**
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

**macOS:**
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/Mitateg/Hack_sum_25.git
cd Hack_sum_25

# Create environment file
cp config.env.template .env
```

### 2. Configure Environment
Edit `.env` file with your API keys:
```bash
# Required: Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Required: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Deploy with Docker Compose
```bash
# Production deployment
docker-compose up -d

# Development deployment
docker-compose -f docker-compose.dev.yml up -d
```

### 4. Verify Deployment
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f telegram-bot
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | - | Bot token from @BotFather |
| `OPENAI_API_KEY` | ✅ | - | OpenAI API key |
| `TELEGRAM_BOT_ENV` | ❌ | `production` | Environment mode |
| `ENABLE_DASHBOARD` | ❌ | `false` | Enable web dashboard |
| `DEBUG` | ❌ | `false` | Enable debug logging |

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./data` | `/app/data` | Persistent bot data |
| `bot-logs` | `/app/data/logs` | Log files |

### Port Mappings

| Host Port | Container Port | Service |
|-----------|----------------|---------|
| `5000` | `5000` | Web Dashboard |
| `8000` | `8000` | Debug Port (dev only) |

## 📁 Docker Files Overview

### Core Files

#### `Dockerfile`
Multi-stage Docker build with security best practices:
- **Stage 1 (builder)**: Installs dependencies
- **Stage 2 (production)**: Lightweight runtime image
- **Security**: Non-root user, minimal base image
- **Size**: Optimized for production use

#### `docker-compose.yml`
Production deployment configuration:
- Resource limits and reservations
- Health checks and restart policies
- Persistent volumes for data
- Security options

#### `docker-compose.dev.yml`
Development deployment with additional services:
- Source code mounting for live reloading
- Redis for caching
- PostgreSQL for database testing
- Monitoring stack (Prometheus + Grafana)

#### `docker-entrypoint.sh`
Container initialization script:
- Environment validation
- Directory setup
- Dependency checks
- Graceful shutdown handling

#### `.dockerignore`
Excludes unnecessary files from build context:
- Development files
- Cache directories
- Documentation
- Git history

## 🎯 Deployment Options

### Production Deployment

**Basic Production Setup:**
```bash
# Start production container
docker-compose up -d

# Scale if needed (not applicable for this bot)
# docker-compose up -d --scale telegram-bot=2
```

**Production with Custom Configuration:**
```bash
# Use custom compose file
docker-compose -f docker-compose.prod.yml up -d

# Override environment variables
TELEGRAM_BOT_ENV=production docker-compose up -d
```

### Development Deployment

**Full Development Stack:**
```bash
# Start all development services
docker-compose -f docker-compose.dev.yml up -d

# Start only the bot
docker-compose -f docker-compose.dev.yml up -d telegram-bot-dev
```

**Development Services:**
- **Bot**: Main application with live reloading
- **Redis**: Caching and session storage
- **PostgreSQL**: Database for testing
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards

### Cloud Deployment

**Docker Swarm:**
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml telegram-bot-stack
```

**Kubernetes:**
```bash
# Convert compose to k8s (using kompose)
kompose convert -f docker-compose.yml

# Apply to cluster
kubectl apply -f .
```

## 🛠️ Management Scripts

### Build Script (`docker-scripts/build.sh`)

Build Docker images with various options:

```bash
# Basic build
./docker-scripts/build.sh

# Development build
./docker-scripts/build.sh -t development

# Build without cache
./docker-scripts/build.sh --no-cache

# Build and push to registry
./docker-scripts/build.sh -T v1.0.0 --push

# Verbose build
./docker-scripts/build.sh -v
```

**Options:**
- `-t, --type`: Build type (production/development)
- `-T, --tag`: Docker image tag
- `--no-cache`: Build without cache
- `--push`: Push to registry
- `-v, --verbose`: Verbose output

### Run Script (`docker-scripts/run.sh`)

Manage container lifecycle:

```bash
# Start bot
./docker-scripts/run.sh

# Start in development mode
./docker-scripts/run.sh -m development

# Start in foreground
./docker-scripts/run.sh -f

# Stop bot
./docker-scripts/run.sh stop

# Restart bot
./docker-scripts/run.sh restart

# View logs
./docker-scripts/run.sh logs

# Check status
./docker-scripts/run.sh status

# Build and run
./docker-scripts/run.sh -b
```

**Commands:**
- `start`: Start the bot (default)
- `stop`: Stop the bot
- `restart`: Restart the bot
- `logs`: Show logs
- `status`: Show container status
- `build`: Build and run

**Options:**
- `-m, --mode`: Run mode (production/development)
- `-f, --foreground`: Run in foreground
- `-b, --build`: Build before running

## 📊 Monitoring

### Built-in Health Checks

The container includes automatic health checks:
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' telegram-promo-bot

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' telegram-promo-bot
```

### Log Management

**View Logs:**
```bash
# Follow logs
docker-compose logs -f telegram-bot

# View specific number of lines
docker-compose logs --tail=100 telegram-bot

# View logs from specific time
docker-compose logs --since="2024-01-01T00:00:00" telegram-bot
```

**Log Rotation:**
Configured in docker-compose.yml:
- Max size: 10MB per file
- Max files: 3 files retained
- Format: JSON for structured logging

### Development Monitoring

When using `docker-compose.dev.yml`:

**Prometheus Metrics:**
- URL: http://localhost:9090
- Collects application and system metrics

**Grafana Dashboards:**
- URL: http://localhost:3000
- Username: admin
- Password: admin

## 🔧 Troubleshooting

### Common Issues

#### Container Won't Start

**Check logs:**
```bash
docker-compose logs telegram-bot
```

**Common causes:**
- Missing `.env` file
- Invalid API keys
- Port conflicts
- Insufficient permissions

#### Permission Issues

**Fix data directory permissions:**
```bash
sudo chown -R 1000:1000 ./data
chmod -R 755 ./data
```

#### Memory Issues

**Check resource usage:**
```bash
docker stats telegram-promo-bot
```

**Increase memory limits in docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      memory: 1G
```

#### Network Connectivity

**Test API connectivity:**
```bash
# Enter container
docker exec -it telegram-promo-bot bash

# Test Telegram API
curl -s https://api.telegram.org

# Test OpenAI API
curl -s https://api.openai.com
```

### Debug Mode

**Enable debug logging:**
```bash
# Set environment variable
echo "DEBUG=true" >> .env

# Restart container
docker-compose restart telegram-bot
```

**Access container shell:**
```bash
# Interactive shell
docker exec -it telegram-promo-bot bash

# Run commands inside container
docker exec telegram-promo-bot python -c "import bot; print('Bot loaded')"
```

### Log Analysis

**Search logs for errors:**
```bash
# Search for errors
docker-compose logs telegram-bot 2>&1 | grep -i error

# Search for specific patterns
docker-compose logs telegram-bot 2>&1 | grep -i "rate limit"
```

## 🏆 Best Practices

### Security

1. **Environment Variables:**
   - Never commit `.env` files
   - Use Docker secrets in production
   - Rotate API keys regularly

2. **Container Security:**
   - Run as non-root user
   - Use minimal base images
   - Keep images updated

3. **Network Security:**
   - Use custom networks
   - Limit exposed ports
   - Enable firewall rules

### Performance

1. **Resource Management:**
   - Set appropriate memory limits
   - Monitor CPU usage
   - Use health checks

2. **Storage:**
   - Use named volumes for persistence
   - Regular backup of data directory
   - Monitor disk usage

3. **Logging:**
   - Configure log rotation
   - Use structured logging
   - Monitor log sizes

### Maintenance

1. **Updates:**
   ```bash
   # Pull latest images
   docker-compose pull
   
   # Rebuild and restart
   docker-compose up -d --build
   ```

2. **Cleanup:**
   ```bash
   # Remove unused containers
   docker container prune
   
   # Remove unused images
   docker image prune
   
   # Remove unused volumes
   docker volume prune
   ```

3. **Backup:**
   ```bash
   # Backup data directory
   tar -czf backup-$(date +%Y%m%d).tar.gz ./data
   
   # Backup container
   docker commit telegram-promo-bot telegram-promo-bot:backup
   ```

### Production Deployment

1. **Environment Separation:**
   - Use different compose files for different environments
   - Separate configuration management
   - Environment-specific secrets

2. **Monitoring:**
   - Set up log aggregation
   - Configure alerting
   - Monitor key metrics

3. **High Availability:**
   - Use orchestration platforms (Docker Swarm/Kubernetes)
   - Implement health checks
   - Plan for disaster recovery

## 📞 Support

For issues related to Docker deployment:

1. Check the [troubleshooting section](#troubleshooting)
2. Review container logs
3. Verify environment configuration
4. Check Docker and system requirements

For bot-specific issues, refer to the main README.md file.

---

**Happy Containerizing! 🐳** 