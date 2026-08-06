import io
import os
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps


# ============================================================
# 基本設定
# ============================================================

APP_NAME = "AI 蝦皮半自動化 2.5 PRO"
GEMINI_MODEL = "gemini-2.5-flash"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMBERS_FILE = DATA_DIR / "members.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 預設管理員
ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123456"


# ============================================================
# Streamlit 頁面設定
# ============================================================

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS 樣式
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .sub-title {
        color: #777;
        margin-bottom: 20px;
    }

    .member-card {
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,.25);
        margin-bottom: 15px;
    }

    .small-note {
        color: #777;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session State 初始化
# ============================================================

DEFAULT_SESSION = {
    "logged_in": False,
    "username": "",
    "name": "",
    "role": "",
    "page": "home",
    "result": "",
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# 密碼處理 (PBKDF2 安全雜湊)
# ============================================================

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200000,
    ).hex()

    return f"{salt}${digest}"


def verify_password(password, stored_password):
    try:
        salt, saved_digest = stored_password.split("$", 1)

        check_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            200000,
        ).hex()

        return secrets.compare_digest(
            check_digest,
            saved_digest,
        )

    except Exception:
        return False


# ============================================================
# 會員資料管理 (JSON 持久化)
# ============================================================

def load_members():
    if not MEMBERS_FILE.exists():
        return []

    try:
        data = json.loads(
            MEMBERS_FILE.read_text(encoding="utf-8")
        )
        if isinstance(data, list):
            return data
    except Exception:
        return []

    return []


def save_members(members):
    temp_file = MEMBERS_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(members, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp_file.replace(MEMBERS_FILE)


def find_member(username):
    username = username.strip()
    for member in load_members():
        if member.get("username") == username:
            return member
    return None


def ensure_admin():
    members = load_members()
    admin = None
    for member in members:
        if member.get("username") == ADMIN_USERNAME:
            admin = member
            break

    if admin is None:
        members.append(
            {
                "username": ADMIN_USERNAME,
                "password_hash": hash_password(DEFAULT_ADMIN_PASSWORD),
                "name": "系統管理員",
                "email": "",
                "role": "admin",
                "status": "active",
                "membership": "永久",
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        save_members(members)


def create_member(username, password, name, email, role="member"):
    username = username.strip()

    if not username:
        return False, "請輸入會員帳號。"
    if len(username) < 3:
        return False, "帳號至少需要 3 個字元。"
    if len(username) > 32:
        return False, "帳號最多 32 個字元。"

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"
    for char in username:
        if char not in allowed:
            return False, "帳號只能使用英文、數字、底線、點或連字號。"

    if len(password) < 6:
        return False, "密碼至少需要 6 個字元。"

    if find_member(username) is not None:
        return False, "這個帳號已存在。"

    if role not in ["member", "vip", "admin"]:
        role = "member"

    members = load_members()
    members.append(
        {
            "username": username,
            "password_hash": hash_password(password),
            "name": name.strip() or username,
            "email": email.strip(),
            "role": role,
            "status": "active",
            "membership": "永久",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_members(members)
    return True, "會員建立成功，期限為永久。"


def login_user(username, password):
    member = find_member(username)
    if member is None:
        return False, "帳號或密碼錯誤。"

    if not verify_password(password, member.get("password_hash", "")):
        return False, "帳號或密碼錯誤。"

    if member.get("status") != "active":
        return False, "這個會員帳號目前已被停用。"

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
# Gemini API Key & Client 設置
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
        raise RuntimeError(
            "找不到 google-genai。請確認 requirements.txt 已經安裝。"
        ) from exc

    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "找不到 GEMINI_API_KEY。請到 Streamlit Cloud → App Settings → Secrets 設定。"
        )

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
        raise RuntimeError("Gemini 沒有回傳內容。")

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
            new_width = max(1, int(image.width * ratio))
            new_height = max(1, int(image.height * ratio))
            image = image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS,
            )

        output = io.BytesIO()
        if image.mode == "RGBA":
            image.save(output, format="PNG", optimize=True)
            return output.getvalue(), "image/png"

        image.save(output, format="JPEG", quality=92, optimize=True)
        return output.getvalue(), "image/jpeg"

    except Exception as exc:
        raise RuntimeError(f"圖片處理失敗：{exc}") from exc


# ============================================================
# 即夢 AI 2.5 核心規則 & 蝦皮/TikTok 指令範本
# ============================================================

JIMENG_25_RULES = """
【即夢 AI 2.5 商品原貌鎖定】
1. 使用上傳圖片中的主要商品作為唯一主要商品。
2. 保留商品品牌、包裝、瓶身、盒子與外觀、形狀比例、顏色、材質、Logo、標籤與文字。
3. 不得自行修改品牌、包裝、顏色、形狀，不得捏造不存在的商品資料。
4. 不確定資訊必須標示「待確認」。

【一致性與畫面規範】
5. 整個畫面只能有一個主要商品，不得商品變形、融化、扭曲、漂浮、閃爍或消失。
6. 不要人物、手、手臂、模特兒，不使用人體拿商品。
7. 不要浮水印、錯誤價格、假贈品、額外商品。商品必須是視覺焦點，適合蝦皮與 TikTok 電商展示。

【即夢 AI 2.5 生圖規格】
- 比例：9:16 直式商業構圖。
- 主體 Prompt 語言：高品質英文描述 (High-end product photography, Studio lighting, 8k resolution)。
- 畫面中文文字：繁體中文（如促銷標題、賣點文字）。
- 必需包含 Negative Prompt，明確剔除人物、變形、多餘雜物與浮水印。

【即夢 AI 2.5 影片規格】
- Opening：完整商品正面置中，清晰展示品牌與外觀。
- Middle：smooth slow push-in / dolly-in，細緻呈現材質與細節。
- Motion & Lighting：平滑穩定的鏡頭運動、商業攝影棚光影、高對比焦點。
- Ending：商品置中且 Ending freeze frame (定格結尾)。
"""

SHOPEE_PROMPT_TEMPLATE = """
【蝦皮高轉化上架文案要求】
1. SEO 搜尋最佳化標題：包含「品牌/品名 + 核心功效 + 規格/適用對象 + 熱門關鍵字」，不超過 60 字。
2. 5 大爆款賣點：簡短有力，解決買家痛點，善用 Emoji 標示。
3. 完整商品描述：包含產品優勢、使用方法、適用對象、安心保障。
4. 規格明細欄位：條列容量、產地、保存期限、材質等。
5. 購買提醒與溫馨提示：包含出貨時間、售後服務政策。
6. 熱門 Hashtag：10~15 個蝦皮熱搜標籤。
"""

TIKTOK_PROMPT_TEMPLATE = """
【TikTok / 短影音帶貨文案要求】
1. 3 秒黃金 Hook (吸睛開頭)：提供 3 種不同切入點 (痛點型、好奇型、促銷型)。
2. 15-30 秒口播腳本：語速明快、口語化、具說服力與親和力。
3. 貼文文案 (Caption)：精簡爆款文案，引導點擊購物車。
4. 強力 CTA (行動呼籲)：促使立即下單的指令。
5. 熱門 Hashtag：精選 TikTok / Reels 爆款標籤。
"""


def build_master_prompt(product):
    p_name = product.get("name", "")
    p_price = product.get("price", "")
    p_cost = product.get("cost", "")
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
