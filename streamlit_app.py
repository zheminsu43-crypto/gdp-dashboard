import os
import json
import requests
import subprocess
import streamlit as st
from google import genai

# ==========================================
# 1. 頁面設定與 API 金鑰配置
# ==========================================
st.set_page_config(page_title="AI 短影音自動生成器", page_icon="🎬", layout="centered")
st.title("🎬 AI 短影音自動生成器")

GEMINI_KEY = "AIzaSyBuQ8Hf8nKJKRLNS1pPTy_vNQNvtf6VvaQ"
PEXELS_KEY = "WnUJedsHItVDgsi7jDVzCkLwk9pcIUflxxkdwfcTWF2wOLtSdVY88ucB"

# ==========================================
# 2. 使用者輸入區域
# ==========================================
topic = st.text_input("請輸入短影音主題：", value="3個提升工作效率的心理學小技巧")

if st.button("🚀 一鍵生成影片", type="primary", use_container_width=True):
    status = st.status("🎬 影片製作中，請稍候...", expanded=True)
    
    try:
        # ------------------------------------------
        # 步驟 A: 呼叫 Gemini 生成腳本
        # ------------------------------------------
        status.write("🤖 1/4 正在使用 Gemini 生成短影音文案與關鍵字...")
        client = genai.Client(api_key=GEMINI_KEY)
        prompt = f"""請針對主題『{topic}』寫一段 15 秒短影音口播文案。
必須回傳純 JSON 格式，不要加任何 Markdown 標記或額外文字：
{{
  "script": "繁體中文口播文案（80字以內）",
  "keyword": "1個英文搜尋關鍵字（例如 focus）"
}}"""
        
        res = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 格式清洗與解析
        clean_text = res.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        script = data.get("script", "")
        keyword = data.get("keyword", "office")
        
        st.info(f"**生成文案：** {script}\n\n**背景關鍵字：** {keyword}")

        # ------------------------------------------
        # 步驟 B: 使用 Edge-TTS 生成真人配音
        # ------------------------------------------
        status.write("🎙️ 2/4 正在生成微軟真人配音...")
        with open("script.txt", "w", encoding="utf-8") as f:
            f.write(script)
        
        subprocess.run(
            ["edge-tts", "--file", "script.txt", "--voice", "zh-TW-HsiaoChenNeural", "--write-media", "audio.mp3"],
            check=True
        )

        # ------------------------------------------
        # 步驟 C: 從 Pexels 下載背景素材
        # ------------------------------------------
        status.write("🎥 3/4 正在從 Pexels 下載高畫質背景影片...")
        headers = {"Authorization": PEXELS_KEY}
        pexels_url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=1"
        res_pexels = requests.get(pexels_url, headers=headers).json()

        # 安全備援：找不到搜尋關鍵字時改用預設素材
        if not res_pexels.get("videos") or len(res_pexels["videos"]) == 0:
            pexels_url = "https://api.pexels.com/videos/search?query=nature&orientation=portrait&per_page=1"
            res_pexels = requests.get(pexels_url, headers=headers).json()

        video_file_url = res_pexels["videos"][0]["video_files"][0]["link"]
        video_bytes = requests.get(video_file_url).content
        with open("bg.mp4", "wb") as f:
            f.write(video_bytes)

        # ------------------------------------------
        # 步驟 D: 使用 FFmpeg 進行影音合成
        # ------------------------------------------
        status.write("⚙️ 4/4 正在進行影音渲染打包...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", "bg.mp4", "-i", "audio.mp3", "-c:v", "copy", "-c:a", "aac", "-shortest", "output_reel.mp4"],
            check=True
        )

        status.update(label="🎉 影片渲染完成！", state="complete")

        # ------------------------------------------
        # 預覽與下載
        # ------------------------------------------
        st.subheader("📹 影片預覽")
        st.video("output_reel.mp4")
        
        with open("output_reel.mp4", "rb") as video_file:
            st.download_button(
                label="⬇️ 下載 MP4 影片",
                data=video_file,
                file_name="output_reel.mp4",
                mime="video/mp4",
                use_container_width=True
            )

    except Exception as e:
        status.update(label="❌ 製作過程發生錯誤", state="error")
        st.error(f"錯誤細節：{e}")name.strip() or username,
            "email": email.strip(),
            "role": role,
            "status": "active",
            "membership": "永久",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_members(members)
    return True, "會員建立成功，已設定為永久權限。"

