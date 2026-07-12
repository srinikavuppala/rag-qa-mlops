import os
import streamlit as st
import requests

# --- Configuration ---
# Reads from Docker environment variable, falls back to local 127.0.0.1 if not in Docker
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# --- Page Setup (SRS 6.1: Single-page application) ---
st.set_page_config(page_title="RAG Document Q&A", page_icon="🤖", layout="wide")

# --- Session State Initialization ---
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Auth Functions ---
def login(username, password):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/login", data={"username": username, "password": password})
        if res.status_code == 200:
            return res.json()["access_token"]
        return None
    except:
        return None

def register(username, password):
    try:
        res = requests.post(f"{BACKEND_URL}/auth/register", params={"username": username, "password": password})
        return res.status_code == 200
    except:
        return False

# --- API Interaction Functions ---
def upload_file(file, token):
    headers = {"Authorization": f"Bearer {token}"}
    # file.type handles PDF, DOCX, TXT automatically
    files = {"file": (file.name, file.getvalue(), file.type)}
    res = requests.post(f"{BACKEND_URL}/documents/upload", files=files, headers=headers)
    return res.json()

def ask_question(query, collection, token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"query": query, "collection_name": collection}
    res = requests.post(f"{BACKEND_URL}/query", json=data, headers=headers)
    return res.json()

# --- UI Rendering ---
if st.session_state.access_token is None:
    st.title("🤖 RAG Document Q&A System")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                token = login(username, password)
                if token:
                    st.session_state.access_token = token
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                    
    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("New Username")
            new_pass = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if register(new_user, new_pass):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username might already exist.")

else:
    # --- MAIN APPLICATION LAYOUT (SRS 6.1) ---
    
    # Sidebar (SRS 6.1: Document upload, settings)
    with st.sidebar:
        st.header("Settings & Upload")
        st.write(f"Logged in as: **{st.session_state.username}**")
        
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
            
        st.divider()
        st.subheader("Upload New Document")
        uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "docx", "md"])
        
        if uploaded_file is not None:
            if st.button("Process Document"):
                with st.spinner("Ingesting, Chunking, and Embedding..."):
                    result = upload_file(uploaded_file, st.session_state.access_token)
                    if "status" in result:
                        st.success(f"Done! Added to collection: `{result['collection_name']}`")
                    else:
                        st.error(result.get("detail", "Upload failed"))
                        
        st.divider()
        collection_name = st.text_input("Query Collection", value="space_history")

    # Main Chat Area (SRS 6.1: Message bubbles, typing indicators)
    st.header("Chat with your Documents")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "citations" in message:
                with st.expander("View Citations"):
                    for cit in message["citations"]:
                        st.markdown(f"📄 **{cit['document_name']}** (Chunk {cit['chunk_index']}) - Relevance: {cit['relevance_score']}%")

    # Chat Input (SRS FR-QA-001)
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Get AI response with typing indicator
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ask_question(prompt, collection_name, st.session_state.access_token)
            
            st.markdown(response["answer"])
            
            # Show citations
            with st.expander("View Citations"):
                for cit in response["citations"]:
                    st.markdown(f"📄 **{cit['document_name']}** (Chunk {cit['chunk_index']}) - Relevance: {cit['relevance_score']}%")
            
            # Save to history
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": response["answer"],
                "citations": response["citations"]
            })