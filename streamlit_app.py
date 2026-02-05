#!/usr/bin/env python3
"""
Content Creator Toolkit - Home Page
Suite of tools for content creators: Viral Script Generator & YouTube Transcriber
"""

import streamlit as st

# Page config
st.set_page_config(
    page_title="Content Creator Toolkit",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main content
st.title("Content Creator Toolkit")
st.markdown("### Your suite of AI-powered content creation tools")

st.divider()

# Tool cards
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ## 🎬 Viral Script Generator

    Generate viral Reels/Shorts scripts from trending Reddit posts using the **Phenomenon formula**.

    **Features:**
    - Scrapes viral Reddit posts
    - Uses AI to generate engaging scripts
    - Applies psychological triggers for virality
    - Multiple content categories

    **Requirements:**
    - SteadyAPI key (for Reddit access)
    - Anthropic API key (for AI generation)
    """)

    if st.button("Open Viral Script Generator", type="primary", key="viral"):
        st.switch_page("pages/1_Viral_Script_Generator.py")

with col2:
    st.markdown("""
    ## 🎥 YouTube Transcriber & Translator

    Transcribe YouTube videos and translate foreign content to English.

    **Features:**
    - Transcribe any YouTube video or Short
    - Auto-detect original language
    - Translate to English automatically
    - Display channel name, title, thumbnail
    - Export to Google Docs
    - Download as JSON

    **Requirements:**
    - Google credentials (for Docs export - optional)
    """)

    if st.button("Open YouTube Transcriber", type="primary", key="youtube"):
        st.switch_page("pages/2_YouTube_Transcriber.py")

st.divider()

# Quick start guide
st.markdown("""
## Quick Start Guide

### Setting Up API Keys

**For Streamlit Cloud deployment:**
1. Go to your app settings (gear icon)
2. Click "Secrets" in the left sidebar
3. Add your secrets in TOML format:

```toml
ANTHROPIC_API_KEY = "your-anthropic-key"
STEADYAPI_KEY = "your-steadyapi-key"

# Optional: For Google Docs export
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
```

**For local development:**
Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your-anthropic-key
STEADYAPI_KEY=your-steadyapi-key
```

### Getting API Keys

- **Anthropic API:** [console.anthropic.com](https://console.anthropic.com/)
- **SteadyAPI:** [steadyapi.com](https://steadyapi.com/)
- **Google Cloud:** [console.cloud.google.com](https://console.cloud.google.com/) (Enable Docs API)
""")

# Sidebar info
with st.sidebar:
    st.header("About")
    st.markdown("""
    **Content Creator Toolkit** is a suite of AI-powered tools designed for content creators.

    Navigate using the sidebar or the buttons above.

    ---

    **Tools Available:**
    - Viral Script Generator
    - YouTube Transcriber

    ---

    Built with Streamlit
    """)

    st.divider()

    st.markdown("**Select a tool from the sidebar to get started!**")
