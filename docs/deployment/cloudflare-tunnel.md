# Cloudflare Tunnel Deployment

Sichere und professionelle externe Erreichbarkeit für RadioX Backend über **api.radiox.cloud** ohne Port-Forwarding.

## 🎯 **Warum Cloudflare Tunnel?**

- ✅ **Keine offenen Ports** - Zero-Trust Sicherheit
- ✅ **Kostenlos** - Unbegrenzter Traffic für private Nutzung
- ✅ **Automatisches SSL** - HTTPS out-of-the-box
- ✅ **DDoS-Schutz** - Enterprise-grade Protection
- ✅ **Global CDN** - Weltweit optimierte Performance
- ✅ **Unabhängig von lokaler IP** - Perfekt für wechselnde Standorte

## 🚀 **Quick Start**

### 1. Prerequisites Setup

⚠️ **WICHTIG**: Folge zuerst der [Cloudflare Setup Anleitung](cloudflare-setup.md) für:
- Cloudflare Account + Domain Setup
- Nameserver Konfiguration  
- Zero Trust Aktivierung
- Terminal Authentication

### 2. Tunnel Setup (Automatisch)

```bash
# Alle Steps in einem Command:
make setup-tunnel
```

**Oder manuell:**

```bash
# Script ausführen:
chmod +x scripts/setup-cloudflare-tunnel.sh
./scripts/setup-cloudflare-tunnel.sh
```

Das Script macht automatisch:
- ✅ Installation von `cloudflared`
- ✅ Tunnel "radiox-backend" erstellen
- ✅ DNS Record für `api.radiox.cloud`
- ✅ Tunnel Token für Docker generieren

### 3. Environment Variable setzen

Das Setup-Script gibt dir den Token aus. Füge ihn zu deiner `.env` hinzu:

```bash
# .env
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiYmM2ZjU0...sehr-langer-token
```

### 4. Production Deployment

```bash
# Auf Proxmox LXC deployen:
LXC_IP=192.168.1.100 make deploy-proxmox

# Oder komplett automatisch:
LXC_IP=192.168.1.100 make deploy-production
```

## 🏗️ **Architektur**

```
Internet → Cloudflare CDN → Cloudflare Tunnel → LXC Container
                                                     ↓
                              Docker Network: api-gateway:8000
                                                     ↓
                              8 Microservices (8001-8007)
```

### Sicherheitsfeatures:

- **Zero-Trust**: Keine eingehenden Firewall-Regeln nötig
- **Nur HTTPS**: Automatische SSL-Verschlüsselung
- **Service Isolation**: Nur API Gateway extern erreichbar
- **Cloudflare DDoS**: Schutz gegen Angriffe

## 📋 **Tunnel Konfiguration**

Die automatische Konfiguration in `~/.cloudflared/config.yml`:

```yaml
tunnel: <tunnel-id>
credentials-file: /home/user/.cloudflared/<tunnel-id>.json

ingress:
  # API Subdomain für Backend
  - hostname: api.radiox.cloud
    service: http://localhost:8000
    
  # Health Check Endpoint
  - hostname: api.radiox.cloud
    path: /health
    service: http://localhost:8000/health
    
  # Catch-all rule (required)
  - service: http_status:404
```

## 🔧 **Management Commands**

```bash
# Tunnel Status prüfen
cloudflared tunnel list

# Tunnel starten (falls nicht via Docker)
cloudflared tunnel run radiox-backend

# Tunnel löschen (falls nötig)
cloudflared tunnel delete radiox-backend

# DNS Records prüfen
cloudflared tunnel route dns list
```

## 📊 **Monitoring & Health Checks**

### Verfügbare Endpoints:

- **🏥 Health Check**: `https://api.radiox.cloud/health`
- **📊 Service Status**: `https://api.radiox.cloud/services/status`
- **📖 API Docs**: `https://api.radiox.cloud/docs`

### Service Monitoring:

```bash
# Production Logs anzeigen
make prod-logs

# Service Status
make prod-status

# Health Check von extern
curl https://api.radiox.cloud/health
```

## 🛠️ **Development vs Production**

| Aspect | Development | Production |
|--------|-------------|------------|
| **Zugriff** | `localhost:8000` | `https://api.radiox.cloud` |
| **Ports** | Alle offen (8000-8007) | Nur API Gateway |
| **SSL** | Nein | Automatisch (Cloudflare) |
| **Sicherheit** | Lokal | Zero-Trust + DDoS |
| **Deployment** | `make up` | `make deploy-production` |

## 🚨 **Troubleshooting**

### Tunnel verbindet nicht:

```bash
# Token prüfen
echo $CLOUDFLARE_TUNNEL_TOKEN

# Tunnel Status
cloudflared tunnel list

# Logs anzeigen
docker-compose -f docker-compose.production.yml logs cloudflared
```

### DNS Record nicht erreichbar:

```bash
# DNS propagation prüfen
dig api.radiox.cloud

# Cloudflare DNS Status
cloudflared tunnel route dns list
```

### Service nicht erreichbar:

```bash
# API Gateway läuft?
docker ps | grep radiox-api-gateway

# Interne Verbindung testen
curl http://localhost:8000/health
```

## 🎯 **Best Practices**

1. **Environment Separation**: Verschiedene Tunnels für dev/staging/prod
2. **Monitoring**: Cloudflare Analytics für Traffic-Überwachung
3. **Security**: WAF Rules bei hohem Traffic aktivieren
4. **Backup**: Tunnel-Credentials sicher aufbewahren

## 🔗 **Nützliche Links**

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Docker Integration](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/docker/)
- [Zero Trust Dashboard](https://dash.teams.cloudflare.com/)

---

**🎉 Nach dem Setup hast du eine professionelle, sichere API unter `https://api.radiox.cloud` - ohne einen einzigen offenen Port!** 🚀 