# RadioX - Professional AI Radio Station Generator

<div align="center">

![Release](https://img.shields.io/badge/release-v3.3.1-brightgreen)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![Audio](https://img.shields.io/badge/audio-professional-orange)

**🎙️ Enterprise-Grade AI Radio Production System with Ultra-Professional Audio Engineering**

[🚀 Quick Start](#-quick-start) • [📚 Features](#-features) • [🎭 Live Demo](#-live-demo) • [🏗️ Architecture](#-architecture)

</div>

---

## ✨ Revolutionary Features

### 🎙️ **Intelligent Show Generation**
- **GPT-4 Powered Scripts** - Natural Marcel & Jarvis dialogues
- **Smart Content Diversity** - Automatic show-to-show variety using Supabase tracking
- **Ultra-Professional Audio Mixing** - 3-phase jingle system with 10% subtle backing
- **Adaptive Voice Selection** - Lucy for weather, Brad for news, dynamic speaker assignment

### 🔊 **Professional Audio Production**  
- **ElevenLabs V3 TTS** - Hollywood-quality voice synthesis
- **Professional Jingle Engineering** - 100% intro → 10% backing → 100% outro (broadcast standard)
- **Multi-Format Jingle Support** - MP3, FLAC, WAV, OGG intelligent selection
- **Parallel Audio Generation** - High-performance segment processing
- **Professional Audio Engineering** - Advanced FFmpeg filtering with speech dominance

### 🎨 **Dynamic Visual Content**
- **DALL-E 3 Cover Art** - AI-generated cover images per show
- **Unified Naming System** - `radiox_yymmdd_hhmm.mp3/html/png` consistency
- **Automatic Archive System** - Old shows moved to timestamped archive folders
- **Tailwind Dashboard** - Modern, responsive show notes interface

### 📊 **Enterprise Data Management**
- **25+ RSS Feeds** - Real-time news from Switzerland & International sources
- **Supabase Integration** - Show tracking, content logging, diversity analytics
- **Smart Content Filtering** - Preset-based news selection with category weights
- **Live Data Integration** - Bitcoin prices, Zurich weather, breaking news

## 🚀 Quick Start

```bash
# 1. Clone & Setup Environment
git clone https://github.com/muraschal/radiox-backend.git
cd radiox-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure API Keys
cp env_template.txt .env
# Add: OPENAI_API_KEY, ELEVENLABS_API_KEY, SUPABASE_URL, SUPABASE_KEY

# 3. Add Jingles (Multiple Formats Supported)
mkdir jingles
# Add your jingle files: .mp3, .flac, .wav, or .ogg

# 4. Generate Your First Professional Show
python main.py --news-count 3

# 5. Access Your Show
# 📻 Audio: outplay/radiox_yymmdd_hhmm.mp3
# 📊 Dashboard: outplay/radiox_yymmdd_hhmm.html  
# 🎨 Cover: outplay/radiox_yymmdd_hhmm.png
```

**🎯 Result**: Professional radio show with ultra-quiet jingle mixing, cover art, and responsive dashboard!

## 🎭 Production Examples

```bash
# 🌅 Quick News Brief (1 article)
python main.py --news-count 1

# 📰 Standard Show (3-4 articles)  
python main.py --news-count 3

# 📻 Extended Show (full processing)
python main.py --news-count 5

# 🎨 Audio-Only Mode
python main.py --news-count 3 --no-audio

# 🗂️ Data Collection Only
python main.py --data-only
```

## 🏗️ Professional Architecture

### 📊 Database Schema

```mermaid
erDiagram
    show_presets ||--|| voice_configurations : "primary_speaker"
    show_presets ||--o| voice_configurations : "secondary_speaker"
    show_presets ||--o| voice_configurations : "weather_speaker"
    show_presets ||--o{ rss_feed_preferences : "uses"
    show_presets ||--o{ broadcast_scripts : "generates"
    broadcast_scripts ||--o{ used_article_titles : "tracks"
    
    show_presets {
        uuid id PK
        text preset_name UK "zurich, basel, etc."
        text display_name "Zürich Lokal"
        text description
        text city_focus "Zurich"
        jsonb news_categories "category weights"
        text primary_speaker FK "marcel, brad, jarvis"
        text secondary_speaker FK "optional co-host"
        text weather_speaker FK "lucy for weather"
        boolean is_duo_show "solo vs dialogue"
        text show_behavior "energetic, professional"
        integer duration_minutes "target length"
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    
    voice_configurations {
        uuid id PK
        text speaker_name UK "marcel, brad, jarvis, lucy"
        text voice_name "Display name"
        text voice_id "ElevenLabs ID"
        text language "en, de, de-CH"
        text model "eleven_turbo_v2"
        decimal stability "0.0-1.0"
        decimal similarity_boost "0.0-1.0"
        decimal style "0.0-1.0"
        boolean use_speaker_boost
        text description "Host, AI Assistant, etc."
        boolean is_active
        timestamptz created_at
    }
    
    rss_feed_preferences {
        uuid id PK
        text feed_name UK "SRF News, 20min"
        text feed_url "RSS endpoint"
        text category "politics, tech, sports"
        text language "de, en"
        text region "CH, international"
        integer priority "1-10 importance"
        integer fetch_frequency_minutes
        boolean is_active
        timestamptz last_fetched
        timestamptz created_at
    }
    
    broadcast_scripts {
        uuid id PK
        text session_id UK "session_YYMMDD_HHMMSS"
        text preset_name FK "references show_presets"
        text radio_script "Final generated script"
        jsonb selected_news "Chosen articles"
        jsonb generation_metadata "GPT params, etc."
        timestamptz created_at
        text status "generated, archived"
    }
    
    used_article_titles {
        uuid id PK
        text article_title UK "Exact title for dedup"
        text source_feed "Origin RSS feed"
        text article_url "Original link"
        timestamptz first_used_at "When first selected"
        timestamptz created_at
        integer usage_count "Times reused"
    }
```

### 🔄 System Workflow

```mermaid
sequenceDiagram
    participant User
    participant Main as "RadioX Master"
    participant Show as "Show Service"
    participant Data as "Data Collection"
    participant GPT as "Content Processing"
    participant Audio as "Audio Generation"
    participant Image as "Image Generation"
    participant DB as "Supabase Database"
    participant APIs as "External APIs<br/>(RSS, Weather, Crypto)"
    
    User->>Main: python main.py --news-count 3
    
    Note over Main: 📻 RadioX v3.3.1 Workflow Start
    
    Main->>Show: get_show_preset("zurich")
    Show->>DB: SELECT show configuration
    DB-->>Show: Show config + speaker voices
    Show-->>Main: Complete show configuration
    
    Main->>Data: collect_data(preset="zurich")
    Data->>APIs: Fetch RSS feeds (25+ sources)
    APIs-->>Data: News articles
    Data->>APIs: Get Zurich weather
    APIs-->>Data: Weather data
    Data->>APIs: Get Bitcoin prices
    APIs-->>Data: Crypto data
    Data-->>Main: Raw collected data
    
    Main->>GPT: process_data(raw_data, show_config)
    GPT->>DB: get_last_show_context()
    DB-->>GPT: Previous show data
    GPT->>DB: get_used_article_titles()
    DB-->>GPT: Used articles list
    GPT->>GPT: Filter & select unique content
    GPT->>APIs: Generate script with GPT-4
    APIs-->>GPT: Radio script (Marcel/Jarvis dialogue)
    GPT->>DB: log_selected_articles()
    GPT-->>Main: Processed script + metadata
    
    Main->>Image: generate_cover_art(script_content)
    Image->>APIs: DALL-E 3 cover generation
    APIs-->>Image: AI-generated cover image
    Image-->>Main: Cover image (.png)
    
    Main->>Audio: generate_audio_from_script(script, show_config)
    Audio->>Audio: Parse script into segments
    Audio->>Audio: Detect solo vs duo show
    
    loop For each script segment
        Audio->>APIs: ElevenLabs TTS (Marcel/Jarvis/Lucy)
        APIs-->>Audio: Audio segment
    end
    
    Audio->>Audio: Combine segments with FFmpeg
    Audio->>Audio: Add 3-phase jingle system<br/>(100% → 10% → 100%)
    Audio->>Image: Embed cover in MP3 metadata
    Audio-->>Main: Final audio (.mp3)
    
    Main->>Main: generate_dashboard(all_data)
    Main->>Main: Finalize files with timestamp
    Main->>Main: Archive previous shows
    
    Main-->>User: ✅ Complete show generated<br/>📻 Audio: radiox_YYMMDD_HHMM.mp3<br/>🎨 Cover: radiox_YYMMDD_HHMM.png<br/>📊 Dashboard: radiox_YYMMDD_HHMM.html
    
    Note over Main,DB: 🎯 Result: Broadcast-ready radio show<br/>with professional audio mixing
```

### 🏗️ Component Architecture

```
🎙️ RadioX v3.3.1 - Enterprise AI Radio Platform
│
├── 🎭 Content Intelligence Layer
│   ├── GPT-4 Script Generation with Show Context
│   ├── Smart Content Diversity (Supabase tracking)
│   ├── Preset-based News Filtering (Zurich focus)
│   └── Multi-language Support (EN/DE)
│
├── 🔊 Ultra-Professional Audio Engine  
│   ├── ElevenLabs V3 TTS (Marcel, Jarvis, Lucy, Brad)
│   ├── Ultra-Quiet Jingle Engineering (10% backing level)
│   ├── Multi-Format Jingle Support (MP3/FLAC/WAV/OGG)
│   ├── Parallel Segment Processing
│   ├── Advanced FFmpeg Audio Engineering
│   └── Broadcast-Standard Audio Mixing
│
├── 🎨 Visual Production Pipeline
│   ├── DALL-E 3 Cover Art Generation
│   ├── Tailwind CSS Dashboard Generation  
│   ├── Unified Naming System
│   └── Automatic Archive Management
│
├── 📊 Enterprise Data Platform
│   ├── Real-time RSS Collection (25+ feeds)
│   ├── Supabase Database Integration
│   ├── Bitcoin/Crypto Live Data
│   ├── Weather API Integration  
│   └── Content Logging & Analytics
│
└── 🌐 Web Interface & APIs
    ├── Responsive Show Notes Dashboard
    ├── Audio Player Integration
    ├── Archive System Management
    └── Performance Analytics
```

## 🚀 Advanced Features

### 🎯 **Intelligent Content Diversity**
```python
# Automatic show-to-show variety
last_show_context = get_last_show_context()  # From Supabase
gpt_prompt += create_diversity_instruction(last_show_context)
# Result: 100% unique content selection every show
```

### 🎵 **Professional Audio Timeline**
```
PHASE 1 - INTRO (0-12s):
0-3s:   100% Pure Jingle (powerful intro without speech)
3-13s:  Ultra-smooth fade 100% → 10% (cinematic transition)

PHASE 2 - BACKGROUND (12s-End-7s):
12s+:   Speech starts at 100% volume (dominant)
        Jingle continues at 10% subtle backing

PHASE 3 - OUTRO (Last 7s):
        Ultra-smooth ramp-up 10% → 100% over 7s
        Cinematic ending with full jingle power

Mix Ratio: Speech 100% : Jingle 10% (speech dominates)
```

### 🎵 **Multi-Format Jingle System**
```python
# Intelligent format detection and selection
supported_formats = ["*.mp3", "*.flac", "*.wav", "*.ogg"]
# Automatic duration analysis and best-fit selection
# FLAC preferred for highest quality, MP3 for compatibility
```

### 📂 **Automatic Archive System**
```bash
outplay/
├── radiox_250609_1845.mp3    ← Current show
├── radiox_250609_1845.html   ← Current dashboard  
├── radiox_250609_1845.png    ← Current cover
└── archive/
    └── show_20250609_184500/  ← Auto-archived previous shows
        ├── radiox_250609_1840.mp3
        ├── radiox_250609_1840.html
        └── radiox_250609_1840.png
```

### 🎭 **Dynamic Voice Assignment**
- **Marcel**: Host, main presenter, conversational
- **Jarvis**: AI assistant, technical content, precise
- **Lucy**: Weather reports (sultry, warm delivery)
- **Brad**: News anchor (professional, authoritative)

## 📊 Production Workflow

```mermaid
graph TD
    A[📊 Data Collection] --> B[🎯 Smart Filtering]
    B --> C[📚 Last Show Context]
    C --> D[🤖 GPT-4 Script Generation]
    D --> E[🔊 Ultra-Professional Audio Production]
    E --> F[🎵 Multi-Format Jingle Integration]
    F --> G[🎨 Cover Art & Dashboard]
    G --> H[📂 Archive Management]
    H --> I[✅ Broadcast Ready]
```

## 🔧 Development Setup

```bash
# Development Mode
python main.py --processing-only  # Skip data collection
python main.py --test            # Run system tests

# Performance Monitoring
python main.py --news-count 3 | grep "✅\|❌\|🎯"

# Archive Management  
ls -la outplay/archive/          # View archived shows

# Jingle Management
ls -la jingles/                  # View available jingles (all formats)
```

## 🎛️ Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--news-count` | 4 | Number of news articles to include |
| `--preset` | zurich | Show preset (zurich, basel, etc.) |
| `--no-audio` | false | Skip audio generation |
| `--data-only` | false | Only collect data |
| `--processing-only` | false | Only process existing data |
| `--test` | false | Run system tests |

## 📈 Performance Metrics

- **🚀 Audio Generation**: ~2-3 minutes for 4-news show
- **🎵 Jingle Integration**: Professional 10% backing with broadcast-standard mixing
- **🎨 Cover Creation**: ~30 seconds via DALL-E 3
- **📊 Dashboard**: Generated in <5 seconds with perfect audio synchronization
- **🔄 Content Diversity**: 100% unique show-to-show
- **📂 Archive**: Automatic, zero-maintenance
- **🎼 Multi-Format**: Supports MP3, FLAC, WAV, OGG jingles

## 🌟 What's New in v3.3.1

### ✨ **Audio Engineering Revolution**
- 🎵 **Professional Jingle Mixing** - 10% backing level for broadcast-professional sound
- 🎼 **Multi-Format Jingle Support** - MP3, FLAC, WAV, OGG intelligent selection
- 🔊 **Advanced FFmpeg Engineering** - 3-phase audio system with speech dominance
- ⚡ **Perfect Workflow Synchronization** - Dashboard always finds correct audio files
- 🌍 **English Codebase** - Complete translation for international development
- 🔧 **Runtime Stability** - Enhanced f-string formatting and deployment reliability

### 🔧 **Technical Improvements**  
- ⚡ **Parallel Processing** - High-performance audio generation
- 🛡️ **Error Resilience** - Graceful fallbacks and recovery
- 📈 **Performance Optimization** - Reduced generation times
- 🔄 **GPT-4 Integration** - Advanced prompt engineering
- 💾 **Supabase Integration** - Enterprise data management
- 🎚️ **Broadcast-Standard Audio** - Professional radio quality mixing

### 🎵 **Professional Audio Features**
```python
# Professional jingle engineering
3-Phase System: 100% → 10% → 100% (cinematic transitions)
Background Level: 10% subtle backing (broadcast standard)
Speech Volume: 100% with dynamic mixing
Mix Dominance: Speech 100% : Jingle 10%
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/developer-guide/contributing.md).

### 🚀 Quick Contribution Setup
```bash
git checkout -b feature/amazing-feature
# Make your changes
git commit -m 'Add amazing feature'  
git push origin feature/amazing-feature
# Open Pull Request
```

## 📚 Documentation

| 📖 Resource | 🎯 Audience | 📝 Content |
|-------------|-------------|-------------|
| **[🎙️ Show Generation Guide](docs/user-guide/show-generation.md)** | Users | Complete show creation workflow |
| **[🎤 Voice Configuration](docs/user-guide/voice-configuration.md)** | Users | Setup Marcel, Jarvis, Lucy, Brad voices |
| **[🎵 Jingle Configuration](docs/user-guide/jingle-setup.md)** | Users | Multi-format jingle setup & optimization |
| **[🏗️ System Architecture](docs/developer-guide/architecture.md)** | Developers | Technical system design |
| **[🔧 Development Setup](docs/developer-guide/development.md)** | Developers | Local development environment |
| **[🚀 Production Deployment](docs/deployment/production.md)** | DevOps | Production setup & scaling |

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - GPT-4 & DALL-E 3 AI Models
- **ElevenLabs** - V3 TTS Technology  
- **Supabase** - Enterprise Database Platform
- **Swiss Media Partners** - RSS Feed Sources
- **FFmpeg Community** - Professional audio engineering tools
- **Open Source Community** - Various libraries & tools

---

<div align="center">

**🎙️ Ultra-Professional AI Radio Production - Made with ❤️ by RadioX Team**

[📚 Documentation](docs/) • [🐛 Issues](https://github.com/muraschal/radiox-backend/issues) • [💡 Features](https://github.com/muraschal/radiox-backend/discussions)

**Ready to create your first broadcast-quality AI radio show?** → `python main.py --news-count 3`

</div>
