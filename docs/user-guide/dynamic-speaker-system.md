# Dynamic Speaker & Voice Quality System

## 🎯 Überblick

Das RadioX Dynamic Speaker System bietet eine vollständig konfigurierbare, datenbankbasierte Lösung für Speaker-Management und Voice Quality Control. Dieses System ersetzt alle hardcodierten Speaker-Namen und ermöglicht intelligente, show-spezifische Speaker-Zuweisungen.

## ✨ Neue Features

### 🎛️ Voice Quality System
- **`--voicequality low`** - Schnelle Generierung (75ms Latenz)
- **`--voicequality mid`** - Ausgewogene Qualität (**Standard**)
- **`--voicequality high`** - Hollywood-Qualität (800ms Latenz)

### 🎤 Dynamic Speaker Registry
- Alle Speaker werden dynamisch aus der Datenbank geladen
- Neue Speaker können ohne Code-Änderungen hinzugefügt werden
- Intelligente Alias-Unterstützung (`ai` → `jarvis`, `host` → Primary Speaker)

### 🎭 Show-Config-basierte Speaker-Zuweisung
- Explizite Kategorien-basierte Logik (`weather`, `news`, `sports`)
- Flexible Role-Assignments pro Show
- Vorhersagbares Verhalten ohne "magische" Auto-Zuweisungen

---

## 🚀 Quick Start

### Basic Usage
```bash
# Standard Show (mid quality)
python3 main.py --news-count 2

# High Quality Production
python3 main.py --voicequality high --news-count 3

# Fast Testing (low quality)
python3 main.py --voicequality low --news-count 1
```

### Voice Quality Vergleich
| Quality | Model | Latenz | Kosten | Use Case |
|---------|-------|--------|--------|----------|
| `low` | `eleven_flash_v2_5` | 75ms | 0.5x | Tests, Live-Shows |
| `mid` | `eleven_turbo_v2_5` | 275ms | 0.5x | **Standard Shows** |
| `high` | `eleven_multilingual_v2` | 800ms | 1.0x | Production, Podcasts |

---

## 🎤 Speaker Registry System

### Verfügbare Speaker
```bash
# Alle Speaker anzeigen
python3 src/services/infrastructure/speaker_registry.py
```

**Ausgabe:**
```
📊 Gefundene Sprecher: 4
  🎙️ marcel: Marcel (Main Host, energetic and passionate)
  🎙️ jarvis: Jarvis (AI Assistant, analytical and precise)
  🎙️ brad: Brad (News Anchor, professional and authoritative)
  🎙️ lucy: Lucy (Weather Reporter, sultry and atmospheric)
```

### Speaker Aliases
Das System unterstützt intelligente Aliases:

```python
# Basic Aliases
"marcel" → "marcel"
"jarvis" → "jarvis"
"brad" → "brad"
"lucy" → "lucy"

# Role-based Aliases
"host" → "marcel"        # Primary Speaker
"moderator" → "marcel"
"presenter" → "marcel"

# AI Aliases
"ai" → "jarvis"
"assistant" → "jarvis"
```

### Neue Speaker hinzufügen
```sql
-- Neuen Speaker in Datenbank einfügen
INSERT INTO voice_configurations (
    speaker_name, voice_name, description, voice_id, 
    language, is_primary, stability, similarity_boost, style
) VALUES (
    'sarah', 'Sarah', 'Tech News Anchor', 'eleven_labs_voice_id',
    'multilingual', false, 0.60, 0.80, 0.55
);
```

**Sofort verfügbar ohne Code-Änderungen!** 🎉

---

## 🎭 Show Configuration System

### Intelligente Speaker-Zuweisung

Das System verwendet **explizite Show-Konfiguration** statt automatischer Content-Detection für maximale Kontrolle und Vorhersagbarkeit.

