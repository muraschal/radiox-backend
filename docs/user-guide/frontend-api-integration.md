# RadioX Frontend API Integration Guide

**🎙️ Complete API Documentation for Frontend Development**

## 🌐 **Production API Base URL**
```
https://api.radiox.cloud
```

## 📊 **Shows Management API**

### **1. List All Shows (Paginated)**

```typescript
GET /api/v1/shows?limit={number}&offset={number}
```

**Purpose**: Get paginated list of all generated radio shows

**Parameters**:
- `limit` (optional): Number of shows per page (default: 10, max: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response**:
```json
{
  "shows": [
    {
      "id": "f8d34ee2-7d58-4182-acd9-0dc403989a9b",
      "title": "Late Night Vibes - Zurich",
      "created_at": "2025-06-24T23:20:04.656418",
      "channel": "zurich",
      "language": "de",
      "news_count": 3,
      "broadcast_style": "Late Night Vibes",
      "script_preview": "MARCEL: Guten Abend, Zürich! Es ist genau 23:19 Uhr..."
    }
  ],
  "total": 7,
  "limit": 5,
  "offset": 0,
  "has_more": true
}
```

**Frontend Usage**:
```typescript
interface Show {
  id: string;
  title: string;
  created_at: string;
  channel: string;
  language: string;
  news_count: number;
  broadcast_style: string;
  script_preview: string;
}

interface ShowsListResponse {
  shows: Show[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Fetch shows
const fetchShows = async (limit = 10, offset = 0): Promise<ShowsListResponse> => {
  const response = await fetch(`https://api.radiox.cloud/api/v1/shows?limit=${limit}&offset=${offset}`);
  return response.json();
};
```

### **2. Get Individual Show Details**

```typescript
GET /api/v1/shows/{show_id}
```

**Purpose**: Get complete details of a specific show

**Response**:
```json
{
  "session_id": "f8d34ee2-7d58-4182-acd9-0dc403989a9b",
  "script_content": "MARCEL: Guten Abend, Zürich! Es ist genau 23:19 Uhr...",
  "broadcast_style": "Late Night Vibes",
  "estimated_duration_minutes": 5,
  "segments": [
    {
      "type": "dialogue",
      "speaker": "marcel",
      "text": "Guten Abend, Zürich! Es ist genau 23:19 Uhr...",
      "estimated_duration": 13.2
    }
  ],
  "metadata": {
    "channel": "zurich",
    "language": "de",
    "speakers": {
      "primary": {
        "id": "marcel",
        "name": "Marcel",
        "voice_id": "pNInz6obpgDQGcFmaJgB"
      },
      "secondary": {
        "name": "jarvis"
      }
    },
    "content_stats": {
      "total_news_collected": 218,
      "news_selected": 3
    },
    "generated_at": "2025-06-24T23:20:04.656418",
    "audio_url": "https://zwcvvbgkqhexfcldwuxq.supabase.co/storage/v1/object/public/radio-shows/shows/2025-06-24_23-20_default_jarvis-marcel_5min.mp3",
    "audio_duration": 320.84
  }
}
```

**Frontend Usage**:
```typescript
interface ShowDetails {
  session_id: string;
  script_content: string;
  broadcast_style: string;
  estimated_duration_minutes: number;
  segments: Array<{
    type: string;
    speaker: string;
    text: string;
    estimated_duration: number;
  }>;
  metadata: {
    channel: string;
    language: string;
    audio_url: string;
    audio_duration: number;
    generated_at: string;
  };
}

