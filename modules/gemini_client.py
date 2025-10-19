import streamlit as st
import google.generativeai as genai
import pandas as pd
import sys
import os

# --- 共通の初期化処理 ---
# --- 共通の初期化処理 ---
def _initialize_gemini():
    """Gemini APIキーを設定し、モデルを初期化する共通関数。"""
    try:
        api_key = st.secrets["gemini_api_key"]
        genai.configure(api_key=api_key)
        # ▼▼▼ 重要な修正箇所 ▼▼▼
        # モデル名を 'gemini-1.5-flash' から、より安定した 'gemini-pro' に変更します。
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
        # ▲▲▲ 重要な修正箇所 ▲▲▲
        return model
    except Exception as e:
        st.error(f"Geminiの初期化中にエラーが発生しました: {e}")
        return None

# --- AI-1: 分析官AIを呼び出す関数 ---
def get_intent_from_ai(user_prompt: str) -> str:
    """
    ユーザーのプロンプトを分析し、意図をJSON形式で返す。
    ストリーミングは行わない。
    """
    print("\n--- get_intent_from_ai関数が実行されました ---", file=sys.stderr)
    model = _initialize_gemini()
    if not model:
        return "{}" # エラー時は空のJSONを返す

    try:
        # 分析官用のプロンプトを読み込む
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'system_prompt_analyzer.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()

        full_prompt = f"{system_prompt}\n\n# ユーザーの要望:\n{user_prompt}"
        
        print("  - AI(分析官)に応答をリクエストします...", file=sys.stderr)
        response = model.generate_content(full_prompt)
        
        # レスポンスからJSON部分だけを抽出する (AIが余計なテキストを付けても対応)
        cleaned_json = response.text.strip().lstrip("```json").rstrip("```")
        print(f"  - AI(分析官)からの応答(JSON)を受信しました: {cleaned_json}", file=sys.stderr)
        
        return cleaned_json

    except Exception as e:
        error_message = f"Gemini API(分析官)との通信中にエラーが発生しました: {e}"
        print(f"!!!!!! エラー !!!!!!: {error_message}", file=sys.stderr)
        st.error(error_message)
        return "{}" # エラー時は空のJSONを返す

# --- AI-2: コピーライターAIを呼び出す関数 (ストリーミング対応) ---
def get_ai_response_writer(
    full_user_prompt: str,
    user_desire_summary: str,
    key_metric_name: str,
    selection_reason: str, # ▼▼▼ この引数を受け取れるように追加します ▼▼▼
    baseline_product_data: str,
    selected_products_data: str,
    chat_history: str,
    nutrition_tip: str  # ★★★ この引数を追加 ★★★
):
    """
    整形済みデータを受け取り、AI(コピーライター)から応答をストリームとして生成するジェネレータ関数。
    """
    print("\n--- get_ai_response_writer関数が実行されました (ストリーミング) ---", file=sys.stderr)
    model = _initialize_gemini()
    if not model:
        yield "申し訳ありません、AIの初期化に失敗しました。"
        return

    try:
        # コピーライター用のプロンプトを読み込む
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'system_prompt_writer.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # 受け取ったデータでプロンプトのプレースホルダーを置換
        system_prompt = prompt_template.replace(
            "[full_user_prompt]", full_user_prompt
        ).replace(
            "[user_desire_summary]", user_desire_summary
        ).replace(
            "[key_metric_name]", key_metric_name
        ).replace(
            "[selection_reason]", selection_reason # ▼▼▼ 受け取った引数をプロンプトに埋め込みます ▼▼▼
        ).replace(
            "[baseline_product_data]", baseline_product_data
        ).replace(
            "[selected_products_data]", selected_products_data
        ).replace(
            "[chat_history]", chat_history # ★★★ 3. この行を追加 ★★★
        ).replace(
            "[nutrition_tip]", nutrition_tip # ★★★ この行を追加 ★★★
        )
        
        # ▼▼▼【ここからが重要】デバッグコードを追加 ▼▼▼
        # ターミナル（コンソール）に、AIに渡す最終的な情報を全て表示させる
        print("\n" + "="*50, file=sys.stderr)
        print("--- DEBUG: AI Writerへの最終入力情報を表示します ---", file=sys.stderr)
        print("="*50, file=sys.stderr)
        print("\n[受け取った商品データ (selected_products_data)]:", file=sys.stderr)
        print(selected_products_data, file=sys.stderr)
        print("\n" + "-"*50, file=sys.stderr)
        print("\n[AIに渡す最終的なプロンプト全体 (system_prompt)]:", file=sys.stderr)
        print(system_prompt, file=sys.stderr)
        print("\n" + "="*50, file=sys.stderr)
        print("--- DEBUG: 表示終了 ---", file=sys.stderr)
        print("="*50 + "\n", file=sys.stderr)
        # ▲▲▲【ここまで】デバッグコード終了 ▲▲▲

        print("  - AI(コピーライター)に応答ストリーム生成をリクエストします...", file=sys.stderr)
        response_stream = model.generate_content(system_prompt, stream=True)
        
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        error_message = f"Gemini API(コピーライター)との通信中にエラーが発生しました: {e}"
        print(f"!!!!!! エラー !!!!!!: {error_message}", file=sys.stderr)
        yield f"申し訳ありません、AIとの通信中にエラーが発生しました: {e}"