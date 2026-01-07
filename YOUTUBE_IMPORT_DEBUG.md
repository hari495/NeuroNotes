# YouTube Import Debugging Guide

This guide helps you troubleshoot issues with YouTube video imports.

## Quick Test: Is the Backend Running?

1. **Check if the backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response: `{"status":"healthy","version":"..."}`

2. **Test the YouTube endpoint directly:**
   ```bash
   python test_youtube_endpoint.py
   ```

## Common Issues & Solutions

### Issue 1: "No response from server"

**Cause:** Backend is not running or running on a different port.

**Solution:**
1. Start the backend:
   ```bash
   python main.py
   ```
   Or:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. Verify it's running on port 8000:
   ```bash
   curl http://localhost:8000/health
   ```

### Issue 2: "Could not extract video ID from URL"

**Cause:** Invalid YouTube URL format.

**Solution:**
Test your URL parsing:
```bash
python test_youtube_url.py
```

Supported URL formats:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`
- `https://m.youtube.com/watch?v=VIDEO_ID`

### Issue 3: "No transcript available for this video"

**Cause:** The video doesn't have captions/subtitles enabled.

**Solution:**
- Choose a different video that has captions
- Check if the video has captions by looking for the "CC" button on YouTube
- Some videos only have auto-generated captions in specific languages

### Issue 4: "Transcripts are disabled for this video"

**Cause:** The video owner disabled transcript access.

**Solution:**
- Try a different video
- This is a limitation of the YouTube Transcript API

### Issue 5: Frontend shows "Processing video..." forever

**Cause:** Backend is taking too long or errored without returning a response.

**Solution:**
1. Check backend logs for errors
2. Check browser console (F12) for error details
3. The timeout is set to 2 minutes - very long videos may take this long

### Issue 6: CORS errors in browser console

**Cause:** CORS middleware configuration.

**Solution:**
The main.py already has CORS enabled for all origins. If you still see errors:
1. Make sure the frontend is calling the correct backend URL
2. Check that the backend is actually running on the expected port

## Step-by-Step Debugging

### Step 1: Test URL Parsing
```bash
python test_youtube_url.py
```
This will show you if the URL extraction is working correctly.

### Step 2: Test Backend Endpoint
```bash
python test_youtube_endpoint.py
```
This tests the actual API endpoint with real HTTP requests.

### Step 3: Check Backend Logs

Start the backend and watch the logs:
```bash
python main.py
```

When you import a video, you should see:
```
🎥 Starting YouTube video ingestion...
   URL: https://...
   Video ID: ...
📺 Fetching video title...
   Title: ...
📥 Fetching transcript (language: en)...
✓ Transcript fetched: X segments
🔄 Processing transcript segments...
✓ Transcript combined: X characters
🔄 Starting chunking and embedding process...
📄 Chunking complete: X chunks created
🔄 Processing in batches of 50...
⏳ Processing batch 1/Y (chunks 1-50/X)...
✓ Batch 1/Y completed successfully (50/X chunks processed)
...
✅ YouTube video ingestion completed successfully!
```

### Step 4: Check Frontend Console

Open browser console (F12) and look for:
```javascript
Importing YouTube video: https://...
Backend response: {video_id: "...", video_title: "...", ...}
```

### Step 5: Check Network Tab

1. Open browser DevTools (F12)
2. Go to Network tab
3. Try importing a video
4. Look for POST request to `/api/notes/youtube`
5. Check:
   - Status code (should be 200)
   - Request payload
   - Response data
   - Any error messages

## Testing with a Known Working Video

Use this video (has captions enabled):
```
https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

Expected result:
- Video Title: "Rick Astley - Never Gonna Give You Up (Official Video)"
- Should create multiple chunks
- Should import successfully

## Still Having Issues?

1. **Check backend requirements are installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make sure Ollama is running** (for embeddings):
   ```bash
   ollama list
   ```

3. **Check ChromaDB path exists**:
   ```bash
   ls -la data/chroma
   ```

4. **Check for port conflicts**:
   ```bash
   lsof -i :8000
   ```

5. **Restart everything**:
   ```bash
   # Kill backend
   pkill -f "python main.py"

   # Kill frontend
   pkill -f "vite"

   # Restart backend
   python main.py &

   # Restart frontend
   cd frontend && npm run dev &
   ```

## Error Messages Reference

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Could not extract video ID from URL" | Invalid URL format | Use a proper YouTube URL |
| "No transcript available" | Video has no captions | Choose a video with captions |
| "Transcripts are disabled" | Owner disabled transcripts | Try a different video |
| "Video is unavailable or private" | Video is private/deleted | Use a public video |
| "No response from server" | Backend not running | Start the backend |
| "Network Error" | Backend URL is wrong | Check VITE_API_URL in frontend |
| "Timeout" | Processing took too long | Video might be too long or backend is slow |

## Contact & Support

If none of these solutions work, check:
1. Backend logs (terminal where `python main.py` is running)
2. Frontend console (browser DevTools, F12)
3. Network requests (browser DevTools → Network tab)
4. Browser console for JavaScript errors