// Fetch show details
const fetchShowDetails = async (showId: string): Promise<ShowDetails> => {
  const response = await fetch(`https://api.radiox.cloud/api/v1/shows/${showId}`);
  return response.json();
};
```

### **3. Generate New Show**

```typescript
POST /api/v1/shows/generate
```

**Purpose**: Generate a new radio show

**Request Body**:
```json
{
  "channel": "zurich",
  "news_count": 3,
  "language": "de",
  "target_time": "01:15",
  "primary_speaker": "marcel",
  "secondary_speaker": "jarvis"
}
```

**Request Parameters**:
- `channel` (optional): "zurich", "basel", "bern" (default: "zurich")
- `news_count` (optional): 1-3 recommended (default: 2)
- `language` (optional): "de", "en" (default: "de")
- `target_time` (optional): Format "HH:MM" for time-based styling
- `primary_speaker` (optional): Speaker ID (default: "marcel")
- `secondary_speaker` (optional): Speaker ID (default: "jarvis")

**Response**: Same as individual show details above

**Frontend Usage**:
```typescript
interface GenerateShowRequest {
  channel?: string;
  news_count?: number;
  language?: string;
  target_time?: string;
  primary_speaker?: string;
  secondary_speaker?: string;
}

// Generate new show
const generateShow = async (request: GenerateShowRequest = {}): Promise<ShowDetails> => {
  const response = await fetch('https://api.radiox.cloud/api/v1/shows/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error(`Generation failed: ${response.statusText}`);
  }
  
  return response.json();
};
```

## 🎵 **Audio Playback Integration**

### **Audio URLs**
- Shows include direct MP3 URLs in `metadata.audio_url`
- Files hosted on Supabase Storage (CDN-enabled)
- Duration available in `metadata.audio_duration` (seconds)

### **Frontend Audio Player**:
```typescript
const AudioPlayer: React.FC<{ show: ShowDetails }> = ({ show }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  
  return (
    <div>
      <h3>{show.metadata.channel} - {show.broadcast_style}</h3>
      <audio 
        ref={audioRef} 
        controls 
        src={show.metadata.audio_url}
        preload="metadata"
      >
        Your browser does not support the audio element.
      </audio>
      <p>Duration: {Math.round(show.metadata.audio_duration / 60)} minutes</p>
    </div>
  );
};
```

## 🔄 **Real-time Updates Pattern**

### **Polling for New Shows**:
```typescript
const useShowsPolling = (intervalMs = 30000) => {
  const [shows, setShows] = useState<Show[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const response = await fetchShows(10, 0);
        setShows(response.shows);
      } catch (error) {
        console.error('Failed to fetch shows:', error);
      }
    };

    poll(); // Initial load
    const interval = setInterval(poll, intervalMs);
    
    return () => clearInterval(interval);
  }, [intervalMs]);

  return { shows, isLoading };
};
```

## 📱 **Complete React Hook Example**

```typescript
import { useState, useEffect, useCallback } from 'react';

