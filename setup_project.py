import os
from pathlib import Path

# --- 設定 ---
ROOT_DIR = "synapse_mvp"

# 作成するディレクトリのリスト
DIRECTORIES = [
    ".streamlit",
    "modules"
]

# 作成するファイルのリストと、その初期内容
# { 'ファイルパス': '初期内容' }
FILES = {
    "app.py": """
import streamlit as st
# from modules.google_sheets_client import get_all_records
# from modules.gemini_client import get_ai_response

st.title("AIプロテインアドバイザー『Synapse』v0.1")

# --- ここから開発を始めます ---

# 例: データベースからデータを読み込む (コメントアウトを外して使用)
# try:
#     records = get_all_records()
#     st.dataframe(records)
# except Exception as e:
#     st.error(f"データベースの読み込み中にエラーが発生しました: {e}")

# チャット入力
if prompt := st.chat_input("あなたの目的や好みを教えてください"):
    st.chat_message("user").write(prompt)
    
    # AIからの応答 (ダミー)
    with st.chat_message("assistant"):
        st.write("ここにAIからの推薦文が表示されます。")
""",
    "modules/__init__.py": "# このファイルを置くことで、'modules'フォルダをPythonパッケージとして扱えます。",
    "modules/google_sheets_client.py": """
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- Google Sheets APIに接続するための設定 ---
# この関数を実装していきます
def get_all_records():
    st.error("Google Sheets連携機能はまだ実装されていません。")
    # 以下に実装コードを書いていく
    # creds = ...
    # client = gspread.authorize(creds)
    # spreadsheet = client.open_by_key(...)
    # worksheet = spreadsheet.worksheet(...)
    # records = worksheet.get_all_records()
    # return pd.DataFrame(records)
    return pd.DataFrame() # 仮の戻り値
""",
    "modules/gemini_client.py": """
import streamlit as st
import google.generativeai as genai

# --- Gemini APIに接続するための設定 ---
# この関数を実装していきます
def get_ai_response(user_prompt, context_data):
    st.error("Gemini連携機能はまだ実装されていません。")
    # 以下に実装コードを書いていく
    # genai.configure(api_key=st.secrets["gemini_api_key"])
    # model = genai.GenerativeModel(...)
    # response = model.generate_content(...)
    # return response.text
    return "AIからのダミーレスポンスです。" # 仮の戻り値
""",
    ".streamlit/secrets.toml": """
# --- ここにAPIキーなどの秘密情報を保存します ---
# Google Gemini API Key
gemini_api_key = "YOUR_GEMINI_API_KEY_HERE"

# Google Sheets Spreadsheet Key (シートのURLから取得)
spreadsheet_key = "YOUR_SPREADSHEET_KEY_HERE"

# 注意: このファイルは絶対にGitHubなどで公開しないでください。
# .gitignoreファイルで管理します。
""",
    "requirements.txt": """
streamlit
google-generativeai
pandas
gspread
oauth2client
""",
    ".gitignore": """
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# Streamlit secrets
.streamlit/secrets.toml

# Google OAuth credentials
credentials.json

# OS-specific
.DS_Store
""",
    "README.md": """
# AIプロテインアドバイザー『Synapse』MVP

## 概要
LLMを活用した次世代のAIエージェント・コマースプラットフォームのMVP（実用最小限の製品）。
客観的なデータに基づき、ユーザーに最適なプロテインを提案します。

## 実行方法
1. `credentials.json` をこのフォルダに配置します。
2. `.streamlit/secrets.toml` にAPIキー等を設定します。
3. `pip install -r requirements.txt` を実行します。
4. `streamlit run app.py` を実行します。
"""
}

def setup_project():
    """
    プロジェクトのディレクトリとファイルの構成を自動生成する関数
    """
    print(f"プロジェクト '{ROOT_DIR}' のセットアップを開始します...")

    # ルートディレクトリの作成
    Path(ROOT_DIR).mkdir(exist_ok=True)
    print(f"  - ディレクトリ作成: {ROOT_DIR}/")

    # サブディレクトリの作成
    for dir_name in DIRECTORIES:
        Path(os.path.join(ROOT_DIR, dir_name)).mkdir(exist_ok=True)
        print(f"  - ディレクトリ作成: {os.path.join(ROOT_DIR, dir_name)}/")

    # ファイルの作成と初期内容の書き込み
    for file_path, content in FILES.items():
        full_path = Path(os.path.join(ROOT_DIR, file_path))
        full_path.parent.mkdir(parents=True, exist_ok=True) # ファイルの親ディレクトリも念のため作成
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())
        print(f"  - ファイル作成: {full_path}")
    
    print("\nプロジェクトのセットアップが完了しました！")
    print(f"'{ROOT_DIR}' フォルダに移動して、開発を始めてください。")

if __name__ == "__main__":
    setup_project()