#### Show Config Struktur
```json
{
  "primary_speaker": {
    "speaker_name": "marcel",
    "voice_name": "Marcel",
    "description": "Main Host"
  },
  "secondary_speaker": {
    "speaker_name": "jarvis",
    "voice_name": "Jarvis", 
    "description": "AI Assistant"
  },
  "weather_speaker": {
    "speaker_name": "lucy",
    "voice_name": "Lucy",
    "description": "Weather Reporter"
  },
  "categories": ["weather", "news", "sports"],
  "show_type": "morning_show",
  "duration_minutes": 5,
  "language": "german"
}
```

### Speaker Assignment Logic

#### Decision Tree:
```
1. Content Type erkannt
   ↓
2. Show Config → "weather" in categories?
   ❌ Nein → Primary Speaker
   ✅ Ja ↓
   
3. Weather Speaker definiert?
   ❌ Nein → Primary Speaker
   ✅ Ja ↓
   
4. Content ist Weather-related?
   ❌ Nein → Normal Speaker Processing
   ✅ Ja → Weather Speaker! 🎯
```

### Beispiel-Szenarien

#### Szenario 1: Separater Weather Speaker
```json
{
  "primary_speaker": {"speaker_name": "marcel"},
  "weather_speaker": {"speaker_name": "lucy"},
  "categories": ["weather", "news"]
}
```
**Ergebnis:**
- Weather Content → Lucy
- News Content → Marcel

#### Szenario 2: Primary ist auch Weather Speaker
```json
{
  "primary_speaker": {"speaker_name": "marcel"},
  "weather_speaker": {"speaker_name": "marcel"},
  "categories": ["weather", "news"]
}
```
**Ergebnis:**
- Weather Content → Marcel
- News Content → Marcel

#### Szenario 3: Weather deaktiviert
```json
{
  "primary_speaker": {"speaker_name": "marcel"},
  "weather_speaker": {"speaker_name": "lucy"},
  "categories": ["news", "sports"]  // Kein "weather"
}
```
**Ergebnis:**
- Weather Content → Marcel (Kategorie nicht aktiv)
- News Content → Marcel

---

## 🎛️ ElevenLabs Models & Quality Tiers

### Verfügbare Modelle

Das System lädt automatisch alle ElevenLabs Modelle mit Qualitätsstufen:

```bash
# Modelle anzeigen
python3 list_elevenlabs_models.py
```

### Quality Tier Mapping

| Tier | Model | Features | Best For |
|------|-------|----------|----------|
| **Low** | `eleven_flash_v2_5` | Ultra-fast, 32 languages | Live shows, testing |
| **Mid** | `eleven_turbo_v2_5` | Balanced, 32 languages | **Standard production** |
| **High** | `eleven_multilingual_v2` | Best quality, style control | Podcasts, final production |

### Model Features

#### Low Quality (`eleven_flash_v2_5`)
- ⚡ **75ms Latenz** (ultraschnell)
- 💰 **0.5x Kosten** (50% günstiger)
- 🌍 **32 Sprachen**
- 🎛️ **Speaker Boost: OFF** (für Geschwindigkeit)

#### Mid Quality (`eleven_turbo_v2_5`) **[DEFAULT]**
- ⚡ **275ms Latenz** (ausgewogen)
- 💰 **0.5x Kosten** (50% günstiger)
- 🌍 **32 Sprachen**
- 🎛️ **Speaker Boost: OFF**

#### High Quality (`eleven_multilingual_v2`)
- ⚡ **800ms Latenz** (beste Qualität)
- 💰 **1.0x Kosten** (Standard-Preis)
- 🌍 **29 Sprachen**
- 🎛️ **Speaker Boost: ON** + Style Control

---

## 🔧 Migration von hardcodierten Namen

### Vor dem Refactoring
```python
# ❌ Hardcodierte Listen
valid_speakers = ['brad', 'marcel', 'lucy']

# ❌ Hardcodierte Defaults  
return "marcel"

# ❌ Hardcodierte Mappings
speaker_map = {
    "marcel": "marcel",
    "jarvis": "jarvis",
    "news": "brad",      # Automatische Zuweisung
    "weather": "lucy"    # Automatische Zuweisung
}
```

