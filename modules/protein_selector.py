# modules/protein_selector.py

import pandas as pd
from typing import Tuple, Dict, Any

def select_products(protein_df: pd.DataFrame, intent: Dict[str, Any], persona: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.Series, str, str, str]:
    """
    ユーザーの意図とペルソナに基づき、最適な商品をデータベースから選定する関数。
    
    戻り値:
    - selected_products (DataFrame): 提案する商品（2つ）
    - baseline_product (Series): 比較基準となる商品
    - selection_reason (str): AIに伝える選定理由
    - key_metric_name_jp (str): AIに伝える比較指標の日本語名
    - key_metric_col_name (str): AIに伝える比較指標の列名
    """
    df = protein_df.copy()
    
    # --- 1. ベースライン商品の特定 ---
    baseline_product = None
    product_id = persona.get('baseline_product_id')
    current_brand = persona.get('current_brand')

    if product_id:
        baseline_product_df = df[df["ProductID"] == product_id]
        if not baseline_product_df.empty:
            baseline_product = baseline_product_df.iloc[0]
    elif current_brand and current_brand in df["Brand"].values:
        baseline_product = df[df["Brand"] == current_brand].iloc[0]

    # --- 2. 意図に基づく商品選定 ---
    key_metric = intent.get("key_metric", "Other")
    
    selected_products = pd.DataFrame()
    key_metric_name_jp = "総合評価"
    key_metric_col_name = "ProteinPurity(%)"
    selection_reason = "総合的な観点"

    if key_metric == "ProteinPerServing(g)":
        # タンパク質含有率でソート
        recommend_df = df.sort_values(by="ProteinPurity(%)", ascending=False)
        key_metric_name_jp = "タンパク質含有率 (%)"
        key_metric_col_name = "ProteinPurity(%)"
        selection_reason = "タンパク質の品質（含有率）の高さ"
        
    elif key_metric == "PricePerKg(JPY)":
        # 価格でソート
        recommend_df = df.sort_values(by="PricePerKg(JPY)", ascending=True)
        key_metric_name_jp = "1kgあたりの価格"
        key_metric_col_name = "PricePerKg(JPY)"
        selection_reason = "優れたコストパフォーマンス"
        
    elif key_metric == "Taste":
        # 味に関するロジック
        relevant_tags = intent.get("relevant_tags", [])
        if relevant_tags:
            search_pattern = '|'.join(relevant_tags)
            tagged_products = df[df["PersonaTags"].str.contains(search_pattern, na=False)]
            if len(tagged_products) >= 2:
                selected_products = tagged_products.head(2)
            elif len(tagged_products) == 1:
                # 1つしか見つからなかった場合、残りはコスパで補う
                remaining_df = df.drop(tagged_products.index)
                best_of_rest = remaining_df.sort_values(by="PricePerKg(JPY)", ascending=True).head(1)
                selected_products = pd.concat([tagged_products, best_of_rest])
        
        if selected_products.empty:
            # タグにヒットしない場合、フォールバック
            fallback_tags = "#フレーバー豊富|#美味しい"
            fallback_products = df[df["PersonaTags"].str.contains(fallback_tags, na=False)]
            if len(fallback_products) >= 2:
                selected_products = fallback_products.head(2)
        
        # それでも見つからなければ、最終手段としてタンパク質含有率で選ぶ
        if selected_products.empty:
            recommend_df = df.sort_values(by="ProteinPurity(%)", ascending=False)
        else:
            recommend_df = pd.DataFrame() # selected_productsが既にある場合は、後のロジックをスキップ

        key_metric_name_jp = "味のバリエーションや評判"
        key_metric_col_name = None # 味には明確な数値指標がない
        selection_reason = "味の良さやフレーバーの豊富さ"
    else:
        # その他（総合評価）
        recommend_df = df.sort_values(by="ProteinPurity(%)", ascending=False)

    # --- 3. 最終的な商品リストの作成 ---
    # recommend_dfが設定されている場合（Taste以外、またはTasteのフォールバック）
    if not recommend_df.empty:
        # もしベースライン商品があれば、それ自身は提案リストから除外する
        if baseline_product is not None:
            recommend_df = recommend_df[recommend_df['ProductID'] != baseline_product['ProductID']]
        selected_products = recommend_df.head(2)

    return selected_products, baseline_product, selection_reason, key_metric_name_jp, key_metric_col_name