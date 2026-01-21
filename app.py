import streamlit as st
import google.generativeai as genai
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Academic AI Coder", layout="wide")
st.title("🎓 Academic Coding Assistant")

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

# --- SESSION STATE INITIALIZATION ---
if "codebook" not in st.session_state:
    st.session_state.codebook = "No codebook generated yet."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- STAGE 1: CODEBOOK BUILDING ---
st.header("Stage 1: Framework Training & Codebook Development")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Training Chat")
    st.write("Describe your 9-category Trust Framework (Trustor, Trustee, Context) and provide examples.")
    
    # Chat Input
    user_input = st.text_area("Message the AI Assistant:", placeholder="e.g., 'The Trustee categories should focus on Competence, Benevolence, and Integrity...'")
    
    if st.button("Send to AI"):
        if not api_key:
            st.error("Please enter your API key in the sidebar.")
        else:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # System instructions to keep it academic
            system_prompt = f"""
            You are an expert academic researcher. Your goal is to help develop a codebook.
            Framework: 9 Categories (Trustor, Trustee, Context).
            Current Codebook: {st.session_state.codebook}
            User instruction: {user_input}
            
            Output a formal codebook including: 
            1. Category Name 
            2. Definition 
            3. Inclusion/Exclusion criteria 
            4. A prototypical example.
            """
            
            response = model.generate_content(system_prompt)
            st.session_state.codebook = response.text
            st.session_state.chat_history.append(("User", user_input))
            st.session_state.chat_history.append(("AI", response.text))

with col2:
    st.subheader("Current Draft Codebook")
    st.markdown(st.session_state.codebook)

# --- PREVIEW OF STAGES 2 & 3 ---
st.divider()
st.info("Stage 2 (Reliability Test) and Stage 3 (SPSS Export) will unlock once the codebook is finalized.")
