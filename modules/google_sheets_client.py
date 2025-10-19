import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import sys
import os # ファイルパスを扱うためにインポート

# @st.cache_dataを一時的にコメントアウトすると、デバッグ中に毎回関数が実行されるようになります。
# 動作が確認できたらコメントを外してください。
# @st.cache_data(ttl=3600)
def get_all_records():
    """
    Googleスプレッドシートからすべてのレコードを取得し、Pandas DataFrameとして返す関数。
    (credentials.json直接読み込み版)
    """
    print("\n--- get_all_records関数が実行されました ---", file=sys.stderr)
    
    # credentials.jsonファイルのパスを指定
    # このスクリプト(google_sheets_client.py)から見て、一つ上の階層(synapse_mvp/)にあるファイルを指す
    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    print(f"ステップ1: 認証ファイル '{credentials_path}' の存在を確認します...", file=sys.stderr)

    if not os.path.exists(credentials_path):
        error_message = "認証ファイル 'credentials.json' が見つかりません。プロジェクトのルートフォルダに配置してください。"
        print(f"!!!!!! エラー !!!!!!: {error_message}", file=sys.stderr)
        st.error(error_message)
        return pd.DataFrame()
    
    print("  - 認証ファイルの存在を確認しました。", file=sys.stderr)

    try:
        # ステップ2: secrets.tomlからスプレッドシートキーのみを読み込む
        print("ステップ2: secrets.tomlからスプレッドシートキーを読み込みます...", file=sys.stderr)
        spreadsheet_key = st.secrets["spreadsheet_key"]
        print("  - スプレッドシートキーの読み込み成功。", file=sys.stderr)

        # ステップ3: 認証ファイルを使ってGoogle APIに接続
        print("ステップ3: 認証ファイルを使ってGoogle APIへの接続を試みます...", file=sys.stderr)
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        print("  - Google APIへの接続成功。", file=sys.stderr)

        # ステップ4: スプレッドシートを開く
        print(f"ステップ4: スプレッドシート (キー: {spreadsheet_key[:10]}...) を開きます...", file=sys.stderr)
        spreadsheet = client.open_by_key(spreadsheet_key)
        worksheet = spreadsheet.sheet1
        print("  - スプレッドシートのオープン成功。", file=sys.stderr)

        # ステップ5: 全レコードを取得
        print("ステップ5: 全レコードの取得を開始します...", file=sys.stderr)
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        print(f"  - {len(records)}件のレコード取得成功。", file=sys.stderr)
        
        # ステップ6: レコードのフィルタリング
        print("ステップ6: 'active'なレコードをフィルタリングします...", file=sys.stderr)
        active_df = df[df['Status'] == 'active']
        print(f"  - フィルタリング後のレコード数: {len(active_df)}件", file=sys.stderr)
        
        print("--- 全ての処理が正常に完了しました ---\n", file=sys.stderr)
        return active_df

    except Exception as e:
        print(f"\n!!!!!! エラーが発生しました !!!!!!", file=sys.stderr)
        print(f"エラーのタイプ: {type(e).__name__}", file=sys.stderr)
        print(f"エラーメッセージ: {e}", file=sys.stderr)
        print("!!!!!! トラブルシューティングのヒント !!!!!", file=sys.stderr)
        if isinstance(e, KeyError) and 'spreadsheet_key' in str(e):
             print("  - 'spreadsheet_key'エラーは、.streamlit/secrets.tomlにスプレッドシートキーが設定されていないことを示します。", file=sys.stderr)
        elif isinstance(e, gspread.exceptions.SpreadsheetNotFound):
            print("  - 'SpreadsheetNotFound'エラーは、スプレッドシートキーが間違っているか、サービスアカウントのメールアドレスにシートが共有されていないことを示します。", file=sys.stderr)
        elif 'invalid_grant' in str(e):
             print("  - 'invalid_grant'エラーは、認証情報(credentials.json)に問題があるか、PCの時刻がずれている可能性があります。", file=sys.stderr)
        print("---------------------------------------\n", file=sys.stderr)
        
        st.error(f"Google Sheetsへの接続中にエラーが発生しました。詳細はターミナル（コンソール）を確認してください。")
        return pd.DataFrame()