import streamlit as st
from modules.google_sheets_client import get_all_records
from modules import ui_components, chat_handler
import pandas as pd
import re
import json
import sys
# import streamlit.components.v1 as components # 不要になったため削除
# --- ページ設定 ---
st.set_page_config(
    page_title="THE PROTEIN LOGIC", # ブラウザのタブに表示されるタイトル
    page_icon="🔬",                 # ブラウザのタブに表示されるアイコン
    layout="centered"
)
# --- 関数定義 (アプリケーションのセットアップ) ---
def load_data():
    return get_all_records()

def initialize_session_state():
    if "diagnosis_complete" not in st.session_state:
        st.session_state.diagnosis_complete = False
    if "persona" not in st.session_state:
        st.session_state.persona = {
            'experience': '継続的に飲んでいる', 
            'current_brand': None, # ★★★ 初期値を None に変更 ★★★
            'baseline_product_id': None, # ★★★ この行を新しく追加 ★★★
            'purpose': '筋肉を大きくしたい',
            'priorities': {'価格の安さ': True, '味のおいしさ': False, '成分の品質': False, '有名ブランド': False}
        }
    if "messages" not in st.session_state:
        st.session_state.messages = []

# 1. セッションを初期化する
initialize_session_state()

# 2. ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
#    if/elseが始まる前に、必ずデータベースを読み込んでおく
#    これが NameError を解決します
#    ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
protein_df = load_data()
# --- ヘッダー ---
st.title("🔬 THE PROTEIN LOGIC - AIプロテインアドバイザー")

if not st.session_state.diagnosis_complete:
    ui_components.render_diagnosis_form(protein_df) # ★★★ ここに (protein_df) を追加します ★★★
else:
    # --- コンサルティング(チャット)フェーズ ---
    
    # 1. チャット画面のUI表示は、ui_componentsモジュールに任せる
    #    ユーザーが新しいプロンプトを入力した場合、その内容が返される
    prompt = ui_components.render_chat_interface(protein_df)

    # ▼▼▼ if prompt: ブロックを以下のように修正 ▼▼▼
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.processing = True  # 処理開始のフラグを立てる
        st.rerun()

# ▼▼▼ AI応答を呼び出す条件を修正 ▼▼▼
if st.session_state.get("processing"):
    chat_handler.handle_ai_response(protein_df)