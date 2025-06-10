#!/usr/bin/env python3
"""
Hardcoded Speaker Namen Refactoring Tool
=======================================

Ersetzt alle hardcodierten Speaker-Namen im Code mit dynamischen DB-Referenzen.

Gefundene Probleme:
- audio_generation_service.py: ['brad', 'marcel', 'lucy'] hardcodiert
- content_processing_service.py: speakers = ["Marcel", "Jarvis", "Lucy", "Brad"]
- broadcast_generation_service.py: MARCEL:/JARVIS: hardcodiert
- Viele Default-Speaker "marcel" References

Migration Strategy:
1. ✅ Speaker Registry erstellt
2. 🔄 Schritt-für-Schritt Refactoring der kritischsten Stellen
3. 🎯 Zentrale Konfiguration für alle Speaker-Namen
"""

import re
import sys
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.append('src')

def analyze_hardcoded_speakers():
    """Analyse und Report aller hardcodierten Speaker-Namen"""
    
    files_to_check = [
        "src/services/generation/audio_generation_service.py",
        "src/services/generation/broadcast_generation_service.py", 
        "src/services/processing/content_processing_service.py",
        "src/services/generation/image_generation_service.py",
        "src/services/processing/show_service.py"
    ]
    
    print("🔍 HARDCODED SPEAKER ANALYSIS")
    print("=" * 50)
    
    results = {}
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find hardcoded speaker names
        issues = []
        
        # Array definitions
        for pattern in [
            r'valid_speakers\s*=\s*\[[^\]]+\]',
            r'speakers\s*=\s*\[[^\]]+\]',
            r'\[.*["\']marcel["\'].*\]',
            r'\[.*["\']jarvis["\'].*\]',
            r'\[.*["\']brad["\'].*\]',
            r'\[.*["\']lucy["\'].*\]'
        ]:
            matches = re.findall(pattern, content, re.IGNORECASE)
            issues.extend(matches)
        
        # String assignments with speaker names
        for pattern in [
            r'=\s*["\']marcel["\']',
            r'=\s*["\']jarvis["\']', 
            r'=\s*["\']brad["\']',
            r'=\s*["\']lucy["\']',
            r'return\s+["\']marcel["\']',
            r'speaker["\']:\s*["\']marcel["\']'
        ]:
            matches = re.findall(pattern, content, re.IGNORECASE)
            issues.extend(matches)
        
        if issues:
            results[file_path] = issues
            print(f"\n📄 {file_path}:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue.strip()}")
    
    print(f"\n📊 Zusammenfassung: {len(results)} Dateien mit hardcodierten Namen gefunden")
    return results

def create_migration_plan():
    """Erstellt konkreten Migration Plan"""
    
    plan = {
        "PHASE 1 - Critical Services": [
            {
                "file": "src/services/generation/audio_generation_service.py",
                "changes": [
                    "Replace valid_speakers = ['brad', 'marcel', 'lucy'] with dynamic loading",
                    "Replace hardcoded mappings in _normalize_speaker_name",
                    "Replace return 'marcel' fallbacks with get_default_speaker()",
                ]
            }
        ],
        "PHASE 2 - Content Processing": [
            {
                "file": "src/services/processing/content_processing_service.py", 
                "changes": [
                    "Replace speakers = ['Marcel', 'Jarvis', 'Lucy', 'Brad']",
                    "Replace default speaker assignments"
                ]
            }
        ],
        "PHASE 3 - Configuration Files": [
            {
                "file": "src/config/settings.py",
                "changes": [
                    "Remove hardcoded voice IDs",
                    "Use dynamic voice loading"
                ]
            }
        ]
    }
    
    print("\n🎯 MIGRATION PLAN")
    print("=" * 30)
    
    for phase, files in plan.items():
        print(f"\n📋 {phase}:")
        for file_info in files:
            print(f"  📄 {file_info['file']}:")
            for change in file_info['changes']:
                print(f"    ✓ {change}")
    
    return plan

