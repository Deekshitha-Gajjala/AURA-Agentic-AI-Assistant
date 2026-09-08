import os
import re

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_MAX_RESULTS = 5
MAX_RESULTS_LIMIT = 10

MAX_TRANSCRIPT_CHARACTERS = 12000


# ============================================================
# YOUTUBE SEARCH
# ============================================================

def search_youtube(
    query: str,
    max_results: int = DEFAULT_MAX_RESULTS
):
    """
    Search YouTube videos using the YouTube Data API.

    Returns a structured dictionary containing video metadata.
    """

    if not query or not query.strip():

        return {
            "success": False,
            "message": "YouTube search query cannot be empty."
        }

    query = query.strip()

    # Keep API requests reasonable.
    max_results = max(
        1,
        min(
            int(max_results),
            MAX_RESULTS_LIMIT
        )
    )

    print("\n==============================")
    print("YOUTUBE SEARCH STARTED")
    print("QUERY:", query)
    print("==============================")

    # --------------------------------------------------------
    # API key validation
    # --------------------------------------------------------

    if not YOUTUBE_API_KEY:

        print(
            "ERROR: YOUTUBE_API_KEY is missing"
        )

        return {
            "success": False,
            "message": (
                "YOUTUBE_API_KEY is missing from .env"
            )
        }

    try:

        # ----------------------------------------------------
        # Build YouTube API client
        # ----------------------------------------------------

        youtube = build(
            "youtube",
            "v3",
            developerKey=YOUTUBE_API_KEY
        )

        # ----------------------------------------------------
        # Search videos
        # ----------------------------------------------------

        response = (
            youtube.search()
            .list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order="relevance",
                regionCode="IN",
                relevanceLanguage="en"
            )
            .execute()
        )

        videos = []
        seen_video_ids = set()

        # ----------------------------------------------------
        # Process results
        # ----------------------------------------------------

        for item in response.get(
            "items",
            []
        ):

            video_id = (
                item
                .get("id", {})
                .get("videoId")
            )

            if not video_id:
                continue

            # Prevent duplicates.
            if video_id in seen_video_ids:
                continue

            seen_video_ids.add(
                video_id
            )

            snippet = item.get(
                "snippet",
                {}
            )

            videos.append(
                {
                    "video_id": video_id,

                    "title": snippet.get(
                        "title",
                        ""
                    ),

                    "channel": snippet.get(
                        "channelTitle",
                        ""
                    ),

                    "published_at": snippet.get(
                        "publishedAt",
                        ""
                    ),

                    "description": snippet.get(
                        "description",
                        ""
                    ),

                    "thumbnail": (
                        snippet
                        .get("thumbnails", {})
                        .get("high", {})
                        .get("url")
                        or
                        snippet
                        .get("thumbnails", {})
                        .get("default", {})
                        .get("url", "")
                    ),

                    "url": (
                        "https://www.youtube.com/watch?v="
                        + video_id
                    )
                }
            )

        print(
            "Videos found:",
            len(videos)
        )

        return {
            "success": True,
            "query": query,
            "videos": videos
        }

    except HttpError as e:

        print(
            "YOUTUBE API ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "message": (
                "YouTube API request failed."
            ),
            "error": str(e)
        }

    except Exception as e:

        print(
            "YOUTUBE SEARCH ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# EXTRACT VIDEO ID
# ============================================================

def extract_video_id(
    url_or_id: str
):
    """
    Extract an 11-character YouTube video ID from:
    
    - Raw video ID
    - youtube.com/watch?v=...
    - youtu.be/...
    - youtube.com/shorts/...
    - youtube.com/embed/...
    """

    if not url_or_id:
        return None

    url_or_id = url_or_id.strip()

    # --------------------------------------------------------
    # Already a YouTube video ID
    # --------------------------------------------------------

    if re.fullmatch(
        r"[A-Za-z0-9_-]{11}",
        url_or_id
    ):
        return url_or_id

    # --------------------------------------------------------
    # Standard YouTube watch URL
    # --------------------------------------------------------

    patterns = [

        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})",

        r"(?:https?://)?(?:www\.)?youtube\.com/watch/([A-Za-z0-9_-]{11})",

        r"(?:https?://)?youtu\.be/([A-Za-z0-9_-]{11})",

        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})",

        r"(?:https?://)?(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})",

        r"(?:https?://)?(?:www\.)?youtube-nocookie\.com/embed/([A-Za-z0-9_-]{11})"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            url_or_id,
            flags=re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# ============================================================
