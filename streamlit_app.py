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
"""et("cost", "")
    p_comm = product.get("commission", "")
    p_sales = product.get("sales", "")
    p_rating = product.get("rating", "")
    p_url = product.get("url", "")
    p_specs = product.get("specs", "")
    p_platform = product.get("platform", "")

    return f"""
你現在是「{APP_NAME}」的核心電商 AI。
請根據使用者提供的商品圖片與商品資料，嚴格產出以下內容：

==============================
【商品資料】
==============================
商品名稱: {p_name}
商品價格: {p_price}
商品成本: {p_cost}
分潤比例: {p_comm}
月銷量: {p_sales}
商品評分: {p_rating}
商品連結: {p_url}
商品規格: {p_specs}
目標平台: {p_platform}

==============================
【重要資料規則】
==============================
只能根據圖片與使用者提供的資料，不能自行捏造。不知道的資訊請寫「待確認」。

==============================
【任務一：商品辨識與 AI 選品分析】
==============================
1. 商品辨識（品名、分類、確定資訊、待確認資訊、主要賣點、目標客群）
2. AI 選品分析（市場定位、優劣勢、短影音切入點、購買誘因、合規提醒）

==============================
【任務二：蝦皮高轉化上架文案】
==============================
{SHOPEE_PROMPT_TEMPLATE}

==============================
【任務三：TikTok 爆款帶貨文案】
==============================
{TIKTOK_PROMPT_TEMPLATE}

==============================
【任務四：即夢 AI 2.5 商業生圖 Prompt】
==============================
請遵循規範：
{JIMENG_25_RULES}

輸出格式：
- 【即夢 AI 2.5 生圖英文 Prompt】
- 【Negative Prompt】
- 【畫面繁體中文文字設計】
- 【9:16 構圖與光影建議】

==============================
【任務五：即夢 AI 2.5 商業影片 Prompt】
==============================
輸出格式：
- 【即夢 AI 2.5 影片英文 Prompt】(包含 Opening, Middle, Camera Motion, Lighting, Product Detail, Ending Freeze)
- 【Negative Prompt】

==============================
【任務六：即夢 AI 2.5 爆款 25 秒帶貨分鏡腳本】
==============================
- 0~3 秒：黃金 Hook (吸引注意)
- 3~8 秒：商品全貌與品質展示
- 8~15 秒：核心賣點與細節特寫
- 15~20 秒：使用情境與價值呈現
- 20~25 秒：強力 CTA 與結尾定格

==============================
【任務七：分潤合規與最終檢查】
==============================
檢查資料是否精確、無虛構誇大，且完整符合即夢 2.5 規範。
"""


# ============================================================
# 頁面元件：登入頁
# ============================================================

def render_login_page():
    st.markdown(
        f"""
        <div class="main-title">🛒 {APP_NAME}</div>
        <div class="sub-title">永久會員｜管理員｜Gemini 2.5 Flash｜即夢 AI 2.5</div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["🔐 會員登入", "📝 會員註冊"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("會員帳號")
            password = st.text_input("會員密碼", type="password")
            submitted = st.form_submit_button("登入", use_container_width=True)

        if submitted:
            ok, message = login_user(username, password)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.info("預設管理員帳號：admin / 密碼：admin123456")

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("新會員帳號")
            name = st.text_input("姓名 / 暱稱")
            email = st.text_input("Email")
            password = st.text_input("密碼", type="password")
            password2 = st.text_input("再次輸入密碼", type="password")
            submitted = st.form_submit_button("註冊永久會員", use_container_width=True)

        if submitted:
            if password != password2:
                st.error("兩次密碼不一致。")
            else:
                ok, message = create_member(username, password, name, email, "member")
                if ok:
                    st.success(message)
                else:
                    st.error(message)


# ============================================================
# 頁面元件：Sidebar
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(f"## 🛒 {APP_NAME}")
        st.markdown(
            f"""
            <div class="member-card">
            👤 <b>{st.session_state.name}</b><br>
            帳號：{st.session_state.username}<br>
            權限：{st.session_state.role}<br>
            會員期限：<b>永久</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🏠 AI 自動化", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        if st.session_state.role == "admin":
            if st.button("👑 管理員中心", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        st.divider()

        if st.button("🚪 登出", use_container_width=True):
            logout_user()
            st.rerun()


# ============================================================
# 頁面元件：管理員中心
# ============================================================

def render_admin_page():
    st.title("👑 管理員中心")
    st.caption("永久會員制：沒有到期日期，管理員可以手動啟用或停用。")

    members = load_members()
    total_members = len(members)
    active_members = sum(1 for m in members if m.get("status") == "active")
    admin_count = sum(1 for m in members if m.get("role") == "admin")

    col1, col2, col3 = st.columns(3)
    col1.metric("會員總數", total_members)
    col2.metric("啟用會員", active_members)
    col3.metric("管理員", admin_count)

    st.divider()

    st.subheader("➕ 建立永久會員")
    with st.form("admin_create_member"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("會員帳號")
            name = st.text_input("姓名 / 暱稱")
        with col2:
            password = st.text_input("會員密碼", type="password")
            email = st.text_input("Email")

        role = st.selectbox(
            "會員等級",
            ["member", "vip", "admin"],
            format_func=lambda v: {"member": "一般會員", "vip": "VIP 會員", "admin": "管理員"}[v],
        )

        submitted = st.form_submit_button("建立永久會員", use_container_width=True)

    if submitted:
        ok, message = create_member(username, password, name, email, role)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.divider()

    st.subheader("👥 會員管理")
    members = load_members()

    if not members:
        st.info("目前沒有會員資料。")
    else:
        for idx, m in enumerate(members):
            with st.expander(f"👤 {m.get('username')} ({m.get('name')}) - {m.get('role').upper()}"):
                st.write(f"**Email:** {m.get('email', '無')}")
                st.write(f"**狀態:** {m.get('status')}")
                st.write(f"**建立時間:** {m.get('created_at')}")

                if m.get("username") != ADMIN_USERNAME:
                    btn_label = "停用帳號" if m.get("status") == "active" else "啟用帳號"
                    if st.button(btn_label, key=f"toggle_{idx}"):
                        m["status"] = "disabled" if m.get("status") == "active" else "active"
                        save_members(members)
                        st.success(f"已更新 {m.get('username')} 的狀態")
                        st.rerun()


# ============================================================
# 頁面元件：AI 自動化主頁
# ============================================================

def render_home_page():
    st.title(f"🛒 {APP_NAME}")
    st.caption("一鍵產生蝦皮高轉化文案、TikTok 爆款腳本及即夢 AI 2.5 提示詞")

    col_left, col_right = st.columns([1, 1])

    with col_left:
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
