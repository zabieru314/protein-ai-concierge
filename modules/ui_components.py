import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components
import sys # ★★★ PowerShellへの出力に必須 ★★★

def render_diagnosis_form(protein_df: pd.DataFrame):
    """
    フェーズ1 & 2: 診断フォームのUIを全て描画する関数。
    ブランド選択後に、製品を動的に選択する『インテリジェント・セレクター』を搭載。
    """
    st.info("あなたに最適な提案をするために、まずは簡単な自己紹介をお願いします。")
    
    with st.container(border=True):
        # --- Q1. プロテインの利用経験は？ ---
        st.subheader("Q1. プロテインの利用経験は？")
        exp_options = ["継続的に飲んでいる", "初めて or ほとんど飲んだことがない"]
        
        # セッション状態を更新するためのコールバック関数
        def set_experience(exp):
            st.session_state.persona['experience'] = exp
        
        cols = st.columns(len(exp_options))
        for i, option in enumerate(exp_options):
            with cols[i]:
                # 選択されているボタンをハイライトするための設定
                button_type = "primary" if st.session_state.persona.get('experience') == option else "secondary"
                st.button(option, on_click=set_experience, args=[option], key=f"q1_{i}", use_container_width=True, type=button_type)

        # --- Q2. 現在、主に飲んでいるブランドと製品は？（インテリジェント・セレクター） ---
        if st.session_state.persona.get('experience') == '継続的に飲んでいる':
            st.subheader("Q2. 現在、主に飲んでいるブランドと製品は？")

            # --- ステップA: ブランド選択 ---
            # ブランドリストをデータベースから動的に生成し、「選択してください」を先頭に追加
            all_brands = ["選択してください"] + sorted(protein_df["Brand"].unique())
            
            # 現在選択されているブランドのインデックスを探す
            try:
                current_brand_index = all_brands.index(st.session_state.persona.get('current_brand'))
            except (ValueError, TypeError):
                current_brand_index = 0 # 見つからなければ「選択してください」をデフォルトにする

            selected_brand = st.selectbox(
                "まずブランドを選択してください",
                options=all_brands,
                index=current_brand_index,
                key="brand_selector"
            )
            
            # ブランドが選択されたらセッションに保存
            if selected_brand != "選択してください":
                st.session_state.persona['current_brand'] = selected_brand
            else:
                # 「選択してください」に戻された場合はクリア
                st.session_state.persona['current_brand'] = None
                st.session_state.persona['baseline_product_id'] = None

            # --- ステップB: 製品選択（ブランドが選択された場合のみ表示）---
            if st.session_state.persona.get('current_brand'):
                # 選択されたブランドの製品のみを抽出
                brand_df = protein_df[protein_df["Brand"] == st.session_state.persona['current_brand']]
                
                # 製品の選択肢を (表示名, 内部ID) のタプルのリストとして作成
                product_options = [("その他 / この中にない", "OTHER")] + list(zip(brand_df['ProductName'], brand_df['ProductID']))
                
                # 現在選択されている製品IDからインデックスを探す
                current_product_id = st.session_state.persona.get('baseline_product_id')
                current_product_index = 0 # デフォルトは「その他」
                if current_product_id:
                    try:
                        # product_optionsの中から、IDが一致するもののインデックスを見つける
                        current_product_index = [item[1] for item in product_options].index(current_product_id)
                    except ValueError:
                        current_product_index = 0 # 見つからなければ「その他」

                # 製品選択のselectbox
                selected_product_tuple = st.selectbox(
                    f"次に「{st.session_state.persona['current_brand']}」の具体的な製品を選択してください（任意）",
                    options=product_options,
                    index=current_product_index,
                    format_func=lambda x: x[0], # 表示上は製品名(タプルの0番目)だけを見せる
                    key="product_selector"
                )
                
                # 選択された製品IDをセッションに保存
                selected_product_id = selected_product_tuple[1]
                if selected_product_id != "OTHER":
                    st.session_state.persona['baseline_product_id'] = selected_product_id
                else:
                    st.session_state.persona['baseline_product_id'] = None
        
        # --- Q3. プロテインを飲む主な目的は何ですか？ ---
        st.subheader("Q3. プロテインを飲む主な目的は何ですか？")
        purpose_options = ["筋肉を大きくしたい", "ダイエット・減量", "健康・栄養補助"]
        st.session_state.persona['purpose'] = st.selectbox("目的", purpose_options, index=purpose_options.index(st.session_state.persona.get('purpose', '筋肉を大きくしたい')), label_visibility="collapsed")
        
        # --- Q4. 新しいプロテインを探す上で、重視する点は何ですか？ (いくつでも) ---
        st.subheader("Q4. 新しいプロテインを探す上で、重視する点は何ですか？ (いくつでも)")
        priorities_map = {'価格の安さ': '価格の安さ (コスパ)', '味のおいしさ': '味のおいしさ', '成分の品質': '成分の品質 (高タンパク, 無添加など)', '有名ブランド': '有名ブランドであることの安心感'}
        cols = st.columns(2)
        for i, (key, label) in enumerate(priorities_map.items()):
            with cols[i % 2]:
                with st.container(border=True):
                    st.session_state.persona['priorities'][key] = st.toggle(label, value=st.session_state.persona['priorities'].get(key, False), key=f"q4_{key}")

    st.markdown("---")
    if st.button("✅ 上の内容で、AIに相談を始める", type="primary", use_container_width=True):
        st.session_state.diagnosis_complete = True
        st.rerun()