# GET YOUTUBE TRANSCRIPT
# ============================================================

def get_youtube_transcript(
    video_id: str
):
    """
    Retrieve a YouTube transcript.

    Preference:
        1. English
        2. Hindi
        3. First available transcript

    Works with both manually-created and
    automatically-generated transcripts.
    """

    if not video_id:

        return {
            "success": False,
            "message": "Invalid YouTube video ID."
        }

    # Validate the ID before making the request.
    if not re.fullmatch(
        r"[A-Za-z0-9_-]{11}",
        video_id
    ):

        return {
            "success": False,
            "video_id": video_id,
            "message": "Invalid YouTube video ID."
        }

    try:

        print(
            "\nGetting transcript for:",
            video_id
        )

        api = YouTubeTranscriptApi()

        # ----------------------------------------------------
        # Get available transcripts
        # ----------------------------------------------------

        transcript_list = api.list(
            video_id
        )

        available_transcripts = []

        for transcript in transcript_list:

            available_transcripts.append(
                transcript
            )

            print(
                "-",
                transcript.language,
                "(",
                transcript.language_code,
                ")",
                "generated=",
                transcript.is_generated
            )

        if not available_transcripts:

            return {
                "success": False,
                "video_id": video_id,
                "message": (
                    "No transcript is available "
                    "for this video."
                )
            }

        # ----------------------------------------------------
        # Select preferred transcript
        # ----------------------------------------------------

        selected_transcript = None

        # First preference: English
        for transcript in available_transcripts:

            if (
                transcript.language_code
                .lower()
                == "en"
            ):

                selected_transcript = transcript
                break

        # Second preference: Hindi
        if selected_transcript is None:

            for transcript in available_transcripts:

                if (
                    transcript.language_code
                    .lower()
                    == "hi"
                ):

                    selected_transcript = transcript
                    break

        # Third preference: first available
        if selected_transcript is None:

            selected_transcript = (
                available_transcripts[0]
            )

        print(
            "\nSelected transcript:",
            selected_transcript.language,
            "(",
            selected_transcript.language_code,
            ")"
        )

        # ----------------------------------------------------
        # Fetch transcript
        # ----------------------------------------------------

        fetched_transcript = (
            selected_transcript.fetch()
        )

        # ----------------------------------------------------
        # Convert transcript snippets to text
        # ----------------------------------------------------

        text_parts = []

        for snippet in fetched_transcript:

            # Current youtube-transcript-api returns
            # FetchedTranscriptSnippet objects.
            text = getattr(
                snippet,
                "text",
                None
            )

            if text:

                text_parts.append(
                    text.strip()
                )

        text = " ".join(
            part
            for part in text_parts
            if part
        ).strip()

        if not text:

            return {
                "success": False,
                "video_id": video_id,
                "message": (
                    "Transcript was found but "
                    "contains no readable text."
                )
            }

        # ----------------------------------------------------
        # Prevent very large transcripts from being passed
        # directly into the LLM.
        # ----------------------------------------------------

        was_truncated = False

        if len(text) > MAX_TRANSCRIPT_CHARACTERS:

            text = text[
                :MAX_TRANSCRIPT_CHARACTERS
            ]

            was_truncated = True

        print(
            "Transcript characters:",
            len(text)
        )

        return {
            "success": True,
            "video_id": video_id,

            "language": (
                selected_transcript.language
            ),

            "language_code": (
                selected_transcript.language_code
            ),

            "is_generated": (
                selected_transcript.is_generated
            ),

            "transcript": text,

            "truncated": was_truncated
        }

    except Exception as e:

        print(
            "YOUTUBE TRANSCRIPT ERROR:",
            repr(e)
        )

        return {
            "success": False,
            "video_id": video_id,
            "message": str(e)
        }


# ============================================================
# GET TRANSCRIPT FROM URL
# ============================================================

def get_transcript_from_url(
    url: str
):
    """
    Extract a video ID from a YouTube URL and
    retrieve its transcript.
    """

    if not url:

        return {
            "success": False,
            "message": (
                "YouTube URL was not provided."
            )
        }

    video_id = extract_video_id(
        url
    )

    if not video_id:

        return {
            "success": False,
            "message": (
                "Could not extract a valid "
                "YouTube video ID."
            )
        }

    return get_youtube_transcript(
        video_id
    )