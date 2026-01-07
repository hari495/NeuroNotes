"""
Test video title fetching using YouTube oEmbed API.
"""

import asyncio
import httpx


async def fetch_video_title(video_id: str) -> str:
    """
    Fetch the video title from YouTube using the oEmbed API.
    """
    try:
        # Use YouTube oEmbed API (official and more reliable)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        print(f"\nFetching title for video ID: {video_id}")
        print(f"URL: {oembed_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(oembed_url, headers=headers, timeout=10.0)

            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"Response Data: {data}")
                title = data.get("title", f"YouTube Video {video_id}")
                print(f"✅ Title: {title}")
                return title.strip()
            else:
                print(f"❌ oEmbed API returned status {response.status_code}")
                print(f"Response: {response.text}")
                return f"YouTube Video {video_id}"

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return f"YouTube Video {video_id}"


async def main():
    print("=" * 60)
    print("YouTube Video Title Fetching Test")
    print("=" * 60)

    test_videos = [
        ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up"),
        ("jNQXAC9IVRw", "Me at the zoo"),
        ("9bZkp7q19f0", "PSY - GANGNAM STYLE"),
    ]

    for video_id, expected_title in test_videos:
        print(f"\n{'=' * 60}")
        title = await fetch_video_title(video_id)
        print(f"\nExpected (approx): {expected_title}")
        print(f"Got: {title}")

        if expected_title.lower() in title.lower() or title.lower() in expected_title.lower():
            print("✅ PASS - Title matches expected")
        else:
            print("⚠️  WARNING - Title might not match expected (but could still be correct)")


if __name__ == "__main__":
    asyncio.run(main())
