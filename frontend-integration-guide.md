# RadioX Frontend API Integration Guide

## 🎯 **API Endpoints & Data Structures**

### **Base Configuration**
```typescript
// lib/radiox-config.ts
export const RADIOX_CONFIG = {
  API_BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://100.109.155.102:8000',
  API_VERSION: 'v1',
  ENDPOINTS: {
    SHOWS: '/api/v1/shows',
    GENERATE_SHOW: '/api/v1/shows/generate',
    HEALTH: '/health'
  }
} as const;
```

### **TypeScript Interfaces**
```typescript
// types/radiox.ts
export interface RadioXShow {
  id: string;
  session_id: string;
  title: string;
  created_at: string;
  channel: string;
  language: string;
  news_count: number;
  broadcast_style: string;
  estimated_duration_minutes: number;
  metadata: {
    total_segments: number;
    news_segments: number;
    music_segments: number;
    style: string;
  };
  script_preview?: string;
}

export interface ShowsResponse {
  shows: RadioXShow[];
  total: number;
  source: 'supabase' | 'redis_fallback';
  timestamp: string;
}

export interface GenerateShowRequest {
  location: string;
  news_count: number;
  style?: 'energetic' | 'calm' | 'professional';
  duration_minutes?: number;
}
```

### **API Client Implementation**
```typescript
// lib/radiox-client.ts
import { RADIOX_CONFIG } from './radiox-config';
import type { ShowsResponse, GenerateShowRequest, RadioXShow } from '@/types/radiox';

class RadioXAPIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = RADIOX_CONFIG.API_BASE_URL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`RadioX API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Get all shows with pagination
  async getShows(limit = 10, offset = 0): Promise<ShowsResponse> {
    return this.request<ShowsResponse>(
      `${RADIOX_CONFIG.ENDPOINTS.SHOWS}?limit=${limit}&offset=${offset}`
    );
  }

  // Get single show by ID
  async getShow(id: string): Promise<RadioXShow> {
    return this.request<RadioXShow>(`${RADIOX_CONFIG.ENDPOINTS.SHOWS}/${id}`);
  }

  // Generate new show
  async generateShow(request: GenerateShowRequest): Promise<{ session_id: string }> {
    return this.request<{ session_id: string }>(
      RADIOX_CONFIG.ENDPOINTS.GENERATE_SHOW,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>(RADIOX_CONFIG.ENDPOINTS.HEALTH);
  }
}

export const radioXAPI = new RadioXAPIClient();
```

### **React Hooks**
```typescript
// hooks/useRadioXAPI.ts
import { useState, useEffect } from 'react';
import { radioXAPI } from '@/lib/radiox-client';
import type { ShowsResponse, RadioXShow } from '@/types/radiox';

export function useShows(limit = 10) {
  const [shows, setShows] = useState<RadioXShow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    async function fetchShows() {
      try {
        setLoading(true);
        const response = await radioXAPI.getShows(limit);
        setShows(response.shows);
        setTotal(response.total);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch shows');
      } finally {
        setLoading(false);
      }
    }

    fetchShows();
  }, [limit]);

  return { shows, loading, error, total };
}

