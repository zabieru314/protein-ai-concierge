import streamlit as st
import pandas as pd
import re
import streamlit.components.v1 as components
import sys
import altair as alt

def render_protein_position_map(all_proteins_df: pd.DataFrame, comparison_df: pd.DataFrame):
    """プロテイン・ポジションマップ（散布図）を描画する関数"""
    st.subheader("プロテイン・ポジションマップ")

    plot_df = all_proteins_df.copy()
    plot_df['Highlight'] = 'その他の商品'

    if not comparison_df.empty:
        baseline_id = comparison_df.iloc[0]['ProductID']
        recommend_ids = comparison_df.iloc[1:]['ProductID'].tolist()
        plot_df.loc[plot_df['ProductID'] == baseline_id, 'Highlight'] = '現在の商品'
        plot_df.loc[plot_df['ProductID'].isin(recommend_ids), 'Highlight'] = 'AIの提案'

    chart = alt.Chart(plot_df).mark_circle(size=100).encode(
        x=alt.X('PricePerKg(JPY):Q', title='価格 (円/kg) ←安い', scale=alt.Scale(zero=False)),
        y=alt.Y('ProteinPurity(%):Q', title='タンパク質含有率 (%) ↑高い', scale=alt.Scale(zero=False)),
        color=alt.Color('Highlight:N', title='凡例',
            scale=alt.Scale(
                domain=['現在の商品', 'AIの提案', 'その他の商品'],
                range=['#1f77b4', '#2ca02c', 'lightgray']
            )
        ),
        tooltip=['Brand', 'ProductName', 'PricePerKg(JPY)', 'ProteinPurity(%)']
    ).properties(
        title='市場全体におけるあなたのプロテインの位置'
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    st.caption("グラフ上の点をクリック＆ドラッグで移動、マウスホイールで拡大・縮小ができます。")

def render_diagnosis_form(protein_df: pd.DataFrame):
    """診断フォームのUIを全て描画する関数"""
    st.info("あなたに最適な提案をするために、まずは簡単な自己紹介をお願いします。")
    
    with st.container(border=True):
        st.subheader("Q1. プロテインの利用経験は？")
        exp_options = ["継続的に飲んでいる", "初めて or ほとんど飲んだことがない"]
        
        def set_experience(exp):
            st.session_state.persona['experience'] = exp
        
        cols = st.columns(len(exp_options))
        for i, option in enumerate(exp_options):
            with cols[i]:
                button_type = "primary" if st.session_state.persona.get('experience') == option else "secondary"
                st.button(option, on_click=set_experience, args=[option], key=f"q1_{i}", use_container_width=True, type=button_type)

        if st.session_state.persona.get('experience') == '継続的に飲んでいる':
            st.subheader("Q2. 現在、主に飲んでいるブランドと製品は？")
            all_brands = ["選択してください"] + sorted(protein_df["Brand"].unique())
            
            try:
                current_brand_index = all_brands.index(st.session_state.persona.get('current_brand'))
            except (ValueError, TypeError):
                current_brand_index = 0

            selected_brand = st.selectbox(
                "まずブランドを選択してください",
                options=all_brands,
                index=current_brand_index,
                key="brand_selector"
            )
            
            if selected_brand != "選択してください":
                st.session_state.persona['current_brand'] = selected_brand
            else:
                st.session_state.persona['current_brand'] = None
                st.session_state.persona['baseline_product_id'] = None

            if st.session_state.persona.get('current_brand'):
                brand_df = protein_df[protein_df["Brand"] == st.session_state.persona['current_brand']]
                product_options = [("その他 / この中にない", "OTHER")] + list(zip(brand_df['ProductName'], brand_df['ProductID']))
                
                current_product_id = st.session_state.persona.get('baseline_product_id')
                current_product_index = 0
                if current_product_id:
                    try:
                        current_product_index = [item[1] for item in product_options].index(current_product_id)
                    except ValueError:
                        current_product_index = 0

                selected_product_tuple = st.selectbox(
                    f"次に「{st.session_state.persona['current_brand']}」の具体的な製品を選択してください（任意）",
                    options=product_options,
                    index=current_product_index,
                    format_func=lambda x: x[0],
                    key="product_selector"
                )
                
                selected_product_id = selected_product_tuple[1]
                if selected_product_id != "OTHER":
                    st.session_state.persona['baseline_product_id'] = selected_product_id
                else:
                    st.session_state.persona['baseline_product_id'] = None
        
        st.subheader("Q3. プロテインを飲む主な目的は何ですか？")
        purpose_options = ["筋肉を大きくしたい", "ダイエット・減量", "健康・栄養補助"]
        st.session_state.persona['purpose'] = st.selectbox("目的", purpose_options, index=purpose_options.index(st.session_state.persona.get('purpose', '筋肉を大きくしたい')), label_visibility="collapsed")
        
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
    チャット画面のUIを描画する関数。
    AIのテキスト表示と、商品カードの表示を完全に分離し、安定性を確保。
    """
    st.subheader("あなただけの『理想のプロテイン』を見つけましょう")
    current_brand = st.session_state.persona.get('current_brand', 'プロテイン')
    if current_brand == "その他 / 特にない": current_brand = "今お使いのプロテイン"
    st.write(f"もし、今の**`{current_brand}`**を超える**『あなたにピッタリな理想のプロテイン』**が存在するとしたら、それはどんなプロテインですか？")

    # --- ステップ1: まず、すべてのチャット履歴を、ありのままに表示する ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # AIの応答も、ユーザーのメッセージも、まずは単純にMarkdownとして表示
            st.markdown(message["content"])

    # --- ステップ2: 最後のメッセージがAIからのものであれば、そこから商品カードを生成する ---
    last_message = st.session_state.messages[-1] if st.session_state.messages else {}
    if last_message and last_message.get("role") == "assistant":
        
        # [新しいロジック] AIの応答テキスト全体から、IDをすべて探し出す
        product_ids_found = re.findall(r'<!-- ID: ([A-Z]{2}\d{3}) -->', last_message["content"])
        
        if product_ids_found:
            st.markdown("---")
            st.subheader("提案商品の詳細")
            protein_df_indexed = protein_df.set_index('ProductID')
            
            # 見つかったIDの数だけ、商品カードを順番に表示する
            for product_id in set(product_ids_found): # set()で重複を除外
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

    # --- ステップ3: 比較表や提案ボタンなど、残りのUIを表示する ---
    if st.session_state.get("table_info") is not None:
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

    if last_message and last_message.get("role") == "assistant":
        suggestions = last_message.get("suggestions", [])
        if suggestions:
            for suggestion in suggestions:
                if st.button(suggestion, key=suggestion, use_container_width=True, disabled=st.session_state.get("processing", False)):
                    if "table_info" in st.session_state:
                        del st.session_state.table_info
                    st.session_state.prompt_from_button = suggestion
                    st.rerun()

    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🤖"):
            st.caption("入力のヒント（下の例をクリックすると、そのまま送信されます）")
            example_prompts = ["味がもっと美味しいプロテイン", "今よりタンパク質が多いプロテイン", "とにかく、今より安いプロテイン"]
            def set_prompt_from_button(prompt_text):
                st.session_state.prompt_from_button = prompt_text
            for example in example_prompts:
                st.button(example, on_click=set_prompt_from_button, args=[example], key=f"example_{example}", use_container_width=True, type="secondary", disabled=st.session_state.get("processing", False))
            st.caption("もちろん、あなたの言葉で自由に入力してくださいね。")
    
    prompt = None
    if st.session_state.get("prompt_from_button"):
        prompt = st.session_state.prompt_from_button
        st.session_state.prompt_from_button = None
    
    chat_input = st.chat_input("あなたの理想を、具体的に教えてください", key="user_chat_input", disabled=st.session_state.get("processing", False))
    if chat_input:
        prompt = chat_input
        
    return prompt