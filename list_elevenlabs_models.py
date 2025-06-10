#!/usr/bin/env python3
"""
ElevenLabs Models API Abfrage
Zeigt alle verfügbaren TTS Modelle über die ElevenLabs API an
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class ElevenLabsModelsAPI:
    """ElevenLabs API Client für Modell-Abfragen"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            raise ValueError("❌ ELEVENLABS_API_KEY fehlt in den Umgebungsvariablen!")
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Holt alle verfügbaren ElevenLabs Modelle"""
        
        url = f"{self.base_url}/models"
        headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    models = await response.json()
                    return models
                else:
                    error_text = await response.text()
                    raise Exception(f"❌ API Fehler {response.status}: {error_text}")
    
    def format_model_info(self, models: List[Dict[str, Any]]) -> str:
        """Formatiert Modell-Informationen für die Ausgabe"""
        
        output = []
        output.append("🎙️ ELEVENLABS TTS MODELLE 2024/2025")
        output.append("=" * 50)
        output.append(f"⏰ Abfrage Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"📊 Anzahl Modelle: {len(models)}")
        output.append("")
        
        # Sortiere Modelle nach Name
        sorted_models = sorted(models, key=lambda x: x.get('name', ''))
        
        for i, model in enumerate(sorted_models, 1):
            output.append(f"🔢 MODELL #{i}")
            output.append(f"📝 ID: {model.get('model_id', 'N/A')}")
            output.append(f"🏷️  Name: {model.get('name', 'N/A')}")
            output.append(f"📖 Beschreibung: {model.get('description', 'N/A')}")
            
            # Features
            features = []
            if model.get('can_do_text_to_speech'):
                features.append("Text-to-Speech")
            if model.get('can_do_voice_conversion'):
                features.append("Voice Conversion")
            if model.get('can_be_finetuned'):
                features.append("Fine-tuning")
            if model.get('can_use_style'):
                features.append("Style Control")
            if model.get('can_use_speaker_boost'):
                features.append("Speaker Boost")
            if model.get('serves_pro_voices'):
                features.append("Pro Voices")
                
            output.append(f"⚡ Features: {', '.join(features) if features else 'Keine angegeben'}")
            
            # Sprachen
            languages = model.get('languages', [])
            if languages:
                lang_names = [lang.get('name', lang.get('language_id', '')) for lang in languages]
                output.append(f"🌍 Sprachen ({len(languages)}): {', '.join(lang_names[:5])}")
                if len(lang_names) > 5:
                    output.append(f"    ... und {len(lang_names) - 5} weitere")
            else:
                output.append("🌍 Sprachen: Nicht angegeben")
            
            # Limits
            max_chars_free = model.get('max_characters_request_free_user')
            max_chars_paid = model.get('max_characters_request_subscribed_user')
            max_text_length = model.get('maximum_text_length_per_request')
            
            if max_chars_free or max_chars_paid or max_text_length:
                output.append("📏 Limits:")
                if max_chars_free:
                    output.append(f"    Free User: {max_chars_free:,} Zeichen")
                if max_chars_paid:
                    output.append(f"    Paid User: {max_chars_paid:,} Zeichen")
                if max_text_length:
                    output.append(f"    Max Text: {max_text_length:,} Zeichen")
            
            # Kosten
            if model.get('model_rates'):
                cost_multiplier = model['model_rates'].get('character_cost_multiplier', 1.0)
                output.append(f"💰 Kosten Multiplikator: {cost_multiplier}x")
            
            # Alpha/Beta Status
            if model.get('requires_alpha_access'):
                output.append("🧪 Status: Alpha (Zugang erforderlich)")
            
            # Concurrency
            concurrency_group = model.get('concurrency_group')
            if concurrency_group:
                output.append(f"⚡ Concurrency Gruppe: {concurrency_group}")
            
            output.append("")
        
        return "\n".join(output)
    
    async def get_detailed_model_stats(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Erstellt detaillierte Statistiken über die Modelle"""
        
        stats = {
            'total_models': len(models),
            'text_to_speech_models': 0,
            'voice_conversion_models': 0,
            'multilingual_models': 0,
            'alpha_models': 0,
            'pro_voice_models': 0,
            'unique_languages': set(),
            'concurrency_groups': {},
            'cost_multipliers': []
        }
        
        for model in models:
            if model.get('can_do_text_to_speech'):
                stats['text_to_speech_models'] += 1
            if model.get('can_do_voice_conversion'):
                stats['voice_conversion_models'] += 1
            if model.get('requires_alpha_access'):
                stats['alpha_models'] += 1
            if model.get('serves_pro_voices'):
                stats['pro_voice_models'] += 1
            
            # Sprachen sammeln
            languages = model.get('languages', [])
            if len(languages) > 1:
                stats['multilingual_models'] += 1
            for lang in languages:
                lang_name = lang.get('name', lang.get('language_id', ''))
                if lang_name:
                    stats['unique_languages'].add(lang_name)
            
            # Concurrency Gruppen
            concurrency_group = model.get('concurrency_group')
            if concurrency_group:
                stats['concurrency_groups'][concurrency_group] = stats['concurrency_groups'].get(concurrency_group, 0) + 1
            
            # Kosten
            if model.get('model_rates'):
                cost_multiplier = model['model_rates'].get('character_cost_multiplier')
                if cost_multiplier:
                    stats['cost_multipliers'].append(cost_multiplier)
        
        return stats
    
    def format_stats(self, stats: Dict[str, Any]) -> str:
        """Formatiert die Statistiken"""
        
        output = []
        output.append("📊 MODELL STATISTIKEN")
        output.append("=" * 30)
        output.append(f"📈 Gesamt Modelle: {stats['total_models']}")
        output.append(f"🎤 Text-to-Speech: {stats['text_to_speech_models']}")
        output.append(f"🔄 Voice Conversion: {stats['voice_conversion_models']}")
        output.append(f"🌍 Mehrsprachig: {stats['multilingual_models']}")
        output.append(f"🧪 Alpha/Beta: {stats['alpha_models']}")
        output.append(f"⭐ Pro Voice Support: {stats['pro_voice_models']}")
        output.append(f"🗣️  Einzigartige Sprachen: {len(stats['unique_languages'])}")
        
        if stats['concurrency_groups']:
            output.append("\n⚡ Concurrency Gruppen:")
            for group, count in stats['concurrency_groups'].items():
                output.append(f"    {group}: {count} Modelle")
        
        if stats['cost_multipliers']:
            avg_cost = sum(stats['cost_multipliers']) / len(stats['cost_multipliers'])
            min_cost = min(stats['cost_multipliers'])
            max_cost = max(stats['cost_multipliers'])
            output.append(f"\n💰 Kosten Multiplier:")
            output.append(f"    Durchschnitt: {avg_cost:.2f}x")
            output.append(f"    Min: {min_cost}x, Max: {max_cost}x")
        
        return "\n".join(output)

async def main():
    """Hauptfunktion"""
    
    print("🔍 ElevenLabs Modelle werden abgerufen...")
    
    try:
        # API Client erstellen
        client = ElevenLabsModelsAPI()
        
        # Modelle abrufen
        models = await client.get_available_models()
        
        # Detaillierte Informationen anzeigen
        model_info = client.format_model_info(models)
        print(model_info)
        
        # Statistiken erstellen und anzeigen
        stats = await client.get_detailed_model_stats(models)
        stats_info = client.format_stats(stats)
        print(stats_info)
        
        # Optional: Als JSON speichern
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"elevenlabs_models_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Rohdaten gespeichert: {filename}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✅ ElevenLabs Modelle erfolgreich abgerufen!")
    else:
        print("\n❌ Fehler beim Abrufen der Modelle.") 