import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import io
import pyreadstat
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats import inter_rater as irr

# --- CONFIG & CATEGORIES ---
st.set_page_config(page_title="Academic AI Coder 2026", layout="wide")

TRUST_CATS = {
    "1.1": "1.1 Ability", "1.2": "1.2 Benevolence", "1.3": "1.3 Integrity",
    "2.1": "2.1 Propensity", "2.2": "2.2 Risk Aversion", "2.3": "2.3 Prior Beliefs", "2.4": "2.4 Literacy",
    "3.1": "3.1 Topic Sensitivity", "3.2": "3.2 Uncertainty", "3.3": "3.3 Context", "3.4": "3.4 Consequences",
    "0.0": "0.0 Uncodable"
}

# --- INITIALIZE SESSION STATE ---
if "super_prompt" not in st.session_state:
    st.session_state.super_prompt = "Protocol: Use categories 1.1 to 3.4. Output only the numerical code."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎓 Academic Hub")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    st.divider()
    page = st.radio("Navigation", ["1. Protocol Co-Design", "2. Reliability Test", "3. Batch Export"])

# --- STAGE 1: CO-DESIGN (Keep as is) ---
if page == "1. Protocol Co-Design":
    st.header("Stage 1: Interactive Protocol Development")
    col_chat, col_prompt = st.columns([1, 1])
    with col_chat:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])
        if user_msg := st.chat_input("Suggest changes..."):
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(f"Protocol: {st.session_state.super_prompt}\nUpdate: {user_msg}")
            st.session_state.super_prompt = response.text
            st.rerun()
    with col_prompt:
        st.text_area("Live Protocol", value=st.session_state.super_prompt, height=600)

# --- STAGE 2: RELIABILITY TEST (Pasted Data) ---
elif page == "2. Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability (Triangulation)")
    
    # Global Context
    context = st.text_input("Global Context (e.g., 'These are responses to a story about X')", placeholder="Optional...")
    
    # Data Entry
    st.subheader("Data Entry")
    st.write("Paste your data into the table below (Double-click cells to edit).")
    
    # Pre-populate with 5 empty rows for pasting
    init_df = pd.DataFrame([{"Response": "", "Ranking": 5, "Human 1": "1.1"}] * 5)
    
    config = {
        "Human 1": st.column_config.SelectboxColumn("Human Code", options=list(TRUST_CATS.keys())),
        "Ranking": st.column_config.NumberColumn("Trust Rank", min_value=1, max_value=10)
    }
    
    edited_df = st.data_editor(init_df, column_config=config, num_rows="dynamic", use_container_width=True)

    if st.button("Run Triangulation"):
        valid_rows = edited_df[edited_df["Response"] != ""]
        if valid_rows.empty:
            st.warning("Please enter at least one response.")
        else:
            model = genai.GenerativeModel('gemini-2.5-flash')
            ai_codes = []
            for _, row in valid_rows.iterrows():
                # INJECT CONTEXT + RANKING INTO PROMPT
                prompt = f"{st.session_state.super_prompt}\nCONTEXT: {context}\nRANKING GIVEN: {row['Ranking']}\nTEXT: {row['Response']}"
                resp = model.generate_content(prompt)
                match = re.search(r'(\d\.\d)', resp.text)
                ai_codes.append(match.group(1) if match else "0.0")
            
            valid_rows["AI Code"] = ai_codes
            st.dataframe(valid_rows)
            
            # Stats
            score = cohen_kappa_score(valid_rows["Human 1"], valid_rows["AI Code"])
            st.metric("Cohen's Kappa", f"{score:.2f}")

# --- STAGE 3: BATCH (Full Paste) ---
elif page == "3. Batch Export":
    st.header("Stage 3: Full Batch Processing")
    context = st.text_input("Global Context for this batch", placeholder="Optional...")
    
    st.subheader("Paste Final Dataset")
    st.info("Tip: You can copy a selection from Excel and paste it into the 'Response' column below.")
    
    # Large dynamic table for pasting thousands of rows
    batch_df = pd.DataFrame([{"Response": "", "Ranking": 5}] * 10)
    final_input_df = st.data_editor(batch_df, num_rows="dynamic", use_container_width=True)
    
    if st.button("Process All Rows"):
        model = genai.GenerativeModel('gemini-2.5-flash')
        # ... (Batch logic similar to Stage 2 loop) ...
        st.success("Batch Complete. Export logic follows.")
