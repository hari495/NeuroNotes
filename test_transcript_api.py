"""
Test the youtube-transcript-api directly to isolate the issue.
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)


def test_transcript_fetch(video_id: str):
    """Test fetching a transcript for a video."""
    print(f"\n{'=' * 60}")
    print(f"Testing Video ID: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")
    print('=' * 60)

    try:
        print("Attempting to fetch transcript...")
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])

        print(f"✅ SUCCESS! Fetched {len(transcript_list)} segments")
        print(f"\nFirst 3 segments:")
        for i, segment in enumerate(transcript_list[:3]):
            print(f"  {i+1}. [{segment['start']:.1f}s] {segment['text'][:60]}...")

        # Combine all text
        full_text = " ".join(segment["text"] for segment in transcript_list)
        print(f"\nTotal characters: {len(full_text)}")
        print(f"Preview: {full_text[:200]}...")

        return True

    except NoTranscriptFound as e:
        print(f"❌ FAILED: NoTranscriptFound")
        print(f"   Error: {str(e)}")
        print(f"   This video may not have captions enabled.")

        # Try to get any available transcript
        try:
            print("\n   Trying to fetch ANY available transcript...")
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            print(f"   ✅ Found transcript in another language: {len(transcript_list)} segments")
            return True
        except Exception as e2:
            print(f"   ❌ No transcripts available at all: {str(e2)}")
            return False

    except TranscriptsDisabled as e:
        print(f"❌ FAILED: TranscriptsDisabled")
        print(f"   Error: {str(e)}")
        print(f"   The video owner has disabled transcripts for this video.")
        return False

    except VideoUnavailable as e:
        print(f"❌ FAILED: VideoUnavailable")
        print(f"   Error: {str(e)}")
        print(f"   The video is private, deleted, or doesn't exist.")
        return False

    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        import traceback
        print(f"\n   Full traceback:")
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("YouTube Transcript API Test")
    print("=" * 60)

    # Test with known working videos
    test_videos = [
        ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up"),
        ("jNQXAC9IVRw", "Me at the zoo (first YouTube video)"),
        ("9bZkp7q19f0", "PSY - GANGNAM STYLE"),
    ]

    results = []
    for video_id, description in test_videos:
        success = test_transcript_fetch(video_id)
        results.append((video_id, description, success))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for video_id, description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {video_id} - {description}")


if __name__ == "__main__":
    main()
