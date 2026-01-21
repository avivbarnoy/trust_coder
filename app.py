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

# Mapping for the Dropdown (Number + Name)
TRUST_CATS = {
    "1.1": "1.1 Ability (Competence/Accuracy)",
    "1.2": "1.2 Benevolence (Intentions/Bias)",
    "1.3": "1.3 Integrity (Honesty/Ethics)",
    "2.1": "2.1 Trust Propensity (General Skepticism)",
    "2.2": "2.2 Risk Aversion (Fear of Error)",
    "2.3": "2.3 Prior Beliefs (Ideology/Identity)",
    "2.4": "2.4 Media Literacy (Personal Experience)",
    "3.1": "3.1 Topic Sensitivity (Stakes)",
    "3.2": "3.2 Uncertainty (Lack of Info)",
    "3.3": "3.3 Communication Context (Platform)",
    "3.4": "3.4 Perceived Consequences",
    "0.0": "0.0 Uncodable/Missing"
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

# --- STAGE 1: CO-DESIGN ---
if page == "1. Protocol Co-Design":
    st.header("Stage 1: Interactive Protocol Development")
    st.write("Collaborate with the AI to refine your coding instructions. The 'Super Prompt' on the right updates as you talk.")
    
    col_chat, col_prompt = st.columns([1, 1])
    
    with col_chat:
        for m in st.session_state.chat_history:
            with st.chat_message(m["role"]): st.write(m["content"])
            
        if user_msg := st.chat_input("How should we refine the codebook?"):
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            model = genai.GenerativeModel('gemini-2.5-flash')
            # Instructions to AI to refine the prompt
            sys_instr = f"Current Protocol: {st.session_state.super_prompt}\n\nUpdate it based on: {user_msg}. Respond with ONLY the new full protocol text."
            response = model.generate_content(sys_instr)
            st.session_state.super_prompt = response.text
            st.session_state.chat_history.append({"role": "assistant", "content": "Updated the protocol based on your feedback."})
            st.rerun()
            
    with col_prompt:
        st.subheader("Current Super Prompt Output")
        st.text_area("Live Protocol", value=st.session_state.super_prompt, height=600, key="live_prompt")

# --- STAGE 2: RELIABILITY ---
elif page == "2. Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability (Triangulation)")
    
    num_humans = st.radio("Number of Human Coders", [1, 2], horizontal=True)
    test_input = st.text_area("Paste test items (one per line):", placeholder="e.g. 'I don't trust them because they've lied before.'")
    items = [i.strip() for i in test_input.split('\n') if i.strip()]
    
    if items:
        # Prepare Dataframe for Editor
        cols = ["Response", "Human 1"]
        if num_humans == 2: cols.append("Human 2")
        
        # Use values (names) for the selectbox display
        options_list = list(TRUST_CATS.values())
        init_data = pd.DataFrame([ [item, options_list[0]] + ([options_list[0]] if num_humans==2 else []) for item in items ], columns=cols)
        
        st.subheader("Coding Table")
        config = {c: st.column_config.SelectboxColumn(label=c, options=options_list) for c in cols if "Human" in c}
        edited_df = st.data_editor(init_data, column_config=config, use_container_width=True, hide_index=True)
        
        if st.button("Run Triangulation"):
            model = genai.GenerativeModel('gemini-2.5-flash')
            ai_results = []
            for item in items:
                resp = model.generate_content(f"{st.session_state.super_prompt}\nDATA:\n{item}")
                match = re.search(r'(\d\.\d)', resp.text)
                code_num = match.group(1) if match else "0.0"
                ai_results.append(TRUST_CATS.get(code_num, "0.0 Uncodable"))
            
            final_df = edited_df.copy()
            final_df["AI Result"] = ai_results
            st.table(final_df)
            
            # --- STATISTICS ---
            # Map back to numbers for stats
            rev_map = {v: k for k, v in TRUST_CATS.items()}
            stats_df = final_df.copy()
            for c in stats_df.columns:
                if c != "Response": stats_df[c] = stats_df[c].map(rev_map)
            
            st.subheader("Reliability Metrics")
            if num_humans == 1:
                score = cohen_kappa_score(stats_df["Human 1"], stats_df["AI Result"])
                st.metric("Cohen's Kappa (Human 1 vs AI)", f"{score:.2f}")
            else:
                rater_data = stats_df[["Human 1", "Human 2", "AI Result"]]
                agg = irr.aggregate_raters(rater_data)[0]
                score = irr.fleiss_kappa(agg)
                st.metric("Fleiss' Kappa (3-Way Agreement)", f"{score:.2f}")

            # --- RECOMMENDATION ENGINE ---
            if score >= 0.80:
                st.success("✅ **Option 1:** Results are sufficient. The AI has mastered the protocol. Proceed to Stage 3.")
            elif score >= 0.65:
                st.warning("⚠️ **Option 2:** Results are good but borderline. Test 5-10 more items to ensure stability before full batch analysis.")
            else:
                st.error("❌ **Option 3:** Reliability low. Refine the codebook in Stage 1. Discrepancy report: AI often struggles where human codes differ.")

# --- STAGE 3: BATCH ---
elif page == "Stage 3: Batch Export":
    st.header("Stage 3: Full Analysis & SPSS Export")
    st.info("Upload your final dataset. The AI will process all rows using your validated protocol.")
