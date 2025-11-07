import streamlit as st
import gspread
import pandas as pd
import json
import os
import sys

def _get_gspread_client():
    """
    クラウド環境(st.secrets)とローカル環境(credentials.json)の両方から
    Googleの認証情報を取得し、gspreadのクライアントオブジェクトを返す関数。
    """
    try:
        # --- Streamlit Cloud環境での認証 ---
        if "google_credentials" in st.secrets and "json" in st.secrets["google_credentials"]:
            
            # ▼▼▼【ここが最後の最重要修正点です】▼▼▼
            # gspreadがGoogle DriveとGoogle Sheetsの両APIにアクセスすることを明示的に宣言します。
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            
            creds_json_str = st.secrets["google_credentials"]["json"]
            creds_dict = json.loads(creds_json_str)
            
            # 辞書から認証情報を作成する際に、スコープを渡します。
            creds = gspread.service_account_from_dict(creds_dict, scopes=scopes)
            print("--- [INFO] Authenticated with Streamlit Secrets for Google Sheets (with explicit scopes) ---", file=sys.stderr)
            return gspread.Client(auth=creds)
            # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    except Exception as e:
        # クラウドでの認証に失敗した場合、デバッグのためにエラーを出力します
        print(f"--- [CRITICAL ERROR] Failed to authenticate with Streamlit Secrets: {e} ---", file=sys.stderr)
        pass

    # --- ローカル環境での認証 ---
    try:
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
        if os.path.exists(creds_path):
            # ローカルファイルからの認証では、スコープは自動で設定されます。
            gc = gspread.service_account(filename=creds_path)
            print("--- [INFO] Authenticated with local credentials.json for Google Sheets ---", file=sys.stderr)
            return gc
    except Exception as e:
        print(f"--- [ERROR] Failed to authenticate with local credentials.json: {e} ---", file=sys.stderr)
        pass
    
    return None

# (以降の get_all_records 関数は変更ありません)
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