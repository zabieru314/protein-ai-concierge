import streamlit as st
import google.generativeai as genai
import pandas as pd
import sys
import os
import json

# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★
# ★★★ ここが、あなたのPCとクラウドの両方で鍵を見つけるための新しいロジックです ★★★
def get_gemini_api_key():
    """クラウド環境(st.secrets)とローカル環境(config.json)の両方からAPIキーを取得する関数"""
    try:
        if "gemini_api_key" in st.secrets:
            return st.secrets["gemini_api_key"]
    except Exception:
        pass
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("gemini_api_key")
    except Exception as e:
        print(f"--- [ERROR] Failed to read Gemini API key from config.json: {e} ---", file=sys.stderr)
    return None
# ★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★★

def _initialize_gemini():
    """Gemini APIキーを設定し、モデルを初期化する共通関数。"""
    api_key = get_gemini_api_key() # ← 新しいキー取得関数を呼び出す
    if not api_key:
        st.error("設定エラー: Gemini APIキーが見つかりません。config.jsonを確認してください。")
        return None
    try:
        genai.configure(api_key=api_key)
        # あなたが指定した、実績のあるモデル名を使用します
        model = genai.GenerativeModel('gemini-2.0-flash-lite') 
        return model
    except Exception as e:
        st.error(f"Geminiの初期化中にエラーが発生しました: {e}")
        return None

# --- ここから下は、あなたのオリジナルのロジックを完全に尊重します ---

def get_intent_from_ai(user_prompt: str) -> str:
    """ユーザーのプロンプトを分析し、意図をJSON形式で返す。"""
    print("\n--- get_intent_from_ai関数が実行されました ---", file=sys.stderr)
    model = _initialize_gemini()
    if not model:
        return "{}"

    try:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'system_prompt_analyzer.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        full_prompt = f"{system_prompt}\n\n# ユーザーの要望:\n{user_prompt}"
        response = model.generate_content(full_prompt)
        cleaned_json = response.text.strip().lstrip("```json").rstrip("```")
        print(f"  - AI(分析官)からの応答(JSON)を受信しました: {cleaned_json}", file=sys.stderr)
        return cleaned_json
    except Exception as e:
        error_message = f"Gemini API(分析官)との通信中にエラーが発生しました: {e}"
        print(f"!!!!!! エラー !!!!!!: {error_message}", file=sys.stderr)
        st.error(error_message)
        return "{}"

def get_ai_response_writer(
    full_user_prompt: str, user_desire_summary: str, key_metric_name: str,
    selection_reason: str, baseline_product_data: str, selected_products_data: str,
    chat_history: str, nutrition_tip: str
):
    """整形済みデータを受け取り、AI(コピーライター)から応答をストリームとして生成する"""
    print("\n--- get_ai_response_writer関数が実行されました (ストリーミング) ---", file=sys.stderr)
    model = _initialize_gemini()
    if not model:
        yield "申し訳ありません、AIの初期化に失敗しました。"
        return

    try:
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'system_prompt_writer.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        system_prompt = prompt_template.replace(
            "[full_user_prompt]", full_user_prompt
        ).replace(
            "[user_desire_summary]", user_desire_summary
        ).replace(
            "[key_metric_name]", key_metric_name
        ).replace(
            "[selection_reason]", selection_reason
        ).replace(
            "[baseline_product_data]", baseline_product_data
        ).replace(
            "[selected_products_data]", selected_products_data
        ).replace(
            "[chat_history]", chat_history
        ).replace(
            "[nutrition_tip]", nutrition_tip
        )
        
        response_stream = model.generate_content(system_prompt, stream=True)
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        error_message = f"Gemini API(コピーライター)との通信中にエラーが発生しました: {e}"
        print(f"!!!!!! エラー !!!!!!: {error_message}", file=sys.stderr)
        yield f"申し訳ありません、AIとの通信中にエラーが発生しました: {e}"