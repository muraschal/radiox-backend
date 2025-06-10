# 🌐 RadioX Web Interface

**Live Website:** [radiox.rapold.io](https://radiox.rapold.io)

## 📂 Inhalt

- **`index.html`** - Intelligente Landing Page mit Auto-Redirect
- **`shows.json`** - Dynamische Show-Liste (automatisch generiert)
- **`radiox_*.html/mp3/png`** - Die neuesten 10 RadioX Shows

## 🔄 Synchronisation

```bash
# Synchronisiere neueste Shows von outplay/ zu web/
python sync_web_shows.py
```

**Was passiert:**
- ✅ Kopiert die 10 neuesten Shows von `outplay/` 
- ✅ Generiert `shows.json` für die Website
- ✅ Optimiert für GitHub + Vercel Deployment
- ✅ Auto-Cleanup alter Shows

## 🚀 Deployment

1. **Automatisch:** Bei jedem Git Push zu `main`
2. **Manuell:** `vercel deploy` im Projekt-Root

## 🎯 Features

- **Auto-Redirect** - Leitet automatisch zur neuesten Show weiter
- **Show-Browser** - Übersicht aller verfügbaren Shows  
- **Responsive Design** - Funktioniert auf allen Geräten
- **Fast Loading** - Optimierte Vercel CDN Integration

---

**🎙️ Made with ❤️ by RadioX Team** 