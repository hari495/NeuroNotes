"""
Test YouTube URL parsing to debug import issues.
"""

import re
from urllib.parse import parse_qs, urlparse


def extract_video_id(url: str) -> str:
    """
    Extract the video ID from a YouTube URL.
    """
    print(f"\n=== Testing URL: {url} ===")

    # Parse the URL
    parsed_url = urlparse(url)
    print(f"Parsed URL:")
    print(f"  - scheme: {parsed_url.scheme}")
    print(f"  - hostname: {parsed_url.hostname}")
    print(f"  - path: {parsed_url.path}")
    print(f"  - query: {parsed_url.query}")

    # Handle youtu.be short URLs
    if parsed_url.hostname in ("youtu.be", "www.youtu.be"):
        video_id = parsed_url.path.lstrip("/").split("/")[0].split("?")[0]
        print(f"  -> Extracted from youtu.be: {video_id}")
        if video_id:
            return video_id

    # Handle youtube.com URLs
    if parsed_url.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        # Handle /watch?v=VIDEO_ID
        if parsed_url.path == "/watch":
            query_params = parse_qs(parsed_url.query)
            print(f"  -> Query params: {query_params}")
            if "v" in query_params:
                video_id = query_params["v"][0]
                print(f"  -> Extracted from /watch: {video_id}")
                if video_id:
                    return video_id

        # Handle /embed/VIDEO_ID or /v/VIDEO_ID
        if parsed_url.path.startswith(("/embed/", "/v/")):
            video_id = parsed_url.path.split("/")[2].split("?")[0]
            print(f"  -> Extracted from embed/v: {video_id}")
            if video_id:
                return video_id

    # Try regex as fallback
    print("  -> Trying regex patterns...")
    regex_patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/|v\/|youtu\.be\/)([0-9A-Za-z_-]{11})",
    ]

    for i, pattern in enumerate(regex_patterns):
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            print(f"  -> Pattern {i+1} matched: {video_id}")
            return video_id
        else:
            print(f"  -> Pattern {i+1} did not match")

    raise ValueError(f"Could not extract video ID from URL: {url}")


# Test with various URL formats
test_urls = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "https://www.youtube.com/embed/dQw4w9WgXcQ",
    "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
    "www.youtube.com/watch?v=dQw4w9WgXcQ",  # No scheme
    "youtube.com/watch?v=dQw4w9WgXcQ",  # No scheme or www
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s",  # With timestamp
]

print("=" * 60)
print("YouTube URL Parsing Test")
print("=" * 60)

for url in test_urls:
    try:
        video_id = extract_video_id(url)
        print(f"✅ SUCCESS: Video ID = {video_id}")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
    print()