### Nach dem Refactoring
```python
# ✅ Dynamisch aus DB
valid_speakers = await get_valid_speakers()

# ✅ Dynamischer Default
return await get_default_speaker_name()

# ✅ Intelligente Show-Config-basierte Zuweisung
if self._should_use_weather_speaker_for_content(text):
    weather_speaker = self._get_configured_weather_speaker()
    if weather_speaker:
        return weather_speaker
```

### Migration Checklist

- [x] ✅ Speaker Registry System implementiert
- [x] ✅ Voice Quality System (`--voicequality`) implementiert  
- [x] ✅ ElevenLabs Models Tabelle erstellt
- [x] ✅ Intelligente Show-Config-Logik implementiert
- [x] ✅ Automatische Content-Detection entfernt
- [x] ✅ Hardcodierte Speaker-Namen durch dynamische Referenzen ersetzt

---

## 🧪 Testing & Debugging

### Speaker Registry testen
```bash
python3 src/services/infrastructure/speaker_registry.py
```

### Voice Quality testen
```bash
python3 test_voice_quality.py
```

### Speaker Assignment testen
```bash
python3 test_intelligent_speaker_assignment.py
```

### Vollständige Show generieren
```bash
# Test verschiedene Quality-Stufen
python3 main.py --voicequality low --news-count 1
python3 main.py --voicequality mid --news-count 2  
python3 main.py --voicequality high --news-count 3
```

---

## 📊 Performance & Kosten

### Quality vs. Performance
```
Low Quality:   75ms  | 0.5x Kosten | Ideal für Live
Mid Quality:   275ms | 0.5x Kosten | Standard Production  
High Quality:  800ms | 1.0x Kosten | Final Production
```

### Empfohlene Verwendung
- **Live Shows** → `--voicequality low`
- **Standard Shows** → `--voicequality mid` (Default)
- **Podcasts/Production** → `--voicequality high`

---

## 🎯 Best Practices

### 1. Show Configuration
- Definiere explizit alle benötigten Speaker
- Verwende `categories` Array für aktive Content-Typen
- Setze `weather_speaker` nur wenn Weather-Content geplant ist

### 2. Voice Quality
- Verwende `mid` als Standard für die meisten Shows
- Nutze `low` für schnelle Tests und Live-Shows
- Verwende `high` nur für finale Produktionen

### 3. Speaker Management
- Neue Speaker via DB hinzufügen, nicht via Code
- Nutze aussagekräftige `description` Felder
- Teste neue Speaker mit verschiedenen Quality-Stufen

### 4. Script Writing
- Verwende explizite Speaker-Tags: `MARCEL:`, `JARVIS:`, etc.
- Vermeide Auto-Assignment durch explizite Angaben
- Nutze Show Config für Role-based Assignments

---

## 🔧 Troubleshooting

### Häufige Probleme

#### Speaker nicht gefunden
```bash
# Prüfe verfügbare Speaker
python3 src/services/infrastructure/speaker_registry.py

# Prüfe Voice Configurations in DB
SELECT speaker_name FROM voice_configurations WHERE is_active = true;
```

#### Voice Quality funktioniert nicht
```bash
# Prüfe ElevenLabs Models
SELECT model_id, quality_tier FROM elevenlabs_models WHERE is_active = true;

# Test Voice Quality System
python3 test_voice_quality.py
```

#### Show Config Probleme
```bash
# Test Speaker Assignment Logic
python3 test_intelligent_speaker_assignment.py
```

---

## 🚀 Zukunftserweiterungen

### Geplante Features
- **Explizite Content Tags** → `[weather]`, `[news]` statt Content-Detection
- **Multi-Language Speaker Support** → Speaker pro Sprache
- **Real-time Speaker Switching** → Dynamic mid-show changes
- **Voice Cloning Integration** → Custom Speaker aus Audio-Samples

### Erweiterbare Struktur
Das System ist designed für einfache Erweiterungen:
- Neue Speaker → Nur DB INSERT
- Neue Quality Tiers → ElevenLabs Models Tabelle
- Neue Roles → Show Config erweitern
- Neue Features → Speaker Registry erweitern

---

*Erstellt: Dezember 2024 | Version: 1.0 | RadioX Dynamic Speaker System* 