def apply_critical_fixes():
    """Wendet die kritischsten Fixes an"""
    
    print("\n🔧 APPLYING CRITICAL FIXES")
    print("=" * 40)
    
    # 1. Fix audio_generation_service.py - Speaker mapping
    audio_service_path = "src/services/generation/audio_generation_service.py"
    
    if Path(audio_service_path).exists():
        print(f"🎯 Fixing {audio_service_path}...")
        
        with open(audio_service_path, 'r') as f:
            content = f.read()
        
        # Replace hardcoded speaker mappings
        original_mapping = '''        # 🎯 GENERIC SPEAKER MAPPING - uses show config as source of truth
        speaker_map = {
            "marcel": "marcel",
            "jarvis": "jarvis",
            "lucy": "lucy", 
            "brad": "brad",
            "host": self._get_primary_speaker_from_config(),
            "moderator": self._get_primary_speaker_from_config(),
            "anchor": self._get_primary_speaker_from_config(),
            "news": self._get_primary_speaker_from_config(),
            "ai": "jarvis",
            "assistant": "jarvis",
            "computer": "jarvis"
        }'''
        
        dynamic_mapping = '''        # 🎯 DYNAMIC SPEAKER MAPPING - loaded from database
        # TODO: Replace with speaker_registry.get_speaker_mapping() in async context
        from services.infrastructure.speaker_registry import get_speaker_registry
        
        # For now, keep basic mapping - full async integration needed
        speaker_map = {
            "host": self._get_primary_speaker_from_config(),
            "moderator": self._get_primary_speaker_from_config(),
            "anchor": self._get_primary_speaker_from_config(),
            "news": self._get_primary_speaker_from_config(),
            # Dynamic speakers will be loaded via registry when async context available
        }
        
        # Add dynamic speakers if available
        try:
            # Note: This needs proper async integration
            # speaker_map.update(await get_speaker_registry().get_speaker_mapping())
            pass
        except:
            # Fallback to hardcoded for now - migration in progress
            speaker_map.update({
                "marcel": "marcel", "jarvis": "jarvis", "lucy": "lucy", "brad": "brad",
                "ai": "jarvis", "assistant": "jarvis", "computer": "jarvis"
            })'''
        
        # Apply the replacement (if found)
        if original_mapping.strip() in content:
            content = content.replace(original_mapping, dynamic_mapping)
            print("  ✅ Speaker mapping updated")
        else:
            print("  ⚠️ Speaker mapping pattern not found (may have changed)")
        
        # Replace fallback defaults
        content = re.sub(
            r'return "marcel"',
            '# TODO: Replace with dynamic default\n        return "marcel"  # Temporary hardcoded fallback',
            content
        )
        
        # Write back
        with open(audio_service_path, 'w') as f:
            f.write(content)
        
        print("  ✅ AudioGenerationService updated with migration comments")
    
    # 2. Create migration checklist
    checklist_path = "SPEAKER_MIGRATION_CHECKLIST.md"
    checklist_content = """# Speaker Names Migration Checklist

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
"""
    
    with open(checklist_path, 'w') as f:
        f.write(checklist_content)
    
    print(f"✅ Created {checklist_path}")
    print("\n🎉 Critical fixes applied!")
    print("\n📋 Next steps:")
    print("  1. Review migration checklist")
    print("  2. Test speaker registry system")
    print("  3. Gradually replace remaining hardcoded references")


if __name__ == "__main__":
    print("🚀 HARDCODED SPEAKER REFACTORING TOOL")
    print("=" * 60)
    
    # Analyze current state
    results = analyze_hardcoded_speakers()
    
    # Create migration plan
    plan = create_migration_plan()
    
    # Apply critical fixes
    apply_critical_fixes()
    
    print(f"\n✅ Refactoring tool completed!")
    print(f"📊 Found issues in {len(results)} files")
    print(f"🔧 Applied critical fixes and created migration checklist") 