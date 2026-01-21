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
    # Ensure we are listing available models to verify connection
    available_models = [m.name for m in genai.list_models()]
    st.sidebar.write(f"Connected to: {available_models[0]}")
    
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
elif page == "2. Reliability Test (ICR)":
    st.header("Stage 2: Active Inter-Coder Reliability Test")
    
    test_input = st.text_area("Paste test items (one per line):", height=150)
    items = [i.strip() for i in test_input.split('\n') if i.strip()]
    
    if items:
        st.subheader("Human Coding Interface")
        # Use a data editor for a more professional "spreadsheet" feel
        human_data = pd.DataFrame({"Text": items, "Your Code": ["1.1"] * len(items)})
        edited_df = st.data_editor(human_data, num_rows="fixed", use_container_width=True)

        if st.button("Finalize & Run AI Comparison"):
            with st.spinner("AI background coding in progress..."):
                # UPDATE: Use the 2026 stable model name here
                model = genai.GenerativeModel('gemini-2.5-flash')
                ai_codes = []
                
                for item in items:
                    prompt = f"{st.session_state.super_prompt}\n\nDATA TO CODE:\n{item}"
                    response = model.generate_content(prompt)
                    # Extract decimal code (e.g., 1.2 or 3.4)
                    found_code = re.search(r'(\d\.\d)', response.text)
                    ai_codes.append(found_code.group(1) if found_code else "N/A")

                # Combine for Comparison
                comparison_df = pd.DataFrame({
                    "Text Snippet": [t[:50] + "..." for t in items],
                    "Human": edited_df["Your Code"].tolist(),
                    "AI": ai_codes
                })
                
                # Calculate Kappa
                kappa = cohen_kappa_score(comparison_df["Human"], comparison_df["AI"])
                
                st.divider()
                st.subheader("Results & Statistics")
                col_a, col_b = st.columns(2)
                col_a.metric("Cohen's Kappa", f"{kappa:.2f}")
                col_b.metric("Agreement Rate", f"{(comparison_df['Human'] == comparison_df['AI']).mean():.0%}")

                st.dataframe(comparison_df.style.apply(lambda x: ['background-color: #ffcccc' if x.Human != x.AI else '' for i in x], axis=1))

                if kappa < 0.7:
                    st.error("Reliability below academic standards (0.70). Suggestion: Clarify the distinction between 'Integrity' and 'Benevolence' in Stage 1.")
                else:
                    st.success("Target reliability reached. Proceed to Stage 3.")

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
