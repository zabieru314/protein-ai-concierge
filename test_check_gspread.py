import gspread
import pandas as pd
import os
import json
import sys

# --------------------------------------------------------------------------
# このプログラムは、あなたの google_sheets_client.py と
# 全く同じロジックでGoogleスプレッドシートに接続し、
# 「何が見えているか」をターミナルに報告します。
# --------------------------------------------------------------------------

def get_gspread_client():
    """認証情報を読み込む関数"""
    try:
        creds_path = os.path.join(os.path.dirname(__file__), 'credentials.json')
        if os.path.exists(creds_path):
            client = gspread.service_account(filename=creds_path)
            return client
    except Exception as e:
        print(f"❌ [エラー] credentials.json の読み込みに失敗しました: {e}")
    return None

def get_spreadsheet_key():
    """スプレッドシートのキーを config.json から読み込む関数"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("g_spreadsheet_key")
    except Exception as e:
        print(f"❌ [エラー] config.json の読み込みに失敗しました: {e}")
    return None

# --- ここからが探偵プログラムのメイン処理です ---

print("🕵️  Googleスプレッドシートの調査を開始します...")
print("-" * 50)

# 1. 認証クライアントの取得を試みる
gc = get_gspread_client()
if not gc:
    print("🛑 [調査結果] 認証に失敗しました。credentials.json を確認してください。")
    sys.exit()
print("✅ [ステップ1] 認証に成功しました。")

# 2. スプレッドシートキーの取得を試みる
spreadsheet_key = get_spreadsheet_key()
if not spreadsheet_key:
    print("🛑 [調査結果] スプレッドシートキーが見つかりません。config.json を確認してください。")
    sys.exit()
print(f"✅ [ステップ2] スプレッドシートキーを取得しました: ...{spreadsheet_key[-6:]}")

# 3. スプレッドシートへの接続を試みる
try:
    print("\n🔍 スプレッドシートに接続しています...")
    spreadsheet = gc.open_by_key(spreadsheet_key)
    print("✅ [ステップ3] スプレッドシートへの接続に成功しました。")
    print("-" * 50)

    # 4. 【最重要】スプレッドシートの情報を徹底的に調査する
    print("📄 [調査報告] プログラムから見えているスプレッドシートの情報:")
    print(f"  - ファイル名: 『{spreadsheet.title}』")
    
    all_worksheets = spreadsheet.worksheets()
    print(f"  - 存在するタブ（シート）の名前: {[ws.title for ws in all_worksheets]}")
    
    print("\n🔍 デフォルトのシート（sheet1）からデータを読み込んでみます...")
    worksheet = spreadsheet.sheet1
    records = worksheet.get_all_records()
    
    print(f"  - 『{worksheet.title}』シートから読み込めた行数: {len(records)} 行")

    if not records:
        print("\n🛑 [最終結論] データの行数が0でした。これがエラーの直接的な原因です。")
        print("   考えられる原因は以下の通りです:")
        print("   1. このスプレッドシートの『Sheet1』タブが本当に空である。")
        print("   2. ヘッダー行（1行目）のすぐ下に空の行があり、ライブラリがそこで読み込みを停止している。")
    else:
        df = pd.DataFrame(records)
        print("\n✅ [最終結論] データを正常に読み込めました。")
        print("   読み込まれた列名の一覧:")
        print(f"   {df.columns.tolist()}")
        if 'Brand' not in df.columns:
            print("   🚨 [警告] 読み込んだ列名の中に 'Brand' がありません！ ヘッダーのスペルを確認してください。")

except gspread.exceptions.SpreadsheetNotFound:
    print("🛑 [調査結果] 指定されたキーのスプレッドシートが見つかりませんでした。")
    print("   キーが正しいか、または credentials.json のサービスアカウントにシートの共有設定がされているか確認してください。")
except Exception as e:
    print(f"🛑 [調査結果] 予期せぬエラーが発生しました: {e}")

print("-" * 50)