export const useRadioXAPI = () => {
  const [shows, setShows] = useState<Show[]>([]);
  const [currentShow, setCurrentShow] = useState<ShowDetails | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch shows list
  const fetchShows = useCallback(async (limit = 10, offset = 0) => {
    try {
      const response = await fetch(`https://api.radiox.cloud/api/v1/shows?limit=${limit}&offset=${offset}`);
      const data = await response.json();
      setShows(data.shows);
      return data;
    } catch (err) {
      setError('Failed to fetch shows');
      throw err;
    }
  }, []);

  // Generate new show
  const generateShow = useCallback(async (request: GenerateShowRequest = {}) => {
    setIsGenerating(true);
    setError(null);
    
    try {
      const response = await fetch('https://api.radiox.cloud/api/v1/shows/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      
      const newShow = await response.json();
      setCurrentShow(newShow);
      
      // Refresh shows list
      await fetchShows();
      
      return newShow;
    } catch (err) {
      setError('Failed to generate show');
      throw err;
    } finally {
      setIsGenerating(false);
    }
  }, [fetchShows]);

  // Load show details
  const loadShow = useCallback(async (showId: string) => {
    try {
      const response = await fetch(`https://api.radiox.cloud/api/v1/shows/${showId}`);
      const show = await response.json();
      setCurrentShow(show);
      return show;
    } catch (err) {
      setError('Failed to load show');
      throw err;
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    fetchShows();
  }, [fetchShows]);

  return {
    shows,
    currentShow,
    isGenerating,
    error,
    fetchShows,
    generateShow,
    loadShow,
    clearError: () => setError(null),
  };
};
```

## 🚨 **Error Handling**

### **Common Error Responses**:

**404 - Show Not Found**:
```json
{
  "detail": "Show not found"
}
```

**503 - Service Unavailable**:
```json
{
  "detail": "Redis cache not available"
}
```

**500 - Generation Failed**:
```json
{
  "detail": "Show generation failed: API timeout"
}
```

### **Frontend Error Handling**:
```typescript
const handleAPIError = (error: any) => {
  if (error.status === 404) {
    return 'Show not found';
  } else if (error.status === 503) {
    return 'Service temporarily unavailable';
  } else if (error.status === 500) {
    return 'Generation failed - please try again';
  } else {
    return 'An unexpected error occurred';
  }
};
```

## 🎯 **Best Practices**

### **1. Pagination Implementation**:
```typescript
const ShowsList: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(0);
  const [shows, setShows] = useState<Show[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const pageSize = 10;

  const loadMore = async () => {
    const response = await fetchShows(pageSize, currentPage * pageSize);
    setShows(prev => [...prev, ...response.shows]);
    setHasMore(response.has_more);
    setCurrentPage(prev => prev + 1);
  };

  return (
    <div>
      {shows.map(show => (
        <ShowCard key={show.id} show={show} />
      ))}
      {hasMore && <button onClick={loadMore}>Load More</button>}
    </div>
  );
};
```

### **2. Optimistic Updates**:
```typescript
const generateShowOptimistic = async (request: GenerateShowRequest) => {
  // Add placeholder show immediately
  const placeholderShow: Show = {
    id: 'generating',
    title: 'Generating...',
    created_at: new Date().toISOString(),
    channel: request.channel || 'zurich',
    language: request.language || 'de',
    news_count: request.news_count || 2,
    broadcast_style: 'Generating',
    script_preview: 'Show is being generated...'
  };
  
  setShows(prev => [placeholderShow, ...prev]);
  
  try {
    const newShow = await generateShow(request);
    // Replace placeholder with real show
    setShows(prev => prev.map(show => 
      show.id === 'generating' ? {
        id: newShow.session_id,
        title: `${newShow.broadcast_style} - ${newShow.metadata.channel}`,
        created_at: newShow.metadata.generated_at,
        channel: newShow.metadata.channel,
        language: newShow.metadata.language,
        news_count: newShow.metadata.content_stats.news_selected,
        broadcast_style: newShow.broadcast_style,
        script_preview: newShow.script_content.substring(0, 200) + '...'
      } : show
    ));
  } catch (error) {
    // Remove placeholder on error
    setShows(prev => prev.filter(show => show.id !== 'generating'));
    throw error;
  }
};
```

## 🎵 **Complete Integration Example**

```typescript
// App.tsx
import { useRadioXAPI } from './hooks/useRadioXAPI';

const App: React.FC = () => {
  const { shows, currentShow, isGenerating, generateShow, loadShow } = useRadioXAPI();

  return (
    <div className="app">
      <header>
        <h1>RadioX AI Radio</h1>
        <button 
          onClick={() => generateShow({ channel: 'zurich', news_count: 3 })}
          disabled={isGenerating}
        >
          {isGenerating ? 'Generating...' : 'Generate New Show'}
        </button>
      </header>

      <main>
        <section className="shows-list">
          <h2>Recent Shows</h2>
          {shows.map(show => (
            <div key={show.id} className="show-card" onClick={() => loadShow(show.id)}>
              <h3>{show.title}</h3>
              <p>{show.script_preview}</p>
              <span>{new Date(show.created_at).toLocaleDateString()}</span>
            </div>
          ))}
        </section>

        {currentShow && (
          <section className="current-show">
            <h2>Now Playing</h2>
            <audio controls src={currentShow.metadata.audio_url} />
            <div className="transcript">
              {currentShow.segments.map((segment, i) => (
                <p key={i}><strong>{segment.speaker}:</strong> {segment.text}</p>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
};
```

---

**🎯 This documentation provides everything needed for complete frontend integration with the RadioX API!** 