def login_user(username, password):
    member = find_member(username)
    if member is None or not verify_password(password, member.get("password_hash", "")):
        return False, "帳號或密碼錯誤。"

    if member.get("status") != "active":
        return False, "該會員帳號已被停用。"

    st.session_state.logged_in = True
    st.session_state.username = member.get("username", "")
    st.session_state.name = member.get("name", member.get("username", ""))
    st.session_state.role = member.get("role", "member")
    st.session_state.page = "home"
    return True, "登入成功。"

def logout_user():
    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = value

# ============================================================
# Gemini API 與圖片處理
# ============================================================

def get_gemini_api_key():
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("GEMINI_API_KEY", "")

def get_gemini_client():
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("系統未安裝 google-genai 模組，請檢查 requirements.txt。") from exc

    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError("未檢測到 GEMINI_API_KEY。請於 Streamlit Secrets 中設定。")

    return genai.Client(api_key=api_key)

def ask_gemini(prompt, image_bytes=None, mime_type="image/jpeg"):
    client = get_gemini_client()
    if image_bytes:
        from google.genai import types
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt,
        ]
    else:
        contents = prompt

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
    )
    text = getattr(response, "text", None)
    if not text:
        raise RuntimeError("Gemini API 未回傳有效內容。")
    return text.strip()

def prepare_image(uploaded_file):
    raw_data = uploaded_file.getvalue()
    try:
        image = Image.open(io.BytesIO(raw_data))
        image = ImageOps.exif_transpose(image)
        if image.mode not in ["RGB", "RGBA"]:
            image = image.convert("RGB")

        max_size = 1600
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        if image.mode == "RGBA":
            image.save(output, format="PNG", optimize=True)
            return output.getvalue(), "image/png"

        image.save(output, format="JPEG", quality=92, optimize=True)
        return output.getvalue(), "image/jpeg"
    except Exception as exc:
        raise RuntimeError(f"圖片處理失敗：{exc}") from exc

# ============================================================
# Prompt 商業邏輯
# ============================================================

JIMENG_25_RULES = """
【即夢 AI 2.5 商品原貌鎖定】
1. 使用上傳圖片中的主要商品作為唯一主要商品。
2. 保留商品品牌、包裝、外觀、顏色、材質與 Logo。
3. 畫面不可包含人物、多餘手部持物，商品必須為視覺焦點。
4. 生圖規格：9:16 直式商業構圖，包含高品質英文描述與 Negative Prompt。
"""

SHOPEE_PROMPT_TEMPLATE = """
【蝦皮高轉化文案要求】
1. SEO 標題 (60字內)
2. 5 大爆款賣點 (搭配 Emoji)
3. 完整商品描述與規格明細
4. 10~15 個熱搜 Hashtag
"""

TIKTOK_PROMPT_TEMPLATE = """
【TikTok 帶貨文案要求】
1. 3 秒黃金 Hook (3種不同切入點)
2. 15-30 秒口播腳本
3. 強力 CTA 引導下單
"""

def build_master_prompt(product):
    name = product.get("name", "")
    price = product.get("price", "")
    cost = product.get("cost", "")
    comm = product.get("commission", "")
    sales = product.get("sales", "")
    rating = product.get("rating", "")
    url = product.get("url", "")
    specs = product.get("specs", "")
    platform = product.get("platform", "")

    return f"""
你現在是「{APP_NAME}」的核心電商 AI。
請根據商品圖片與資料產出內容：

【商品資料】
- 名稱: {name}
- 售價: {price} | 成本: {cost} | 分潤: {comm}
- 銷量: {sales} | 評分: {rating} | 平台: {platform}
- 連結: {url}
- 規格: {specs}

【任務一：AI 選品分析】
【任務二：蝦皮高轉化上架文案】
{SHOPEE_PROMPT_TEMPLATE}

【任務三：TikTok 爆款帶貨文案】
{TIKTOK_PROMPT_TEMPLATE}

【任務四：即夢 AI 2.5 商業生圖與影片 Prompt】
{JIMENG_25_RULES}
"""

