import streamlit as st
import google.generativeai as genai
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
import krippendorff
import pyreadstat
import io

# --- CONFIG ---
st.set_page_config(page_title="Academic AI Coder", layout="wide")
st.title("🎓 Professional Academic Coding Engine")

# --- SHARED STATE ---
if "super_prompt" not in st.session_state:
    st.session_state.super_prompt = ""
if "test_results" not in st.session_state:
    st.session_state.test_results = pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    page = st.radio("Navigate Stages", ["1. Protocol Development", "2. Reliability Test (ICR)", "3. Full Analysis & Export"])

# --- STAGE 1: PROTOCOL ---
if page == "1. Protocol Development":
    st.header("Stage 1: Define Coding Protocol")
    st.write("Paste your 'Super Prompt' or coding protocol below. This defines the categories and rules for the AI.")
    
    st.session_state.super_prompt = st.text_area(
        "Current Protocol / Super Prompt", 
        value=st.session_state.super_prompt,
        height=400,
        placeholder="Paste Part 3 (Super Prompt) here..."
    )
    
    if st.button("Save Protocol"):
        st.success("Protocol saved and loaded into AI memory.")

# --- STAGE 2: ICR ---
elif page == "2. Reliability Test (ICR)":
    st.header("Stage 2: Inter-Coder Reliability Test")
    
    # Input Test Data
    test_input = st.text_area("Paste sample texts to code (one per line):", height=150)
    test_items = [t.strip() for t in test_input.split('\n') if t.strip()]
    
    if test_items:
        st.subheader("Human Coding")
        st.write("Enter the primary numerical code for each item:")
        
        human_codes = []
        for i, item in enumerate(test_items):
            code = st.text_input(f"Code for: '{item[:60]}...'", key=f"human_{i}")
            human_codes.append(code)
            
        if st.button("Run AI Comparison"):
            with st.spinner("AI is coding..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                results = []
                
                for text in test_items:
                    # Construct request based on your protocol
                    prompt = f"{st.session_state.super_prompt}\n\nDATA TO CODE:\n{text}\n\nProduce only the requested table row."
                    response = model.generate_content(prompt)
                    # Simple extraction logic (assuming CSV-like or Table output from prompt)
                    results.append({"text": text, "ai_output": response.text})
                
                # Mock analysis of AI output for display
                # Note: In a real run, we'd use regex to extract the specific 'Primary Code' column
                st.session_state.test_results = pd.DataFrame(results)
                st.write("AI Results received. (Statistical calculation would appear here once extraction logic is mapped to your specific table columns).")

# --- STAGE 3: EXPORT ---
elif page == "3. Full Analysis & Export":
    st.header("Stage 3: SPSS Data Export")
    
    if st.button("Download as SPSS (.sav)"):
        # Dummy data for demonstration
        df = pd.DataFrame({
            "Response": ["Example 1", "Example 2"],
            "Trust_Rank": [8, 3],
            "Primary_Code": [1.1, 2.1]
        })
        
        # Buffer to save the file
        buf = io.BytesIO()
        pyreadstat.write_sav(df, buf)
        
        st.download_button(
            label="Download .sav file",
            data=buf.getvalue(),
            file_name="coding_results.sav",
            mime="application/x-spss-sav"
        )
