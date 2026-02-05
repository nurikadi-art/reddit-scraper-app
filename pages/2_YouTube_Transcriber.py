#!/usr/bin/env python3
"""
YouTube Transcriber & Translator
Transcribes YouTube videos, translates foreign languages to English.
No API keys required!
"""

import streamlit as st
import re
import json
from datetime import datetime
from typing import Optional

# YouTube libraries
from youtube_transcript_api import YouTubeTranscriptApi
from pytubefix import YouTube
from deep_translator import GoogleTranslator

# Page config
st.set_page_config(
    page_title="YouTube Transcriber & Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

    if re.match(r'^[a-zA-Z0-9_-]{11}$', url.strip()):
        return url.strip()

    return None


def get_video_metadata(video_id: str) -> dict:
    """Get video metadata using pytubefix"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url)

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
    """Get transcript for a YouTube video with optional translation."""
    transcript_data = None
    original_language = 'en'
    is_auto_generated = False
    last_error = None

    # Method 1: Try listing all transcripts and get the best one
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # First try to get manual transcript (more accurate)
        for transcript in transcript_list:
            if not transcript.is_generated:
                transcript_data = transcript.fetch()
                original_language = transcript.language_code
                is_auto_generated = False
                break

        # If no manual, get auto-generated
        if transcript_data is None:
            for transcript in transcript_list:
                if transcript.is_generated:
                    transcript_data = transcript.fetch()
                    original_language = transcript.language_code
                    is_auto_generated = True
                    break

        # If still nothing, just get the first available
        if transcript_data is None:
            for transcript in transcript_list:
                transcript_data = transcript.fetch()
                original_language = transcript.language_code
                break

    except Exception as e:
        last_error = str(e)

    # Method 2: Direct fetch with language preferences
    if transcript_data is None:
        try:
            transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
            original_language = 'en'
        except Exception as e:
            if last_error is None:
                last_error = str(e)

    if transcript_data is None:
        error_msg = f"No transcript available for this video. "
        if last_error:
            if "disabled" in last_error.lower():
                error_msg += "Transcripts are disabled by the video owner."
            elif "no transcript" in last_error.lower():
                error_msg += "This video has no captions/subtitles."
            else:
                error_msg += f"({last_error})"
        return {'error': error_msg, 'video_id': video_id}

    # Extract text from transcript data
    original_text = ' '.join([entry.get('text', '') for entry in transcript_data])

    needs_translation = original_language and not original_language.startswith('en')
    translated_text = None

    if needs_translation and translate_to_english:
        try:
            translator = GoogleTranslator(source='auto', target='en')
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


def generate_export_text(results: list) -> str:
    """Generate formatted text for export"""
    output = []
    output.append(f"YouTube Transcriptions - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append("=" * 60)
    output.append("")

    for i, result in enumerate(results, 1):
        metadata = result.get('metadata', {})
        transcript = result.get('transcript', {})

        if 'error' in metadata:
            continue

        output.append(f"{'='*60}")
        output.append(f"VIDEO {i}")
        output.append(f"{'='*60}")
        output.append("")
        output.append(f"CHANNEL: {metadata.get('channel_name', 'Unknown')}")
        output.append(f"TITLE: {metadata.get('title', 'Unknown')}")
        output.append(f"VIDEO URL: {metadata.get('video_url', '')}")
        output.append(f"THUMBNAIL: {metadata.get('thumbnail_url', '')}")
        output.append(f"TYPE: {metadata.get('video_type', 'Video')} | Duration: {metadata.get('duration', 0)} seconds")
        output.append("")

        if 'error' not in transcript:
            lang_info = f"ORIGINAL LANGUAGE: {transcript.get('language_name', 'Unknown')}"
            if transcript.get('was_translated'):
                lang_info += " (Translated to English)"
            output.append(lang_info)
            output.append("")
            output.append("TRANSCRIPT (ENGLISH):")
            output.append("-" * 40)
            output.append(transcript.get('english_transcript', 'No transcript available'))
        else:
            output.append(f"TRANSCRIPT ERROR: {transcript.get('error', 'Unknown error')}")

        output.append("")
        output.append("")

    return '\n'.join(output)


def generate_json_export(results: list) -> str:
    """Generate JSON string for download"""
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

    return json.dumps(output_data, indent=2, ensure_ascii=False)


# ============== STREAMLIT UI ==============

st.title("YouTube Transcriber & Translator")
st.markdown("**Transcribe YouTube videos and translate to English - No API keys required!**")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = []

# Sidebar
with st.sidebar:
    st.header("Settings")

    auto_translate = st.checkbox("Auto-translate to English", value=True,
                                  help="Automatically translate non-English transcripts to English")

    st.divider()

    st.header("About")
    st.markdown("""
    **Features:**
    - Transcribe any YouTube video
    - Auto-detect language
    - Translate to English
    - Support for Shorts & Videos
    - Download as Text or JSON

    **No API keys needed!**
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

            metadata = get_video_metadata(video_id)

            if 'error' in metadata:
                st.error(f"Error getting metadata for {url}: {metadata['error']}")
                st.session_state.results.append({
                    'metadata': metadata,
                    'transcript': {'error': 'Could not get metadata'}
                })
                continue

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
        export_text = generate_export_text(st.session_state.results)
        st.download_button(
            label="Download as Text",
            data=export_text,
            file_name=f"youtube_transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

    with col2:
        export_json = generate_json_export(st.session_state.results)
        st.download_button(
            label="Download as JSON",
            data=export_json,
            file_name=f"youtube_transcriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
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

        video_type_label = "[SHORT]" if metadata.get('is_short') else "[VIDEO]"

        with st.expander(
            f"{video_type_label} {metadata.get('channel_name', 'Unknown')} - {metadata.get('title', 'Unknown')[:50]}...",
            expanded=(i == 0)
        ):
            col1, col2 = st.columns([1, 2])

            with col1:
                if metadata.get('thumbnail_url'):
                    st.image(metadata['thumbnail_url'], use_container_width=True)

                if metadata.get('is_short'):
                    st.markdown("**YouTube Short**")
                else:
                    st.markdown("**YouTube Video**")

            with col2:
                st.markdown(f"### {metadata.get('title', 'Unknown Title')}")
                st.markdown(f"**Channel:** {metadata.get('channel_name', 'Unknown')}")
                st.markdown(f"**Video URL:** {metadata.get('video_url', '')}")

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

            if 'error' in transcript:
                st.error(f"Transcript Error: {transcript['error']}")
            else:
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

                st.markdown("#### Transcript (English)")
                transcript_text = transcript.get('english_transcript', 'No transcript available')
                st.text_area(
                    "Transcript",
                    value=transcript_text,
                    height=300,
                    key=f"transcript_{i}",
                    label_visibility="collapsed"
                )

# Footer
st.divider()
st.markdown("**YouTube Transcriber & Translator** | Built with Streamlit | *No API keys required*")
