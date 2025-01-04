import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from environment variable, default to localhost
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Configure the page
st.set_page_config(
    page_title="Transcript Chat",
    page_icon="💬",
    layout="centered"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display header
st.title("💬 Transcript Chat")
st.markdown("""
Chat with your transcripts using AI. Upload your transcripts to the `/transcripts` 
directory and start asking questions!
""")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your transcripts"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Get bot response
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={"message": prompt},
                    timeout=30  # Add timeout
                )
                if response.status_code == 400:
                    st.error("No transcripts are loaded. Please add transcript files to the /transcripts directory and restart the application.")
                else:
                    response.raise_for_status()
                    data = response.json()
                    answer = data["response"]
                    st.write(answer)
                    
                    # Display sources if available
                    if "sources" in data and data["sources"]:
                        with st.expander("📚 Source Snippets"):
                            st.markdown("These are the relevant excerpts from the transcripts that informed the response:")
                            for i, source in enumerate(data["sources"], 1):
                                with st.container():
                                    # Header with relevance score
                                    st.markdown(f"**Source {i}** *(Relevance: {source['score']:.2f})*")
                                    
                                    # Source text in a quote block
                                    st.markdown("> " + source['text'].replace("\n", "\n> "))
                                    
                                    # Metadata in a cleaner format
                                    if source['metadata']:
                                        metadata_str = " | ".join([
                                            f"**{key}**: {value}" 
                                            for key, value in source['metadata'].items()
                                        ])
                                        st.markdown(metadata_str)
                                    
                                    # Add space between sources
                                    st.divider()
                    
                    st.session_state.messages.append({"role": "assistant", "content": answer})
    except requests.exceptions.ConnectionError as e:
        st.error(f"Cannot connect to the backend at {BACKEND_URL}. Error: {str(e)}")
    except requests.exceptions.Timeout:
        st.error(f"Request to {BACKEND_URL} timed out. The server might be busy.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Display info about available transcripts
with st.sidebar:
    st.header("About")
    st.markdown("""
    This application allows you to chat with your transcripts using AI. 
    
    To use:
    1. Add your transcript files to the `/transcripts` directory
    2. Restart the application
    3. Start asking questions!
    """)

    # Add a divider
    st.divider()

    # Show system status
    st.subheader("System Status")
    try:
        # Add debug information
        st.write(f"Attempting to connect to: {BACKEND_URL}")
        
        health_response = requests.get(
            f"{BACKEND_URL}/health",
            timeout=5  # Add a shorter timeout for health check
        )
        st.write(f"Response status code: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            st.write(f"Health data: {health_data}")
            
            if health_data.get("index_loaded"):
                st.success("Backend: Connected and ready")
            else:
                st.warning("Backend: Connected but no transcripts loaded")
        else:
            st.error(f"Backend: Error (Status {health_response.status_code})")
    except requests.exceptions.ConnectionError as e:
        st.error(f"Backend: Not Connected - Connection Error ({BACKEND_URL})")
        st.write(f"Error details: {str(e)}")
    except requests.exceptions.Timeout:
        st.error(f"Backend: Not Connected - Timeout ({BACKEND_URL})")
    except Exception as e:
        st.error(f"Backend: Not Connected - Unknown Error ({BACKEND_URL})")
        st.write(f"Error details: {str(e)}")
