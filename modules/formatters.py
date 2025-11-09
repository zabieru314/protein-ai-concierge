# modules/formatters.py

import pandas as pd

def format_chat_history(messages: list) -> str:
    """
    Streamlitのチャット履歴(辞書のリスト)を、
    AIが読みやすいシンプルなテキスト形式に変換する関数。
    """
    history_text = ""
    for message in messages:
        role = "あなた" if message["role"] == "user" else "AIコンシェルジュ"
        history_text += f"{role}: {message['content']}\n\n"
    return history_text.strip()

def format_persona(persona_data: dict) -> str:
    """
    診断結果の辞書を、AIが理解しやすいテキスト形式に変換する関数。
    """
    priorities_list = [key for key, value in persona_data['priorities'].items() if value]
    persona_text = "【ユーザープロフィール】\n"
    if 'experience' in persona_data: persona_text += f"- 利用経験: {persona_data['experience']}\n"
    if 'current_brand' in persona_data: persona_text += f"- 現在のブランド: {persona_data['current_brand']}\n"
    if 'purpose' in persona_data: persona_text += f"- 目的: {persona_data['purpose']}\n"
    if priorities_list: persona_text += f"- 重視する点: {', '.join(priorities_list)}\n"
    return persona_text

def format_baseline_for_ai(product_series: pd.Series, key_metric_name: str, key_metric_col: str) -> str:
    """
    ベースライン商品を、AIが扱いやすい、より文脈的なテキスト形式に変換する関数。
    """
    if product_series is None or product_series.empty:
        return "N/A"
    
    brand_name = product_series.get('Brand', '不明なブランド')
    product_name = product_series.get('ProductName', '不明な商品')
    
    # key_metric_colが指定されている場合のみ、その値を表示
    if key_metric_col and key_metric_col in product_series:
        metric_value = product_series.get(key_metric_col)
        # 数値の場合はフォーマットする
        if isinstance(metric_value, (int, float)):
            return f"ブランド名: {brand_name}, 代表商品名: {product_name}, {key_metric_name}: {metric_value:,.0f}"
        else:
            return f"ブランド名: {brand_name}, 代表商品名: {product_name}, {key_metric_name}: {metric_value}"
    else:
        # key_metric_colがない場合（例: Taste）は、指標の値は含めない
        return f"ブランド名: {brand_name}, 代表商品名: {product_name}"