#!/usr/bin/env python3

"""
Weather Service
===============

Service for weather data:
- OpenWeatherMap API Integration
- Current weather for Swiss cities
- Weather forecasts
- Radio-formatted weather reports

DEPENDENCIES: Only OpenWeatherMap API Key
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass

# Import Settings
from config.settings import get_settings

@dataclass
class WeatherLocation:
    """Weather location definition"""
    name: str
    city_id: int  # OpenWeatherMap City ID
    country_code: str = "CH"

class WeatherService:
    """OpenWeatherMap Weather Service for RadioX"""
    
    def __init__(self):
        # Load Weather API Key from Settings
        settings = get_settings()
        self.api_key = settings.weather_api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        
        # Swiss cities with OpenWeatherMap City IDs
        self.locations = {
            "zurich": WeatherLocation("Zürich", 2657896, "CH"),
            "basel": WeatherLocation("Basel", 2661604, "CH"),
            "geneva": WeatherLocation("Geneva", 2660646, "CH"),
            "bern": WeatherLocation("Bern", 2661552, "CH"),
            "lausanne": WeatherLocation("Lausanne", 2659994, "CH"),
            "winterthur": WeatherLocation("Winterthur", 2657970, "CH"),
            "lucerne": WeatherLocation("Lucerne", 2659811, "CH"),
            "st_gallen": WeatherLocation("St. Gallen", 2658822, "CH")
        }
        
    def _check_api_key(self) -> bool:
        """Checks if API key is available"""
        if not self.api_key or self.api_key == "your_openweathermap_api_key_here":
            logger.warning("⚠️ Weather API Key not configured")
            return False
        return True
    
    async def get_current_weather(self, location: str = "zurich") -> Optional[Dict[str, Any]]:
        """Retrieves current weather for a city"""
        try:
            if not self._check_api_key():
                return None
                
            # Normalize city names
            location_mapping = {
                "zürich": "zurich",
                "zuerich": "zurich",
                "Zürich": "zurich",
                "Zuerich": "zurich"
            }
            location = location_mapping.get(location, location.lower())
            
            if location not in self.locations:
                logger.warning(f"Unknown city: {location}, using fallback: zurich")
                location = "zurich"
            
            loc = self.locations[location]
            
            # Build API URL
            url = f"{self.base_url}/weather"
            params = {
                "id": loc.city_id,
                "appid": self.api_key,
                "units": "metric",
                "lang": "en"
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Get weather data from OpenWeatherMap
                    response = await session.get(url, params=params)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract relevant data
                        weather_info = {
                            "temperature": round(data["main"]["temp"], 1),
                            "feels_like": round(data["main"]["feels_like"], 1),
                            "humidity": data["main"]["humidity"],
                            "pressure": data["main"]["pressure"],
                            "description": data["weather"][0]["description"],
                            "wind_speed": round(data.get("wind", {}).get("speed", 0) * 3.6, 1),  # m/s to km/h
                            "wind_direction": data.get("wind", {}).get("deg", 0),
                            "visibility": round(data.get("visibility", 0) / 1000, 1),  # km
                            "clouds": data.get("clouds", {}).get("all", 0),
                            "location": loc.name,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        return weather_info
                    else:
                        logger.error(f"❌ OpenWeatherMap API error: {response.status}")
                        return None
                        
                except Exception as e:
                    logger.error(f"❌ Error retrieving weather: {e}")
                    return None
                        
        except Exception as e:
            logger.error(f"❌ Error retrieving weather: {e}")
            return None

    async def get_weather_forecast(self, location: str = "zurich", days: int = 3) -> Optional[Dict[str, Any]]:
        """Retrieves weather forecast for a city"""
        try:
            if not self._check_api_key():
                return None
                
            # Normalize city names
            location_mapping = {
                "zürich": "zurich",
                "zuerich": "zurich",
                "Zürich": "zurich",
                "Zuerich": "zurich"
            }
            location = location_mapping.get(location, location.lower())
            
            if location not in self.locations:
                logger.warning(f"Unknown city: {location}, using fallback: zurich")
                location = "zurich"
            
            loc = self.locations[location]
            
            # Build API URL for 5-day forecast
            url = f"{self.base_url}/forecast"
            params = {
                "id": loc.city_id,
                "appid": self.api_key,
                "units": "metric",
                "lang": "en"
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    # Get forecast data from OpenWeatherMap
                    response = await session.get(url, params=params)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process forecast data for next days
                        forecast_data = []
                        processed_dates = set()
                        
                        for item in data["list"][:days*8]:  # Each day has ~8 3-hour intervals
                            forecast_time = datetime.fromtimestamp(item["dt"])
                            day_date = forecast_time.date()
                            
                            # Take first forecast entry per day that's not today
                            if day_date not in processed_dates and day_date > datetime.now().date():
                                processed_dates.add(day_date)
                                forecast_data.append({
                                    "date": day_date.strftime("%Y-%m-%d"),
                                    "day_name": day_date.strftime("%A"),
                                    "time": forecast_time.strftime("%H:%M"),
                                    "temperature": round(item["main"]["temp"], 1),
                                    "feels_like": round(item["main"]["feels_like"], 1),
                                    "humidity": item["main"]["humidity"],
                                    "description": item["weather"][0]["description"],
                                    "wind_speed": round(item.get("wind", {}).get("speed", 0) * 3.6, 1),
                                    "clouds": item.get("clouds", {}).get("all", 0),
                                    "rain_probability": round(item.get("pop", 0) * 100, 1)  # Probability of precipitation
                                })
                                
                                if len(forecast_data) >= days:
                                    break
                        
                        return {
                            "location": loc.name,
                            "forecast": forecast_data,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"❌ OpenWeatherMap Forecast API error: {response.status}")
                        return None
                        
                except Exception as e:
                    logger.error(f"❌ Error retrieving forecast: {e}")
                    return None
                        
        except Exception as e:
            logger.error(f"❌ Error retrieving forecast: {e}")
            return None

    async def get_complete_weather(self, location: str = "zurich") -> Optional[Dict[str, Any]]:
        """Gets both current weather and forecast"""
        try:
            current = await self.get_current_weather(location)
            forecast = await self.get_weather_forecast(location, days=3)
            
            if current and forecast:
                return {
                    "current": current,
                    "forecast": forecast["forecast"],
                    "location": current["location"],
                    "timestamp": datetime.now().isoformat()
                }
            return current  # Fallback to current only
        except Exception as e:
            logger.error(f"❌ Error retrieving complete weather: {e}")
            return None

    async def get_weather_summary_with_gpt(self, location: str = "zurich") -> str:
        """Get intelligent weather summary using GPT based on raw data and time of day"""
        try:
            raw_data = await self.get_raw_weather_data(location)
            if not raw_data:
                return "Wetter nicht verfügbar"
            
            # Import here to avoid circular dependency
            from src.config.settings import Settings
            import openai
            
            settings = Settings()
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            
            current_time = raw_data.get("current_time", "unknown")
            current = raw_data.get("current", {})
            forecasts = raw_data.get("all_forecasts", [])
            
            # Create focused prompt for weather summary
            weather_prompt = f"""You are a weather expert for Radio Zurich speaking in English.

