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

import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
from sklearn.metrics import cohen_kappa_score

# --- HELPER: EXTRACT NUMERICAL CODE ---
def extract_primary_code(ai_text):
    # Searches for a pattern like "Primary code: 1.1" or just a decimal number
    match = re.search(r'(\d\.\d)', ai_text)
    return match.group(1) if match else "None"

# --- STAGE 2: THE INTER-CODER TEST ---
if page == "2. Reliability Test (ICR)":
    st.header("Stage 2: Active Inter-Coder Reliability Test")
    
    # 1. Provide Test Data
    test_input = st.text_area("Paste test items (one per line):", placeholder="Response 1...\nResponse 2...")
    items = [i.strip() for i in test_input.split('\n') if i.strip()]
    
    if items:
        st.subheader("Your Turn: Code the Items")
        human_selections = []
        for idx, item in enumerate(items):
            code = st.selectbox(f"Item {idx+1}: {item[:80]}...", 
                                ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "2.4", "3.1", "3.2", "3.3", "3.4"], 
                                key=f"h_{idx}")
            human_selections.append(code)

        if st.button("Finalize & Run AI Comparison"):
            with st.spinner("AI is analyzing based on your protocol..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                ai_selections = []
                explanations = []

                for item in items:
                    # The "Super Prompt" is injected here
                    prompt = f"{st.session_state.super_prompt}\n\nDATA:\n{item}"
                    response = model.generate_content(prompt)
                    
                    ai_code = extract_primary_code(response.text)
                    ai_selections.append(ai_code)
                    explanations.append(response.text)

                # --- RESULTS TABLE ---
                results_df = pd.DataFrame({
                    "Text": items,
                    "Human Code": human_selections,
                    "AI Code": ai_selections,
                    "Match": [h == a for h, a in zip(human_selections, ai_selections)]
                })

                st.table(results_df)

                # --- STATS ---
                kappa = cohen_kappa_score(human_selections, ai_selections)
                st.metric("Cohen's Kappa (Reliability)", f"{kappa:.2f}")
                
                if kappa > 0.7:
                    st.success("High reliability! You can proceed to Stage 3.")
                else:
                    st.warning("Reliability is low. Refine your 'Super Prompt' in Stage 1 and try again.")

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
