import streamlit as st
import google.generativeai as genai
import sys
import os

# ▼▼▼【ここからが修正箇所です】▼▼▼
# ローカルのconfig.jsonを読むロジックを完全に削除し、
# Streamlit CloudのSecretsからのみキーを読み込むように簡潔化します。

def _initialize_gemini():
    """
    StreamlitのSecretsからGemini APIキーを取得し、モデルを初期化する関数。
    """
    try:
        # より確実な「辞書アクセス」方式で、Secretsから直接キーを取得します。
        api_key = st.secrets["gemini_api_key"]
        
        if not api_key:
            st.error("設定エラー: Gemini APIキーが空です。StreamlitのSecretsを確認してください。")
            return None

        genai.configure(api_key=api_key)
        # 安定性と性能のバランスが良い、最新のモデル名を指定します。
        model = genai.GenerativeModel('gemini-2.0-flash-lite') 
        print("--- [SUCCESS] Authenticated with Streamlit Secrets for Gemini. ---", file=sys.stderr)
        return model

    except KeyError:
        # st.secrets["gemini_api_key"] が存在しない場合のエラー
        st.error("設定エラー: Gemini APIキーがStreamlitのSecretsに設定されていません。")
        print("--- [CRITICAL ERROR] 'gemini_api_key' not found in st.secrets. ---", file=sys.stderr)
        return None
    except Exception as e:
        # その他の予期せぬエラー
        st.error(f"Geminiの初期化中に予期せぬエラーが発生しました: {e}")
        print(f"--- [CRITICAL ERROR] An unexpected error occurred during Gemini initialization: {e} ---", file=sys.stderr)
        return None

# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

# --- ここから下のコードは、上記の修正により、変更の必要がありません ---
# 呼び出し元の _initialize_gemini() がシンプルになっただけで、
# これらの関数のロジックはそのまま正しく動作します。

def get_intent_from_ai(user_prompt: str) -> str:
    """ユーザーのプロンプトを分析し、意図をJSON形式で返す。"""
    print("\n--- get_intent_from_ai function called ---", file=sys.stderr)
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
        print(f"  - AI Analyzer response (JSON) received.", file=sys.stderr)
        return cleaned_json
    except Exception as e:
        error_message = f"Gemini API (Analyzer) communication error: {e}"
        print(f"!!!!!! ERROR !!!!!!: {error_message}", file=sys.stderr)
        st.error(error_message)
        return "{}"

def get_ai_response_writer(
    full_user_prompt: str, user_desire_summary: str, key_metric_name: str,
    selection_reason: str, baseline_product_data: str, selected_products_data: str,
    chat_history: str, nutrition_tip: str
):
    """整形済みデータを受け取り、AI(コピーライター)から応答をストリームとして生成する"""
    print("\n--- get_ai_response_writer function called (streaming) ---", file=sys.stderr)
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
        error_message = f"Gemini API (Writer) communication error: {e}"
        print(f"!!!!!! ERROR !!!!!!: {error_message}", file=sys.stderr)
        yield f"申し訳ありません、AIとの通信中にエラーが発生しました: {e}"