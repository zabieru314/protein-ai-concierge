import streamlit as st
from modules.google_sheets_client import get_all_records
from modules import ui_components, chat_handler
import pandas as pd
import re
import json
import sys

# --- ページ設定 ---
st.set_page_config(
    page_title="THE PROTEIN LOGIC",
    page_icon="🔬",
    layout="centered"
)

# --- 関数定義 ---
@st.cache_data(ttl=600)
def load_data():
    df = get_all_records()
    if not df.empty and 'ProteinPerServing(g)' in df.columns and 'ServingSize(g)' in df.columns:
        df['ProteinPurity(%)'] = (df['ProteinPerServing(g)'] / df['ServingSize(g)']) * 100
    return df

def initialize_session_state():
    if "diagnosis_complete" not in st.session_state:
        st.session_state.diagnosis_complete = False
    if "persona" not in st.session_state:
        st.session_state.persona = {
            'experience': '継続的に飲んでいる', 
            'current_brand': None,
            'baseline_product_id': None,
            'purpose': '筋肉を大きくしたい',
            'priorities': {'価格の安さ': True, '味のおいしさ': False, '成分の品質': False, '有名ブランド': False}
        }
    if "messages" not in st.session_state:
        st.session_state.messages = []

# --- メイン処理 ---
initialize_session_state()
protein_df = load_data()

if protein_df.empty:
    st.error("データベースからプロテイン情報を読み込めませんでした。")
    st.stop()

st.title("🔬 THE PROTEIN LOGIC - AIプロテインアドバイザー")

if not st.session_state.diagnosis_complete:
    ui_components.render_diagnosis_form(protein_df)
else:
    # --- コンサルティング(チャット)フェーズ ---
    prompt = ui_components.render_chat_interface(protein_df)

    # [指揮者による、第一のタクト] ユーザーからの入力を受け付け、仕切り直す
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.processing = True
        st.rerun()

    # [指揮者による、第二のタクト] 仕切り直した後、AIの処理を実行する
    if st.session_state.get("processing"):
        chat_handler.handle_ai_response(protein_df)