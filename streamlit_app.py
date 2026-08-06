import streamlit as st
import os
import json
import hashlib
import secrets
import io

from pathlib import Path
from datetime import datetime

from PIL import Image, ImageOps


# =====================================================
# APP 設定
# =====================================================

APP_NAME = "AI 蝦皮半自動化 2.5 PRO"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🛒",
    layout="wide"
)


# =====================================================
# 路徑
# =====================================================

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MEMBERS_FILE = DATA_DIR / "members.json"


# =====================================================
# Session
# =====================================================

if "login" not in st.session_state:
    st.session_state.login = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "result" not in st.session_state:
    st.session_state.result = ""


# =====================================================
# 密碼加密
# =====================================================

def hash_password(password):

    salt = secrets.token_hex(16)

    result = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    )

    return salt + "$" + result.hex()



def check_password(password, saved):

    try:

        salt, old_hash = saved.split("$")

        result = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            100000
        ).hex()

        return secrets.compare_digest(
            result,
            old_hash
        )

    except:

        return False



# =====================================================
# 會員資料
# =====================================================

def load_members():

    if not MEMBERS_FILE.exists():

        return []

    try:

        return json.loads(
            MEMBERS_FILE.read_text(
                encoding="utf-8"
            )
        )

    except:

        return []



def save_members(data):

    MEMBERS_FILE.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )



def create_admin():

    members = load_members()

    for m in members:

        if m["username"] == "admin":
            return


    members.append({

        "username":"admin",

        "password":hash_password(
            "admin123456"
        ),

        "name":"系統管理員",

        "role":"admin",

        "status":"active",

        "created":
            datetime.now().isoformat()

    })


    save_members(members)



def find_member(username):

    for m in load_members():

        if m["username"] == username:

            return m

    return None



def register(
    username,
    password,
    name
):

    if find_member(username):

        return False,"帳號已存在"


    members = load_members()


    members.append({

        "username":username,

        "password":
            hash_password(password),

        "name":
            name,

        "role":
            "member",

        "status":
            "active",

        "created":
            datetime.now().isoformat()

    })


    save_members(members)


    return True,"註冊成功"



def login(username,password):

    user=find_member(username)


    if not user:

        return False


    if not check_password(
        password,
        user["password"]
    ):

        return False


    if user["status"]!="active":

        return False


    st.session_state.login=True

    st.session_state.username=user["username"]

    st.session_state.role=user["role"]


    return True



# 建立管理員
create_admin()
# =====================================================
# Gemini AI 設定
# =====================================================

GEMINI_MODEL = "gemini-2.5-flash"


def get_api_key():

    try:

        key = st.secrets["GEMINI_API_KEY"]

        if key:
            return key

    except:

        pass


    return os.getenv(
        "GEMINI_API_KEY",
        ""
    )



def gemini_client():

    try:

        from google import genai

    except Exception:

        raise Exception(
            "缺少 google-genai 套件"
        )


    key=get_api_key()


    if not key:

        raise Exception(
            "沒有設定 GEMINI_API_KEY"
        )


    return genai.Client(
        api_key=key
    )



def ask_gemini(
    prompt,
    image_data=None,
    mime_type="image/jpeg"
):

    client=gemini_client()


    if image_data:

        from google.genai import types


        content=[

            types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            ),

            prompt

        ]

    else:

        content=prompt



    response=client.models.generate_content(

        model=GEMINI_MODEL,

        contents=content

    )


    if not response.text:

        return "AI沒有回覆"


    return response.text



# =====================================================
# 圖片處理
# =====================================================


def process_image(upload):

    data=upload.getvalue()


    image=Image.open(
        io.BytesIO(data)
    )


    image=ImageOps.exif_transpose(
        image
    )


    if image.mode!="RGB":

        image=image.convert(
            "RGB"
        )


    max_size=1600


    if max(image.size)>max_size:


        ratio=max_size/max(image.size)


        image=image.resize(

            (

                int(image.width*ratio),

                int(image.height*ratio)

            )

        )


    output=io.BytesIO()


    image.save(

        output,

        format="JPEG",

        quality=92

    )


    return output.getvalue()



# =====================================================
# AI 商品核心規則
# =====================================================


