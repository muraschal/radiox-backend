# 🎙️ Professional Show Generation Guide v3.2

<div align="center">

![User Guide](https://img.shields.io/badge/guide-user-blue)
![Version](https://img.shields.io/badge/version-v3.2-brightgreen)
![Difficulty](https://img.shields.io/badge/difficulty-beginner-green)
![Time](https://img.shields.io/badge/time-15%20min-orange)

**🎭 Complete guide to professional AI radio production with enterprise features**

[🏠 Documentation](../) • [👤 User Guides](../README.md#-user-guides) • [🎤 Voice Config](voice-configuration.md) • [📡 API Reference](api-reference.md)

</div>

---

## ✨ What's New in v3.2

### **🌟 Revolutionary Features**
- 🎯 **Smart Content Diversität** - Automatic show-to-show variety via Supabase
- 📂 **Automatic Archive System** - Zero-maintenance timestamped folders
- 🎵 **Professional Audio Ramping** - 6-stage jingle mixing with 6% backing
- 🎭 **Multi-Voice Support** - Marcel, Jarvis, Lucy (weather), Brad (news)
- 🔄 **Unified Naming System** - Consistent `radiox_yymmdd_hhmm.*` files

---

## 🎯 Overview

RadioX v3.2 is an **enterprise-grade AI radio production system** that creates unique shows every time while automatically managing your content library.

### ✨ **Core Features**
- 🧠 **GPT-4 Intelligence** - Never repeats content thanks to Supabase tracking
- 🎙️ **Professional Voices** - Marcel, Jarvis, Lucy, Brad with dynamic assignment
- 📂 **Smart Archive System** - Old shows automatically organized
- 🎵 **Radio-Quality Audio** - 6% jingle backing during speech segments
- 🎨 **Complete Production** - MP3 + HTML dashboard + AI cover art

---

## 🚀 Quick Start

### **🎬 Generate Your First Professional Show**

```bash
# Quick news brief (1 article)
python main.py --news-count 1

# Standard production show (3 articles) 
python main.py --news-count 3

# Extended professional show (5 articles)
python main.py --news-count 5
```

**🎯 Result:** Professional radio show with:
- 📻 `outplay/radiox_yymmdd_hhmm.mp3` - Professional audio with 6% jingle backing
- 📊 `outplay/radiox_yymmdd_hhmm.html` - Responsive dashboard with audio player
- 🎨 `outplay/radiox_yymmdd_hhmm.png` - AI-generated cover art

---

## 🎯 Smart Content Diversität

### **🧠 How RadioX Guarantees Unique Shows**

RadioX v3.2 uses **Supabase show tracking** to ensure 100% content variety:

```python
# Automatic behind-the-scenes process:
last_show_context = get_last_show_context()  # Previous topics, sources, angles
gpt_instruction = create_diversity_instruction(last_show_context)
# Result: GPT-4 avoids repeating similar content
```

### **🎯 What Gets Tracked**
- **📰 News Sources** - Avoids same RSS feeds
- **🏷️ Topic Categories** - Prevents topic repetition  
- **📝 Discussion Angles** - Ensures fresh perspectives
- **🎭 Voice Dynamics** - Varies conversation styles

**Result:** Every show feels completely fresh and unique!

---

## 📂 Automatic Archive System

### **🗂️ Zero-Maintenance File Management**

RadioX automatically archives old shows when creating new ones:

```bash
outplay/
├── radiox_250609_1845.mp3    ← Current show
├── radiox_250609_1845.html   ← Current dashboard  
├── radiox_250609_1845.png    ← Current cover
└── archive/                  ← Automatic archiving
    ├── show_20250609_184000/ ← Previous show (timestamped)
    │   ├── radiox_250609_1840.mp3
    │   ├── radiox_250609_1840.html
    │   └── radiox_250609_1840.png
    └── show_20250609_183500/ ← Earlier show
        ├── radiox_250609_1835.mp3
        ├── radiox_250609_1835.html
        └── radiox_250609_1835.png
```

### **📂 Archive Management Commands**

```bash
# View archived shows
ls -la outplay/archive/

# Check archive size
du -sh outplay/archive/

# Find specific archived show
find outplay/archive/ -name "*1840*"
```

---

## 🎵 Professional Audio Engineering

### **🎚️ 6-Stage Intelligent Jingle Ramping**

RadioX v3.2 features **professional radio-quality audio mixing**:

```
📻 Professional Audio Timeline:

0-5s:     100% 🎵 Kraftvoller Jingle Intro
5-8s:     Smooth Fade 100% → 6%
8s-end:   6% 🎵 Subtle Professional Backing  ← Radio-quality sound
end+5s:   15% → 70% 🎵 Dramatic Buildup  
end+10s:  100% 🎵 Power Outro
final:    100% → 0% Epic Fadeout
```

**🎯 Key Feature:** During speech segments, jingle plays at **6% volume** - the perfect professional radio backing level!

---

## 🎭 Multi-Voice Professional Cast

### **🎤 Voice Assignment System**

RadioX v3.2 intelligently assigns voices based on content:

| 🎤 Voice | 🎭 Role | 📝 Characteristics | 🎯 Used For |
|----------|---------|-------------------|-------------|
| **Marcel** | Main Host | Enthusiastic, conversational, warm | Intros, discussions, audience connection |
| **Jarvis** | AI Assistant | Analytical, precise, informative | Technical content, analysis, facts |  
| **Lucy** | Weather Reporter | Sultry, warm, engaging | Weather reports, atmospheric content |
| **Brad** | News Anchor | Professional, authoritative, clear | Breaking news, serious topics |

### **🎭 Dynamic Voice Examples**

```bash
# Show with weather → Lucy automatically used
python main.py --news-count 3  # Includes weather → Lucy speaks

# News-heavy show → Brad for major stories
python main.py --news-count 5  # Brad handles breaking news

# Standard show → Marcel + Jarvis dialogue
python main.py --news-count 2  # Classic Marcel/Jarvis conversation
```

---

## 🎛️ Production Commands

### **📻 Quick Production**

```bash
# Quick news brief (perfect for testing)
python main.py --news-count 1

# Standard production show (3-4 news articles)
python main.py --news-count 3

# Extended professional show (5+ articles)
python main.py --news-count 5
```

### **🔧 Development & Testing**

```bash
# Data collection only (no processing)
python main.py --data-only

# Processing only (use existing data)
python main.py --processing-only

# System health check
python main.py --test

# Audio-only mode (skip cover generation)
python main.py --news-count 3 --no-audio
```

### **📊 Performance Monitoring**

```bash
# Verbose output with status indicators
python main.py --news-count 3 | grep "✅\|❌\|🎯"

# Check last show context (diversity system)
python -c "from src.services.utilities.content_logging_service import ContentLoggingService; import asyncio; asyncio.run(ContentLoggingService().get_last_show_context())"
```

---

## 📁 Professional Output Structure

### **🎵 Unified Naming System**

All files use consistent `radiox_yymmdd_hhmm.*` naming:

```bash
# Example: Show generated on June 9th, 2025 at 18:45
radiox_250609_1845.mp3     # Professional audio (4-6MB)
radiox_250609_1845.html    # Responsive dashboard with player
radiox_250609_1845.png     # AI-generated cover (1024x1024)
```

### **🎵 Audio Specifications**
- **Format:** MP3, 128kbps, stereo
- **Duration:** 3-8 minutes (content-dependent)  
- **Quality:** Professional radio-ready
- **Jingle:** 6% backing during speech, 100% intros/outros
- **Voices:** Multi-cast with dynamic assignment
- **Metadata:** Embedded cover art & show info

### **📊 Dashboard Features**
- **Responsive Design** - Tailwind CSS, mobile-friendly
- **Audio Player** - Built-in MP3 player with correct paths
- **Show Notes** - Complete transcript & news sources
- **Cover Display** - AI-generated artwork showcase
- **Archive Links** - Easy access to previous shows

---

## 🎭 Professional Show Examples

### **🌅 Quick Morning Brief**
```bash
python main.py --news-count 1
```
**Result:** 3-minute energetic show with 1 major news story, weather by Lucy, Marcel hosting

### **📰 Standard Production Show** 
```bash
python main.py --news-count 3
```
**Result:** 5-minute professional show with 3 news stories, Marcel/Jarvis dialogue, Brad for breaking news

### **📻 Extended Professional Show**
```bash
python main.py --news-count 5
```
**Result:** 7-minute comprehensive show with 5 stories, full voice cast, detailed discussions

### **🔧 Development Testing**
```bash
python main.py --news-count 2 --processing-only
```
**Result:** Fast generation using existing data, perfect for testing changes

---

## 🎯 Content Diversity in Action

### **🧠 How It Works**

1. **📊 Previous Show Analysis** - Supabase tracks last show content
2. **🎯 GPT-4 Instructions** - AI receives diversity constraints  
3. **📰 Smart Selection** - Different sources, angles, topics chosen
4. **✅ 100% Unique Content** - No repetition between shows

### **📈 Diversity Metrics**

Track your content variety:

```bash
# Check Supabase show history
python -c "
from src.services.utilities.content_logging_service import ContentLoggingService
import asyncio
context = asyncio.run(ContentLoggingService().get_last_show_context())
print(f'Last show topics: {context}')
"
```

---

## 🔧 Troubleshooting v3.2

### **❌ Common Issues**

| 🚨 Problem | 🔍 Cause | ✅ Solution |
|------------|----------|-------------|
| **Archive not working** | Permission issues | Check `outplay/` folder permissions |
| **Same content repeated** | Supabase connection | Verify `SUPABASE_URL` & `SUPABASE_KEY` |
| **Audio too quiet** | Jingle ramping issue | Check FFmpeg installation |
| **Files missing** | Archive moved files | Check `outplay/archive/` folders |
| **HTML player broken** | Path resolution | Regenerate with `--processing-only` |

### **🧪 Diagnostic Commands**

```bash
# Test archive system
python main.py --news-count 1  # Should move old files

# Test diversity system  
python main.py --news-count 2  # Generate two shows, compare content

# Test voice assignment
python main.py --news-count 3  # Should use multiple voices

# Test complete pipeline
python main.py --test
```

---

## 💡 Pro Tips for v3.2

### **🎯 Best Practices**

1. **🔄 Generate Regularly** - Daily shows maximize content diversity
2. **📂 Monitor Archives** - Check archive folder growth
3. **🎵 Listen for Quality** - Notice 6% jingle backing during speech
4. **🎭 Voice Variety** - Weather shows automatically use Lucy
5. **📊 Track Performance** - Use verbose output for monitoring

### **⚡ Professional Workflows**

```bash
# Daily production routine
python main.py --news-count 3

# Weekly content review
ls -la outplay/archive/show_*/

# Performance monitoring
python main.py --news-count 4 | grep "✅\|❌"

# Archive management (monthly)
du -sh outplay/archive/ && ls outplay/archive/
```

### **🚀 Advanced Usage**

```bash
# Batch testing (multiple shows)
for i in {1..3}; do
  python main.py --news-count 2
  sleep 60  # Wait between shows
done

# Custom data pipeline
python main.py --data-only      # Collect fresh data
python main.py --processing-only # Process with custom logic
```

---

## 📈 Performance Metrics

### **⚡ Generation Times (v3.2)**
- **🚀 Data Collection**: ~30 seconds
- **🎯 Content Processing**: ~45 seconds  
- **🔊 Audio Generation**: ~90 seconds
- **🎨 Cover Creation**: ~20 seconds
- **📊 Dashboard**: ~5 seconds
- **📂 Archive Management**: ~3 seconds

**Total:** ~3-4 minutes for complete professional show

### **📊 Quality Metrics**
- **🎯 Content Diversity**: 100% unique show-to-show
- **🎵 Audio Quality**: Professional radio-grade
- **📂 Archive Efficiency**: Zero maintenance required
- **🎭 Voice Variety**: 4-voice professional cast
- **📱 Dashboard**: Fully responsive design

---

## 🔗 Related Documentation

- **🎤 [Voice Configuration](voice-configuration.md)** - Setup Marcel, Jarvis, Lucy, Brad
- **🏗️ [Architecture](../developer-guide/architecture.md)** - Understand v3.2 system design  
- **🗄️ [Database Schema](../developer-guide/database-schema.md)** - Supabase integration details
- **🚀 [Production Deployment](../deployment/production.md)** - Enterprise setup

---

<div align="center">

**🎙️ Ready to create professional AI radio shows with guaranteed uniqueness!**

[🏠 Documentation](../) • [🎤 Voice Setup](voice-configuration.md) • [💬 Get Support](../README.md#-support)

**Start now:** `python main.py --news-count 3`

</div> 