CURRENT TIME: {current_time}
CURRENT WEATHER: {current['temperature']}°C, {current['description']}
FORECAST ({len(forecasts)} entries): {str(forecasts)[:500]}...

TASK: Create an intelligent, time-dependent weather summary:
- Morning: Full day + weekly outlook  
- Midday: Rest of day + trend
- Evening: Today only

FORMAT: Maximum 3 sentences, concise, suitable for radio.
EXAMPLE: "Currently 21°C and hazy in Zurich. The rest of the day remains mild at 22°C with few clouds. Tomorrow looks sunnier with up to 25°C."

Your answer in English:"""

            # Call GPT for weather summary - dynamic model
            try:
                from config.api_config import get_gpt_model
                model = get_gpt_model()
            except ImportError:
                model = "gpt-4"  # Fallback
                
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": weather_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ GPT Weather Summary Error: {e}")
            return "Weather summary not available"

    async def get_raw_weather_data(self, location: str = "zurich") -> Optional[Dict[str, Any]]:
        """Gets ALL available weather data for GPT processing"""
        try:
            current = await self.get_current_weather(location)
            
            if not self._check_api_key():
                return current  # Fallback to current only
                
            # Normalize city names
            location_mapping = {
                "zürich": "zurich",
                "zuerich": "zurich", 
                "Zürich": "zurich",
                "Zuerich": "zurich"
            }
            location = location_mapping.get(location, location.lower())
            
            if location not in self.locations:
                location = "zurich"
            
            loc = self.locations[location]
            
            # Get 5-day/3-hour forecast (40 entries total)
            url = f"{self.base_url}/forecast"
            params = {
                "id": loc.city_id,
                "appid": self.api_key,
                "units": "metric",
                "lang": "en"
            }
            
            async with aiohttp.ClientSession() as session:
                try:
                    response = await session.get(url, params=params)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process ALL forecast entries for GPT
                        forecast_entries = []
                        for item in data["list"]:
                            forecast_time = datetime.fromtimestamp(item["dt"])
                            
                            forecast_entries.append({
                                "datetime": forecast_time.isoformat(),
                                "date": forecast_time.strftime("%Y-%m-%d"),
                                "day_name": forecast_time.strftime("%A"),
                                "time": forecast_time.strftime("%H:%M"),
                                "temperature": round(item["main"]["temp"], 1),
                                "feels_like": round(item["main"]["feels_like"], 1),
                                "humidity": item["main"]["humidity"],
                                "description": item["weather"][0]["description"],
                                "wind_speed": round(item.get("wind", {}).get("speed", 0) * 3.6, 1),
                                "clouds": item.get("clouds", {}).get("all", 0),
                                "rain_probability": round(item.get("pop", 0) * 100, 1)
                            })
                        
                        return {
                            "current": current,
                            "all_forecasts": forecast_entries,
                            "current_time": datetime.now().isoformat(),
                            "location": current["location"] if current else loc.name,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        logger.warning(f"⚠️ Forecast API error: {response.status}, using current only")
                        return {"current": current} if current else None
                        
                except Exception as e:
                    logger.warning(f"⚠️ Forecast error: {e}, using current only")
                    return {"current": current} if current else None
                        
        except Exception as e:
            logger.error(f"❌ Error retrieving raw weather data: {e}")
            return None


    
    def format_for_radio(self, weather_data: Optional[Dict[str, Any]] = None, location: str = "Zurich") -> str:
        """Formats weather data for radio announcement"""
        if not weather_data:
            return f"Weather data for {location} not available"
        
        temp = weather_data.get('temperature', 0)
        description = weather_data.get('description', 'unknown')
        wind_speed = weather_data.get('wind_speed', 0)
        humidity = weather_data.get('humidity', 0)
        
        return f"Current weather in {location}: {description.title()}, {temp:.1f} degrees Celsius, wind {wind_speed:.1f} kilometers per hour, humidity {humidity} percent."