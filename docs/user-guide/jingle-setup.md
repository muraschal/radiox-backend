# 🎵 Jingle Configuration & Multi-Format Setup

**Professional jingle integration with multi-format support and ultra-quiet background mixing**

---

## 🚀 Quick Setup

```bash
# 1. Create jingles directory
mkdir jingles

# 2. Add your jingle files (any format)
cp your-jingle.mp3 jingles/
cp high-quality.flac jingles/
cp professional.wav jingles/
cp broadcast.ogg jingles/

# 3. Test with RadioX
python main.py --news-count 1
```

## 🎼 Supported Formats

RadioX supports all major audio formats with intelligent selection:

| Format | Quality | Compatibility | Recommendation |
|--------|---------|---------------|----------------|
| **FLAC** | ⭐⭐⭐⭐⭐ | Good | Best for studio masters |
| **WAV** | ⭐⭐⭐⭐⭐ | Excellent | Perfect for broadcast |
| **MP3** | ⭐⭐⭐⭐ | Universal | Great for compatibility |
| **OGG** | ⭐⭐⭐⭐ | Good | Efficient compression |

## 🎯 Professional Audio Timeline

RadioX uses a sophisticated 3-phase jingle system:

```
PHASE 1 - INTRO (0-12s):
┌─────────────────────────────────────┐
│ 0-3s:  Pure 100% jingle (powerful) │
│ 3-13s: Ultra-smooth fade 100%→10%  │
└─────────────────────────────────────┘

PHASE 2 - BACKGROUND (12s-End-7s):
┌─────────────────────────────────────┐
│ Speech: 100% volume (dominant)     │
│ Jingle: 10% volume (subtle backing)│
└─────────────────────────────────────┘

PHASE 3 - OUTRO (Last 7s):
┌─────────────────────────────────────┐
│ Ultra-smooth ramp-up 10%→100%      │
│ Cinematic ending with full power   │
└─────────────────────────────────────┘
```

## 📏 Duration Requirements

### Automatic Duration Analysis
RadioX automatically analyzes jingle duration and selects the best fit:

```python
# Required duration calculation
total_needed = speech_duration + intro(12s) + outro(17s) + buffer(5s)

# Intelligent selection
if jingle_duration >= total_needed:
    selected_jingles.append(jingle)
else:
    # Use longest available as fallback
```

### Recommended Durations
- **Minimum:** 60 seconds
- **Optimal:** 120-300 seconds  
- **Maximum:** No limit (will be trimmed automatically)

## 🔧 Advanced Configuration

### Custom Jingle Directory
```python
# In audio_generation_service.py
jingle_dir = Path("custom/jingle/path")
```

### Volume Levels
```python
# Current professional settings
INTRO_VOLUME = 1.0      # 100% powerful intro
BACKGROUND_VOLUME = 0.1  # 10% subtle backing  
OUTRO_VOLUME = 1.0      # 100% cinematic ending
SPEECH_VOLUME = 1.0     # 100% speech dominance
```

### Fade Timing
```python
# Cinematic transition timing
pure_intro_duration = 3.0     # 3s pure jingle
intro_fade_duration = 10.0    # 10s smooth fade
outro_fade_duration = 7.0     # 7s outro ramp-up
```

## 🎚️ Audio Engineering Details

### FFmpeg Filter Chain
```bash
# 3-phase system using asplit
[jingle]asplit=3[intro][background][outro]

# Phase 1: Intro with fadeout
[intro]volume=1.0,afade=t=out:st=3:d=10[jingle_intro]

# Phase 2: Background at 10%  
[background]volume=0.1,afade=t=in:st=3:d=10,afade=t=out:st=X:d=7[jingle_bg]

# Phase 3: Outro with fadein
[outro]volume=1.0,afade=t=in:st=Y:d=7[jingle_outro]

# Final mix with speech
[jingle_intro][jingle_bg][jingle_outro]amix=inputs=3[jingle_mixed]
[jingle_mixed][speech]amix=inputs=2[final]
```

### Quality Settings
- **Sample Rate:** 44.1kHz (broadcast standard)
- **Bit Depth:** 16-bit minimum, 24-bit preferred
- **Format:** MP3 320kbps output
- **Dynamic Range:** Full range preserved

## 📂 Organization Best Practices

### Directory Structure
```
jingles/
├── morning/
│   ├── energetic_intro_01.flac
│   └── news_theme_bright.wav
├── afternoon/
│   ├── smooth_jazz_news.mp3
│   └── corporate_professional.ogg
├── evening/
│   ├── sophisticated_news.flac
│   └── prime_time_theme.wav
└── night/
    ├── ambient_late_news.mp3
    └── minimal_electronic.ogg
```

### Naming Conventions
```
[mood]_[type]_[variation].[format]
Examples:
- energetic_intro_01.flac
- smooth_background_news.wav  
- dramatic_outro_prime.mp3
- ambient_late_night.ogg
```

## 🎯 Optimization Tips

### 1. **Multiple Versions**
```bash
# Provide multiple lengths for same jingle
jingles/
├── news_theme_60s.mp3    # Short shows
├── news_theme_120s.mp3   # Standard shows
└── news_theme_300s.mp3   # Extended shows
```

### 2. **Quality Hierarchy**
```python
# RadioX selection priority
1. FLAC (highest quality)
2. WAV (excellent compatibility)  
3. MP3 (universal support)
4. OGG (efficient compression)
```

### 3. **Performance Optimization**
- Pre-normalize all jingles to same loudness
- Use consistent sample rates (44.1kHz)
- Keep jingles under 10MB for faster loading

## 🔍 Troubleshooting

### Common Issues

**❌ "No suitable jingle found"**
```bash
# Solution: Check jingle duration vs speech length
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 jingles/your-jingle.mp3
```

**❌ "Jingle too quiet/loud"**
```python
# Adjust volume levels in audio_generation_service.py
BACKGROUND_VOLUME = 0.05  # Lower for quieter
BACKGROUND_VOLUME = 0.15  # Higher for more presence
```

**❌ "Poor audio quality"**
```bash
# Use higher quality source files
# FLAC > WAV > MP3 320kbps > MP3 128kbps
```

### Debug Commands
```bash
# List available jingles with info
ls -la jingles/

# Check jingle duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 jingles/*.mp3

# Test audio generation
python main.py --news-count 1 --test
```

## 📈 Professional Results

### Audio Characteristics
- **Speech Clarity:** 100% dominance during content
- **Background Presence:** Subtle 10% jingle atmosphere  
- **Transition Quality:** Ultra-smooth cinematic fades
- **Dynamic Range:** Full broadcast-standard range
- **Compatibility:** Universal MP3 output

### Success Metrics
- ✅ **Zero Audio Clipping:** Professional limiting
- ✅ **Seamless Transitions:** Inaudible phase changes
- ✅ **Speech Intelligibility:** 100% clarity maintained
- ✅ **Musical Cohesion:** Jingle enhances, never distracts
- ✅ **Broadcast Ready:** Professional radio standards

---

**🎵 Ready to create broadcast-quality shows?** → Place your jingles in `/jingles/` and run `python main.py` 