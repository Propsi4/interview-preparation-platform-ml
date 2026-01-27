"""RAG components for file upload and URL indexing."""

# Standart library imports
import asyncio

# Thirdparty imports
import streamlit as st

# Local imports
from ui.api.client import PETClient


def render_file_uploader(client: PETClient):
    """
    Render the file uploader component.

    Parameters
    ----------
    client : PETClient
        The API client.
    """
    st.subheader("Upload Documents")
    uploaded_file = st.file_uploader(
        "Choose a file", type=["pdf", "docx", "pptx", "txt"], help="Supported formats: PDF, DOCX, PPTX, TXT"
    )

    if uploaded_file is not None:
        if st.button("Upload & Index", key="upload_btn"):
            with st.spinner("Uploading and indexing..."):
                try:
                    content = uploaded_file.read()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        client.upload_document(content, uploaded_file.name, uploaded_file.type)
                    )
                    loop.close()
                    st.success(f"Successfully indexed {len(result)} " f"chunks from {uploaded_file.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload document: {str(e)}")


def render_url_indexer(client: PETClient):
    """
    Render the URL indexer component.

    Parameters
    ----------
    client : PETClient
        The API client.
    """
    st.subheader("Index URL")
    url = st.text_input("Enter URL to index", placeholder="https://tntu.edu.ua/...")

    if url:
        if st.button("Index URL", key="index_url_btn"):
            with st.spinner("Scraping and indexing..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(client.index_url(url))
                    loop.close()
                    st.success(f"Successfully indexed {len(result)} chunks from URL")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to index URL: {str(e)}")
