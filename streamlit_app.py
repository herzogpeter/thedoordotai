import streamlit as st
import requests
import os
import time
from typing import List, Dict
from datetime import datetime

# Initialize session state for messages and debug info if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_health_check" not in st.session_state:
    st.session_state.last_health_check = None
if "backend_stats" not in st.session_state:
    st.session_state.backend_stats = {
        "response_times": [],
        "error_count": 0,
        "last_error": None
    }

def get_backend_details() -> dict:
    """Get detailed backend configuration and status"""
    backend_url = os.getenv("BACKEND_URL", "http://backend:10000")
    try:
        start_time = time.time()
        response = requests.get(f"{backend_url}/health", timeout=5)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "connected",
                "response_time": response_time,
                "index_loaded": data.get("index_loaded", False),
                "config": data.get("config", {}),
                "error": None
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "response_time": None,
            "index_loaded": False,
            "config": {}
        }

def check_backend_health() -> bool:
    """Check if backend is healthy and update stats"""
    details = get_backend_details()
    st.session_state.last_health_check = datetime.now()
    
    if details["response_time"]:
        st.session_state.backend_stats["response_times"].append(details["response_time"])
        # Keep only last 10 response times
        st.session_state.backend_stats["response_times"] = st.session_state.backend_stats["response_times"][-10:]
    
    if details["status"] == "error":
        st.session_state.backend_stats["error_count"] += 1
        st.session_state.backend_stats["last_error"] = details["error"]
    
    return details["status"] == "connected" and details["index_loaded"]

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

st.title("Sermon Transcript Chat")

# Add enhanced status to sidebar
with st.sidebar:
    st.title("System Status")
    backend_details = get_backend_details()
    
    # Connection Status
    if backend_details["status"] == "connected":
        st.success("Backend Connected")
        st.info("Ready to answer questions")
        
        # Backend Configuration
        with st.expander("Backend Configuration"):
            st.json(backend_details["config"])
        
        # Performance Metrics
        with st.expander("Performance Metrics"):
            if st.session_state.backend_stats["response_times"]:
                avg_response_time = sum(st.session_state.backend_stats["response_times"]) / len(st.session_state.backend_stats["response_times"])
                st.metric("Average Response Time", f"{avg_response_time:.3f}s")
            st.metric("Current Response Time", f"{backend_details['response_time']:.3f}s")
            st.metric("Error Count", st.session_state.backend_stats["error_count"])
        
        # Last Check Time
        if st.session_state.last_health_check:
            st.text(f"Last checked: {st.session_state.last_health_check.strftime('%H:%M:%S')}")
    else:
        st.error("Backend Disconnected")
        st.warning("Please wait for the backend to initialize")
        
        # Error Details
        with st.expander("Error Details"):
            st.error(f"Last Error: {backend_details['error']}")
            st.metric("Total Errors", st.session_state.backend_stats["error_count"])
            if st.session_state.last_health_check:
                st.text(f"Last checked: {st.session_state.last_health_check.strftime('%H:%M:%S')}")

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
