"""
Modular Configuration Manager for RadioX
Replaces all hardcoded values with database lookups
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .supabase_client import get_db


@dataclass
class BroadcastStyle:
    style_name: str
    display_name: str
    marcel_mood: str
    jarvis_mood: str
    duration_target: int
    time_range_start: int
    time_range_end: int


@dataclass
class Location:
    location_code: str
    display_name: str
    timezone: str
    weather_api_name: str
    latitude: float
    longitude: float


@dataclass
class ShowTemplate:
    template_name: str
    display_name: str
    language: str
    system_prompt: str
    format_instructions: str
    speaker_tags: Dict[str, str]


@dataclass
class ShowPreset:
    preset_name: str
    display_name: str
    primary_speaker: str
    secondary_speaker: Optional[str]
    weather_speaker: Optional[str]
    location: Location
    broadcast_style: BroadcastStyle
    template: ShowTemplate
    gpt_selection_instructions: str


class ModularConfig:
    """Central configuration manager that replaces all hardcoded values"""
    
    def __init__(self):
        self.db_client = get_db()
        self.supabase = self.db_client.client  # Access the underlying Supabase client
        self._cache = {}
    
    async def get_dynamic_config(self, category: str, key: str) -> Any:
        """Get dynamic configuration value"""
        cache_key = f"{category}:{key}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self.supabase.table('dynamic_config').select('*').eq('config_category', category).eq('config_key', key).eq('is_active', True).execute()
        
        if result.data:
            config = result.data[0]
            value = config['config_json'] if config['config_json'] else config['config_value']
            self._cache[cache_key] = value
            return value
        return None
    
    async def get_config_by_category(self, category: str) -> Dict[str, Any]:
        """Get all configuration values for a category"""
        cache_key = f"category:{category}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self.supabase.table('dynamic_config').select('*').eq('config_category', category).eq('is_active', True).execute()
        
        config_dict = {}
        for item in result.data:
            key = item['config_key']
            value = item['config_json'] if item['config_json'] else item['config_value']
            
            # Try to parse JSON if it's a string that looks like JSON
            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON
            
            config_dict[key] = value
        
        self._cache[cache_key] = config_dict
        return config_dict
    
    async def get_default_values(self) -> Dict[str, str]:
        """Get all default values"""
        if 'defaults' in self._cache:
            return self._cache['defaults']
        
        result = self.supabase.table('dynamic_config').select('*').eq('config_category', 'defaults').eq('is_active', True).execute()
        
        defaults = {}
        for item in result.data:
            defaults[item['config_key']] = item['config_value']
        
        self._cache['defaults'] = defaults
        return defaults
    
    async def get_broadcast_style_by_time(self, hour: int) -> Optional[BroadcastStyle]:
        """Get broadcast style based on current hour"""
        result = self.supabase.table('broadcast_styles').select('*').eq('is_active', True).execute()
        
        for style_data in result.data:
            start = style_data['time_range_start']
            end = style_data['time_range_end']
            
            # Handle overnight ranges (e.g., 23-5)
            if start > end:
                if hour >= start or hour <= end:
                    return BroadcastStyle(**style_data)
            else:
                if start <= hour <= end:
                    return BroadcastStyle(**style_data)
        
        # Fallback to first active style
        if result.data:
            return BroadcastStyle(**result.data[0])
        return None
    
    async def get_broadcast_style(self, style_name: str) -> Optional[BroadcastStyle]:
        """Get specific broadcast style by name"""
        result = self.supabase.table('broadcast_styles').select('*').eq('style_name', style_name).eq('is_active', True).execute()
        
        if result.data:
            return BroadcastStyle(**result.data[0])
        return None
    
    async def get_location(self, location_code: str) -> Optional[Location]:
        """Get location by code"""
        result = self.supabase.table('locations').select('*').eq('location_code', location_code).eq('is_active', True).execute()
        
        if result.data:
            return Location(**result.data[0])
        return None
    
    async def get_show_template(self, template_name: str) -> Optional[ShowTemplate]:
        """Get show template by name"""
        result = self.supabase.table('show_templates').select('*').eq('template_name', template_name).eq('is_active', True).execute()
        
        if result.data:
            template_data = result.data[0]
            return ShowTemplate(
                template_name=template_data['template_name'],
                display_name=template_data['display_name'],
                language=template_data['language'],
                system_prompt=template_data['system_prompt'],
                format_instructions=template_data['format_instructions'],
                speaker_tags=template_data.get('speaker_tags', {})
            )
        return None
    
    async def get_show_preset(self, preset_name: str) -> Optional[ShowPreset]:
        """Get complete show preset with all related data"""
        query = """
        SELECT 
            sp.*,
            l.location_code, l.display_name as location_display, l.timezone, l.weather_api_name, l.latitude, l.longitude,
            bs.style_name, bs.display_name as style_display, bs.marcel_mood, bs.jarvis_mood, bs.duration_target, bs.time_range_start, bs.time_range_end,
            st.template_name, st.display_name as template_display, st.language, st.system_prompt, st.format_instructions, st.speaker_tags
        FROM show_presets sp
        LEFT JOIN locations l ON sp.location_code = l.location_code
        LEFT JOIN broadcast_styles bs ON sp.broadcast_style_name = bs.style_name
        LEFT JOIN show_templates st ON sp.template_name = st.template_name
        WHERE sp.preset_name = %s AND sp.is_active = true
        """
        
        result = self.supabase.rpc('execute_sql', {'query': query, 'params': [preset_name]}).execute()
        
        if result.data:
            data = result.data[0]
            
            location = Location(
                location_code=data['location_code'],
                display_name=data['location_display'],
                timezone=data['timezone'],
                weather_api_name=data['weather_api_name'],
                latitude=data['latitude'],
                longitude=data['longitude']
            )
            
            broadcast_style = BroadcastStyle(
                style_name=data['style_name'],
                display_name=data['style_display'],
                marcel_mood=data['marcel_mood'],
                jarvis_mood=data['jarvis_mood'],
                duration_target=data['duration_target'],
                time_range_start=data['time_range_start'],
                time_range_end=data['time_range_end']
            )
            
            template = ShowTemplate(
                template_name=data['template_name'],
                display_name=data['template_display'],
                language=data['language'],
                system_prompt=data['system_prompt'],
                format_instructions=data['format_instructions'],
                speaker_tags=data.get('speaker_tags', {})
            )
            
            return ShowPreset(
                preset_name=data['preset_name'],
                display_name=data['display_name'],
                primary_speaker=data['primary_speaker'],
                secondary_speaker=data['secondary_speaker'],
                weather_speaker=data['weather_speaker'],
                location=location,
                broadcast_style=broadcast_style,
                template=template,
                gpt_selection_instructions=data['gpt_selection_instructions']
            )
        
        return None
    
    async def normalize_speaker_name(self, speaker_name: str) -> str:
        """Normalize speaker name using mapping"""
        mapping = await self.get_dynamic_config('speakers', 'speaker_name_mapping')
        if mapping and isinstance(mapping, str):
            mapping = json.loads(mapping)
        
        return mapping.get(speaker_name, speaker_name.lower()) if mapping else speaker_name.lower()
    
    async def get_speaker_tags(self) -> Dict[str, str]:
        """Get speaker tag formatting rules"""
        return await self.get_dynamic_config('formats', 'speaker_tags') or {}
    
    async def get_fallback_script(self, language: str = 'de') -> str:
        """Get fallback script for when generation fails"""
        fallback = await self.get_dynamic_config('formats', f'fallback_intro_{language}')
        if fallback and isinstance(fallback, dict):
            return fallback.get('script', '')
        return ''
    
    async def get_city_display_name(self, location_code: str) -> str:
        """Get display name for city code"""
        mapping = await self.get_dynamic_config('formats', 'city_display_mapping')
        if mapping:
            return mapping.get(location_code, location_code)
        return location_code
    
    def clear_cache(self):
        """Clear configuration cache"""
        self._cache.clear()


# Global instance
modular_config = ModularConfig() 