export function useGenerateShow() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateShow = async (request: GenerateShowRequest) => {
    try {
      setLoading(true);
      setError(null);
      const result = await radioXAPI.generateShow(request);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate show';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return { generateShow, loading, error };
}
```

### **React Components**
```tsx
// components/ShowsList.tsx
import { useShows } from '@/hooks/useRadioXAPI';
import { formatDistanceToNow } from 'date-fns';

export function ShowsList() {
  const { shows, loading, error, total } = useShows(10);

  if (loading) return <div>Loading shows...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">RadioX Shows ({total})</h2>
      
      {shows.map((show) => (
        <div key={show.id} className="border rounded-lg p-4 shadow-sm">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-lg font-semibold">{show.title}</h3>
              <p className="text-gray-600">
                {show.channel} • {show.language} • {show.news_count} news items
              </p>
              <p className="text-sm text-gray-500">
                {formatDistanceToNow(new Date(show.created_at), { addSuffix: true })}
              </p>
            </div>
            <div className="text-right">
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                {show.broadcast_style}
              </span>
              <p className="text-sm text-gray-500 mt-1">
                {show.estimated_duration_minutes} min
              </p>
            </div>
          </div>
          
          {show.script_preview && (
            <div className="mt-3 p-3 bg-gray-50 rounded">
              <p className="text-sm">{show.script_preview}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

```tsx
// components/ShowGenerator.tsx
import { useState } from 'react';
import { useGenerateShow } from '@/hooks/useRadioXAPI';

export function ShowGenerator() {
  const [location, setLocation] = useState('Zurich');
  const [newsCount, setNewsCount] = useState(2);
  const [style, setStyle] = useState<'energetic' | 'calm' | 'professional'>('energetic');
  
  const { generateShow, loading, error } = useGenerateShow();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await generateShow({
        location,
        news_count: newsCount,
        style,
        duration_minutes: 30
      });
      
      alert(`Show generated! Session ID: ${result.session_id}`);
    } catch (err) {
      console.error('Failed to generate show:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <div>
        <label className="block text-sm font-medium mb-1">Location</label>
        <input
          type="text"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="w-full border rounded px-3 py-2"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">News Count</label>
        <select
          value={newsCount}
          onChange={(e) => setNewsCount(Number(e.target.value))}
          className="w-full border rounded px-3 py-2"
        >
          <option value={1}>1 News Item</option>
          <option value={2}>2 News Items</option>
          <option value={3}>3 News Items</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Style</label>
        <select
          value={style}
          onChange={(e) => setStyle(e.target.value as any)}
          className="w-full border rounded px-3 py-2"
        >
          <option value="energetic">Energetic</option>
          <option value="calm">Calm</option>
          <option value="professional">Professional</option>
        </select>
      </div>

      {error && (
        <div className="text-red-600 text-sm">{error}</div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {loading ? 'Generating...' : 'Generate Show'}
      </button>
    </form>
  );
}
```

### **Next.js API Routes (Optional Proxy)**
```typescript
// pages/api/radiox/shows.ts (or app/api/radiox/shows/route.ts)
import { NextApiRequest, NextApiResponse } from 'next';

const RADIOX_API_URL = 'http://100.109.155.102:8000';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { limit = 10, offset = 0 } = req.query;
    
    const response = await fetch(
      `${RADIOX_API_URL}/api/v1/shows?limit=${limit}&offset=${offset}`,
      {
        headers: {
          'Accept': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`RadioX API responded with ${response.status}`);
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('RadioX API Error:', error);
    res.status(500).json({ error: 'Failed to fetch shows' });
  }
}
```

## 🚀 **Current API Status**

### **Live Data (aktuell verfügbar):**
- **Total Shows**: 3 ✅
- **Latest Show**: "Midday Energy - Zurich" (13:00 Uhr) ✅
- **API Source**: Supabase ✅
- **Alle Services**: Healthy ✅

### **API Endpoints Ready:**
```bash
# Shows abrufen
GET http://100.109.155.102:8000/api/v1/shows?limit=10

# Neue Show generieren  
POST http://100.109.155.102:8000/api/v1/shows/generate
{
  "location": "Zurich",
  "news_count": 2,
  "style": "energetic"
}

# Health Check
GET http://100.109.155.102:8000/health
```

## 🔧 **Quick Start**

1. **Kopiere** die TypeScript Interfaces in dein Frontend
2. **Erstelle** den API Client mit der Tailscale IP
3. **Implementiere** die React Hooks
4. **Teste** mit der aktuellen 13 Uhr Show

**Die API läuft bereits perfekt** - dein Frontend kann sofort loslegen! 🎉 