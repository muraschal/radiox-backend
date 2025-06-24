# RadioX API Quick Reference - Copy-Paste Ready

**🚀 Production API: `https://api.radiox.cloud`**

## 📋 **Essential Endpoints**

```typescript
// 1. LIST SHOWS (with pagination)
GET /api/v1/shows?limit=10&offset=0

// 2. GET SHOW DETAILS  
GET /api/v1/shows/{show_id}

// 3. GENERATE NEW SHOW
POST /api/v1/shows/generate
Body: { "channel": "zurich", "news_count": 3, "language": "de" }
```

## 🎯 **TypeScript Interfaces**

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

interface ShowsListResponse {
  shows: Show[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
```

## ⚡ **Ready-to-Use React Hook**

```typescript
import { useState, useEffect, useCallback } from 'react';

export const useRadioXAPI = () => {
  const [shows, setShows] = useState<Show[]>([]);
  const [currentShow, setCurrentShow] = useState<ShowDetails | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchShows = useCallback(async (limit = 10, offset = 0) => {
    const response = await fetch(`https://api.radiox.cloud/api/v1/shows?limit=${limit}&offset=${offset}`);
    const data = await response.json();
    setShows(data.shows);
    return data;
  }, []);

  const generateShow = useCallback(async (request = {}) => {
    setIsGenerating(true);
    try {
      const response = await fetch('https://api.radiox.cloud/api/v1/shows/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      const newShow = await response.json();
      setCurrentShow(newShow);
      await fetchShows(); // Refresh list
      return newShow;
    } finally {
      setIsGenerating(false);
    }
  }, [fetchShows]);

  const loadShow = useCallback(async (showId: string) => {
    const response = await fetch(`https://api.radiox.cloud/api/v1/shows/${showId}`);
    const show = await response.json();
    setCurrentShow(show);
    return show;
  }, []);

  useEffect(() => { fetchShows(); }, [fetchShows]);

  return { shows, currentShow, isGenerating, error, fetchShows, generateShow, loadShow };
};
```

## 🎵 **Audio Player Component**

```typescript
const AudioPlayer: React.FC<{ show: ShowDetails }> = ({ show }) => (
  <div>
    <h3>{show.metadata.channel} - {show.broadcast_style}</h3>
    <audio controls src={show.metadata.audio_url} preload="metadata">
      Your browser does not support audio.
    </audio>
    <p>Duration: {Math.round(show.metadata.audio_duration / 60)} min</p>
  </div>
);
```

## 📱 **Complete App Example**

```typescript
import { useRadioXAPI } from './hooks/useRadioXAPI';

const App: React.FC = () => {
  const { shows, currentShow, isGenerating, generateShow, loadShow } = useRadioXAPI();

  return (
    <div>
      <button 
        onClick={() => generateShow({ channel: 'zurich', news_count: 3 })}
        disabled={isGenerating}
      >
        {isGenerating ? 'Generating...' : 'Generate Show'}
      </button>

      <div className="shows-list">
        {shows.map(show => (
          <div key={show.id} onClick={() => loadShow(show.id)}>
            <h3>{show.title}</h3>
            <p>{show.script_preview}</p>
          </div>
        ))}
      </div>

      {currentShow && (
        <div>
          <AudioPlayer show={currentShow} />
          <div className="transcript">
            {currentShow.segments.map((segment, i) => (
              <p key={i}><strong>{segment.speaker}:</strong> {segment.text}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

## 🧪 **Test API Calls**

```bash
# Test shows list
curl "https://api.radiox.cloud/api/v1/shows?limit=5"

# Test specific show
curl "https://api.radiox.cloud/api/v1/shows/f8d34ee2-7d58-4182-acd9-0dc403989a9b"

# Test generation
curl -X POST "https://api.radiox.cloud/api/v1/shows/generate" \
  -H "Content-Type: application/json" \
  -d '{"channel": "zurich", "news_count": 3}'
```

## 🎯 **Example Response (Shows List)**

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

---

**✅ Ready to copy-paste into radiox-frontend!** 