def render_chat_interface(protein_df: pd.DataFrame):
    """
    チャット画面のUIを描画し、最後に比較表と次のアクションを提示する関数。
    """
    st.subheader("あなただけの『理想のプロテイン』を見つけましょう")
    current_brand = st.session_state.persona.get('current_brand', 'プロテイン')
    if current_brand == "その他 / 特にない": current_brand = "今お使いのプロテイン"
    st.write(f"もし、今の**`{current_brand}`**を超える**『あなたにピッタリな理想のプロテイン』**が存在するとしたら、それはどんなプロテインですか？")

    # --- ステップ1: チャット履歴の表示 ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                full_text = message["content"]
                final_question_keyword = "今回の提案をまとめると、"
                if final_question_keyword in full_text:
                    proposal_text = full_text.split(final_question_keyword)[0]
                else:
                    proposal_text = full_text
                
                proposal_parts = re.split(r'(### .*?<!-- ID: .*? -->)', proposal_text)
                protein_df_indexed = protein_df.set_index('ProductID')
                if proposal_parts and proposal_parts[0].strip():
                    st.markdown(proposal_parts[0].strip())
                for j in range(1, len(proposal_parts), 2):
                    headline_part = proposal_parts[j]
                    description_part = proposal_parts[j + 1] if (j + 1) < len(proposal_parts) else ""
                    cleaned_headline = re.sub(r'<!-- ID: .*? -->', '', headline_part).strip()
                    st.markdown(cleaned_headline)
                    st.markdown(description_part.strip())
                    match = re.search(r'<!-- ID: ([A-Z]{2}\d{3}) -->', headline_part)
                    if match:
                        product_id = match.group(1)
                        if product_id in protein_df_indexed.index:
                            product_data = protein_df_indexed.loc[product_id]
                            with st.container(border=True):
                                cols = st.columns([1, 2])
                                with cols[0]:
                                    if 'ImageURL' in product_data and product_data['ImageURL']:
                                        st.image(product_data['ImageURL'], use_container_width=True)
                                with cols[1]:
                                    st.markdown(f"**{product_data['Brand']}**")
                                    st.markdown(f"*{product_data['ProductName']}*")
                                    st.link_button("Amazonで見る 🛍️", product_data['AmazonURL'], use_container_width=True)
            else:
                st.markdown(message["content"])

    # --- ステップ2: サマリー（比較表、最終質問、提案ボタン）の表示 ---
    if st.session_state.get("table_info") is not None:
        
        # 1. 性能比較表の表示
        st.markdown("---")
        st.subheader("性能比較表")
        table_info = st.session_state.table_info
        table_df = table_info["data"]
        key_metric = table_info["metric"]
        display_columns = ['ProductName', 'ProteinPurity(%)', 'Price(JPY)', 'WeightInKg']
        if key_metric == 'PricePerKg(JPY)':
            display_columns.append('PricePerKg(JPY)')
        final_table = table_df[display_columns].rename(columns={
            'ProductName': '商品名', 'ProteinPurity(%)': 'タンパク質含有率 (%)',
            'Price(JPY)': '価格 (円)', 'WeightInKg': '内容量 (kg)',
            'PricePerKg(JPY)': '価格 (円/kg)'
        })
        st.table(final_table.set_index('商品名').style.format({
            'タンパク質含有率 (%)': '{:.1f}%', '価格 (円)': '{:,.0f}',
            '内容量 (kg)': '{:.2f}', '価格 (円/kg)': '{:,.0f}'
        }))

        # 2. 最後の質問の表示
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "assistant":
            final_question_keyword = "今回の提案をまとめると、"
            if final_question_keyword in last_message["content"]:
                final_question_text = final_question_keyword + last_message["content"].split(final_question_keyword)[1]
                st.markdown("---")
                st.markdown(final_question_text)

