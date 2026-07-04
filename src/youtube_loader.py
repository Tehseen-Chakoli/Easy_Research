"""YouTube transcript loading for research ingestion."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def extract_youtube_video_id(youtube_url: str) -> str:
    """Extract a video identifier from supported YouTube URL shapes."""
    parsed_url = urlparse(youtube_url)

    if parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
        if parsed_url.path == "/watch":
            return parse_qs(parsed_url.query).get("v", [None])[0]
        if parsed_url.path.startswith("/shorts/"):
            return parsed_url.path.split("/shorts/")[1].split("/")[0]

    if parsed_url.hostname == "youtu.be":
        return parsed_url.path.lstrip("/")

    raise ValueError("Invalid or unsupported YouTube URL.")


def load_youtube_transcript(youtube_url: str) -> str:
    """Fetch the transcript text for a YouTube video."""
    video_id = extract_youtube_video_id(youtube_url)

    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
    except Exception as exc:
        raise RuntimeError(
            "Failed to fetch transcript. This video may not have captions enabled."
        ) from exc

    transcript_text = " ".join(
        snippet.text.replace("\n", " ").strip()
        for snippet in transcript
    )
    return transcript_text.strip()


def create_extracted_item_from_youtube(youtube_url: str) -> dict:
    """Normalize a YouTube transcript into the shared extracted-item schema."""
    video_id = extract_youtube_video_id(youtube_url)
    transcript_text = load_youtube_transcript(youtube_url)

    if not transcript_text:
        raise ValueError("Transcript is empty.")

    return {
        "title": f"YouTube Video - {video_id}",
        "url": youtube_url,
        "snippet": "YouTube transcript content",
        "content": transcript_text,
        "extraction_method": "youtube_transcript",
        "source_type": "youtube",
        "video_id": video_id,
    }