CORE_RULES = """

你是 AI 蝦皮半自動化 2.5 PRO。

最高規則：

1. 商品圖片是唯一真實來源。

2. 不可修改商品：
品牌、Logo、包裝、瓶身、
顏色、材質、文字、比例。

3. 不可幻想不存在資訊。

4. 不確定資料必須寫：
待確認。

5. 禁止：
人物、手、模特、
錯誤品牌、
錯誤文字、
多餘商品。

6. 商品必須保持一致。

7. 適用：
蝦皮電商、
TikTok短影音、
即夢AI 2.5。

"""



# =====================================================
# 商品分析 Prompt
# =====================================================


def build_prompt(data):


    return f"""

{CORE_RULES}


請分析以下商品：


商品名稱：
{data['name']}


價格：
{data['price']}


成本：
{data['cost']}


分潤：
{data['commission']}


規格：
{data['specs']}



請輸出：


【一、商品辨識】

【二、AI選品分析】

【三、蝦皮SEO標題】

【四、五大商品賣點】

【五、完整商品描述】

【六、TikTok爆款腳本】

【七、即夢AI2.5生圖英文Prompt】

【八、Negative Prompt】

【九、即夢AI2.5影片Prompt】

【十、25秒影片分鏡】

【十一、合規檢查】

"""
  # =====================================================
# 即夢 AI 2.5 完整規則
# =====================================================

JIMENG_RULES = """

【即夢 AI 2.5 商品原貌鎖定】

商品圖片為唯一來源。

必須保持：

- 品牌
- Logo
- 包裝
- 瓶身
- 外型
- 顏色
- 材質
- 標籤
- 印刷文字


禁止：

- 改造商品
- 改變品牌
- 生成相似商品
- 添加不存在配件


====================

【商品一致性】

影片全程：

第一秒商品 = 最後一秒商品


禁止：

- 變形
- 融化
- 扭曲
- 漂浮
- 重複商品
- 文字錯亂
- Logo錯誤


====================

【人物限制】

禁止：

- 人物
- 手
- 模特
- 主播


商品必須單獨展示。


====================

【商業攝影】

風格：

High-end commercial product photography

要求：

- 8K
- realistic
- studio lighting
- premium advertising
- clean background


====================

【即夢圖片 Prompt】

輸出：

English Prompt

Negative Prompt

繁體中文海報文字


====================

【即夢影片 Prompt】

比例：

9:16


流程：

Opening：

商品正面置中


Middle：

slow camera push in

展示：

包裝
材質
細節


Ending：

Freeze frame

商品置中


====================

【Negative Prompt】

no people,
no hands,
no watermark,
no extra products,
no wrong logo,
no deformation,
no duplicate product,
no fake text

"""



# =====================================================
# 登入畫面
# =====================================================


def show_login():


    st.title(
        "🛒 "+APP_NAME
    )


    tab1,tab2=st.tabs(
        [
            "登入",
            "註冊"
        ]
    )


    with tab1:


        user=st.text_input(
            "帳號"
        )

        pwd=st.text_input(
            "密碼",
            type="password"
        )


        if st.button(
            "登入"
        ):


            if login(user,pwd):

                st.success(
                    "登入成功"
                )

                st.rerun()


            else:

                st.error(
                    "帳號或密碼錯誤"
                )



        st.info(
            "管理員：admin / admin123456"
        )



    with tab2:


        new_user=st.text_input(
            "新帳號"
        )


        new_name=st.text_input(
            "名稱"
        )


        new_pwd=st.text_input(
            "新密碼",
            type="password"
        )



        if st.button(
            "註冊"
        ):


            ok,msg=register(

                new_user,

                new_pwd,

                new_name

            )


            if ok:

                st.success(msg)

            else:

                st.error(msg)



# =====================================================
# Sidebar
# =====================================================


def sidebar():


    with st.sidebar:


        st.title(
            "會員中心"
        )


        st.write(
            "帳號：",
            st.session_state.username
        )


        st.write(
            "權限：",
            st.session_state.role
        )


        if st.button(
            "登出"
        ):

            st.session_state.login=False

            st.session_state.username=""

            st.rerun()
