import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import io
import pyreadstat
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats import inter_rater as irr

# --- CONFIG ---
st.set_page_config(page_title="Academic AI Coder 2026", layout="wide")

TRUST_CATEGORIES = {
    "1.1": "1.1 Ability", "1.2": "1.2 Benevolence", "1.3": "1.3 Integrity",
    "2.1": "2.1 Propensity", "2.2": "2.2 Risk Aversion", "2.3": "2.3 Prior Beliefs", "2.4": "2.4 Literacy",
    "3.1": "3.1 Topic Sensitivity", "3.2": "3.2 Uncertainty", "3.3": "3.3 Context", "3.4": "3.4 Consequences",
    "0.0": "0.0 Uncodable"
}

if "super_prompt" not in st.session_state:
    st.session_state.super_prompt = "Protocol: Use numerical codes 1.1-3.4..."
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Research Portal")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    page = st.radio("Navigation", ["1. Protocol Co-Design", "2. Reliability Test", "3. Batch Export"])

# --- STAGE 1: CO-DESIGN ---
if page == "1. Protocol Co-Design":
    st.header("Stage 1: Interactive Protocol Development")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Design Conversation")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])
            
        if user_msg := st.chat_input("Suggest changes to the protocol..."):
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(f"Current Protocol: {st.session_state.super_prompt}\nUpdate based on: {user_msg}\nReturn ONLY the new full protocol.")
            st.session_state.super_prompt = response.text
            st.session_state.chat_history.append({"role": "assistant", "content": "Protocol updated."})
            st.rerun()
            
    with col2:
        st.subheader("Current Super Prompt")
        st.text_area("Final Protocol Output", value=st.session_state.super_prompt, height=500)

# --- STAGE 2: RELIABILITY ---
elif page == "2. Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability")
    num_humans = st.radio("Number of Human Coders", [1, 2], horizontal=True)
    test_input = st.text_area("Paste test items (one per line):")
    items = [i.strip() for i in test_input.split('\n') if i.strip()]
    
    if items:
        # Build Table
        cols = ["Response", "Human 1"]
        if num_humans == 2: cols.append("Human 2")
        
        input_df = pd.DataFrame(columns=cols, data=[[item, "1.1"] + (["1.1"] if num_humans==2 else []) for item in items])
        
        st.subheader("Coding Table")
        config = {c: st.column_config.SelectboxColumn(options=list(TRUST_CATEGORIES.keys())) for c in cols if "Human" in c}
        edited_df = st.data_editor(input_df, column_config=config, use_container_width=True)
        
        if st.button("Run Triangulation"):
            model = genai.GenerativeModel('gemini-2.5-flash')
            ai_codes = []
            for item in items:
                resp = model.generate_content(f"{st.session_state.super_prompt}\nCode this: {item}")
                m = re.search(r'(\d\.\d)', resp.text)
                ai_codes.append(m.group(1) if m else "0.0")
            
            final_comparison = edited_df.copy()
            final_comparison["AI Code"] = ai_codes
            st.dataframe(final_comparison)
            
            # Statistics
            st.subheader("Statistical Analysis")
            if num_humans == 1:
                score = cohen_kappa_score(final_comparison["Human 1"], final_comparison["AI Code"])
                metric_name = "Cohen's Kappa"
            else:
                # Fleiss' Kappa calculation
                data_for_kappa = final_comparison[["Human 1", "Human 2", "AI Code"]]
                # Convert to category counts
                cat_counts = irr.aggregate_raters(data_for_kappa)[0]
                score = irr.fleiss_kappa(cat_counts)
                metric_name = "Fleiss' Kappa"
                
            st.metric(metric_name, f"{score:.2f}")

            # RECOMMENDATION LOGIC
            if score >= 0.80:
                st.success("✅ **Option 1:** Results are sufficient. Proceed to Stage 3.")
            elif score >= 0.65:
                st.warning("⚠️ **Option 2:** Results are good, but more examples need to be tested (n+5) to ensure stability.")
            else:
                st.error("❌ **Option 3:** Reliability low. Refine the codebook in Stage 1. Discrepancy noted in complex categories.")

# --- STAGE 3: BATCH ---
elif page == "Stage 3: Batch Export":
    st.header("Stage 3: Final Analysis")
    st.info("Upload your full dataset here to apply the trained AI protocol and export for SPSS.")
