import streamlit as st
import pandas as pd
import json
from modules import gemini_client
import sys
import re

# --- ステップ1: 『賢い豆知識データベース』の定義 ---

NUTRITION_TIPS = {
    "general": {
        "title": "一般的なタンパク質摂取量",
        "template": (
            "ちなみに、ご存知でしたか？ 一般的に、健康維持のための1日のタンパク質推奨量は、体重1kgあたり約1.0gと言われています。"
            "例えば、平均的な体重の65kgの方なら、1日に65gのタンパク質が必要という計算になります。"
            "もし、1回の食事で20gのタンパク質が摂れるとすると、残りの45gをプロテインなどで賢く補うのが、理想的な栄養バランスへの近道ですよ。"
        )
    },
    "for_bulk_up": {
        "title": "筋肉を大きくしたい方向け",
        "template": (
            "筋肉を大きくしたいあなたに、一つ豆知識です！"
            "本格的にトレーニングをする方は、体重1kgあたり2.0gのタンパク質摂取が推奨されています。"
            "例えば、体重70kgの方なら、なんと1日に140gものタンパク質が必要になるんです。"
            "1回の食事で25g摂れたとしても、残りの115gを食事だけで補うのは大変ですよね。だからこそ、トレーニング後のプロテインが、目標達成のための強力な味方になるんです。"
        )
    },
    "for_diet": {
        "title": "ダイエット・引き締めたい方向け",
        "template": (
            "ダイエット中のあなたに、ぜひ知っておいてほしい豆知識があります。"
            "実は、ダイエット中でも筋肉を落とさないために、体重1kgあたり1.2gのタンパク質をしっかり摂ることが大切なんです。"
            "例えば、体重55kgの方なら、66gは必要になります。"
            "特に、食事制限で不足しがちな分をプロテインで補うと、満足感も得られて、キレイな体づくりに繋がりますよ。"
        )
    },
    "PricePerKg(JPY)": {
        "title": "コストパフォーマンスに関する豆知識",
        "template": (
            "プロテインの価格について、一つ面白い豆知識があります。"
            "実は、プロテインの価格は、ブランドや原材料だけでなく、**パッケージの容量**によっても大きく変わるんです。"
            "一般的に、1kgのパッケージよりも3kgや5kgといった大容量のパッケージの方が、1kgあたりの価格（コストパフォーマンス）は劇的に良くなることが多いんですよ。もしお気に入りのプロテインが見つかったら、次は大容量サイズを検討してみるのも賢い選択です。"
        )
    },
    "Taste": {
        "title": "プロテインの味に関する豆知識",
        "template": (
            "プロテインの「味」について、一つ豆知識です！"
            "味を左右するのはフレーバーだけでなく、ベースとなる**原料（ホエイかソイかなど）**も大きく影響するんです。"
            "一般的に、牛乳由来の「ホエイプロテイン」はクリーミーで飲みやすく、大豆由来の「ソイプロテイン」は少し素朴で、腹持ちが良いのが特徴です。もし今のプロテインの味が合わないと感じたら、次はベースの原料を変えてみるのも面白いかもしれませんよ。"
        )
    },
    "ProteinPerServing(g)": {
        "title": "タンパク質含有率に関する豆知識",
        "template": (
            "タンパク質の「質」を重視するあなたに、ぜひ知っておいてほしい豆知識があります。"
            "プロテインには主に**WPC**と**WPI**という種類があるのをご存知でしたか？"
            "WPIは、一般的なWPCからさらに脂質や乳糖などを取り除いた、より高純度なプロテインなんです。そのため、タンパク質含有率が非常に高く、お腹がゴロゴロしやすい方にもおすすめと言われています。少し価格は高めですが、品質を追求するなら、WPIと書かれた商品を探してみる価値はありますよ。"
        )
    }
}

# (get_formatted_nutrition_tip 関数は、計算機能が不要になったため、シンプルなものに置き換えます)
def get_formatted_nutrition_tip(tip_id: str) -> str:
    """
    指定されたIDの豆知識テキストをデータベースから取得する関数。
    """
    # tip_idがNUTRITION_TIPSに存在すればそのtemplateを、なければgeneralのtemplateを返す
    return NUTRITION_TIPS.get(tip_id, NUTRITION_TIPS["general"])["template"]

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

