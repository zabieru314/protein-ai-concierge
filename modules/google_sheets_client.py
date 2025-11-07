import streamlit as st
import gspread
import pandas as pd
import json
import os
import sys

def _get_gspread_client():
    try:
        # ▼▼▼【ここを修正しました】▼▼▼
        # より確実な「辞書アクセス」方式に変更しました。
        if "google_credentials" in st.secrets and "json" in st.secrets["google_credentials"]:
            creds_json_str = st.secrets["google_credentials"]["json"]
            creds_dict = json.loads(creds_json_str)
            gc = gspread.service_account_from_dict(creds_dict)
            print("--- [INFO] Authenticated with Streamlit Secrets for Google Sheets ---", file=sys.stderr)
            return gc
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
    except Exception:
        pass

    try:
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if os.path.exists(creds_path):
            gc = gspread.service_account(filename=creds_path)
            print("--- [INFO] Authenticated with local credentials.json for Google Sheets ---", file=sys.stderr)
            return gc
    except Exception as e:
        print(f"--- [ERROR] Failed to authenticate with local credentials.json: {e} ---", file=sys.stderr)
        pass
    
    return None

def get_all_records():
    gc = _get_gspread_client()

    if not gc:
        st.error("Google Sheetsへの接続認証に失敗しました。StreamlitのSecretsまたはcredentials.jsonファイルを確認してください。")
        return pd.DataFrame()

    try:
        spreadsheet_name = "Synapse_ProteinDB_v1"
        worksheet_name = "シート1"
        
        spreadsheet = gc.open(spreadsheet_name) 
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        records = worksheet.get_all_records()
        print("--- [SUCCESS] Successfully fetched records from Google Sheets. ---", file=sys.stderr)
        return pd.DataFrame(records)

    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"エラー: Googleスプレッドシートが見つかりません。名前が「{spreadsheet_name}」で正しいか、サービスアカウントに共有設定がされているか確認してください。")
        return pd.DataFrame()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"エラー: ワークシート（タブ）が見つかりません。名前が「{worksheet_name}」で正しいか確認してください。")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Google Sheetsからのデータ読み込み中に予期せぬエラーが発生しました: {e}")
        return pd.DataFrame()