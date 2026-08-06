import io
import os
import json
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image, ImageOps


# =====================================================
# APP 基礎設定
# =====================================================

APP_NAME = "AI 蝦皮半自動化 2.5 PRO"
GEMINI_MODEL = "gemini-2.5-flash"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MEMBERS_FILE = DATA_DIR / "members.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# Session State 初始化
# =====================================================

DEFAULT_SESSION = {
    "login": False,
    "username": "",
    "name": "",
    "role": "",
    "page": "home",
    "result": ""
}

for key, value in DEFAULT_SESSION.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 密碼安全雜湊 (PBKDF2)
# =====================================================

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

    return f"{salt}${digest}"


def check_password(password, saved):
    try:
        salt, saved_digest = saved.split("$", 1)
        check_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        ).hex()
        return secrets.compare_digest(check_digest, saved_digest)
    except Exception:
        return False


# =====================================================
# 會員資料庫管理 (JSON 持久化)
# =====================================================

def load_members():
    if not MEMBERS_FILE.exists():
        return []
    try:
        data = json.loads(MEMBERS_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except Exception:
        return []
    return []


def save_members(data):
    temp_file = MEMBERS_FILE.with_suffix(".tmp")
    temp_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temp_file.replace(MEMBERS_FILE)


def find_member(username):
    username = username.strip()
    for m in load_members():
        if m.get("username") == username:
            return m
    return None


def ensure_admin():
    members = load_members()
    admin_exists = any(m.get("username") == "admin" for m in members)
    if not admin_exists:
        members.append({
            "username": "admin",
            "password": hash_password("admin123456"),
            "name": "系統管理員",
            "role": "admin",
            "status": "active",
            "created": datetime.now().isoformat()
        })
        save_members(members)


def register_user(username, password, name):
    username = username.strip()
    if not username:
        return False, "請輸入帳號。"
    if len(username) < 3:
        return False, "帳號長度至少需 3 個字元。"
    if len(password) < 6:
        return False, "密碼長度至少需 6 個字元。"
    if find_member(username):
        return False, "該帳號已存在。"

    members = load_members()
    members.append({
        "username": username,
        "password": hash_password(password),
        "name": name.strip() or username,
        "role": "member",
        "status": "active",
        "created": datetime.now().isoformat()
    })
    save_members(members)
    return True, "註冊成功！請登入使用。"


def login_user(username, password):
    user = find_member(username)
    if not user:
        return False
    if not check_password(password, user.get("password", "")):
        return False
    if user.get("status") != "active":
        return False

    st.session_state.login = True
    st.session_state.username = user.get("username", "")
    st.session_state.name = user.get("name", user.get("username", ""))
    st.session_state.role = user.get("role", "member")
    st.session_state.page = "home"
    return True


def logout_user():
    for key, value in DEFAULT_SESSION.items():
        st.session_state[key] = value


# =====================================================
# Gemini API 與 Client 設定
# =====================================================

def get_gemini_key():
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
        raise RuntimeError("缺少 google-genai 套件，請檢查 requirements.txt。") from exc

    key = get_gemini_key()
    if not key:
        raise RuntimeError("未設定 GEMINI_API_KEY，請於 Secrets 或環境變數中設定。")

    return genai.Client(api_key=key)


def ask_gemini(prompt, image_bytes=None, mime_type="image/jpeg"):
    client = get_gemini_client()

    if image_bytes:
        from google.genai import types
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt
        ]
    else:
        contents = prompt

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents
    )

    text = getattr(response, "text", None)
    if not text:
        return "AI 沒有回傳內容。"
    return text.strip()


def prepare_image(uploaded_file):
    raw_bytes = uploaded_file.getvalue()
    image = Image.open(io.BytesIO(raw_bytes))
    image = ImageOps.exif_transpose(image)

    if image.mode not in ["RGB", "RGBA"]:
        image = image.convert("RGB")

    max_size = 1600
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_w = int(image.width * ratio)
        new_h = int(image.height * ratio)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    if image.mode == "RGBA":
        image.save(output, format="PNG", optimize=True)
        return output.getvalue(), "image/png"

    image.save(output, format="JPEG", quality=92, optimize=True)
    return output.getvalue(), "image/jpeg"


# =====================================================
# Prompt 指令範本規則
# =====================================================