# 3. 提案ボタンの表示 (縦並び & 無効化対応)
            has_suggestions = "suggestions" in last_message and last_message["suggestions"]
            if has_suggestions:
                for suggestion in last_message["suggestions"]:
                    if st.button(
                        suggestion, 
                        key=suggestion, 
                        use_container_width=True,
                        disabled=st.session_state.get("processing", False)
                    ):
                        # ▼▼▼【修正箇所】ここから▼▼▼
                        # ボタンが押されたら、古いテーブル情報をクリアし、
                        # 次の入力プロンプトをセッションに保存するだけにする。
                        if "table_info" in st.session_state:
                            del st.session_state.table_info
                        st.session_state.prompt_from_button = suggestion
                        # ▲▲▲【修正箇所】ここまで▲▲▲

    # --- チャット入力欄の表示 ---
    # 初回表示時のヒントボタン
    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🤖"):
            st.caption("入力のヒント（下の例をクリックすると、そのまま送信されます）")
            example_prompts = ["味がもっと美味しいプロテイン", "今よりタンパク質が多いプロテイン", "とにかく、今より安いプロテイン"]
            
            # この関数内でpromptを直接設定するヘルパー関数
            def set_prompt_from_button(prompt_text):
                st.session_state.prompt_from_button = prompt_text

            for example in example_prompts:
                st.button(
                    example, 
                    on_click=set_prompt_from_button, 
                    args=[example], 
                    key=f"example_{example}", 
                    use_container_width=True, 
                    type="secondary",
                    disabled=st.session_state.get("processing", False) # 処理中はボタンを無効化
                )
            st.caption("もちろん、あなたの言葉で自由に入力してくださいね。")
    
    # ユーザーからの入力を受け取る
    prompt = None
    # まずボタンからの入力があったかチェック
    if st.session_state.get("prompt_from_button"):
        prompt = st.session_state.prompt_from_button
        # 一度使ったらクリアする
        st.session_state.prompt_from_button = None
    
    # 次にチャット入力欄からの入力をチェック
    chat_input = st.chat_input(
        "あなたの理想を、具体的に教えてください", 
        key="user_chat_input",
        disabled=st.session_state.get("processing", False) # 処理中は入力欄を無効化
    )
    if chat_input:
        prompt = chat_input
        
    return prompt