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
    
    # [ステップ1] まず、UIを描画し、手足の脳からの「報告」を受け取る
    prompt = ui_components.render_chat_interface(protein_df)

    # [ステップ2] もし、新しい報告があった場合のみ、メインの脳が処理を開始する
    if prompt and not st.session_state.get("processing", False):
        
        st.session_state.processing = True
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # AIの処理を呼び出す（この中で st.rerun() は呼ばれない）
        chat_handler.handle_ai_response(protein_df)
        
        # [ステップ3] すべての処理が終わった後、メインの脳が、ただ一度だけ「再起動せよ」と命令する
        st.rerun()