BASE_AI_RULES = """
你是 AI 蝦皮半自動化 2.5 PRO。

最高規則：
1. 商品圖片是唯一真實來源。
2. 保持商品原貌：品牌、Logo、包裝、瓶身、盒型、顏色、材質、比例、標籤、文字。
3. 禁止自行創造：不存在的品牌、不存在的規格、不存在的功能或價格。
4. 資料不清楚或無法確認時，必須輸出：待確認。
5. 禁止畫面出現：人物、手、模特、錯誤商品、多餘雜物或浮水印。
6. 所有產出內容須符合蝦皮電商、TikTok 短影音與即夢 AI 2.5 規範。
"""

JIMENG_25_RULES = """
【即夢 AI 2.5 控制規則】
1. 商品原貌鎖定：上傳圖片中的商品為唯一主體，不得任意修改外觀、品牌或顏色。
2. 一致性控制：影片與圖片全程維持同一商品，不可變形、融化、扭曲、漂浮或重複。
3. 人物限制：禁止人物、手部、模特或主播，商品需獨立展示。
4. 商業攝影風格：High-end commercial product photography, 8K quality, studio lighting, clean background.
5. 即夢生圖規格：
   - 提供詳細 English Prompt (包含構圖、光影、材質與風格)。
   - 固定 Negative Prompt (no people, no hands, no watermark, no extra products, no wrong logo, no deformation, no fake text)。
   - 繁體中文畫面文字設計。
6. 即夢影片規格：
   - 比例：9:16 直式。
   - Opening (0-3s)：商品正面清晰置中。
   - Middle (3-20s)：慢速推近 (smooth camera push in)，展現材質與細節。
   - Ending：商品置中定格 (Freeze frame)。
"""

SHOPEE_RULES = """
【蝦皮高轉化內容規則】
1. SEO 標題：品牌 + 商品名稱 + 核心特色 + 規格 + 熱門關鍵字。
2. 五大賣點：使用 Emoji 標示，簡短有力，切中買家痛點。
3. 完整商品描述：包含特色優勢、使用方式、適用對象與溫馨提示。
4. 規格明細：條列容量、尺寸、產地等詳細資訊。
5. 10~15 個熱門 Hashtag。
"""

TIKTOK_RULES = """
【TikTok / 短影音帶貨規則】
1. 3 秒黃金 Hook：提供痛點型、好奇型、優惠型開頭。
2. 15-30 秒口播帶貨腳本：節奏明快，具吸引力。
3. 短文案 Caption 與強效 CTA (引導點擊購物車)。
4. 爆款 Hashtag。
"""


def create_master_prompt(product):
    name = product.get("name", "")
    price = product.get("price", "")
    cost = product.get("cost", "")
    commission = product.get("commission", "")
    specs = product.get("specs", "")

    return f"""
{BASE_AI_RULES}

{JIMENG_25_RULES}

{SHOPEE_RULES}

{TIKTOK_RULES}

==============================
【輸入商品資料】
==============================
商品名稱：{name}
價格：{price}
成本：{cost}
分潤：{commission}
規格：{specs}

==============================
【請完整輸出以下項目】
==============================
【一、商品辨識與資訊標記】
【二、AI 選品與市場分析】
【三、蝦皮 SEO 標題與高轉化文案】
【四、五大商品爆款賣點】
【五、完整蝦皮商品描述與規格】
【六、TikTok 爆款帶貨腳本與 3 秒 Hook】
【七、即夢 AI 2.5 商業生圖 Prompt (英文 + Negative Prompt + 中文海報字體)】
【八、即夢 AI 2.5 商業影片 Prompt (9:16 直式鏡頭與光影軌跡)】
【九、25 秒短影音爆款分鏡腳本】
【十、分潤與合規檢查 (不確定者標示待確認)】
"""


# =====================================================
# UI 頁面：登入 / 註冊
# =====================================================

