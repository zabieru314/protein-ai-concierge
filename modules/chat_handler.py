import streamlit as st
import pandas as pd
import json
import re
import sys

# ▼▼▼【ここからが新しい構造です】▼▼▼
# 新しく作成した専門家たちをインポートします
from modules import gemini_client
from modules import formatters
from modules import nutrition_data
from modules import protein_selector
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲

def handle_ai_response(protein_df: pd.DataFrame):
    """
    ユーザーからのプロンプトを受け取り、各専門家と連携してAIの応答を生成・管理する司令塔。
    """
    try:
        # --- 1. ユーザー入力とペルソナの準備 ---
        prompt = st.session_state.messages[-1]["content"]
        
        # 最初の質問か、2回目以降かでAIに渡すプロンプトを整形
        if len(st.session_state.messages) == 1:
            persona_text = formatters.format_persona(st.session_state.persona)
            full_user_prompt = f"{persona_text}\n\n**ユーザーの『乗り換えの決め手』:**\n{prompt}"
        else:
            full_user_prompt = prompt
        
        # --- 2. AI分析官による意図の分析 ---
        # (gemini_clientは外部の専門家なので、そのまま呼び出します)
        intent_json = gemini_client.get_intent_from_ai(full_user_prompt)
        intent = json.loads(intent_json)
        user_desire = intent.get("user_desire_summary", "総合的なおすすめ")

        # --- 3. データ分析官による商品選定 ---
        # (最も複雑なロジックを、protein_selector専門家に完全に委任します)
        selected_products, baseline_product, selection_reason, key_metric_name_jp, key_metric_col_name = protein_selector.select_products(
            protein_df, intent, st.session_state.persona
        )

        # --- 4. AIコピーライターに渡すための情報整形 ---
        # (テキスト整形は、formatters専門家に完全に委任します)
        baseline_text = formatters.format_baseline_for_ai(baseline_product, key_metric_name_jp, key_metric_col_name)
        chat_history_text = formatters.format_chat_history(st.session_state.messages)
        
        # (豆知識の選定は、nutrition_data専門家に完全に委任します)
        nutrition_tip_text = nutrition_data.get_formatted_nutrition_tip(intent)

        # --- 5. AIコピーライターによる応答文の生成 ---
        ai_response_stream = gemini_client.get_ai_response_writer(
            full_user_prompt=full_user_prompt,
            user_desire_summary=user_desire,
            key_metric_name=key_metric_name_jp,
            selection_reason=selection_reason,
            baseline_product_data=baseline_text,
            selected_products_data=selected_products.to_markdown(index=False),
            chat_history=chat_history_text,
            nutrition_tip=nutrition_tip_text
        )

        # --- 6. 応答のストリーミングと解析 ---
        with st.chat_message("assistant"):
            full_response = st.write_stream(ai_response_stream)

        # 応答から[SUGGESTIONS]ブロックを抽出する
        # (この解析ロジックは司令塔の責務として残します)
        main_content = full_response
        suggestions = []
        
        suggestion_match = re.search(r'\[SUGGESTIONS\](.*)\[/SUGGESTIONS\]', full_response, re.DOTALL | re.IGNORECASE)
        if suggestion_match:
            main_content = full_response.replace(suggestion_match.group(0), '').strip()
            suggestion_text = suggestion_match.group(1).strip()
            suggestions = [line.strip() for line in suggestion_text.split('\n') if line.strip()]
            # 数字やハイフン、アスタリスクなどを除去
            suggestions = [re.sub(r'^\s*[\d\.\-\*]+\s*', '', s) for s in suggestions]

        # --- 7. セッション状態の更新 ---
        st.session_state.messages.append({"role": "assistant", "content": main_content, "suggestions": suggestions})
        
        # 比較表やポジションマップで使うデータを保存
        if not selected_products.empty:
            table_data = selected_products
            if baseline_product is not None and not baseline_product.empty:
                table_data = pd.concat([baseline_product.to_frame().T, selected_products]).reset_index(drop=True)
            
            st.session_state.table_info = {
                "data": table_data, 
                "metric": intent.get("key_metric", "Other")
            }

    except Exception as e:
        error_msg = f"処理中に予期せぬエラーが発生しました: {e}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        # エラー発生時はログに詳細を出力
        print(f"--- [CRITICAL ERROR in handle_ai_response] ---", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    
    finally:
        # 処理中フラグをリセット
        if "processing" in st.session_state:
            st.session_state.processing = False