def format_persona(persona_data):
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
    """ベースライン商品を、AIが扱いやすい、より文脈的なテキスト形式に変換する"""
    if product_series.empty:
        return "N/A"
    
    brand_name = product_series.get('Brand', '不明なブランド')
    product_name = product_series.get('ProductName', '不明な商品')
    metric_value = product_series.get(key_metric_col, '不明')
    
    return f"ブランド名: {brand_name}, 代表商品名: {product_name}, {key_metric_name}: {metric_value}"

def handle_ai_response(protein_df: pd.DataFrame):
    try:
        # [DEBUG] --- 処理開始 ---
        print("\n" + "="*80, file=sys.stderr)
        print(f"--- [DEBUG] handle_ai_response が実行されました (現在 {len(st.session_state.messages)} 件のメッセージあり) ---", file=sys.stderr)
        print("="*80, file=sys.stderr)

        prompt = st.session_state.messages[-1]["content"]
        
        if len(st.session_state.messages) == 1:
            full_user_prompt = f"{format_persona(st.session_state.persona)}\n\n**ユーザーの『乗り換えの決め手』:**\n{prompt}"
        else:
            full_user_prompt = prompt
        
        with st.chat_message("assistant"):
            response_placeholder = st.empty()

        # --- ステップ1: AIによる意図分析 ---
        with st.spinner("お客様のご要望を分析中..."):
            intent_json = gemini_client.get_intent_from_ai(full_user_prompt)
            intent = json.loads(intent_json)
            key_metric = intent.get("key_metric", "Other")
            user_desire = intent.get("user_desire_summary", "総合的なおすすめ")

        # --- ステップ2: データベースからの商品選定 ---
        with st.spinner("データベースから最適な商品を選定中..."):
            df = protein_df.copy()
            df['ProteinPurity(%)'] = (df['ProteinPerServing(g)'] / df['ServingSize(g)']) * 100
            recommend_df = df.copy()
            
            # ▼▼▼【ここからが新しいロジック】▼▼▼
            baseline_product = pd.Series()
            product_id = st.session_state.persona.get('baseline_product_id')
            current_brand = st.session_state.persona.get('current_brand')

            # 1. 具体的な製品IDが選択されている場合、それを最優先で基準にする
            if product_id:
                baseline_product = df[df["ProductID"] == product_id].iloc[0]
            
            # 2. 製品IDがなく、ブランド名だけが選択されている場合（「その他」を選んだなど）
            elif current_brand and current_brand in df["Brand"].values:
                # これまで通り、そのブランドの最初の製品を代表として基準にする
                baseline_product = df[df["Brand"] == current_brand].iloc[0]
            # ▲▲▲【ここまでが新しいロジック】▲▲▲            
            selected_products = pd.DataFrame()
            key_metric_name_jp = "総合評価"
            key_metric_col_name = "ProteinPurity(%)"
            selection_reason = "総合的な観点"

            if key_metric == "ProteinPerServing(g)":
                selected_products = recommend_df.sort_values(by="ProteinPurity(%)", ascending=False).head(2)
                key_metric_name_jp = "タンパク質含有率 (%)"
                key_metric_col_name = "ProteinPurity(%)"
                selection_reason = "タンパク質の品質（含有率）の高さ"
            elif key_metric == "PricePerKg(JPY)":
                selected_products = recommend_df.sort_values(by="PricePerKg(JPY)", ascending=True).head(2)
                key_metric_name_jp = "1kgあたりの価格"
                key_metric_col_name = "PricePerKg(JPY)"
                selection_reason = "優れたコストパフォーマンス"
            elif key_metric == "Taste":
                relevant_tags = intent.get("relevant_tags", [])
                if relevant_tags:
                    search_pattern = '|'.join(relevant_tags)
                    tagged_products = recommend_df[recommend_df["PersonaTags"].str.contains(search_pattern, na=False)]
                    if len(tagged_products) >= 2:
                        selected_products = tagged_products.head(2)
                    elif len(tagged_products) == 1:
                        selected_products = pd.concat([tagged_products, recommend_df.drop(tagged_products.index).sort_values(by="PricePerKg(JPY)", ascending=True).head(1)])
                if selected_products.empty:
                    fallback_products = recommend_df[recommend_df["PersonaTags"].str.contains("#フレーバー豊富|#美味しい", na=False)]
                    selected_products = fallback_products.head(2) if len(fallback_products) >= 2 else recommend_df.sort_values(by="ProteinPurity(%)", ascending=False).head(2)
                key_metric_name_jp = "味のバリエーションや評判"
                key_metric_col_name = None
                selection_reason = "味の良さやフレーバーの豊富さ"
            else:
                selected_products = recommend_df.sort_values(by="ProteinPurity(%)", ascending=False).head(2)

        # --- ステップ3: ストリーミング表示とデータ保存 ---
        with st.spinner("AIがあなたに最適なご提案を作成中です..."):
            baseline_text = format_baseline_for_ai(baseline_product, key_metric_name_jp, key_metric_col_name)
            chat_history_text = format_chat_history(st.session_state.messages)
            # ▼▼▼【ここからが新しいロ-ジック】▼▼▼
            # ユーザーの意図に合った豆知識を選択する
            tip_id = "general" # デフォルト
            
            # まず、key_metricが豆知識DBに存在するかチェック
            if key_metric in NUTRITION_TIPS:
                tip_id = key_metric
            
            # 次に、タグによる上書きを試みる（より具体的な意図を優先）
            relevant_tags = intent.get("relevant_tags", [])
            if "#増量" in relevant_tags or "#バルクアップ" in relevant_tags:
                tip_id = "for_bulk_up"
            elif "#減量" in relevant_tags or "#ダイエット" in relevant_tags or "#引き締め" in relevant_tags:
                tip_id = "for_diet"
            
            # 選択したIDを元に、豆知識テキストを取得
            nutrition_tip_text = get_formatted_nutrition_tip(tip_id)
            # ▲▲▲【ここまでが新しいロジック】▲▲▲            
            ai_response_stream = gemini_client.get_ai_response_writer(
                full_user_prompt=full_user_prompt, user_desire_summary=user_desire,
                key_metric_name=key_metric_name_jp, selection_reason=selection_reason,
                baseline_product_data=baseline_text,
                selected_products_data=selected_products.to_markdown(index=False),
                chat_history=chat_history_text, nutrition_tip=nutrition_tip_text
            )

            # ▼▼▼【ここからが新しい、安定したストリーミング処理】▼▼▼
            # st.empty() と手動ループを削除し、st.write_stream に置き換える。
            # これだけで、画面へのストリーミング表示と、全テキストの変数への格納を同時に行ってくれる。
            full_response = response_placeholder.write_stream(ai_response_stream)
            # ▲▲▲【ここまでが新しい処理】▲▲▲

        # [EVIDENCE A] AIからの生の応答を、加工せずにそのまま表示
        print("\n" + "-"*80, file=sys.stderr)
        print("--- [EVIDENCE A] AIから受信した、加工前の完全な応答 (full_response) ---", file=sys.stderr)
        print(full_response, file=sys.stderr)
        print("-"*80 + "\n", file=sys.stderr)

        # ▼▼▼【重要】NameErrorを防ぐため、変数をここで初期化します ▼▼▼
        main_content = full_response
        suggestions = []

        # [DEEP ANALYSIS B] 提案ブロックの解析プロセスを、科学的に検証します
        print("--- [DEEP ANALYSIS B] 提案ブロックの科学的検証を開始します ---", file=sys.stderr)
        
        start_tag = "[suggestions]"
        end_tag = "[/suggestions]"
        lower_response = full_response.lower()
        start_index = lower_response.find(start_tag)
        end_index = lower_response.find(end_tag)
        print(f"\n[検証1: find()による単純検索]", file=sys.stderr)
        print(f"  - 開始タグ '{start_tag}' の検索結果 (位置): {start_index}", file=sys.stderr)
        print(f"  - 終了タグ '{end_tag}' の検索結果 (位置): {end_index}", file=sys.stderr)
        if end_index == -1:
            print("  - [検証結果] 終了タグが見つかりませんでした。これが問題の起点です。", file=sys.stderr)

        print(f"\n[検証2: repr()による内部表現の比較]", file=sys.stderr)
        target_end_tag = "[/suggestions]"
        if start_index != -1:
            search_area = full_response[start_index:]
            print(f"  - AIの応答の該当部分のrepr(): {repr(search_area)}", file=sys.stderr)
        else:
            print("  - (開始タグが見つからないため、調査スキップ)", file=sys.stderr)
        print(f"  - 私たちが探している終了タグのrepr(): {repr(target_end_tag)}", file=sys.stderr)
        print("  - [検証ポイント] もし、上の二つの文字列の見た目が違う場合（例: `\\n` や ` ` が混入しているなど）、それが原因です。", file=sys.stderr)

        print(f"\n[検証3: 文字コードの直接比較]", file=sys.stderr)
        if start_index != -1:
            end_tag_area = full_response[start_index + len(start_tag):]
            end_tag_candidate = end_tag_area.strip()[:20] 
            print("  --- AIの応答に含まれる終了タグ候補 ---", file=sys.stderr)
            for char in end_tag_candidate:
                print(f"    文字: '{char}', 文字コード (ord): {ord(char)}", file=sys.stderr)
            print("  --- 私たちが探している正しい終了タグ ---", file=sys.stderr)
            for char in target_end_tag:
                print(f"    文字: '{char}', 文字コード (ord): {ord(char)}", file=sys.stderr)
            print("  - [検証ポイント] もし、同じ文字に見えるのに、この数値が異なっている場合、それは『見た目が同じだけの別の文字』であることが確定します。", file=sys.stderr)
        else:
            print("  - (開始タグが見つからないため、調査スキップ)", file=sys.stderr)

        print("\n--- [DEEP ANALYSIS B] 科学的検証を終了しました ---", file=sys.stderr)
        
        # ▼▼▼【ここからが新しい、より強力な解析処理】▼▼▼
        # 実際の解析処理
        # 開始タグさえ見つかれば、終了タグが不完全でも処理を試みる
        if start_index != -1:
            # 本文 = 開始タグの前まで
            main_content = full_response[:start_index].strip()
            
            # 提案テキスト = 開始タグ以降の全て
            suggestion_block = full_response[start_index:]
            
            # 提案テキストから、開始タグと、もし存在するなら終了タグを「掃除」する
            suggestion_text = suggestion_block.lower().replace(start_tag, "").replace(end_tag, "").strip()

            # 綺麗になった提案テキストを、これまで通り解析する
            raw_lines = suggestion_text.split('\n')
            suggestions = [re.sub(r'^\s*[\d\.\-\*]+\s*', '', line).strip() for line in raw_lines if line.strip()]
            
            print("\n--- [NEW LOGIC] 新しい解析ロジックが実行されました ---", file=sys.stderr)
            print(f"  - 抽出された提案ブロック (suggestion_block):\n---\n{suggestion_block}\n---", file=sys.stderr)
            print(f"  - タグを掃除した後のテキスト (suggestion_text):\n---\n{suggestion_text}\n---", file=sys.stderr)

        else:
            # 開始タグが見つからない場合は、これまで通り何もしない
            main_content = full_response
            suggestions = []
        # ▲▲▲【ここまでが新しい解析処理】▲▲▲
        # [RESULT C] 最終的に st.session_state に保存される内容を表示
        print("\n" + "-"*80, file=sys.stderr)
        print("--- [RESULT C] st.session_state に保存する最終的な内容 ---", file=sys.stderr)
        print(f"  - 本文 (main_content):\n---\n{main_content}\n---", file=sys.stderr)
        print(f"  - 提案ボタンのリスト (suggestions): {suggestions}", file=sys.stderr)
        print("-"*80 + "\n", file=sys.stderr)

        # ▲▲▲【ここまでが最重要デバッグエリア】▲▲▲

        st.session_state.messages.append({"role": "assistant", "content": main_content, "suggestions": suggestions})
        
        if not selected_products.empty:
            table_data = selected_products
            if not baseline_product.empty:
                table_data = pd.concat([baseline_product.to_frame().T, selected_products]).reset_index(drop=True)
            st.session_state.table_info = {"data": table_data, "metric": key_metric}

    except Exception as e:
        error_msg = f"処理中に予期せぬエラーが発生しました: {e}"
        st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    finally:
        st.session_state.processing = False