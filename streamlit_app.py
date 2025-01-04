import streamlit as st
import requests
import os
from typing import List, Dict

# Initialize session state for messages if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

def send_message(message: str, history: List[Dict[str, str]]) -> dict:
    """Send message to backend API with conversation history"""
    backend_url = os.getenv("BACKEND_URL", "http://backend:10000")
    try:
        response = requests.post(
            f"{backend_url}/chat",
            json={"message": message, "history": history},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error communicating with backend: {str(e)}")
        return None

def check_backend_health() -> bool:
    """Check if backend is healthy"""
    backend_url = os.getenv("BACKEND_URL", "http://backend:10000")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        return response.status_code == 200 and response.json().get("index_loaded", False)
    except requests.exceptions.RequestException:
        return False

st.title("Sermon Transcript Chat")

# Add status to sidebar
with st.sidebar:
    st.title("Status")
    if check_backend_health():
        st.success("Backend Connected")
        st.info("Ready to answer questions")
    else:
        st.error("Backend Disconnected")
        st.warning("Please wait for the backend to initialize")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if "sources" in message:
            with st.expander("View Sources"):
                for source in message["sources"]:
                    st.markdown(f"**Relevance Score:** {source['score']:.2f}")
                    st.markdown(f"**Source Text:**\n{source['text']}")
                    if "metadata" in source:
                        st.markdown(f"**Metadata:**\n{source['metadata']}")
                    st.markdown("---")

# Chat input
if prompt := st.chat_input("Ask a question about the sermon transcripts"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Prepare conversation history for backend
    history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages[:-1]  # Exclude the latest message
    ]

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = send_message(prompt, history)
            if response:
                st.write(response["response"])
                # Add assistant message to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["response"],
                    "sources": response.get("sources", [])
                })
                # Display sources in expandable section
                if response.get("sources"):
                    with st.expander("View Sources"):
                        for source in response["sources"]:
                            st.markdown(f"**Relevance Score:** {source['score']:.2f}")
                            st.markdown(f"**Source Text:**\n{source['text']}")
                            if "metadata" in source:
                                st.markdown(f"**Metadata:**\n{source['metadata']}")
                            st.markdown("---")
