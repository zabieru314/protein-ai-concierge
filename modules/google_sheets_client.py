import streamlit as st
import gspread
import pandas as pd
import os
import json
import sys

def get_gspread_client():
    """Streamlit Secretsとローカルの認証ファイルを両方試す、堅牢な関数"""
    # Streamlit Cloud環境の認証情報を試す
    try:
        if "g_credentials" in st.secrets:
            creds_json_str = st.secrets["g_credentials"]
            creds_json = json.loads(creds_json_str)
            client = gspread.service_account_from_dict(creds_json)
            print("--- [INFO] Authenticated with Streamlit Secrets. ---", file=sys.stderr)
            return client
    except Exception:
        # st.secrets がないローカル環境では、静かに失敗し、次の方法に進む
        pass

    # ローカル環境の認証情報(credentials.json)を試す
    try:
        # このファイルがある場所から見て、一つ上の階層にある credentials.json を探す
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if os.path.exists(creds_path):
            client = gspread.service_account(filename=creds_path)
            print("--- [INFO] Authenticated with local credentials.json. ---", file=sys.stderr)
            return client
    except Exception as e:
        print(f"--- [ERROR] Failed to read local credentials file: {e} ---", file=sys.stderr)

    return None

def get_spreadsheet_key():
    """
    クラウド環境(st.secrets)とローカル環境(config.json)の両方から
    スプレッドシートのキーを取得する、賢い関数。
    """
    # まずクラウド用の金庫(st.secrets)を探す
    try:
        if "g_spreadsheet_key" in st.secrets:
            print("--- [INFO] Found spreadsheet key in Streamlit Secrets. ---", file=sys.stderr)
            return st.secrets["g_spreadsheet_key"]
    except Exception:
        pass # ローカル環境では失敗するので、次に進む

    # なければ、PC用の住所メモ(config.json)を探す
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                key = config.get("g_spreadsheet_key")
                if key:
                    print("--- [INFO] Found spreadsheet key in local config.json. ---", file=sys.stderr)
                    return key
    except Exception as e:
        print(f"--- [ERROR] Failed to read spreadsheet key from config.json: {e} ---", file=sys.stderr)
    
    return None

def get_all_records():
    """Googleスプレッドシートから全てのプロテインデータを取得し、DataFrameとして返す"""
    gc = get_gspread_client()
    if not gc:
        st.error("認証エラー: Googleへの接続に必要な認証情報(credentials.json)が見つかりません。")
        return pd.DataFrame()

    spreadsheet_key = get_spreadsheet_key()
    if not spreadsheet_key:
        st.error("設定エラー: スプレッドシートのキーが見つかりません。config.jsonファイルを確認してください。")
        return pd.DataFrame()

    try:
        spreadsheet = gc.open_by_key(spreadsheet_key)
        worksheet = spreadsheet.sheet1
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if df.empty:
            st.warning("データ警告: スプレッドシートからデータを読み込みましたが、中身が空です。ヘッダーの直下に空行がないか確認してください。")
            return pd.DataFrame()

        if 'Status' in df.columns:
            df = df[df['Status'] == 'active']
        
        return df

    except Exception as e:
        st.error(f"データ取得エラー: スプレッドシートの読み込み中に問題が発生しました。詳細: {e}")
        return pd.DataFrame()