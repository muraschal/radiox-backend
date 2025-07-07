# RadioX Local Development Guide

## 🏠 Development Environment Strategy

### Environment Overview

```
┌─────────────────────────────────────┐
│         DEVELOPMENT FLOW            │
├─────────────────────────────────────┤
│                                     │
│  🏠 LOCAL DEVELOPMENT               │
│  • Fast iteration (seconds)         │
│  • Hot reload & quick testing       │
│  • localhost:8000                   │
│  • docker-compose up                │
│                                     │
│         ↓ (when ready)              │
│                                     │
│  ☁️  PRODUCTION DEPLOYMENT          │
│  • Full pipeline testing            │
│  • api.radiox.cloud                 │
│  • LXC Container + Cloudflare       │
│                                     │
└─────────────────────────────────────┘
```

## 🎯 Environment Identification

### Clear Command Patterns

| Action | Local Development | Production |
|--------|------------------|------------|
| **Testing** | `curl localhost:8000/health` | `curl https://api.radiox.cloud/health` |
| **Starting** | `docker-compose up --build` | `sshpass -p 'XXX' ssh root@100.109.155.102` |
| **Logs** | `docker-compose logs -f` | SSH + container logs |
| **URL** | `http://localhost:8000` | `https://api.radiox.cloud` |

### 🚨 Never Mix Commands

- ❌ **NEVER** use `localhost` when testing production
- ❌ **NEVER** use `api.radiox.cloud` for local development  
- ❌ **NEVER** use SSH commands for local development
- ✅ **ALWAYS** specify which environment you're working on

## 🛠️ Local Development Setup

### Prerequisites
```bash
# Required tools
- Docker & Docker Compose
- Git
- curl (for testing)
- Node.js (for frontend)
```

### Environment Variables
```bash
# Same as production (shared Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
OPENAI_API_KEY=your-openai-key
REDIS_URL=redis://localhost:6379
```

### Quick Start
```bash
# 1. Start local stack
docker-compose up --build

# 2. Test health
curl http://localhost:8000/health

# 3. Generate test show
curl -X POST "http://localhost:8000/shows/generate" \
  -H "Content-Type: application/json" \
  -d '{"channel": "zurich", "duration_minutes": 3}'

# 4. View logs
docker-compose logs -f show-service
```

## 🚀 Production Deployment

### When to Deploy
- ✅ Local tests pass
- ✅ Code committed to git
- ✅ No breaking changes

### Deployment Process
```bash
# 1. Commit changes locally
git add .
git commit -m "feat: your changes"
git push origin main

# 2. Deploy to production
sshpass -p '83nsada9c83nsada9c' ssh root@100.109.155.102 \
  "cd /opt/radiox-backend && git pull origin main && docker-compose down && docker-compose up -d --build"

# 3. Test production
curl https://api.radiox.cloud/health
```

## 🔄 Development Workflow

### Recommended Flow
1. **Local Development**
   - Make changes
   - `docker-compose up --build`
   - Test on `localhost:8000`
   - Iterate quickly

2. **Local Testing**
   - Generate test shows
   - Check audio generation
   - Verify all services

3. **Production Deployment**
   - Commit & push changes
   - Deploy to LXC container
   - Final production test

4. **Monitoring**
   - Check production health
   - Monitor logs if needed

## 🚨 Common Pitfalls

### Environment Confusion
- **Problem**: Testing localhost in production context
- **Solution**: Always check URL before running commands

### Credential Issues  
- **Problem**: Different API keys between environments
- **Solution**: Use same credentials (shared Supabase)

### Port Conflicts
- **Problem**: Local services conflicting with system
- **Solution**: Use docker-compose port mapping

## 📊 Monitoring & Debugging

### Local Debugging
```bash
# Service logs
docker-compose logs -f [service-name]

# Service status
docker-compose ps

# Restart specific service
docker-compose restart [service-name]
```

### Production Monitoring
```bash
# Health check
curl https://api.radiox.cloud/health

# Service status (via SSH)
sshpass -p 'XXX' ssh root@100.109.155.102 "cd /opt/radiox-backend && docker-compose ps"

# Monitoring script
sshpass -p 'XXX' ssh root@100.109.155.102 "cd /opt/radiox-backend && ./scripts/monitor-radiox.sh"
```

## 🎯 Key Differences

| Aspect | Local | Production |
|--------|-------|------------|
| **URL** | localhost:8000 | api.radiox.cloud |
| **SSL** | HTTP | HTTPS (Cloudflare) |
| **Tunnel** | None | Cloudflare Tunnel |
| **Access** | Direct | SSH required |
| **Speed** | Fast builds | Slower deploys |
| **Database** | Shared Supabase | Shared Supabase |

## 🔧 Troubleshooting

### Local Issues
- **Port 8000 busy**: `docker-compose down` first
- **Build fails**: Clear Docker cache: `docker system prune`
- **Service unhealthy**: Check logs: `docker-compose logs [service]`

### Production Issues  
- **API unreachable**: Check Cloudflare tunnel status
- **Service down**: SSH and restart: `docker-compose restart`
- **Build fails**: Check disk space and memory

---

**Remember**: Local development for speed, production for final validation! 🚀 