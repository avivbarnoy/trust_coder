import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import io
import pyreadstat
from sklearn.metrics import cohen_kappa_score
from statsmodels.stats import inter_rater as irr

# --- APP CONFIG ---
st.set_page_config(page_title="Academic AI Coder 2026", layout="wide")

TRUST_CATS = {
    "1.1": "1.1 Ability", "1.2": "1.2 Benevolence", "1.3": "1.3 Integrity",
    "2.1": "2.1 Propensity", "2.2": "2.2 Risk Aversion", "2.3": "2.3 Prior Beliefs", 
    "2.4": "2.4 Literacy", "3.1": "3.1 Topic Sensitivity", "3.2": "3.2 Uncertainty", 
    "3.3": "3.3 Context", "3.4": "3.4 Consequences", "0.0": "0.0 Uncodable"
}

# --- INITIALIZE STATE ---
if "super_prompt" not in st.session_state:
    st.session_state.super_prompt = "You are a professional research assistant..."
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

# --- HELPER FUNCTION: CALL GEMINI SAFE ---
def call_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        # Setting safety filters to 'BLOCK_NONE' for academic processing
        safety = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        response = model.generate_content(prompt, safety_settings=safety)
        return response.text
    except Exception as e:
        return f"Error: The AI could not generate a response. (Details: {str(e)})"

# --- STAGE 1: CO-DESIGN ---
if page == "1. Protocol Co-Design":
    st.header("Stage 1: Co-Generating the Super Prompt")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Design Conversation")
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])
        
        if user_msg := st.chat_input("How should we refine the codebook?"):
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            full_instr = f"Current Protocol: {st.session_state.super_prompt}\n\nUpdate it based on: {user_msg}. Return the FULL new protocol."
            ai_resp = call_gemini(full_instr)
            st.session_state.super_prompt = ai_resp
            st.session_state.chat_history.append({"role": "assistant", "content": "Protocol updated on the right."})
            st.rerun()
            
    with col2:
        st.subheader("Current Master Protocol")
        st.text_area("Live Super Prompt", value=st.session_state.super_prompt, height=600)

# --- STAGE 2: RELIABILITY (Updated for Name Display) ---
elif page == "2. Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability")
    
    # 1. Global Context Area
    st.info("💡 **Tip:** Instead of changing your Master Prompt for every story, paste the story background here. The AI will treat this as 'Context' for its analysis.")
    context = st.text_area("Global Context (News Story/Background):", placeholder="e.g., 'This article is about a 2024 political rally in London...'")
    
    num_humans = st.radio("Number of Human Coders", [1, 2], horizontal=True)
    
    # FIX: Initialize with the full descriptive name from TRUST_CATS values
    default_cat_name = TRUST_CATS["1.1"] 
    init_rows = [{"Response": "", "Ranking": 5, "Human 1": default_cat_name}] * 10
    
    if num_humans == 2:
        for r in init_rows: r["Human 2"] = default_cat_name
    
    st.subheader("Coding Table")
    # Dropdown Options (Display Names)
    options_list = list(TRUST_CATS.values())
    
    config = {
        "Human 1": st.column_config.SelectboxColumn("Human 1 Code", options=options_list, required=True),
        "Human 2": st.column_config.SelectboxColumn("Human 2 Code", options=options_list, required=True),
        "Ranking": st.column_config.NumberColumn("Trust Rank", min_value=1, max_value=10)
    }
    
    edited_df = st.data_editor(pd.DataFrame(init_rows), column_config=config, num_rows="dynamic", use_container_width=True)

    if st.button("Run Reliability Check"):
        valid_df = edited_df[edited_df["Response"] != ""].copy()
        if not valid_df.empty:
            ai_codes = []
            
            # Progress bar for visual feedback
            progress_bar = st.progress(0)
            for idx, (_, row) in enumerate(valid_df.iterrows()):
                # CONTEXT INJECTION: We send the context and the ranking as separate variables
                p = f"{st.session_state.super_prompt}\n\nCONTEXT: {context}\nRANKING GIVEN BY USER: {row['Ranking']}\nPARTICIPANT TEXT: {row['Response']}"
                res = call_gemini(p)
                
                # Extract numeric code and map back to name
                m = re.search(r'(\d\.\d)', res)
                code_num = m.group(1) if m else "0.0"
                ai_codes.append(TRUST_CATS.get(code_num, "0.0 Uncodable"))
                
                progress_bar.progress((idx + 1) / len(valid_df))
            
            valid_df["AI Code"] = ai_codes
            st.write("### Comparison Table")
            st.dataframe(valid_df, use_container_width=True)
            
            # Statistics Calculation
            # Map descriptive names back to numbers for math functions
            rev_map = {v: k for k, v in TRUST_CATS.items()}
            stats_df = valid_df.copy()
            stats_df["Human 1"] = stats_df["Human 1"].map(rev_map)
            stats_df["AI Code"] = stats_df["AI Code"].map(rev_map)
            
            score = cohen_kappa_score(stats_df["Human 1"], stats_df["AI Code"])
            st.metric("Agreement (Cohen's Kappa)", f"{score:.2f}")
            
# --- STAGE 3: BATCH ---
elif page == "3. Batch Export":
    st.header("Stage 3: Full Batch Processing")
    context = st.text_area("Context for this Batch:", height=100)
    
    # Table for pasting thousands of rows
    batch_init = pd.DataFrame([{"Response": "", "Ranking": 5}] * 20)
    batch_data = st.data_editor(batch_init, num_rows="dynamic", use_container_width=True)
    
    if st.button("Analyze All Rows"):
        rows_to_process = batch_data[batch_data["Response"] != ""].copy()
        ai_final = []
        bar = st.progress(0)
        
        for idx, row in enumerate(rows_to_process.iterrows()):
            p = f"{st.session_state.super_prompt}\nCONTEXT: {context}\nRANKING: {row[1]['Ranking']}\nTEXT: {row[1]['Response']}"
            res = call_gemini(p)
            m = re.search(r'(\d\.\d)', res)
            ai_final.append(m.group(1) if m else "0.0")
            bar.progress((idx + 1) / len(rows_to_process))
        
        rows_to_process["AI_Code"] = ai_final
        rows_to_process["Context"] = context
        
        # SPSS Export
        buf = io.BytesIO()
        pyreadstat.write_sav(rows_to_process, buf)
        st.download_button("Download SPSS (.sav)", data=buf.getvalue(), file_name="final_results.sav")
