import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- 設定 ---
# あなたの secrets.toml からスプレッドシートキーをコピーして貼り付けてください
SPREADSHEET_KEY = "1CB7gs7jL_L0LhWq6B5Ns2Zlke-JQYG6WD-pYO_UhuE8" 
CREDENTIALS_PATH = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def diagnose():
    """Google Sheets APIへの接続を診断するスクリプト"""
    print("--- Google Sheets API 接続診断を開始します ---")

    # 1. 認証ファイルの存在確認
    print(f"\n[ステップ1] 認証ファイル '{CREDENTIALS_PATH}' を探しています...")
    if not os.path.exists(CREDENTIALS_PATH):
        print("  [エラー] 認証ファイルが見つかりません。")
        return
    print("  [成功] 認証ファイルを発見しました。")

    # 2. 認証情報を使ってGoogle APIサービスクライアントを構築
    try:
        print("\n[ステップ2] 認証情報を使ってAPIクライアントを構築しています...")
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        print("  [成功] APIクライアントを構築しました。")
    except Exception as e:
        print(f"  [エラー] APIクライアントの構築中にエラーが発生しました: {e}")
        return

    # 3. 実際にAPIを叩いてスプレッドシートの情報を取得
    try:
        print(f"\n[ステップ3] APIを呼び出してスプレッドシート '{SPREADSHEET_KEY[:10]}...' の情報を取得します...")
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_KEY).execute()
        sheet_title = sheet_metadata.get('properties', {}).get('title', '（タイトル不明）')
        print(f"  [成功] スプレッドシートの情報を取得しました！")
        print(f"  -> スプレッドシートのタイトル: '{sheet_title}'")
    except HttpError as err:
        print(f"  [エラー] API呼び出し中にHTTPエラーが発生しました。")
        print(f"  -> ステータスコード: {err.resp.status}")
        print(f"  -> エラー詳細: {err.content}")
        if err.resp.status == 403:
            print("\n  [診断結果] HTTP 403 (Forbidden) は権限エラーです。")
            print("  -> あなたのサービスアカウントに、このスプレッドシートへの『閲覧者』以上の権限が付与されているか、再度確認してください。")
    except Exception as e:
        print(f"  [エラー] API呼び出し中に予期せぬエラーが発生しました: {e}")

if __name__ == '__main__':
    diagnose()