# ============================================================
# UI 介面渲染
# ============================================================

def render_login_page():
    st.title(f"🛒 {APP_NAME}")
    st.caption("全自動電商文案與多模態 AI 提示詞生成系統")

    tab1, tab2 = st.tabs(["🔐 會員登入", "📝 帳號註冊"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("會員帳號")
            password = st.text_input("密碼", type="password")
            if st.form_submit_button("登入系統", use_container_width=True):
                ok, msg = login_user(username, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.info(f"預設管理員帳號：{ADMIN_USERNAME} / 密碼：{DEFAULT_ADMIN_PASSWORD}")

    with tab2:
        with st.form("register_form"):
            username = st.text_input("新帳號")
            name = st.text_input("使用者暱稱")
            email = st.text_input("電子信箱")
            p1 = st.text_input("設定密碼", type="password")
            p2 = st.text_input("確認密碼", type="password")
            if st.form_submit_button("註冊永久會員", use_container_width=True):
                if p1 != p2:
                    st.error("兩次密碼輸入不一致。")
                else:
                    ok, msg = create_member(username, p1, name, email, "member")
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 🛒 {APP_NAME}")
        st.write(f"👤 **{st.session_state.name}** ({st.session_state.role.upper()})")
        st.caption("授權狀態：永久會員")

        if st.button("🏠 電商自動化主頁", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        if st.session_state.role == "admin":
            if st.button("👑 會員與系統管理", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        st.divider()

        if st.button("🚪 安全登出", use_container_width=True):
            logout_user()
            st.rerun()

def render_admin_page():
    st.title("👑 會員管理中心")
    members = load_members()

    c1, c2 = st.columns(2)
    c1.metric("會員總數", len(members))
    c2.metric("啟用中會員", sum(1 for m in members if m.get("status") == "active"))

    st.divider()
    st.subheader("➕ 手動新增會員")
    with st.form("admin_create_form"):
        u = st.text_input("帳號")
        n = st.text_input("暱稱")
        p = st.text_input("密碼", type="password")
        e = st.text_input("Email")
        r = st.selectbox("層級", ["member", "vip", "admin"])
        if st.form_submit_button("新增會員", use_container_width=True):
            ok, msg = create_member(u, p, n, e, r)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.subheader("👥 現有會員")
    for idx, m in enumerate(members):
        with st.expander(f"👤 {m.get('username')} ({m.get('name')})"):
            st.write(f"角色：{m.get('role')} | 狀態：{m.get('status')}")
            if m.get("username") != ADMIN_USERNAME:
                is_act = m.get("status") == "active"
                if st.button("停用" if is_act else "啟用", key=f"btn_{idx}"):
                    m["status"] = "disabled" if is_act else "active"
                    save_members(members)
                    st.rerun()

def render_home_page():
    st.title(f"🛒 {APP_NAME}")
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 商品資訊輸入")
        uploaded_file = st.file_uploader("上傳商品圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="預覽圖片", use_container_width=True)

        p_name = st.text_input("商品名稱")
        p_price = st.text_input("售價 (NTD)")
        p_cost = st.text_input("成本 (NTD)")
        p_comm = st.text_input("分潤比例 (%)")
        p_sales = st.text_input("月銷量")
        p_rating = st.text_input("評分")
        p_url = st.text_input("商品連結")
        p_specs = st.text_area("規格描述")
        p_platform = st.selectbox("目標平台", ["蝦皮購物 + TikTok", "僅蝦皮購物", "僅 TikTok"])

        gen_btn = st.button("🚀 開始生成文案報告", type="primary", use_container_width=True)

    with col2:
        st.subheader("2. AI 分析報告")
        if gen_btn:
            if not uploaded_file:
                st.warning("請先上傳商品圖片。")
            elif not p_name.strip():
                st.warning("請填寫商品名稱。")
            else:
                with st.spinner("AI 分析中..."):
                    try:
                        img_bytes, mime_type = prepare_image(uploaded_file)
                        p_data = {
                            "name": p_name,
                            "price": p_price,
                            "cost": p_cost,
                            "commission": p_comm,
                            "sales": p_sales,
                            "rating": p_rating,
                            "url": p_url,
                            "specs": p_specs,
                            "platform": p_platform,
                        }
                        prompt = build_master_prompt(p_data)
                        res = ask_gemini(prompt, img_bytes, mime_type)
                        st.session_state.result = res
                    except Exception as exc:
                        st.error(f"生成失敗：{exc}")

        if st.session_state.result:
            st.markdown(st.session_state.result)
            st.download_button(
                label="📥 下載報告 (.txt)",
                data=st.session_state.result,
                file_name=f"{p_name}_報告.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ============================================================
# 主程式
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
    main()'')}
商品價格: {product.get('price', '')}
商品成本: {product.get('cost', '')}
分潤比例: {product.get('commission', '')}
月銷量: {product.get('sales', '')}
商品評分: {product.get('rating', '')}
商品連結: {product.get('url', '')}
商品規格: {product.get('specs', '')}
目標平台: {product.get('platform', '')}

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
# 視圖渲染模組
# ============================================================

def render_login_page():
    st.markdown(
        f"""
        <div class="biz-header">🛒 {APP_NAME}</div>
        <div class="biz-sub">全自動電商文案與多模態 AI 提示詞生成系統</div>
        """,
        unsafe_allow_html=True,
    )
    login_tab, register_tab = st.tabs(["🔐 會員登入", "📝 帳號註冊"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("會員帳號")
            password = st.text_input("密碼", type="password")
            if st.form_submit_button("登入系統", use_container_width=True):
                ok, msg = login_user(username, password)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
        st.info(f"預設管理員帳號：{ADMIN_USERNAME} / 密碼：{DEFAULT_ADMIN_PASSWORD}")

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("新帳號")
            name = st.text_input("使用者暱稱")
            email = st.text_input("電子信箱")
            p1 = st.text_input("設定密碼", type="password")
            p2 = st.text_input("確認密碼", type="password")
            if st.form_submit_button("註冊永久會員", use_container_width=True):
                if p1 != p2:
                    st.error("兩次密碼輸入不一致。")
                else:
                    ok, msg = create_member(username, p1, name, email, "member")
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 🛒 {APP_NAME}")
        st.markdown(
            f"""
            <div class="sidebar-user-box">
                <b>👤 {st.session_state.name}</b><br>
                <small>帳號：{st.session_state.username}</small><br>
                <small>權限：{st.session_state.role.upper()}</small><br>
                <small>狀態：永久授權</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("🏠 電商自動化主頁", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        if st.session_state.role == "admin":
            if st.button("👑 會員與系統管理", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()

        st.divider()

        if st.button("🚪 安全登出", use_container_width=True):
            logout_user()
            st.rerun()

def render_admin_page():
    st.title("👑 會員管理中心")
    st.caption("檢視並管理系統內所有註冊會員之權限與狀態。")

    members = load_members()
    c1, c2, c3 = st.columns(3)
    c1.metric("會員總數", len(members))
    c2.metric("啟用中會員", sum(1 for m in members if m.get("status") == "active"))
    c3.metric("管理員人數", sum(1 for m in members if m.get("role") == "admin"))

    st.divider()
    st.subheader("➕ 手動新增會員")
    with st.form("admin_create_member_form"):
        col1, col2 = st.columns(2)
        with col1:
            u = st.text_input("帳號")
            n = st.text_input("暱稱")
        with col2:
            p = st.text_input("密碼", type="password")
            e = st.text_input("Email")
        r = st.selectbox("會員層級", ["member", "vip", "admin"], format_func=lambda x: {"member":"一般會員", "vip":"VIP會員", "admin":"管理員"}[x])
        
        if st.form_submit_button("新增會員", use_container_width=True):
            ok, msg = create_member(u, p, n, e, r)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    st.subheader("👥 現有會員清單")
    for idx, m in enumerate(members):
        with st.expander(f"👤 {m.get('username')} ({m.get('name')}) - {m.get('role').upper()}"):
            st.write(f"**Email:** {m.get('email', '未設定')}")
            st.write(f"**狀態:** {m.get('status')}")
            st.write(f"**建立時間:** {m.get('created_at')}")

            if m.get("username") != ADMIN_USERNAME:
                is_active = m.get("status") == "active"
                btn_label = "停用帳號" if is_active else "啟用帳號"
                if st.button(btn_label, key=f"toggle_user_{idx}"):
                    m["status"] = "disabled" if is_active else "active"
                    save_members(members)
                    st.success(f"已更新 {m.get('username')} 的權限狀態。")
                    st.rerun()

def render_home_page():
    st.title(f"🛒 {APP_NAME}")
    st.caption("上傳產品圖片並輸入關鍵參數，由 AI 一鍵生成蝦皮、TikTok 及即夢 2.5 提示詞模組。")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("1. 商品圖片與基本資訊")
        uploaded_file = st.file_uploader("上傳商品主圖 (JPG/PNG)", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.image(uploaded_file, caption="已載入商品圖片", use_container_width=True)

        p_name = st.text_input("商品名稱", placeholder="例：極致保濕修護精華液")
        p_price = st.text_input("售價 (NTD)", placeholder="例：499")
        p_cost = st.text_input("成本 (NTD)", placeholder="例：150")
        p_comm = st.text_input("分潤比例 (%)", placeholder="例：15")
        p_sales = st.text_input("預估月銷量", placeholder="例：1000")
        p_rating = st.text_input("商品評分", placeholder="例：4.9")
        p_url = st.text_input("商品連結", placeholder="例：https://shopee.tw/...")
        p_specs = st.text_area("詳細規格描述", placeholder="例：容量 30ml，適用敏感肌，台灣製造...")
        p_platform = st.selectbox("目標發布平台", ["蝦皮購物 + TikTok", "僅蝦皮購物", "僅 TikTok"])

        gen_btn = st.button("🚀 開始全自動生成報告", type="primary", use_container_width=True)

    with col_right:
        st.subheader("2. AI 分析與文案輸出")
        if gen_btn:
            if not uploaded_file:
                st.warning("請先上傳商品圖片。")
            elif not p_name.strip():
                st.warning("請填寫商品名稱。")
            else:
                with st.spinner("Gemini 多模態模型正在分析圖片與撰寫全套文案..."):
                    try:
                        img_bytes, mime_type = prepare_image(uploaded_file)
                        product_data = {
                            "name": p_name,
                            "price": p_price,
                            "cost": p_cost,
                            "commission": p_comm,
                            "sales": p_sales,
                            "rating": p_rating,
                            "url": p_url,
                            "specs": p_specs,
                            "platform": p_platform,
                        }
                        prompt = build_master_prompt(product_data)
                        res_text = ask_gemini(prompt, img_bytes, mime_type)
                        st.session_state.result = res_text
                    except Exception as exc:
                        st.error(f"執行過程中發生錯誤：{exc}")

        if st.session_state.result:
            st.markdown(st.session_state.result)
            st.download_button(
                label="📥 下載完整電商報告 (.txt)",
                data=st.session_state.result,
                file_name=f"{p_name}_AI電商報告.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ============================================================
# 應用程式進入點 (Main Entry)
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
    main()_comm = product.get("commission", "")
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
        if st.sess_comm = product.get("commission", "")
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
        if st.sess
