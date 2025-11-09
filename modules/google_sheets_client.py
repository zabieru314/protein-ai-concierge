import streamlit as st
import gspread
import pandas as pd
import json
import sys

def _get_gspread_client():
    """
    Streamlit CloudのSecretsのみを使い、gspreadの認証済みクライアントを返す関数。
    """
    try:
        # gspreadがGoogle DriveとGoogle Sheetsの両APIにアクセスすることを明示的に宣言します。
        # これは辞書から認証情報を作成する際に必須です。
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        # Secretsから認証情報を「辞書形式」で安全に読み込みます。
        creds_json_str = st.secrets["google_credentials"]["json"]
        creds_dict = json.loads(creds_json_str)

        # ▼▼▼【これが最後の、そして最も重要な修正点です】▼▼▼
        # gspread.service_account_from_dict は、認証情報だけでなく、
        # それを使って認証された「クライアントオブジェクトそのもの」を返します。
        # これを直接 return するのが、公式に推奨されている正しい使い方です。
        creds = gspread.service_account_from_dict(creds_dict, scopes=scopes)
        print("--- [SUCCESS] Authenticated with Streamlit Secrets for Google Sheets. ---", file=sys.stderr)
        return creds
        # ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

    except Exception as e:
        # 認証に失敗した場合、ログに具体的なエラーを出力します。
        print("--- [CRITICAL ERROR] Failed to authenticate with Streamlit Secrets. ---", file=sys.stderr)
        print(f"--- [DETAILS] {e} ---", file=sys.stderr)
        return None

def get_all_records():
    """
    Googleスプレッドシートから全レコードをDataFrameとして取得するメイン関数。
    """
    # 上で定義した、クラウド専用の認証関数を呼び出します。
    gc = _get_gspread_client()

    if not gc:
        st.error("Google Sheetsへの接続認証に失敗しました。StreamlitのSecretsの設定を確認してください。")
        return pd.DataFrame()

    try:
        # あなたの正しいファイル名とシート名を指定します。
        spreadsheet_name = "Synapse_ProteinDB_v1"
        worksheet_name = "シート1"
        
        spreadsheet = gc.open(spreadsheet_name) 
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        records = worksheet.get_all_records()
        print(f"--- [SUCCESS] Successfully fetched records from '{spreadsheet_name}'. ---", file=sys.stderr)
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