"""
Test YouTube transcript fetching with cookies.
"""

import pathlib
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


def test_with_cookies():
    """Test fetching transcripts with cookies."""
    cookies_path = pathlib.Path("youtube_cookies.txt")

    print("=" * 60)
    print("YouTube Transcript API - Cookies Test")
    print("=" * 60)

    # Check if cookies file exists
    if not cookies_path.exists():
        print("\n❌ ERROR: youtube_cookies.txt not found!")
        print("\nPlease follow these steps:")
        print("1. Install a cookie exporter extension (see YOUTUBE_COOKIES_SETUP.md)")
        print("2. Go to YouTube.com (make sure you're logged in)")
        print("3. Export cookies as 'youtube_cookies.txt'")
        print("4. Place the file in the project root directory")
        print("\nFor detailed instructions, see: YOUTUBE_COOKIES_SETUP.md")
        return False

    print(f"\n✅ Found cookies file: {cookies_path}")
    print(f"   File size: {cookies_path.stat().st_size} bytes")

    # Test with a known video
    video_id = "dQw4w9WgXcQ"
    print(f"\n📺 Testing with video: {video_id}")
    print(f"   URL: https://www.youtube.com/watch?v={video_id}")

    try:
        print("\n🔄 Fetching transcript with cookies...")
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=['en'],
            cookies=str(cookies_path),
        )

        print(f"\n✅ SUCCESS! Fetched {len(transcript_list)} transcript segments")
        print(f"\nFirst 3 segments:")
        for i, segment in enumerate(transcript_list[:3]):
            text = segment['text'][:60]
            print(f"  {i+1}. [{segment['start']:.1f}s] {text}...")

        # Combine all text
        full_text = " ".join(segment["text"] for segment in transcript_list)
        print(f"\n📊 Stats:")
        print(f"   Total segments: {len(transcript_list)}")
        print(f"   Total characters: {len(full_text)}")
        print(f"   Preview: {full_text[:150]}...")

        print("\n" + "=" * 60)
        print("✅ COOKIES ARE WORKING!")
        print("=" * 60)
        print("\nYou can now use the YouTube import feature in the app.")
        print("Make sure to restart the backend if it's running:")
        print("  python main.py")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}")
        print(f"   Error: {str(e)}")

        if "ParseError" in str(type(e).__name__) or "no element found" in str(e):
            print("\n🔧 Troubleshooting:")
            print("   1. Your cookies might be expired - try re-exporting them")
            print("   2. Make sure you're logged into YouTube when exporting")
            print("   3. Try using a different browser to export cookies")
            print("   4. Make sure the cookies file is in Netscape format")
        elif "NoTranscriptFound" in str(type(e).__name__):
            print("\n🔧 This error means cookies are working, but:")
            print("   The video doesn't have English captions")
            print("   Try a different video or let the API fetch any available language")
        else:
            print("\n🔧 Unexpected error. Please check:")
            print("   1. Cookies file format is correct")
            print("   2. You're using youtube-transcript-api version 0.6.3")
            print("   3. See full error above for details")

        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

        return False


if __name__ == "__main__":
    success = test_with_cookies()
    exit(0 if success else 1)
