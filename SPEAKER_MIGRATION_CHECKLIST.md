# Speaker Names Migration Checklist

## ✅ Completed
- [x] Created `speaker_registry.py` - Dynamic speaker loading from DB
- [x] Created `elevenlabs_models` table with quality tiers
- [x] Added `--voicequality low/mid/high` support
- [x] Added migration comments to critical files

## 🔄 In Progress
- [ ] Refactor `audio_generation_service.py` - Replace all hardcoded lists
- [ ] Refactor `content_processing_service.py` - Dynamic speaker arrays
- [ ] Refactor `broadcast_generation_service.py` - Remove MARCEL:/JARVIS: hardcoding

## 📋 Next Steps
1. **Phase 1**: Replace hardcoded speaker arrays with `get_valid_speakers()`
2. **Phase 2**: Replace default speaker assignments with `get_default_speaker()`
3. **Phase 3**: Implement async speaker loading in all services
4. **Phase 4**: Remove all hardcoded fallbacks

## 🎯 Benefits After Migration
- ✅ New speakers can be added via DB only
- ✅ No code changes needed for new voices
- ✅ Centralized speaker management
- ✅ Dynamic quality assignment per speaker
- ✅ Better scalability and maintainability

## 🧪 Test Strategy
```bash
# Test current system
python3 src/services/infrastructure/speaker_registry.py

# Test voice quality system  
python3 test_voice_quality.py

# Test full generation with new speakers
python3 main.py --voicequality mid --news-count 1
```

## 🔧 Migration Commands
```bash
# Create new speaker in DB
INSERT INTO voice_configurations (speaker_name, voice_name, description, voice_id, language, is_primary) 
VALUES ('new_speaker', 'Voice Name', 'Description', 'eleven_labs_id', 'multilingual', false);

# No code changes needed after migration! 🎉
```
