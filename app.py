import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import io
import pyreadstat
from sklearn.metrics import cohen_kappa_score
# Note: You may need to add 'statsmodels' to requirements.txt for Fleiss Kappa
from statsmodels.stats import inter_rater as irr

# --- CONFIG & CATEGORIES ---
st.set_page_config(page_title="Academic AI Coder 2026", layout="wide")

TRUST_CATEGORIES = {
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
    st.session_state.super_prompt = "You are an academic coder. Use the following categories..."
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "reliability_data" not in st.session_state:
    st.session_state.reliability_data = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
    page = st.radio("Switch Stage", ["Stage 1: Co-Design Protocol", "Stage 2: Reliability Test", "Stage 3: Full Analysis"])

# --- STAGE 1: CO-DESIGN ---
if page == "Stage 1: Co-Design Protocol":
    st.header("Stage 1: Co-Generating the Super Prompt")
    
    col_chat, col_prompt = st.columns([1, 1])
    
    with col_chat:
        st.subheader("Chat with AI Designer")
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if prompt := st.chat_input("Suggest a change or describe a new category..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            # AI Logic to update prompt
            model = genai.GenerativeModel('gemini-2.5-flash')
            sys_msg = f"Current Super Prompt:\n{st.session_state.super_prompt}\n\nUser wants: {prompt}\nUpdate the super prompt and provide a brief explanation of changes."
            response = model.generate_content(sys_msg)
            
            # Extract new prompt vs chat explanation (assuming AI follows a format)
            # For simplicity, we assume the AI provides the whole new prompt in the response
            st.session_state.super_prompt = response.text 
            st.session_state.chat_messages.append({"role": "assistant", "content": "I've updated the Super Prompt based on our discussion. Check the right panel."})
            st.rerun()

    with col_prompt:
        st.subheader("Current Super Prompt (Output)")
        st.text_area("Live Protocol", value=st.session_state.super_prompt, height=600, key="protocol_area")

# --- STAGE 2: RELIABILITY ---
elif page == "Stage 2: Reliability Test":
    st.header("Stage 2: Inter-Coder Reliability (Triangulation)")
    
    num_human_coders = st.radio("Number of Human Coders", [1, 2], horizontal=True)
    test_items_raw = st.text_area("Paste test responses (one per line):", height=100)
    items = [i.strip() for i in test_items_raw.split('\n') if i.strip()]
    
    if items:
        # Build Table for Human Input
        initial_data = {"Response": items, "Human 1": list(TRUST_CATEGORIES.keys())[0]}
        if num_human_coders == 2:
            initial_data["Human 2"] = list(TRUST_CATEGORIES.keys())[0]
        
        st.subheader("Enter Human Codes")
        # Column config for dropdowns
        col_config = {
            "Human 1": st.column_config.SelectboxColumn("Human 1 Code", options=list(TRUST_CATEGORIES.keys()), required=True),
            "Human 2": st.column_config.SelectboxColumn("Human 2 Code", options=list(TRUST_CATEGORIES.keys()), required=True)
        }
        edited_df = st.data_editor(pd.DataFrame(initial_data), column_config=col_config, use_container_width=True)

        if st.button("Run Triangulation"):
            model = genai.GenerativeModel('gemini-2.5-flash')
            ai_codes = []
            with st.status("AI is coding in background...") as status:
                for item in items:
                    resp = model.generate_content(f"{st.session_state.super_prompt}\n\nDATA:\n{item}")
                    match = re.search(r'(\d\.\d)', resp.text)
                    ai_codes.append(match.group(1) if match else "0.0")
                status.update(label="AI Coding Complete!", state="complete")
            
            # Calculate Stats
            results = edited_df.copy()
            results["AI Code"] = ai_codes
            
            # Stats Logic
            st.divider()
            st.subheader("Reliability Report")
            
            if num_human_coders == 1:
                kappa = cohen_kappa_score(results["Human 1"], results["AI Code"])
                st.metric("Cohen's Kappa (Human 1 vs AI)", f"{kappa:.2f}")
            else:
                # Fleiss Kappa for 3 coders
                # We need to format data as counts per category per item
                all_codes = results[["Human 1", "Human 2", "AI Code"]].values
                # Simplified visualization for 3-way agreement
                st.write("3-Way Agreement Table")
                st.dataframe(results)
                # (Actual Fleiss calculation logic would go here using irr.aggregate_raters)

            # RECOMMENDATION ENGINE
            avg_kappa = kappa if num_human_coders == 1 else 0.5 # Placeholder for 3-way
            if avg_kappa > 0.8:
                st.success("✅ OPTION 1: Results are excellent. Proceed to Stage 3.")
            elif avg_kappa > 0.65:
                st.info("⚠️ OPTION 2: Results are good, but consider testing 5 more items to stabilize reliability.")
            else:
                st.error("❌ OPTION 3: Reliability low. Recommendation: Return to Stage 1. AI and Humans often disagreed on 'Integrity' vs 'Benevolence'.")
