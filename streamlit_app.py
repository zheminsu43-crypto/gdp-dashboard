JIMENG_25_RULES = """
==================================================
即夢 AI 2.5 PRO 核心控制規則
==================================================

【AI 商品辨識最高原則】

1. 上傳圖片中的商品為唯一真實來源。
2. AI 必須優先辨識：
- 最大面積商品
- 最清楚商品
- 有品牌標誌商品
- 包裝文字最完整商品

3. 禁止自行幻想商品資訊。
4. 圖片看不清楚：
必須輸出：
「待確認」

禁止：
- 自創品牌
- 自創容量
- 自創功效
- 自創成分
- 自創價格


==================================================
【商品原貌鎖定 Product Identity Lock】
==================================================

生成任何圖片與影片：

必須保持：

✓ 商品品牌
✓ Logo
✓ 包裝
✓ 瓶身
✓ 盒型
✓ 顏色
✓ 材質
✓ 比例
✓ 標籤
✓ 印刷文字

完全一致。


禁止：

❌ 改變瓶身
❌ 改變盒子
❌ 改變顏色
❌ 改變品牌
❌ 改變文字
❌ 生成類似商品代替


==================================================
【商品一致性控制】
==================================================

整個影片：

第一秒商品是什麼，
最後一秒必須還是同一個商品。


禁止：

❌ 商品變形
❌ 商品融化
❌ 商品漂浮
❌ 商品複製
❌ 多個商品
❌ 包裝變形
❌ Logo錯亂
❌ 文字漂移
❌ 閃爍


==================================================
【人物限制】
==================================================

所有商業圖片：

禁止：

❌ 人物
❌ 手拿商品
❌ 模特展示
❌ 人體部位
❌ 主播


商品必須：

單獨展示。


==================================================
【商業攝影規格】
==================================================

風格：

High-end commercial product photography

要求：

- Studio lighting
- Ultra realistic
- 8K quality
- Professional advertising style
- Clean background
- Product centered


適合：

✓ Shopee 主圖
✓ TikTok 商品影片
✓ 電商廣告


==================================================
【即夢 AI 2.5 生圖輸出格式】
==================================================

每次必須輸出：

【English Prompt】

內容包含：

Product
Material
Lighting
Camera angle
Composition
Background
Commercial style


【Negative Prompt】

固定加入：

no people,
no hands,
no watermark,
no extra products,
no wrong logo,
no fake text,
no deformation,
no duplicate object,
no floating package


【繁體中文海報文字】

只能使用：

繁體中文

禁止：

簡體中文


==================================================
【即夢 AI 2.5 影片控制】
==================================================

影片比例：

9:16


時間：

15-30秒


影片結構：


Opening 0-3秒

完整商品正面展示

商品置中


Middle 3-20秒

慢慢推近：

smooth camera push in

展示：

- 包裝細節
- 材質
- Logo
- 商品特色


Ending 20-30秒

商品置中

畫面停止

Freeze Frame


==================================================
【爆款帶貨影片腳本】
==================================================


0-3秒：

黃金Hook

方式：

痛點
驚喜
好奇


3-8秒：

商品展示


8-15秒：

核心賣點


15-20秒：

使用情境


20-30秒：

CTA

例如：

立即購買
加入購物車
限時優惠


==================================================
【蝦皮SEO規則】
==================================================

標題：

品牌 + 商品名稱 + 核心特色 + 規格 + 熱搜詞


禁止：

❌ 過度誇大
❌ 虛假醫療效果
❌ 100%保證


輸出：

1. SEO標題

2. 五大賣點

3. 商品描述

4. 規格表

5. 使用方式

6. 注意事項

7. Hashtag


==================================================
【TikTok 爆款規則】
==================================================


輸出：

Hook 3版本

↓

15-30秒口播稿

↓

Caption

↓

CTA

↓

熱門Hashtag


語氣：

自然
快速
有購買衝動


==================================================
【AI 合規檢查】
==================================================


最後必須檢查：

✓ 是否符合商品圖片
✓ 是否虛構資訊
✓ 是否誇大效果
✓ 是否違反平台規則
✓ 是否符合電商展示


如果資料不足：

輸出：

「待確認」
"""
        st.subheader("1. 上傳商品圖片")
        uploaded_file = st.file_uploader("選擇圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            st.image(uploaded_file, caption="預覽商品圖片", use_container_width=True)

        st.subheader("2. 填寫商品資料")
        product_name = st.text_input("商品名稱", placeholder="例如：極致保濕修護精華液")
        product_price = st.text_input("商品售價", placeholder="例如：499")
        product_cost = st.text_input("商品成本", placeholder="例如：150")
        product_commission = st.text_input("分潤比例 (%)", placeholder="例如：15")
        product_sales = st.text_input("預估月銷量", placeholder="例如：1000")
        product_rating = st.text_input("商品評分", placeholder="例如：4.9")
        product_url = st.text_input("商品連結", placeholder="例如：https://shopee.tw/...")
        product_specs = st.text_area("商品規格/細節描述", placeholder="例如：容量 30ml，保存期限 3 年...")
        platform = st.selectbox("主要目標平台", ["蝦皮購物 + TikTok", "僅蝦皮購物", "僅 TikTok"])

        generate_btn = st.button("🚀 開始 AI 文案與提示詞生成", type="primary", use_container_width=True)

    with col_right:
        st.subheader("3. AI 分析與生成結果")

        if generate_btn:
            if not uploaded_file:
                st.warning("請先上傳商品圖片。")
            elif not product_name.strip():
                st.warning("請輸入商品名稱。")
            else:
                with st.spinner("AI 正在分析圖片並為您撰寫蝦皮、TikTok 與即夢 2.5 提示詞中..."):
                    try:
                        img_bytes, mime_type = prepare_image(uploaded_file)
                        product_data = {
                            "name": product_name,
                            "price": product_price,
                            "cost": product_cost,
                            "commission": product_commission,
                            "sales": product_sales,
                            "rating": product_rating,
                            "url": product_url,
                            "specs": product_specs,
                            "platform": platform,
                        }
                        prompt = build_master_prompt(product_data)
                        result = ask_gemini(prompt, img_bytes, mime_type)
                        st.session_state.result = result
                    except Exception as e:
                        st.error(f"生成失敗：{e}")

        if st.session_state.result:
            st.markdown(st.session_state.result)
            st.download_button(
                label="📥 下載完整報告 (.txt)",
                data=st.session_state.result,
                file_name=f"{product_name}_AI電商報告.txt",
                mime="text/plain",
                use_container_width=True,
            )


# ============================================================
# 主程式入口 (Main)
# ============================================================

def main():
    ensure_admin()

    if not st.session_state.logged_in:
        render_login_page()
    else:
        render_sidebar()
        if st.session_state.page == "admin" and st.session_state.role == "admin":
            render_admin_page()
        else:
            render_home_page()


if __name__ == "__main__":
    main()
