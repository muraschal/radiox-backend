# Cloudflare Setup für RadioX Backend

Schritt-für-Schritt Anleitung zur Konfiguration von Cloudflare für **api.radiox.cloud** Zugriff.

## 📋 **Prerequisites**

- ✅ Domain `radiox.cloud` (bereits im Besitz)
- ✅ Cloudflare Account (kostenlos)
- ✅ Domain Nameserver-Zugriff
- ✅ Terminal-Zugang für cloudflared

## 🚀 **Step 1: Cloudflare Account & Domain Setup**

### 1.1 Cloudflare Account erstellen

1. Gehe zu [cloudflare.com](https://cloudflare.com) 
2. **"Sign Up"** für kostenlosen Account
3. Email bestätigen

### 1.2 Domain zu Cloudflare hinzufügen

1. **Dashboard** → **"Add Site"**
2. Domain eingeben: `radiox.cloud`
3. **Plan auswählen**: **"Free"** (völlig ausreichend!)
4. **DNS Records scannen** - Cloudflare erkennt automatisch deine bestehenden Records

### 1.3 Nameservers ändern (WICHTIG!)

Cloudflare gibt dir **2 neue Nameserver**. Diese musst du bei deinem **Domain-Provider** (wo du radiox.cloud gekauft hast) eintragen:

**Beispiel:**
```
aria.ns.cloudflare.com
beau.ns.cloudflare.com
```

**Wo ändern:**
- **Namecheap**: Domain List → Manage → Nameservers
- **GoDaddy**: DNS Management → Nameservers  
- **Andere**: Suche nach "Nameserver" oder "DNS" Settings

⚠️ **Wichtig**: Das kann **24-48h dauern** bis es propagiert ist!

### 1.4 Domain-Status prüfen

Warte bis Cloudflare **"Active"** anzeigt:
- Dashboard → radiox.cloud → Status sollte **"Active"** sein (nicht "Pending")

## 🚀 **Step 2: Cloudflare Zero Trust Setup**

### 2.1 Zero Trust aktivieren

1. **Cloudflare Dashboard** → **"Zero Trust"** (linke Sidebar)
2. **Team Name eingeben**: z.B. `radiox-team`
3. **Plan auswählen**: **"Free"** (50 Benutzer kostenlos)

### 2.2 Cloudflare Login (Terminal)

Jetzt erst kannst du dich authentifizieren:

```bash
# Cloudflare Login - Browser öffnet sich automatisch
cloudflared tunnel login
```

Das öffnet deinen Browser und du musst:
1. **Bei Cloudflare einloggen**
2. **Domain autorisieren**: `radiox.cloud` auswählen
3. **"Authorize"** klicken

✅ **Erfolgreich wenn**: `You have successfully logged in` erscheint

## 🚀 **Step 3: Tunnel erstellen**

```bash
# Jetzt funktioniert das Setup-Script:
make setup-tunnel
```

**Oder manuell:**

```bash
# 1. Tunnel erstellen
cloudflared tunnel create radiox-backend

# 2. DNS Record erstellen  
cloudflared tunnel route dns radiox-backend api.radiox.cloud

# 3. Token für Docker generieren
cloudflared tunnel token radiox-backend
```

## 🔧 **Step 4: Environment Variable**

Das Token vom vorherigen Schritt in `.env` eintragen:

```bash
# .env hinzufügen:
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiYmM2ZjU0...sehr-langer-token
```

## ✅ **Verification Steps**

### DNS Check:
```bash
# Prüfen ob DNS Record existiert:
dig api.radiox.cloud

# Sollte eine Cloudflare IP zeigen (104.16.x.x oder 172.67.x.x)
```

### Tunnel Status:
```bash
# Alle deine Tunnels anzeigen:
cloudflared tunnel list

# Sollte "radiox-backend" mit Status "HEALTHY" zeigen
```

### Cloudflare Dashboard:
1. **Zero Trust Dashboard** → **Access** → **Tunnels**
2. Du solltest **"radiox-backend"** tunnel sehen
3. Status: **"HEALTHY"** mit grünem Punkt

## 🚨 **Häufige Probleme**

### "Domain not found" beim Login:
- ✅ Nameservers korrekt gesetzt?
- ✅ DNS Propagation abgewartet? (dig radiox.cloud)
- ✅ Domain Status "Active" in Cloudflare?

### "No zones" beim Tunnel erstellen:
- ✅ `cloudflared tunnel login` erfolgreich?
- ✅ Zero Trust aktiviert?
- ✅ radiox.cloud in "Authorized Domains"?

### Tunnel "UNHEALTHY":
- ✅ Docker Container läuft auf Port 8000?
- ✅ `curl localhost:8000/health` funktioniert?
- ✅ CLOUDFLARE_TUNNEL_TOKEN korrekt gesetzt?

## 🎯 **Nächste Schritte**

Nach erfolgreichem Setup:

```bash
# Production Deployment auf Proxmox:
LXC_IP=192.168.1.100 make deploy-proxmox

# Testen:
curl https://api.radiox.cloud/health
```

## 📞 **Support Resources**

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Zero Trust Dashboard](https://dash.teams.cloudflare.com/)
- [Community Forum](https://community.cloudflare.com/)

---

**🎉 Nach diesem Setup hast du eine professionelle, sichere API-Infrastruktur!** 🚀 