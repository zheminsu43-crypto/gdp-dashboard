import os
import io
import re
import json
import uuid
import shutil
import hashlib
import secrets
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime, date, timedelta

import streamlit as st
from PIL import Image, ImageOps

# =========================================================
# AI 蝦皮全自動化 2.5 PRO
# =========================================================
APP_NAME = "AI 蝦皮全自動化 2.5 PRO"

DATA_DIR = Path("data")
HISTORY_DIR = Path("history")
MEDIA_DIR = DATA_DIR / "media"
MEMBERS_FILE = DATA_DIR / "members.json"

DATA_DIR.mkdir(exist_ok=True)
HISTORY_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

MAX_IMAGE_SIZE = 1600
MAX_IMAGE_MB = 20
MAX_VIDEO_MB = 300

ADMIN_USERNAME = "admin"
DEFAULT_MEMBER_DAYS = 30

GEMINI_MODEL = "gemini-2.5-flash"

VIDEO_MIME_MAP = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".webm": "video/webm",
}

# =========================================================
# Streamlit 設定
# =========================================================
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CSS
# =========================================================
st.markdown(
    """
<style>
.main-title {
    font-size: 36px;
    font-weight: 800;
}
.sub-title {
    color: #777;
    margin-bottom: 20px;
}
.card {
    padding: 20px;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 15px;
}
.small {
    color: #777;
    font-size: 14px;
}
.success-box {
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #35a66f;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# Session State
# =========================================================
DEFAULT_STATE = {
    "logged_in": False,
    "username": "",
    "member": {},
    "page": "Dashboard",
    "analysis_result": {},
    "last_product": {},
    "last_image_bytes": None,
    "last_image_name": "",
    "last_video_bytes": None,
    "last_video_name": "",
    "last_video_mime": "video/mp4",
    "last_zip_bytes": None,
    "last_zip_name": "",
    "last_history_id": "",
    "gemini_model": GEMINI_MODEL,
    "gemini_error": "",
    "generated": False,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# Secrets / API
# =========================================================
def get_secret(name):
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass

    return os.environ.get(name, "")


GEMINI_KEY = get_secret("GEMINI_KEY") or get_secret("GEMINI_API_KEY")
PEXELS_KEY = get_secret("PEXELS_KEY")


# =========================================================
# 基礎工具
# =========================================================
def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    return date.today()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def safe_filename(name):
    name = str(name or "file")
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    return name[:100]


def load_json(path, default):
    try:
        if not path.exists():
            return default
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    temp.replace(path)


def load_members():
    members = load_json(MEMBERS_FILE, {})

    if not isinstance(members, dict):
        members = {}

    return members


def save_members(members):
    save_json(MEMBERS_FILE, members)


# =========================================================
# 初始化 Admin
# =========================================================
def ensure_admin():
    members = load_members()

    if ADMIN_USERNAME not in members:
        members[ADMIN_USERNAME] = {
            "username": ADMIN_USERNAME,
            "password_hash": hash_password("admin123"),
            "created_at": now_text(),
            "expire_date": None,
            "permanent": True,
            "role": "admin",
            "status": "active",
        }

        save_members(members)


ensure_admin()


# =========================================================
# 會員
# =========================================================
def member_expiration(member):
    if member.get("permanent"):
        return "永久會員", True

    expire = member.get("expire_date")

    if not expire:
        return "未設定", False

    try:
        expire_date = date.fromisoformat(expire)
    except Exception:
        return "日期錯誤", False

    days = (expire_date - today()).days

    if days < 0:
        return f"已到期 ({abs(days)} 天)", False

    if days <= 7:
        return f"即將到期（剩 {days} 天）", True

    return f"正常（剩 {days} 天）", True


def create_member(username, password, days=30, permanent=False, role="member"):
    username = username.strip()

    if not username or not password:
        return False, "帳號與密碼不能為空。"

    members = load_members()

    if username in members:
        return False, "帳號已存在。"

    expire_date = None

    if not permanent:
        expire_date = (today() + timedelta(days=int(days))).isoformat()

    members[username] = {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": now_text(),
        "expire_date": expire_date,
        "permanent": permanent,
        "role": role,
        "status": "active",
    }

    save_members(members)

    return True, "會員建立成功。"


def authenticate(username, password):
    members = load_members()

    member = members.get(username)

    if not member:
        return None, "帳號不存在。"

    if member.get("status") != "active":
        return None, "此帳號目前已停用。"

    if member.get("password_hash") != hash_password(password):
        return None, "密碼錯誤。"

    status, valid = member_expiration(member)

    if not valid:
        return None, f"會員已無法使用：{status}"

    return member, ""


# =========================================================
# Gemini
# =========================================================
def get_gemini_client():
    if not GEMINI_KEY:
        return None

    try:
        from google import genai

        return genai.Client(api_key=GEMINI_KEY)
    except Exception as e:
        st.session_state.gemini_error = str(e)
        return None


def clean_json_text(text):
    if not text:
        return ""

    text = text.strip()

    text = re.sub(r"^```json", "", text, flags=re.I)
    text = re.sub(r"^```", "", text)
    text = re.sub(r"```$", "", text)

    return text.strip()


def gemini_text(prompt, image_bytes=None, mime_type="image/jpeg"):
    client = get_gemini_client()

    if not client:
        raise RuntimeError(
            "找不到 Gemini API Key。請在 Streamlit Secrets 設定 GEMINI_KEY。"
        )

    try:
        contents = []

        if image_bytes:
            from google.genai import types

            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            )

        contents.append(prompt)

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )

        text = getattr(response, "text", None)

        if not text:
            raise RuntimeError("Gemini 沒有返回內容。")

        st.session_state.gemini_model = GEMINI_MODEL

        return text

    except Exception as e:
        error = str(e)

        if "404" in error:
            error = "Gemini 模型不存在或目前 API 不支援此模型（404）。"
        elif "401" in error:
            error = "Gemini API Key 無效（401）。"
        elif "403" in error:
            error = "Gemini API 權限不足（403）。"
        elif "429" in error:
            error = "Gemini API 額度或頻率限制（429）。"
        elif "400" in error:
            error = "Gemini 請求格式錯誤（400）。"

        st.session_state.gemini_error = error
        raise RuntimeError(error)


def gemini_json(prompt, image_bytes=None, mime_type="image/jpeg"):
    text = gemini_text(
        prompt,
        image_bytes=image_bytes,
        mime_type=mime_type,
    )

    cleaned = clean_json_text(text)

    try:
        return json.loads(cleaned)
    except Exception:
        # 嘗試找 JSON 區塊
        match = re.search(r"\{.*\}", cleaned, re.S)

        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        raise RuntimeError("Gemini 回傳內容不是有效 JSON。")


# =========================================================
# 圖片處理
# =========================================================
def process_image(uploaded_file):
    if not uploaded_file:
        return None, None

    raw = uploaded_file.getvalue()

    if len(raw) > MAX_IMAGE_MB * 1024 * 1024:
        raise ValueError(f"圖片超過 {MAX_IMAGE_MB}MB。")

    image = Image.open(io.BytesIO(raw))

    image = ImageOps.exif_transpose(image)

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    image.thumbnail(
        (MAX_IMAGE_SIZE, MAX_IMAGE_SIZE),
        Image.Resampling.LANCZOS,
    )

    output = io.BytesIO()

    if image.mode == "RGBA":
        image.save(output, format="PNG")
        mime = "image/png"
    else:
        image.save(
            output,
            format="JPEG",
            quality=92,
        )
        mime = "image/jpeg"

    return output.getvalue(), mime


# =========================================================
# 商品分類
# =========================================================
def detect_category(text):
    text = (text or "").lower()

    categories = {
        "保養美妝": [
            "洗面",
            "面膜",
            "乳液",
            "精華",
            "保養",
            "化妝",
            "美容",
            "防曬",
        ],
        "3C": [
            "手機",
            "耳機",
            "充電",
            "電腦",
            "鍵盤",
            "滑鼠",
            "3c",
            "平板",
        ],
        "居家生活": [
            "收納",
            "清潔",
            "家居",
            "廚房",
            "杯",
            "居家",
        ],
        "服飾": [
            "衣服",
            "褲",
            "鞋",
            "帽",
            "包",
            "服飾",
        ],
        "食品": [
            "食品",
            "零食",
            "餅乾",
            "飲料",
            "茶",
            "咖啡",
        ],
        "汽機車": [
            "汽車",
            "機車",
            "車用",
            "汽機車",
        ],
    }

    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "其他"


# =========================================================
# Gemini 完整商品分析
# =========================================================
def run_product_ai(product):
    prompt = f"""
你現在是「AI 蝦皮全自動化 2.5 PRO」電商 AI。

請分析以下商品，並產生完整電商行銷資料。

商品資料：
商品名稱：{product['name']}
分類：{product['category']}
價格：{product['price']}
商品特色：{product['features']}
商品賣點：{product['selling_points']}

重要規則：

1. 如果有商品圖片，圖片是商品外觀的主要依據。
2. 不得虛構圖片中不存在的品牌、Logo、文字、功能、配件。
3. 不得自行修改商品外觀。
4. 不得虛構價格、折扣、贈品。
5. 如果資訊不足，明確標示「未確認」。
6. 所有內容使用繁體中文。
7. 蝦皮標題要自然，不要塞滿無意義關鍵字。
8. TikTok 必須前 3 秒有 Hook。
9. 即夢 Prompt 必須保護商品一致性。
10. 影片預設 9:16。

請只回傳 JSON：

{{
  "product_analysis": {{
    "basic": "",
    "appearance": "",
    "material": "",
    "color": "",
    "packaging": "",
    "logo_text": "",
    "features": []
  }},
  "selling_points": [],
  "target_audience": [],
  "consumer_needs": [],
  "market_positioning": "",
  "purchase_reasons": [],
  "advantages": [],
  "disadvantages": [],
  "risks": [],
  "selection_score": 0,
  "market_attractiveness": 0,
  "visual_attractiveness": 0,
  "short_video_score": 0,
  "tiktok_score": 0,
  "shopee_score": 0,
  "selling_direction": "",
  "shopee": {{
    "title": "",
    "description": "",
    "selling_points": [],
    "keywords": [],
    "long_tail_keywords": []
  }},
  "tiktok": {{
    "title": "",
    "hook": "",
    "copy": "",
    "hashtags": [],
    "script_15": "",
    "script_30": ""
  }},
  "jimeng": {{
    "image_prompt": "",
    "cover_prompt": "",
    "video_prompt_15": "",
    "video_prompt_30": ""
  }}
}}
"""

    return gemini_json(
        prompt,
        image_bytes=product.get("image_bytes"),
        mime_type=product.get("image_mime", "image/jpeg"),
    )


# =========================================================
# 本機 fallback
# =========================================================
def local_fallback(product):
    category = product["category"]

    name = product["name"]

    return {
        "product_analysis": {
            "basic": f"{name}，分類：{category}",
            "appearance": "請以商品原圖為準",
            "material": "未確認",
            "color": "請以商品原圖為準",
            "packaging": "請以商品原圖為準",
            "logo_text": "請以商品原圖為準",
            "features": [product["features"]],
        },
        "selling_points": [product["selling_points"]],
        "target_audience": ["對此類商品有需求的消費者"],
        "consumer_needs": ["便利性", "實用性", "商品特色"],
        "market_positioning": "實用型電商商品",
        "purchase_reasons": ["商品特色", "使用便利"],
        "advantages": ["適合短影音展示"],
        "disadvantages": ["缺少實際市場數據"],
        "risks": ["AI 分析不能取代實際市場測試"],
        "selection_score": 75,
        "market_attractiveness": 75,
        "visual_attractiveness": 75,
        "short_video_score": 80,
        "tiktok_score": 78,
        "shopee_score": 80,
        "selling_direction": "以商品特色、實際使用情境與視覺展示為主要行銷方向。",
        "shopee": {
            "title": f"{name}｜高質感實用好物",
            "description": f"✨ {name}\n\n{product['features']}\n\n推薦給需要此類商品的消費者。",
            "selling_points": [
                product["selling_points"],
                product["features"],
            ],
            "keywords": [name, category],
            "long_tail_keywords": [
                f"{name}推薦",
                f"{category}好物",
            ],
        },
        "tiktok": {
            "title": f"{name}實用好物推薦",
            "hook": f"如果你正在找 {name}，這個一定要看！",
            "copy": f"今天分享一個實用好物：{name}。",
            "hashtags": [
                "#TikTok",
                "#好物推薦",
                "#生活好物",
                "#蝦皮",
            ],
            "script_15": (
                f"前3秒：你還在找好用的{category}嗎？\n"
                f"接著展示{name}。\n"
                f"快速介紹商品特色。\n"
                f"最後：想了解更多可以到賣場看看。"
            ),
            "script_30": (
                f"開場：你還在找實用的{category}嗎？\n"
                f"展示：這款{name}。\n"
                f"特色：{product['features']}。\n"
                f"賣點：{product['selling_points']}。\n"
                f"結尾：如果剛好有需求，可以進一步了解。"
            ),
        },
        "jimeng": {
            "image_prompt": (
                f"使用上傳商品圖片作為唯一商品外觀依據，"
                f"保持{name}原始品牌、Logo、包裝、顏色、"
                f"材質、比例、形狀與文字完全一致。"
                f"高級商業商品攝影，乾淨背景，自然光，"
                f"9:16 電商視覺。禁止修改商品。"
            ),
            "cover_prompt": (
                f"以原商品圖片為唯一商品依據，製作高級電商封面，"
                f"商品外觀完全保持原樣，不修改Logo、文字、顏色、"
                f"包裝與比例，9:16。"
            ),
            "video_prompt_15": (
                f"9:16 直式15秒商品廣告。"
                f"使用原商品圖片作為唯一商品依據。"
                f"商品外觀完全保持一致。"
                f"高級商業攝影、自然光、慢速推鏡、"
                f"商品特寫、輕微環繞。禁止改品牌、Logo、"
                f"包裝、顏色、比例、文字或增加不存在的物件。"
            ),
            "video_prompt_30": (
                f"9:16 直式30秒商品廣告。"
                f"以原商品圖片為唯一依據。"
                f"開場商品特寫，中段展示商品細節與使用情境，"
                f"結尾高級產品英雄鏡頭。"
                f"保持商品外觀、品牌、Logo、包裝、文字、"
                f"顏色、材質與比例完全一致。"
                f"禁止虛構商品資訊。"
            ),
        },
    }


# =========================================================
# Edge TTS
# =========================================================
def edge_tts_available():
    return shutil.which("edge-tts") is not None


def create_tts(text, output_path):
    if not edge_tts_available():
        raise RuntimeError(
            "找不到 edge-tts。請確認 requirements.txt 已安裝 edge-tts。"
        )

    subprocess.run(
        [
            "edge-tts",
            "--text",
            text,
            "--voice",
            "zh-TW-HsiaoChenNeural",
            "--write-media",
            str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


# =========================================================
# Pexels
# =========================================================
def download_pexels_video(keyword, output_path):
    if not PEXELS_KEY:
        raise RuntimeError("未設定 PEXELS_KEY。")

    import requests

    headers = {
        "Authorization": PEXELS_KEY,
    }

    url = "https://api.pexels.com/videos/search"

    params = {
        "query": keyword,
        "orientation": "portrait",
        "per_page": 5,
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    videos = data.get("videos", [])

    if not videos:
        params["query"] = "product commercial"

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        videos = response.json().get("videos", [])

    if not videos:
        raise RuntimeError("Pexels 找不到適合的影片素材。")

    video_files = videos[0].get("video_files", [])

    if not video_files:
        raise RuntimeError("Pexels 影片沒有可下載檔案。")

    # 優先挑直式/高畫質
    video_files = sorted(
        video_files,
        key=lambda x: (
            x.get("width", 0) * x.get("height", 0)
        ),
        reverse=True,
    )

    video_url = video_files[0]["link"]

    video_response = requests.get(
        video_url,
        timeout=120,
    )

    video_response.raise_for_status()

    output_path.write_bytes(video_response.content)

    return output_path


# =========================================================
# FFmpeg
# =========================================================
def ffmpeg_available():
    return shutil.which("ffmpeg") is not None


def create_video(background, audio, output):
    if not ffmpeg_available():
        raise RuntimeError(
            "找不到 FFmpeg。Streamlit Cloud 需要另外設定 FFmpeg。"
        )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(background),
        "-i",
        str(audio),
        "-vf",
        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    return output


# =========================================================
# 歷史紀錄
# =========================================================
def save_history(product, result):
    history_id = (
        datetime.now().strftime("%Y%m%d_%H%M%S")
        + "_"
        + secrets.token_hex(3)
    )

    folder = HISTORY_DIR / history_id
    folder.mkdir(parents=True, exist_ok=True)

    product_copy = dict(product)

    # bytes 不寫進 JSON
    product_copy.pop("image_bytes", None)

    save_json(
        folder / "product.json",
        product_copy,
    )

    save_json(
        folder / "ai_result.json",
        r        client = genai.Client(api_key=GEMINI_KEY)
        
        prompt = f"請針對主題『{topic}』寫一段適合15秒短影音的口播文案。文案需簡潔有力、吸引人。"
        
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoScriptSchema
            )
        )
        
        data = json.loads(res.text)
        script = data.get("script", "預設文案")
        keyword = data.get("keyword", "focus")
        
        st.info(f"**生成文案**：\n{script}\n\n**搜尋關鍵字**：`{keyword}`")

        # B. 微軟 TTS 語音合成
        status.write("🎙️ 2/4 正在生成語音...")
        with open("script.txt", "w", encoding="utf-8") as f:
            f.write(script)
        
        subprocess.run(
            ["edge-tts", "--file", "script.txt", "--voice", "zh-TW-HsiaoChenNeural", "--write-media", "audio.mp3"],
            check=True
        )

        # C. Pexels 背景素材下載
        status.write("🎥 3/4 正在下載背景影片...")
        headers = {"Authorization": PEXELS_KEY}
        pexels_url = f"https://api.pexels.com/videos/search?query={keyword}&orientation=portrait&per_page=3"
        res_pexels = requests.get(pexels_url, headers=headers).json()

        videos = res_pexels.get("videos", [])
        if not videos:
            fallback_url = "https://api.pexels.com/videos/search?query=abstract+motion&orientation=portrait&per_page=1"
            res_pexels = requests.get(fallback_url, headers=headers).json()
            videos = res_pexels.get("videos", [])

        if not videos:
            raise Exception("無法從 Pexels 取得影片素材，請稍後再試。")

        video_files = videos[0].get("video_files", [])
        selected_video = next(
            (v for v in video_files if v.get("height") == 1920 or v.get("quality") == "hd"),
            video_files[0]
        )
        
        video_file_url = selected_video["link"]
        video_bytes = requests.get(video_file_url).content
        with open("bg.mp4", "wb") as f:
            f.write(video_bytes)

        # D. FFmpeg 影音渲染合成
        status.write("⚙️ 4/4 正在合成影片...")
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", "bg.mp4",
            "-i", "audio.mp3",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-shortest",
            "output_reel.mp4"
        ], check=True)

        status.update(label="🎉 影片完成！", state="complete")

        # 4. 影片預覽與下載
        st.subheader("📹 影片預覽")
        st.video("output_reel.mp4")
        
        with open("output_reel.mp4", "rb") as video_file:
            st.download_button(
                label="⬇️ 下載影片",
                data=video_file,
                file_name="output_reel.mp4",
                mime="video/mp4",
                use_container_width=True
            )

    except Exception as e:
        status.update(label="❌ 製作發生錯誤", state="error")
        st.error(f"錯誤細節：{e}")st.button("🚀 開始生成文案報告", type="primary", use_container_width=True)

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
