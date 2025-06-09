# 📚 RadioX Documentation

<div align="center">

![Documentation](https://img.shields.io/badge/docs-comprehensive-brightgreen)
![Version](https://img.shields.io/badge/version-v3.2-blue)
![Status](https://img.shields.io/badge/status-complete-success)

**🎙️ Professional AI Radio Production System Documentation**

[🏠 Main Project](../) • [🚀 Quick Start](#-quick-start) • [📖 All Guides](#-all-guides) • [💬 Support](#-support)

</div>

---

## 🎯 Quick Start

| 👤 **I am a...** | 🎯 **I want to...** | 📖 **Start here** |
|-------------------|---------------------|-------------------|
| **User** | Generate professional radio shows | [🎙️ Show Generation](user-guide/show-generation.md) |
| **User** | Configure Marcel, Jarvis, Lucy, Brad voices | [🎤 Voice Configuration](user-guide/voice-configuration.md) |
| **Developer** | Understand the enterprise architecture | [🏗️ Architecture](developer-guide/architecture.md) |
| **Developer** | Set up development environment | [🔧 Development](developer-guide/development.md) |
| **DevOps** | Deploy production system | [🏭 Production](deployment/production.md) |
| **DevOps** | Use containerized deployment | [🐳 Docker](deployment/docker.md) |

---

## 📖 All Guides

### 👥 **User Guides**
*Perfect for content creators, radio hosts, and production teams*

| 📋 Guide | ⏱️ Time | 🎯 Difficulty | 📝 Description |
|----------|---------|---------------|----------------|
| **[🎙️ Show Generation](user-guide/show-generation.md)** | 15 min | Beginner | Complete workflow with archiving & diversity |
| **[🎤 Voice Configuration](user-guide/voice-configuration.md)** | 10 min | Beginner | Marcel, Jarvis, Lucy, Brad voice management |
| **[📰 RSS Dashboard](user-guide/rss-dashboard.md)** | 10 min | Beginner | Professional news dashboard with filtering |
| **[📚 API Reference](user-guide/api-reference.md)** | 20 min | Intermediate | Complete API documentation |

### 👨‍💻 **Developer Guides**
*Essential for developers working with RadioX v3.2*

| 📋 Guide | ⏱️ Time | 🎯 Difficulty | 📝 Description |
|----------|---------|---------------|----------------|
| **[🏗️ Architecture](developer-guide/architecture.md)** | 25 min | Intermediate | Enterprise system design & microservices |
| **[🔧 Development](developer-guide/development.md)** | 30 min | Intermediate | Local development with new features |
| **[🔄 Migration v3.2](developer-guide/migration-v3.2.md)** | 15 min | Intermediate | Archive system & unified naming |
| **[📊 Data Collection](developer-guide/data-collection.md)** | 20 min | Intermediate | Enhanced data pipeline with Supabase |
| **[⚙️ Services](developer-guide/services.md)** | 25 min | Intermediate | Bitcoin, Weather & Content services |
| **[🗄️ Database Schema](developer-guide/database-schema.md)** | 20 min | Intermediate | Supabase schema with show tracking |
| **[🧪 Testing](developer-guide/testing.md)** | 15 min | Intermediate | Testing with archive & diversity features |
| **[🤝 Contributing](developer-guide/contributing.md)** | 10 min | Beginner | Contributing to v3.2 codebase |

### 🚀 **Deployment Guides**
*For production deployments and system administration*

| 📋 Guide | ⏱️ Time | 🎯 Difficulty | 📝 Description |
|----------|---------|---------------|----------------|
| **[🏭 Production](deployment/production.md)** | 45 min | Advanced | Enterprise production deployment |
| **[🐳 Docker](deployment/docker.md)** | 30 min | Intermediate | Containerized deployment with volumes |
| **[📊 Monitoring](deployment/monitoring.md)** | 25 min | Intermediate | Monitoring with archive management |

---

## 🌟 What's New in v3.2

### **✨ Revolutionary Features**

#### 🎯 **Smart Content Diversität**
- **Supabase Show Tracking** - Automatic previous show analysis
- **100% Unique Content** - GPT-4 avoids repeating topics/sources
- **Intelligent News Selection** - Context-aware article selection

#### 📂 **Automatic Archive System**
- **Zero-Maintenance Archiving** - Old shows moved to timestamped folders
- **Unified File Organization** - `radiox_yymmdd_hhmm.*` naming consistency
- **Archive Management** - Clean production environment

#### 🎵 **Professional Audio Engineering**
- **6-Stage Jingle Ramping** - 100% intro → 6% backing → epic outro
- **Enhanced Voice Pipeline** - Lucy weather, Brad news, dynamic assignment
- **Audio Player Integration** - Correct path mapping for dashboards

#### 🏗️ **Enterprise Architecture**
- **Microservices Design** - Modular, scalable components
- **Supabase Integration** - Enterprise database with show logging
- **Performance Optimization** - Parallel processing & efficient workflows

---

## 🎭 Features Overview

### **🎙️ Professional Show Generation**
- **Dynamic AI Conversations** - Marcel & Jarvis with contextual variety
- **Multi-Voice Support** - Lucy (sultry weather) & Brad (authoritative news)
- **Time-based Adaptation** - Morning energetic, evening relaxed styles
- **Content Diversity Engine** - Guaranteed unique shows via Supabase tracking

### **🔊 Hollywood-Quality Audio**
- **ElevenLabs V3 TTS** - Professional voice synthesis with emotions
- **Intelligent Audio Ramping** - 6% backing during speech, 100% outros
- **DALL-E 3 Cover Art** - AI-generated artwork per show
- **Complete Production Pipeline** - MP3 with metadata, HTML dashboard, PNG cover

### **📊 Enterprise Data Management**
- **25+ RSS Feeds** - Swiss & international sources with smart filtering
- **Live Data Integration** - Bitcoin prices, Zurich weather, breaking news
- **Supabase Backend** - Show tracking, content logging, analytics
- **Automatic Archive System** - Timestamped folder organization

### **🏗️ Professional Architecture**
- **Clean Microservices** - Modular, maintainable components
- **Unified Naming System** - Consistent `radiox_yymmdd_hhmm.*` files
- **Archive Management** - Automatic old show organization
- **Enterprise Database** - Supabase with comprehensive logging

---

## 🚀 Quick Commands

### **🎙️ Professional Show Generation**

```bash
# Quick news brief (1 article)
python main.py --news-count 1

# Standard production show (3 articles) 
python main.py --news-count 3

# Extended show (5 articles)
python main.py --news-count 5

# Data collection only
python main.py --data-only

# Processing with existing data
python main.py --processing-only
```

### **📂 Archive Management**

```bash
# View archived shows
ls -la outplay/archive/

# Show current files
ls -la outplay/radiox_*

# Archive stats
du -sh outplay/archive/
```

### **🧪 Testing & Validation**

```bash
# System health check
python main.py --test

# Quick generation test
python main.py --news-count 1

# Data collection test
python main.py --data-only

# Check Supabase integration
python cli/cli_master.py quick
```

### **🔧 Development & Debugging**

```bash
# Development with verbose output
python main.py --news-count 2 | grep "✅\|❌\|🎯"

# Audio-only generation (skip covers)
python main.py --news-count 3 --no-audio

# Check last show context
python -c "from src.services.utilities.content_logging_service import ContentLoggingService; import asyncio; asyncio.run(ContentLoggingService().get_last_show_context())"
```

---

## 📂 File Structure (v3.2)

### **🎵 Professional Output Structure**
```bash
outplay/
├── radiox_250609_1845.mp3    ← Current show (unified naming)
├── radiox_250609_1845.html   ← Dashboard with audio player
├── radiox_250609_1845.png    ← AI-generated cover art
└── archive/                  ← Automatic archiving
    ├── show_20250609_184000/ ← Timestamped archive folders
    │   ├── radiox_250609_1840.mp3
    │   ├── radiox_250609_1840.html
    │   └── radiox_250609_1840.png
    └── show_20250609_183500/
        ├── radiox_250609_1835.mp3
        ├── radiox_250609_1835.html
        └── radiox_250609_1835.png
```

### **🎵 Professional Audio Timeline**
```
📻 RadioX Professional Audio Engineering:

0-5s:     100% 🎵 Kraftvoller Jingle Intro
5-8s:     Smooth Fade 100% → 6%
8s-end:   6% 🎵 Subtle Professional Backing  ← Radio-quality sound
end+5s:   15% → 70% 🎵 Dramatic Buildup  
end+10s:  100% 🎵 Power Outro
final:    100% → 0% Epic Fadeout
```

---

## 📈 Documentation Stats

<div align="center">

| 📊 Metric | 📈 Value |
|-----------|----------|
| **Version** | v3.2 Professional |
| **Total Guides** | 15 comprehensive guides |
| **Architecture** | Enterprise microservices |
| **New Features** | Archive system, show diversity, unified naming |
| **Code Examples** | 400+ practical examples |
| **Audio Quality** | Professional 6-stage ramping |
| **Database** | Supabase enterprise integration |
| **Voices** | Marcel, Jarvis, Lucy, Brad |
| **Archive Management** | Automatic timestamped folders |
| **Show Diversity** | 100% unique content via AI tracking |

</div>

---

## 🔍 Find What You Need

### **🎯 By v3.2 Features**

| 🌟 **New Feature** | 📖 **Documentation** |
|--------------------|--------------------|
| Archive old shows automatically | [🎙️ Show Generation](user-guide/show-generation.md) |
| Generate unique content every show | [🎙️ Show Generation](user-guide/show-generation.md) |
| Professional 6% jingle backing | [🎤 Voice Configuration](user-guide/voice-configuration.md) |
| Lucy sultry weather reports | [🎤 Voice Configuration](user-guide/voice-configuration.md) |
| Unified naming system | [🏗️ Architecture](developer-guide/architecture.md) |
| Supabase show tracking | [🗄️ Database Schema](developer-guide/database-schema.md) |
| Enterprise deployment | [🏭 Production](deployment/production.md) |

### **🎯 By Use Case**

| 🎯 **I want to...** | 📖 **Guide** |
|---------------------|--------------|
| Create my first professional show | [🎙️ Show Generation](user-guide/show-generation.md) |
| Configure Marcel, Jarvis, Lucy, Brad | [🎤 Voice Configuration](user-guide/voice-configuration.md) |
| Understand the new architecture | [🏗️ Architecture](developer-guide/architecture.md) |
| Set up professional development | [🔧 Development](developer-guide/development.md) |
| Manage archived shows | [🎙️ Show Generation](user-guide/show-generation.md) |
| Deploy enterprise system | [🏭 Production](deployment/production.md) |

---

## 💡 Pro Tips for v3.2

### **🚀 For Content Creators**
1. **Start Fresh**: Each show is automatically unique thanks to Supabase tracking
2. **Professional Audio**: Listen for the 6% jingle backing during speech
3. **Archive Management**: Old shows automatically organized in timestamped folders
4. **Voice Variety**: Lucy for weather, Brad for news, Marcel for hosting

### **👨‍💻 For Developers**
1. **New Architecture**: Microservices with Supabase integration
2. **Testing**: Use `python main.py --test` for comprehensive checks
3. **Debugging**: Archive system logs show file movement operations
4. **Performance**: Parallel processing significantly reduces generation time

### **🚀 For Production**
1. **Enterprise Ready**: Supabase backend handles show tracking & analytics
2. **Zero Maintenance**: Archive system requires no manual intervention
3. **Scalable**: Microservices architecture supports high-volume production
4. **Monitoring**: Track show diversity and archive growth metrics

---

## 💬 Support

### **🆘 Getting Help with v3.2**

| 🎯 **Type** | 📍 **Where** | ⏱️ **Response Time** |
|-------------|--------------|----------------------|
| **Archive Issues** | [GitHub Issues](https://github.com/your-org/RadioX/issues) | 12-24 hours |
| **Audio Quality** | [GitHub Issues](https://github.com/your-org/RadioX/issues) | 24-48 hours |
| **Supabase Integration** | [GitHub Discussions](https://github.com/your-org/RadioX/discussions) | 24 hours |
| **Feature Questions** | [GitHub Discussions](https://github.com/your-org/RadioX/discussions) | 12 hours |

### **🤝 v3.2 Community**

- **💬 Discord #v3-2-features** - Real-time help with new features
- **🐦 Twitter @RadioXAI** - Updates and feature announcements  
- **📧 enterprise@radiox.ai** - Enterprise support and consulting
- **📱 Telegram RadioX_v32** - Community discussions

---

<div align="center">

**🎙️ Professional AI Radio Production - RadioX v3.2**

[🏠 Main Project](../) • [🎙️ Generate Your First Show](user-guide/show-generation.md) • [💬 Get Support](#-support)

**Ready to create professional radio shows?** → `python main.py --news-count 3`

</div> 