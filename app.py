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
    # --- コンサルティング(チャット)フェーズ ---
    
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    # ★★★ ここが、指揮者を一人にするための、最後のロジック修正です ★★★
    # ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
    
    # [ステップ1] まず、UIを描画し、ユーザーからの入力を受け取る
    #            (この中でボタンが押されると、ui_componentsが一度目のrerunを呼び出します)
    prompt = ui_components.render_chat_interface(protein_df)

    # [ステップ2] もし、新しい入力があった場合のみ、AIの処理を実行する
    #            st.session_state.get("processing", False) のチェックで、二重実行を完全に防ぎます
    if prompt and not st.session_state.get("processing", False):
        
        # 処理開始を宣言
        st.session_state.processing = True
        
        # ユーザーの入力を履歴に追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # AIの処理を呼び出す（この中で st.rerun() は、もう呼ばれません）
        chat_handler.handle_ai_response(protein_df)
        
        # [ステップ3] すべての処理が終わった後、指揮者が、ただ一度だけタクトを振る
        #            これにより、AIの応答が画面に最終的に反映されます
        st.rerun()