#!/usr/bin/env python3
"""
YouTube Transcriber & Translator
Transcribes YouTube videos, translates foreign languages to English,
and exports results to Google Docs.
"""

import streamlit as st
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import tempfile

# YouTube libraries
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from pytubefix import YouTube
from deep_translator import GoogleTranslator

# Google Docs libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Page config
st.set_page_config(
    page_title="YouTube Transcriber & Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Google Docs API Scopes
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']

# Language codes mapping
LANGUAGE_NAMES = {
    'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
    'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
    'ko': 'Korean', 'zh': 'Chinese', 'zh-Hans': 'Chinese (Simplified)',
    'zh-Hant': 'Chinese (Traditional)', 'ar': 'Arabic', 'hi': 'Hindi',
    'th': 'Thai', 'vi': 'Vietnamese', 'id': 'Indonesian', 'tr': 'Turkish',
    'pl': 'Polish', 'nl': 'Dutch', 'sv': 'Swedish', 'da': 'Danish',
    'fi': 'Finnish', 'no': 'Norwegian', 'uk': 'Ukrainian', 'cs': 'Czech',
    'el': 'Greek', 'he': 'Hebrew', 'ro': 'Romanian', 'hu': 'Hungarian'
}


def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/watch\?.*v=)([a-zA-Z0-9_-]{11})',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Check if it's already just a video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url.strip()):
        return url.strip()

    return None