def show_login_page():
    st.title(f"🛒 {APP_NAME}")
    st.caption("Gemini 2.5 + 即夢 AI 2.5 電商半自動化系統")

    tab1, tab2 = st.tabs(["🔐 登入", "📝 註冊會員"])

    with tab1:
        username = st.text_input("帳號", key="login_user")
        password = st.text_input("密碼", type="password", key="login_pwd")

        if st.button("登入", use_container_width=True, type="primary"):
            if login_user(username, password):
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("帳號或密碼錯誤，或帳號已被停用。")

        st.info("預設管理員帳號：admin\n\n預設密碼：admin123456")

    with tab2:
        new_username = st.text_input("新帳號", key="reg_user")
        new_name = st.text_input("姓名 / 暱稱", key="reg_name")
        new_password = st.text_input("新密碼", type="password", key="reg_pwd")

        if st.button("註冊會員", use_container_width=True):
            ok, msg = register_user(new_username, new_password, new_name)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


# =====================================================
# UI 頁面：Sidebar
# =====================================================

def show_sidebar():
    with st.sidebar:
        st.title("👤 會員中心")
        st.write(f"**使用者：** {st.session_state.name}")
        st.write(f"**帳號：** {st.session_state.username}")
        st.write(f"**權限：** {st.session_state.role.upper()}")

        st.divider()

        if st.button("🏠 AI 分析主頁", use_container_width=True):
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


# =====================================================
# UI 頁面：AI 商品分析主頁
# =====================================================

def show_home_page():
    st.title(f"🛒 {APP_NAME}")
    st.caption("自動生成蝦皮高轉化文案、TikTok 腳本及即夢 AI 2.5 提示詞")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1. 上傳商品圖片")
        image_file = st.file_uploader("選擇商品圖片 (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if image_file:
            st.image(image_file, caption="預覽圖片", use_container_width=True)

        st.subheader("2. 填寫商品資料")
        name = st.text_input("商品名稱", placeholder="例：極致保濕精華液")
        price = st.text_input("商品售價", placeholder="例：499")
        cost = st.text_input("商品成本", placeholder="例：150")
        commission = st.text_input("分潤比例", placeholder="例：15%")
        specs = st.text_area("商品規格與細節描述", placeholder="例：容量 30ml，保存期限 3 年...")

        run_btn = st.button("🚀 開始 AI 分析與生成", type="primary", use_container_width=True)

    with col2:
        st.subheader("3. AI 生成結果")

        if run_btn:
            if not image_file:
                st.warning("請先上傳商品圖片。")
            elif not name.strip():
                st.warning("請輸入商品名稱。")
            else:
                try:
                    with st.spinner("AI 正在分析圖片並生成全套文案與提示词..."):
                        img_bytes, mime_type = prepare_image(image_file)
                        product_data = {
                            "name": name,
                            "price": price,
                            "cost": cost,
                            "commission": commission,
                            "specs": specs
                        }
                        prompt = create_master_prompt(product_data)
                        result = ask_gemini(prompt, img_bytes, mime_type)
                        st.session_state.result = result
                except Exception as e:
                    st.error(f"分析失敗：{e}")

        if st.session_state.result:
            st.markdown(st.session_state.result)
            st.download_button(
                label="📥 下載 AI 電商分析報告 (.txt)",
                data=st.session_state.result,
                file_name=f"{name or '商品'}_AI電商報告.txt",
                mime="text/plain",
                use_container_width=True
            )


# =====================================================
# UI 頁面：管理員中心
# =====================================================

def show_admin_page():
    st.title("👑 管理員中心")
    members = load_members()

    st.metric("目前註冊會員總數", len(members))

    st.subheader("會員列表")
    for idx, m in enumerate(members):
        with st.expander(f"👤 {m.get('username')} ({m.get('name')}) - 權限: {m.get('role')}"):
            st.write(f"**狀態：** {m.get('status')}")
            st.write(f"**建立時間：** {m.get('created')}")

            if m.get("username") != "admin":
                status = m.get("status", "active")
                btn_label = "停用帳號" if status == "active" else "啟用帳號"
                if st.button(btn_label, key=f"toggle_{idx}"):
                    m["status"] = "disabled" if status == "active" else "active"
                    save_members(members)
                    st.success("會員狀態已更新")
                    st.rerun()


# =====================================================
# 主程式進入點
# =====================================================

def main():
    ensure_admin()

    if not st.session_state.login:
        show_login_page()
    else:
        show_sidebar()
        if st.session_state.page == "admin" and st.session_state.role == "admin":
            show_admin_page()
        else:
            show_home_page()


if __name__ == "__main__":
    main()
