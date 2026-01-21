import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import io
import pyreadstat
from sklearn.metrics import cohen_kappa_score

# --- BASIC APP CONFIG ---
st.set_page_config(page_title="Academic AI Coder 2026", layout="wide")

# --- PERSISTENT STORAGE ---
if "super_prompt" not in st.session_state:
    st.session_state.super_prompt = ""
if "final_df" not in st.session_state:
    st.session_state.final_df = pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 Research Portal")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    
    st.divider()
    page = st.radio("Navigation", ["1. Protocol Development", "2. Reliability Test", "3. Batch Analysis & Export"])

# --- STAGE 1: PROTOCOL ---
if page == "1. Protocol Development":
    st.header("Stage 1: Coding Protocol")
    st.write("Paste your full 'Super Prompt' here. This acts as the AI's training manual.")
    st.session_state.super_prompt = st.text_area("Super Prompt Content", value=st.session_state.super_prompt, height=400)
    if st.button("Save Protocol"):
        st.success("Protocol saved successfully.")

# --- STAGE 2: RELIABILITY ---
elif page == "2. Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability (ICR)")
    test_input = st.text_area("Paste 5-10 sample responses (one per line):")
    items = [i.strip() for i in test_input.split('\n') if i.strip()]
    
    if items:
        # User input table
        st.subheader("Human Input")
        human_df = pd.DataFrame({"Text": items, "Human_Code": ["1.1"] * len(items)})
        edited_df = st.data_editor(human_df, use_container_width=True)

        if st.button("Run AI & Calculate Kappa"):
            if not api_key:
                st.error("Please enter API Key in sidebar.")
            else:
                model = genai.GenerativeModel('gemini-2.5-flash')
                ai_codes = []
                for item in items:
                    response = model.generate_content(f"{st.session_state.super_prompt}\n\nDATA:\n{item}")
                    match = re.search(r'(\d\.\d)', response.text)
                    ai_codes.append(match.group(1) if match else "0.0")
                
                # Result logic
                comparison = pd.DataFrame({
                    "Human": edited_df["Human_Code"].tolist(),
                    "AI": ai_codes
                })
                kappa = cohen_kappa_score(comparison["Human"], comparison["AI"])
                st.metric("Cohen's Kappa", f"{kappa:.2f}")
                st.dataframe(comparison)

# --- STAGE 3: BATCH & SPSS ---
elif page == "3. Batch Analysis & Export":
    st.header("Stage 3: Batch Processing & SPSS Export")
    uploaded_file = st.file_uploader("Upload CSV or Excel file", type=['csv', 'xlsx'])
    
    if uploaded_file and st.button("Run Full Analysis"):
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        # Simplified batch logic for demo
        st.write("Processing... (This would iterate through your file)")
        
        # Prepare SPSS file
        buf = io.BytesIO()
        pyreadstat.write_sav(df, buf)
        st.download_button("Download SPSS (.sav)", data=buf.getvalue(), file_name="analysis_results.sav")
