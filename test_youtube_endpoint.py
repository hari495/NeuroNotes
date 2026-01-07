"""
Test the YouTube import endpoint directly.
"""

import asyncio
import httpx


async def test_youtube_import():
    """Test importing a YouTube video."""
    url = "http://localhost:8000/api/notes/youtube"

    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
    ]

    for youtube_url in test_urls:
        print(f"\n{'=' * 60}")
        print(f"Testing: {youtube_url}")
        print('=' * 60)

        payload = {
            "url": youtube_url,
            "language": "en",
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                print(f"Sending POST request to {url}")
                print(f"Payload: {payload}")
                response = await client.post(url, json=payload)
                print(f"\nStatus Code: {response.status_code}")
                print(f"Response: {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"\n✅ SUCCESS!")
                    print(f"Video Title: {data.get('video_title')}")
                    print(f"Video ID: {data.get('video_id')}")
                    print(f"Chunks Created: {data.get('chunks_created')}")
                else:
                    print(f"\n❌ FAILED!")
                    try:
                        error_data = response.json()
                        print(f"Error: {error_data.get('detail')}")
                    except:
                        print(f"Error: {response.text}")

        except httpx.ConnectError as e:
            print(f"\n❌ CONNECTION ERROR: Cannot connect to {url}")
            print(f"Make sure the backend is running on http://localhost:8000")
            print(f"Error: {str(e)}")
        except Exception as e:
            print(f"\n❌ ERROR: {type(e).__name__}")
            print(f"Message: {str(e)}")


if __name__ == "__main__":
    print("YouTube Import Endpoint Test")
    print("Make sure the backend is running on http://localhost:8000")
    print()
    asyncio.run(test_youtube_import())
