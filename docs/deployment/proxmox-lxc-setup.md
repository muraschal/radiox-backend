# Proxmox LXC Container Setup für RadioX Backend

Schritt-für-Schritt Anleitung zur Erstellung eines LXC Containers auf Proxmox für RadioX Backend mit Docker.

## 🎯 **Container Spezifikationen**

| Spec | Empfohlen | Warum |
|------|-----------|-------|
| **OS** | Ubuntu 22.04 LTS | Docker Support + LTS |
| **CPU** | 4 Cores | 8 Microservices + Compile |
| **RAM** | 8 GB | GPT-4 + Audio Processing |
| **Storage** | 50 GB | Audio Files + Logs |
| **Network** | DHCP oder Static IP | Für Cloudflare Tunnel |

## 🚀 **Step 1: LXC Container erstellen**

### 1.1 Proxmox Web Interface

1. **Proxmox Web Interface öffnen**: `https://192.168.1.103:8006`
2. **Node auswählen**: `PVE-3` (linke Sidebar)
3. **"Create CT" Button** (oben rechts)

### 1.2 Container Konfiguration

**📋 General Tab:**
```
Node: PVE-3
CT ID: 200 (oder nächste freie ID)
Hostname: radiox-backend
Resource Pool: (leer lassen)
Password: [Sicheres Password setzen]
Confirm password: [Wiederholen]
SSH public key: [Optional - für Key-based Auth]
```

**💿 Template Tab:**
```
Storage: local
Template: ubuntu-22.04-standard_22.04-1_amd64.tar.zst
(Falls nicht vorhanden: "Templates" → Download)
```

**💾 Disks Tab:**
```
Storage: local-lvm (oder dein bevorzugter Storage)
Disk size (GiB): 50
```

**🔧 CPU Tab:**
```
Cores: 4
CPU limit: [leer lassen]
CPU units: 1024
```

**🧠 Memory Tab:**
```
Memory (MiB): 8192 (= 8 GB)
Swap (MiB): 2048 (= 2 GB)
```

**🌐 Network Tab:**
```
Bridge: vmbr0
VLAN Tag: [leer lassen]
Rate limit: [leer lassen]  
Firewall: ✅ (aktiviert)
IPv4: DHCP (oder static mit 192.168.1.xxx)
IPv6: DHCP (oder deaktiviert)
```

**🔒 DNS Tab:**
```
Use host settings: ✅ (aktiviert)
```

**✅ Confirm Tab:**
- Alle Settings prüfen
- **"Finish"** klicken

## 🚀 **Step 2: Container starten & konfigurieren**

### 2.1 Container starten

1. **Container auswählen** (ID 200 in der Liste)
2. **"Start" Button** klicken
3. **"Console" Tab** öffnen für Terminal-Zugang

### 2.2 Initial Setup (im LXC Console)

```bash
# 1. System updaten
apt update && apt upgrade -y

# 2. Essential packages
apt install -y curl wget unzip git nano htop

# 3. Docker installieren
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 4. Docker Compose installieren
apt install -y docker-compose

# 5. Docker ohne sudo (optional)
usermod -aG docker root

# 6. Docker starten & aktivieren
systemctl start docker
systemctl enable docker

# 7. Test Docker Installation
docker --version
docker-compose --version
```

### 2.3 Network & SSH Setup

```bash
# IP-Adresse notieren:
ip addr show

# SSH Server aktivieren (falls gewünscht):
apt install -y openssh-server
systemctl enable ssh
systemctl start ssh

# Firewall konfigurieren (optional):
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable
```

## 🔧 **Step 3: RadioX Backend Deployment**

### 3.1 Deployment Directory erstellen

```bash
# Im LXC Container:
mkdir -p /opt/radiox-backend
cd /opt/radiox-backend
```

### 3.2 Von deinem Laptop deployen

```bash
# Auf deinem Mac:
LXC_IP=192.168.1.xxx make deploy-proxmox

# Dabei wird automatisch:
# - Build aller Docker Images
# - Upload zum LXC Container  
# - Docker Compose Start
# - Health Check über https://api.radiox.cloud
```

## 📊 **Step 4: Monitoring & Management**

### 4.1 Proxmox Monitoring

- **Proxmox Dashboard**: CPU/RAM/Network Usage
- **Container Console**: Direkter Terminal-Zugang
- **Log Viewer**: Container-spezifische Logs

### 4.2 Docker Monitoring (im LXC)

```bash
# Service Status
docker-compose -f docker-compose.production.yml ps

# Logs anzeigen
docker-compose -f docker-compose.production.yml logs -f

# Resource Usage
docker stats

# Health Check
curl http://localhost:8000/health
```

## 🚨 **Troubleshooting**

### Container startet nicht:
- **RAM Check**: 8GB verfügbar auf PVE-3?
- **Storage Check**: 50GB verfügbar?
- **Network Check**: Bridge konfiguriert?

### Docker Installation Fehler:
```bash
# Container neustarten:
# Proxmox: Container auswählen → Shutdown → Start

# Docker neu installieren:
apt remove docker docker-engine docker.io containerd runc
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

### Network Probleme:
```bash
# IP-Konfiguration prüfen:
ip addr show
ping 8.8.8.8
ping google.com

# DNS prüfen:
cat /etc/resolv.conf
```

## 🎯 **Nächste Schritte**

Nach erfolgreichem LXC Setup:

```bash
# Deployment vom Mac:
LXC_IP=192.168.1.xxx make deploy-production

# API Test:
curl https://api.radiox.cloud/health
```

## 📞 **Support Resources**

- [Proxmox LXC Documentation](https://pve.proxmox.com/wiki/Linux_Container)
- [Docker in LXC Guide](https://pve.proxmox.com/wiki/Docker)
- [LXC vs VM Comparison](https://pve.proxmox.com/wiki/Container_and_VM_comparison)

---

**🎉 Nach diesem Setup hast du einen production-ready LXC Container für RadioX Backend!** 🚀 