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
    """データベースからプロテイン情報を読み込み、キャッシュする関数"""
    df = get_all_records()
    return df

def initialize_session_state():
    """セッション状態の変数を初期化する関数"""
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

# 1. セッションを初期化
initialize_session_state()

# 2. データベースを読み込む
protein_df = load_data()

# 3. データが正常に読み込めたかを確認
if protein_df.empty:
    st.error("データベースからプロテイン情報を読み込めませんでした。管理者にお問い合わせください。")
    st.stop()

# 4. データの前処理
if 'ProteinPerServing(g)' in protein_df.columns and 'ServingSize(g)' in protein_df.columns:
    protein_df['ProteinPurity(%)'] = (protein_df['ProteinPerServing(g)'] / protein_df['ServingSize(g)']) * 100
else:
    st.error("データベースに必要な列（ProteinPerServing(g) or ServingSize(g)）がありません。")
    st.stop()

# --- ヘッダー ---
st.title("🔬 THE PROTEIN LOGIC - AIプロテインアドバイザー")

# --- 画面描画 ---
if not st.session_state.diagnosis_complete:
    # 診断フォームの表示
    ui_components.render_diagnosis_form(protein_df)
else:
    # チャット画面の表示
    prompt = ui_components.render_chat_interface(protein_df)
    
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ ここが、あなたのコードを尊重した、最後のロジック修正です ★★★
    # ★★★ 二重の st.rerun() をなくし、AIの処理をここに統合します ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    if prompt:
        # ユーザーからの新しい入力があった場合
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 処理中のフラグを立て、スピナーを表示する
        st.session_state.processing = True
        with st.spinner("AIが応答を生成中です..."):
            # AIの応答処理を、このままの流れで直接呼び出す
            chat_handler.handle_ai_response(protein_df)
        
        # 処理が終わったら、フラグを解除し、一度だけ再実行して画面を最終的に更新する
        st.session_state.processing = False
        st.rerun()