def get_video_metadata(video_id: str) -> dict:
    """Get video metadata using pytubefix"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url)

        # Determine if it's a short based on duration (shorts are <= 60 seconds)
        is_short = yt.length <= 60 if yt.length else False

        return {
            'video_id': video_id,
            'title': yt.title,
            'channel_name': yt.author,
            'channel_url': yt.channel_url,
            'thumbnail_url': yt.thumbnail_url,
            'duration': yt.length,
            'views': yt.views,
            'publish_date': yt.publish_date.strftime('%Y-%m-%d') if yt.publish_date else 'Unknown',
            'video_url': url,
            'is_short': is_short,
            'video_type': 'Short' if is_short else 'Video'
        }
    except Exception as e:
        return {'error': str(e), 'video_id': video_id}


def get_transcript(video_id: str, translate_to_english: bool = True) -> dict:
    """
    Get transcript for a YouTube video.
    Returns original transcript and English translation if needed.
    """
    try:
        # Get list of available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to get manually created transcript first, then auto-generated
        transcript = None
        original_language = None
        is_auto_generated = False

        # First try manually created transcripts
        try:
            for t in transcript_list:
                if not t.is_generated:
                    transcript = t
                    original_language = t.language_code
                    break
        except:
            pass

        # If no manual transcript, try auto-generated
        if transcript is None:
            try:
                for t in transcript_list:
                    if t.is_generated:
                        transcript = t
                        original_language = t.language_code
                        is_auto_generated = True
                        break
            except:
                pass

        # If still no transcript, try to get any available
        if transcript is None:
            try:
                transcript = transcript_list.find_transcript(['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'])
                original_language = transcript.language_code
            except:
                # Get the first available transcript
                for t in transcript_list:
                    transcript = t
                    original_language = t.language_code
                    break

        if transcript is None:
            return {'error': 'No transcript available', 'video_id': video_id}

        # Fetch the transcript data
        transcript_data = transcript.fetch()

        # Combine all text segments
        original_text = ' '.join([entry['text'] for entry in transcript_data])

        # Determine if translation is needed
        needs_translation = original_language and not original_language.startswith('en')
        translated_text = None

        if needs_translation and translate_to_english:
            try:
                # Use deep-translator for translation
                translator = GoogleTranslator(source='auto', target='en')

                # Split text into chunks if too long (Google Translate has limits)
                max_chars = 4500
                if len(original_text) > max_chars:
                    chunks = [original_text[i:i+max_chars] for i in range(0, len(original_text), max_chars)]
                    translated_chunks = [translator.translate(chunk) for chunk in chunks]
                    translated_text = ' '.join(translated_chunks)
                else:
                    translated_text = translator.translate(original_text)
            except Exception as e:
                translated_text = f"Translation error: {str(e)}"

        language_name = LANGUAGE_NAMES.get(original_language, original_language)

        return {
            'video_id': video_id,
            'original_language': original_language,
            'language_name': language_name,
            'is_auto_generated': is_auto_generated,
            'original_transcript': original_text,
            'english_transcript': translated_text if needs_translation else original_text,
            'was_translated': needs_translation,
            'transcript_segments': transcript_data
        }

    except TranscriptsDisabled:
        return {'error': 'Transcripts are disabled for this video', 'video_id': video_id}
    except NoTranscriptFound:
        return {'error': 'No transcript found for this video', 'video_id': video_id}
    except Exception as e:
        return {'error': str(e), 'video_id': video_id}


def get_google_credentials():
    """Get or refresh Google API credentials"""
    creds = None
    token_path = Path('token.pickle')

    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except:
            creds = None

    return creds


def authenticate_google():
    """Authenticate with Google OAuth"""
    try:
        # Check for credentials in Streamlit secrets
        if 'GOOGLE_CLIENT_ID' in st.secrets and 'GOOGLE_CLIENT_SECRET' in st.secrets:
            client_config = {
                "installed": {
                    "client_id": st.secrets['GOOGLE_CLIENT_ID'],
                    "client_secret": st.secrets['GOOGLE_CLIENT_SECRET'],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        elif Path('credentials.json').exists():
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        else:
            return None, "No Google credentials found. Please add credentials.json or set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in secrets."

        creds = flow.run_local_server(port=0)

        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

        return creds, None
    except Exception as e:
        return None, str(e)


def create_google_doc(results: list, doc_title: str = None) -> dict:
    """
    Create a Google Doc with transcription results.

    Returns dict with 'doc_url' on success or 'error' on failure.
    """
    creds = get_google_credentials()

    if not creds or not creds.valid:
        return {'error': 'Not authenticated with Google. Please authenticate first.'}

    try:
        # Build the Docs and Drive services
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # Create document title
        if not doc_title:
            doc_title = f"YouTube Transcriptions - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Create a new document
        doc = docs_service.documents().create(body={'title': doc_title}).execute()
        doc_id = doc.get('documentId')

        # Build the document content
        requests = []
        current_index = 1

        for i, result in enumerate(results):
            metadata = result.get('metadata', {})
            transcript = result.get('transcript', {})

            if 'error' in metadata:
                continue

            # Channel Name as main heading
            channel_text = f"{metadata.get('channel_name', 'Unknown Channel')}\n"
            requests.append({
                'insertText': {'location': {'index': current_index}, 'text': channel_text}
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_index, 'endIndex': current_index + len(channel_text)},
                    'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                    'fields': 'namedStyleType'
                }
            })
            current_index += len(channel_text)

            # Video Title
            title_text = f"{metadata.get('title', 'Unknown Title')}\n"
            requests.append({
                'insertText': {'location': {'index': current_index}, 'text': title_text}
            })
            requests.append({
                'updateParagraphStyle': {
                    'range': {'startIndex': current_index, 'endIndex': current_index + len(title_text)},
                    'paragraphStyle': {'namedStyleType': 'HEADING_2'},
                    'fields': 'namedStyleType'
                }
            })
            current_index += len(title_text)

            # Video Link
            link_text = f"Video Link: {metadata.get('video_url', '')}\n"
            requests.append({
                'insertText': {'location': {'index': current_index}, 'text': link_text}
            })
            current_index += len(link_text)

            # Video Type (Short or Video)
            type_text = f"Type: {metadata.get('video_type', 'Video')} | Duration: {metadata.get('duration', 0)} seconds\n"
            requests.append({
                'insertText': {'location': {'index': current_index}, 'text': type_text}
            })
            current_index += len(type_text)

            # Thumbnail (as inline image)
            thumbnail_url = metadata.get('thumbnail_url', '')
            if thumbnail_url:
                thumb_text = f"Thumbnail: {thumbnail_url}\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': thumb_text}
                })
                current_index += len(thumb_text)

                # Try to insert inline image
                try:
                    requests.append({
                        'insertInlineImage': {
                            'location': {'index': current_index},
                            'uri': thumbnail_url,
                            'objectSize': {
                                'height': {'magnitude': 200, 'unit': 'PT'},
                                'width': {'magnitude': 356, 'unit': 'PT'}
                            }
                        }
                    })
                    current_index += 1
                    requests.append({
                        'insertText': {'location': {'index': current_index}, 'text': '\n'}
                    })
                    current_index += 1
                except:
                    pass

            # Language info
            if 'error' not in transcript:
                lang_info = f"Original Language: {transcript.get('language_name', 'Unknown')}"
                if transcript.get('was_translated'):
                    lang_info += " (Translated to English)"
                if transcript.get('is_auto_generated'):
                    lang_info += " [Auto-generated]"
                lang_info += "\n\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': lang_info}
                })
                current_index += len(lang_info)

                # Transcript heading
                transcript_heading = "Transcript (English):\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': transcript_heading}
                })
                requests.append({
                    'updateParagraphStyle': {
                        'range': {'startIndex': current_index, 'endIndex': current_index + len(transcript_heading)},
                        'paragraphStyle': {'namedStyleType': 'HEADING_3'},
                        'fields': 'namedStyleType'
                    }
                })
                current_index += len(transcript_heading)

                # Transcript content
                transcript_text = transcript.get('english_transcript', 'No transcript available') + "\n\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': transcript_text}
                })
                current_index += len(transcript_text)
            else:
                error_text = f"Transcript Error: {transcript.get('error', 'Unknown error')}\n\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': error_text}
                })
                current_index += len(error_text)

            # Divider between videos
            if i < len(results) - 1:
                divider = "\n" + "=" * 50 + "\n\n"
                requests.append({
                    'insertText': {'location': {'index': current_index}, 'text': divider}
                })
                current_index += len(divider)

        # Execute all requests
        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return {'doc_url': doc_url, 'doc_id': doc_id}

    except Exception as e:
        return {'error': str(e)}


def save_results_json(results: list, filename: str = None) -> str:
    """Save results to JSON file"""
    if not filename:
        filename = f"youtube_transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    output_data = {
        'exported_at': datetime.now().isoformat(),
        'total_videos': len(results),
        'videos': []
    }

    for result in results:
        metadata = result.get('metadata', {})
        transcript = result.get('transcript', {})

        video_data = {
            'channel_name': metadata.get('channel_name', 'Unknown'),
            'title': metadata.get('title', 'Unknown'),
            'video_url': metadata.get('video_url', ''),
            'thumbnail_url': metadata.get('thumbnail_url', ''),
            'video_type': metadata.get('video_type', 'Video'),
            'duration_seconds': metadata.get('duration', 0),
            'views': metadata.get('views', 0),
            'publish_date': metadata.get('publish_date', ''),
            'original_language': transcript.get('language_name', 'Unknown'),
            'was_translated': transcript.get('was_translated', False),
            'english_transcript': transcript.get('english_transcript', ''),
            'error': metadata.get('error') or transcript.get('error')
        }
        output_data['videos'].append(video_data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return filename


# ============== STREAMLIT UI ==============

st.title("YouTube Transcriber & Translator")
st.markdown("**Transcribe YouTube videos, translate to English, and export to Google Docs**")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = []
if 'google_authenticated' not in st.session_state:
    st.session_state.google_authenticated = False

# Check existing Google auth
creds = get_google_credentials()
if creds and creds.valid:
    st.session_state.google_authenticated = True

# Sidebar
with st.sidebar:
    st.header("Settings")

    auto_translate = st.checkbox("Auto-translate to English", value=True,
                                  help="Automatically translate non-English transcripts to English")

    st.divider()

    st.header("Google Docs Export")

    if st.session_state.google_authenticated:
        st.success("Connected to Google")
        if st.button("Disconnect Google"):
            if Path('token.pickle').exists():
                Path('token.pickle').unlink()
            st.session_state.google_authenticated = False
            st.rerun()
    else:
        st.warning("Not connected to Google")
        st.markdown("""
        To export to Google Docs, you need to:
        1. Set up Google Cloud credentials
        2. Add `credentials.json` to this directory

        Or add to Streamlit secrets:
        - `GOOGLE_CLIENT_ID`
        - `GOOGLE_CLIENT_SECRET`
        """)

        if st.button("Connect Google Account"):
            with st.spinner("Authenticating..."):
                creds, error = authenticate_google()
                if creds:
                    st.session_state.google_authenticated = True
                    st.success("Successfully connected!")
                    st.rerun()
                else:
                    st.error(f"Authentication failed: {error}")

    st.divider()

    st.header("About")
    st.markdown("""
    **Features:**
    - Transcribe any YouTube video
    - Auto-detect language
    - Translate to English
    - Support for Shorts & Videos
    - Export to Google Docs
    - Save as JSON
    """)

# Main content area
st.header("Enter YouTube URLs")

url_input = st.text_area(
    "Paste YouTube URLs (one per line)",
    placeholder="https://www.youtube.com/watch?v=VIDEO_ID\nhttps://youtu.be/VIDEO_ID\nhttps://youtube.com/shorts/VIDEO_ID",
    height=150
)

col1, col2 = st.columns([1, 4])
with col1:
    process_button = st.button("Transcribe Videos", type="primary", use_container_width=True)
with col2:
    if st.session_state.results:
        st.info(f"{len(st.session_state.results)} videos processed")

if process_button and url_input.strip():
    urls = [u.strip() for u in url_input.strip().split('\n') if u.strip()]

    if not urls:
        st.warning("Please enter at least one YouTube URL")
    else:
        st.session_state.results = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, url in enumerate(urls):
            video_id = extract_video_id(url)

            if not video_id:
                st.warning(f"Could not extract video ID from: {url}")
                continue

            status_text.text(f"Processing video {i+1}/{len(urls)}: {video_id}")

            # Get metadata
            metadata = get_video_metadata(video_id)

            if 'error' in metadata:
                st.error(f"Error getting metadata for {url}: {metadata['error']}")
                st.session_state.results.append({
                    'metadata': metadata,
                    'transcript': {'error': 'Could not get metadata'}
                })
                continue

            # Get transcript
            transcript = get_transcript(video_id, translate_to_english=auto_translate)

            st.session_state.results.append({
                'metadata': metadata,
                'transcript': transcript
            })

            progress_bar.progress((i + 1) / len(urls))

        status_text.text("Processing complete!")
        st.success(f"Processed {len(st.session_state.results)} videos")

# Display results
if st.session_state.results:
    st.divider()
    st.header("Results")

    # Export buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export to Google Docs", disabled=not st.session_state.google_authenticated):
            with st.spinner("Creating Google Doc..."):
                result = create_google_doc(st.session_state.results)
                if 'doc_url' in result:
                    st.success("Google Doc created!")
                    st.markdown(f"[Open Google Doc]({result['doc_url']})")
                else:
                    st.error(f"Error: {result.get('error', 'Unknown error')}")

    with col2:
        if st.button("Download as JSON"):
            filename = save_results_json(st.session_state.results)
            with open(filename, 'r') as f:
                st.download_button(
                    label="Download JSON File",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json"
                )

    with col3:
        if st.button("Clear Results"):
            st.session_state.results = []
            st.rerun()

    # Display each video result
    for i, result in enumerate(st.session_state.results):
        metadata = result.get('metadata', {})
        transcript = result.get('transcript', {})

        if 'error' in metadata:
            with st.expander(f"Video {i+1}: Error - {metadata.get('video_id', 'Unknown')}", expanded=False):
                st.error(metadata['error'])
            continue

        video_type_emoji = "[SHORT]" if metadata.get('is_short') else "[VIDEO]"

        with st.expander(
            f"{video_type_emoji} {metadata.get('channel_name', 'Unknown')} - {metadata.get('title', 'Unknown')[:50]}...",
            expanded=(i == 0)
        ):
            # Two columns: thumbnail and info
            col1, col2 = st.columns([1, 2])

            with col1:
                # Thumbnail
                if metadata.get('thumbnail_url'):
                    st.image(metadata['thumbnail_url'], use_container_width=True)

                # Video type badge
                if metadata.get('is_short'):
                    st.markdown("**YouTube Short**")
                else:
                    st.markdown("**YouTube Video**")

            with col2:
                st.markdown(f"### {metadata.get('title', 'Unknown Title')}")
                st.markdown(f"**Channel:** [{metadata.get('channel_name', 'Unknown')}]({metadata.get('channel_url', '#')})")
                st.markdown(f"**Video URL:** [{metadata.get('video_url', '')}]({metadata.get('video_url', '')})")

                # Stats
                duration = metadata.get('duration', 0)
                duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"

                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("Duration", duration_str)
                with stats_col2:
                    views = metadata.get('views', 0)
                    views_str = f"{views:,}" if views else "Unknown"
                    st.metric("Views", views_str)
                with stats_col3:
                    st.metric("Published", metadata.get('publish_date', 'Unknown'))

            st.divider()

            # Transcript section
            if 'error' in transcript:
                st.error(f"Transcript Error: {transcript['error']}")
            else:
                # Language info
                lang_col1, lang_col2 = st.columns(2)
                with lang_col1:
                    st.markdown(f"**Original Language:** {transcript.get('language_name', 'Unknown')}")
                with lang_col2:
                    if transcript.get('was_translated'):
                        st.markdown("**Status:** Translated to English")
                    else:
                        st.markdown("**Status:** Original (English)")

                if transcript.get('is_auto_generated'):
                    st.info("This transcript was auto-generated by YouTube")

                # Show transcript
                st.markdown("#### Transcript (English)")
                transcript_text = transcript.get('english_transcript', 'No transcript available')
                st.text_area(
                    "Transcript",
                    value=transcript_text,
                    height=300,
                    key=f"transcript_{i}",
                    label_visibility="collapsed"
                )

                # Copy button
                st.code(transcript_text, language=None)

# Footer
st.divider()
st.markdown("""
---
**YouTube Transcriber & Translator** | Built with Streamlit
*Supports both YouTube Videos and Shorts*
""")
