import streamlit as st
import gspread
import pandas as pd
import os
import json
import sys

def get_gspread_client():
    """
    StreamlitのSecretsとローカルの認証ファイルを両方試し、
    gspreadの認証済みクライアントを返す、より堅牢な関数。
    """
    print("--- get_gspread_client関数が実行されました ---", file=sys.stderr)
    
    # --- 方法1: Streamlit Secrets (デプロイ環境用) ---
    try:
        if "g_credentials" in st.secrets:
            print("  - Streamlit Secretsから認証情報を読み込みます...", file=sys.stderr)
            creds_json_str = st.secrets["g_credentials"]
            creds_json = json.loads(creds_json_str)
            client = gspread.service_account_from_dict(creds_json)
            print("  - [成功] Secretsを使った認証に成功しました。", file=sys.stderr)
            return client
    except Exception as e:
        print(f"  - [警告] Secretsの解析中にエラーが発生しました: {e}", file=sys.stderr)

    # --- 方法2: ローカルのcredentials.json (ローカル開発環境用) ---
    try:
        print("  - ローカルの認証ファイルを探します...", file=sys.stderr)
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if os.path.exists(creds_path):
            client = gspread.service_account(filename=creds_path)
            print("  - [成功] ローカルファイルを使った認証に成功しました。", file=sys.stderr)
            return client
    except Exception as e:
        print(f"  - [警告] ローカルファイルの読み込み中にエラーが発生しました: {e}", file=sys.stderr)

    # --- どちらも失敗した場合 ---
    print("  - [エラー] 有効な認証情報が見つかりませんでした。", file=sys.stderr)
    return None

def get_all_records():
    """Googleスプレッドシートから全てのプロテインデータを取得し、DataFrameとして返す"""
    print("\n--- get_all_records関数が実行されました ---", file=sys.stderr)
    
    gc = get_gspread_client()
    if not gc:
        st.error("Googleスプレッドシートへの認証に失敗しました。Secretsまたは認証ファイルを確認してください。")
        return pd.DataFrame() # 認証失敗時は空のDataFrameを返す

    try:
        spreadsheet_key = st.secrets["g_spreadsheet_key"] # g_spreadsheet_key に統一
        spreadsheet = gc.open_by_key(spreadsheet_key)
        worksheet = spreadsheet.sheet1
        
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if 'Status' in df.columns:
            df = df[df['Status'] == 'active']

        print(f"  - [成功] {len(df)}件の'active'なレコードを取得しました。", file=sys.stderr)
        return df

    except Exception as e:
        st.error(f"スプレッドシートのデータ取得中にエラーが発生しました: {e}")
        return pd.DataFrame() # エラー時も空のDataFrameを返す