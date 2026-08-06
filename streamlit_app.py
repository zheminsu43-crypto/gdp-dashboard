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
            # =====================================================
# AI 主頁
# =====================================================


def show_home():


    st.title(
        "🛒 AI 蝦皮半自動化 2.5 PRO"
    )


    st.caption(
        "Gemini 2.5 + 即夢 AI 2.5 電商自動化"
    )


    col1,col2=st.columns(2)



    with col1:


        st.subheader(
            "1. 上傳商品圖片"
        )


        image_file=st.file_uploader(

            "選擇商品圖片",

            type=[
                "jpg",
                "jpeg",
                "png"
            ]

        )


        if image_file:


            st.image(
                image_file,
                use_container_width=True
            )



        st.subheader(
            "2. 商品資料"
        )


        name=st.text_input(
            "商品名稱"
        )


        price=st.text_input(
            "商品價格"
        )


        cost=st.text_input(
            "商品成本"
        )


        commission=st.text_input(
            "分潤比例"
        )


        specs=st.text_area(
            "商品規格"
        )



        run=st.button(

            "🚀 開始 AI 分析",

            type="primary"

        )



    with col2:


        st.subheader(
            "3. AI生成結果"
        )


        if run:


            if not image_file:


                st.warning(
                    "請上傳商品圖片"
                )


            elif not name:


                st.warning(
                    "請輸入商品名稱"
                )


            else:


                try:


                    with st.spinner(
                        "AI分析中..."
                    ):


                        img=process_image(
                            image_file
                        )


                        data={

                            "name":name,

                            "price":price,

                            "cost":cost,

                            "commission":commission,

                            "specs":specs

                        }



                        prompt=build_prompt(
                            data
                        )


                        result=ask_gemini(

                            prompt,

                            img

                        )


                        st.session_state.result=result



                except Exception as e:


                    st.error(
                        str(e)
                    )



        if st.session_state.result:


            st.markdown(
                st.session_state.result
            )


            st.download_button(

                "下載報告",

                st.session_state.result,

                file_name="AI電商報告.txt"

            )





# =====================================================
# 管理員
# =====================================================


def admin_page():


    st.title(
        "👑 管理員中心"
    )


    members=load_members()


    st.write(
        "會員數量：",
        len(members)
    )


    for m in members:


        st.write(
            m["username"],
            m["role"],
            m["status"]
        )





# =====================================================
# 主程式
# =====================================================


def main():


    if not st.session_state.login:


        show_login()


    else:


        sidebar()


        if st.session_state.role=="admin":


            page=st.selectbox(

                "功能",

                [
                    "AI商品分析",
                    "管理員中心"
                ]

            )


            if page=="管理員中心":

                admin_page()

            else:

                show_home()


        else:

            show_home()



if __name__=="__main__":

    main()
# =====================================================
# Gemini API
# =====================================================

def get_gemini_key():

    try:

        key = st.secrets.get(
            "GEMINI_API_KEY",
            ""
        )

        if key:
            return key

    except:

        pass


    return os.getenv(
        "GEMINI_API_KEY",
        ""
    )



def get_gemini_client():

    try:

        from google import genai

    except Exception:

        raise Exception(
            "缺少 google-genai 套件"
        )


    key=get_gemini_key()


    if not key:

        raise Exception(
            "請設定 GEMINI_API_KEY"
        )


    return genai.Client(
        api_key=key
    )



def ask_gemini(
    prompt,
    image_bytes=None,
    mime_type="image/jpeg"
):

    client=get_gemini_client()


    if image_bytes:


        from google.genai import types


        contents=[

            types.Part.from_bytes(

                data=image_bytes,

                mime_type=mime_type

            ),

            prompt

        ]


    else:

        contents=prompt



    response=client.models.generate_content(

        model=GEMINI_MODEL,

        contents=contents

    )


    if hasattr(response,"text"):

        return response.text


    return "AI沒有回傳內容"



# =====================================================
# 圖片處理
# =====================================================

def prepare_image(uploaded_file):

    raw=uploaded_file.getvalue()


    image=Image.open(
        io.BytesIO(raw)
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
# 商品資料 Prompt 基礎規則
# =====================================================

BASE_AI_RULES = """

你是 AI 蝦皮半自動化 2.5 PRO。

最高規則：

1.
商品圖片是唯一真實來源。


2.
保持商品原貌：

品牌
Logo
包裝
瓶身
盒型
顏色
材質
比例
標籤
文字


3.
禁止自行創造：

不存在品牌
不存在規格
不存在功能
不存在價格


4.
資料不清楚：

必須輸出：

待確認


5.
禁止：

人物
手
模特
錯誤商品
多餘商品
浮水印


6.
所有內容適合：

蝦皮電商
TikTok短影音
即夢AI 2.5


"""
# =====================================================
# 即夢 AI 2.5 完整控制規則
# =====================================================

JIMENG_25_RULES = """

【商品原貌鎖定】

上傳圖片中的商品為唯一主體。

必須保持：

- 品牌
- Logo
- 包裝
- 瓶身
- 盒子
- 顏色
- 材質
- 比例
- 標籤
- 商品文字


禁止：

- 修改商品外觀
- 改品牌
- 改包裝
- 捏造商品
- 生成相似商品


--------------------------------


【商品一致性】

圖片與影片全程：

同一個商品

禁止：

- 變形
- 融化
- 扭曲
- 漂浮
- 複製商品
- Logo錯亂
- 文字變形
- 閃爍


--------------------------------


【人物限制】

禁止：

- 人物
- 手
- 手臂
- 模特
- 主播


商品必須獨立展示。


--------------------------------


【商業攝影風格】

使用：

High-end commercial product photography

包含：

- Studio lighting
- Ultra realistic
- Premium advertising style
- 8K quality
- Clean background


--------------------------------


【即夢 AI 2.5 生圖輸出】

必須產生：


1.
English Prompt


包含：

Product description

Camera angle

Lighting

Composition

Background

Commercial style



2.
Negative Prompt


固定包含：


no people,
no hands,
no watermark,
no extra products,
no wrong logo,
no deformation,
no duplicate object,
no fake text



3.
繁體中文畫面文字


只能使用：

繁體中文



--------------------------------


【即夢 AI 2.5 影片規則】

比例：

9:16


時間：

15-30秒



Opening：

0-3秒

商品完整正面

置中展示



Middle：

3-20秒

慢速推近：

smooth camera push in


展示：

包裝
材質
細節
特色



Ending：

商品置中

Freeze Frame



"""



# =====================================================
# 蝦皮 SEO 規則
# =====================================================


SHOPEE_RULES = """

請生成蝦皮高轉換內容：


【SEO標題】

格式：

品牌 + 商品名稱 + 核心特色 + 規格 + 熱門搜尋詞



【五大賣點】

使用 Emoji

簡短有力

解決買家需求



【完整商品描述】

包含：

商品特色

使用方式

適用族群

注意事項



【規格】

條列：

容量

尺寸

材質

產地

其他資訊



【Hashtag】

10-15個熱門標籤



禁止：

虛假效果

誇大保證

不存在資料


"""



# =====================================================
# TikTok 爆款規則
# =====================================================


TIKTOK_RULES = """

生成 TikTok 帶貨內容：


【3秒Hook】

提供：

痛點型

好奇型

優惠型



【15-30秒腳本】

包含：

開場吸引

商品展示

賣點介紹

購買理由



【Caption】

短版爆款文案



【CTA】

引導：

立即購買

加入購物車



【Hashtag】

熱門短影音標籤


"""



# =====================================================
# 最終 AI Prompt 建立
# =====================================================


def create_master_prompt(product):


    return f"""

{BASE_AI_RULES}


{JIMENG_25_RULES}


{SHOPEE_RULES}


{TIKTOK_RULES}



商品資料：

商品名稱：
{product.get("name","")}


價格：
{product.get("price","")}


成本：
{product.get("cost","")}


分潤：
{product.get("commission","")}


規格：
{product.get("specs","")}



請完整輸出：

1. 商品辨識

2. AI選品分析

3. 蝦皮SEO文案

4. TikTok腳本

5. 即夢AI2.5生圖Prompt

6. Negative Prompt

7. 即夢AI2.5影片Prompt

8. 25秒爆款影片分鏡

9. 合規檢查


資料不足請標示：

待確認

"""
    # =====================================================
# 登入頁
# =====================================================

def login_page():

    st.title(
        "🛒 " + APP_NAME
    )


    tab1, tab2 = st.tabs(
        [
            "🔐 登入",
            "📝 註冊"
        ]
    )


    with tab1:

        username = st.text_input(
            "帳號"
        )

        password = st.text_input(
            "密碼",
            type="password"
        )


        if st.button(
            "登入",
            use_container_width=True
        ):

            if login_user(
                username,
                password
            ):

                st.success(
                    "登入成功"
                )

                st.rerun()

            else:

                st.error(
                    "帳號或密碼錯誤"
                )


        st.info(
            "管理員帳號：admin\n\n密碼：admin123456"
        )



    with tab2:


        new_username = st.text_input(
            "新帳號"
        )


        new_name = st.text_input(
            "姓名/暱稱"
        )


        new_password = st.text_input(
            "新密碼",
            type="password"
        )


        if st.button(
            "註冊會員",
            use_container_width=True
        ):


            ok,msg = register_user(

                new_username,

                new_password,

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
            "👤 會員中心"
        )


        st.write(
            "帳號：",
            st.session_state.username
        )


        st.write(
            "權限：",
            st.session_state.role
        )


        st.write(
            "期限：永久"
        )


        if st.button(
            "🚪 登出"
        ):

            logout()

            st.rerun()



# =====================================================
# AI 主頁
# =====================================================

def home_page():


    st.title(
        "🛒 AI 蝦皮半自動化 2.5 PRO"
    )


    st.caption(
        "Gemini 2.5 + 即夢 AI 2.5 電商自動化"
    )


    left,right = st.columns(2)



    with left:


        st.subheader(
            "1. 商品圖片"
        )


        image = st.file_uploader(

            "上傳商品圖片",

            type=[
                "png",
                "jpg",
                "jpeg"
            ]

        )


        if image:

            st.image(
                image,
                use_container_width=True
            )



        st.subheader(
            "2. 商品資料"
        )


        name = st.text_input(
            "商品名稱"
        )


        price = st.text_input(
            "商品價格"
        )


        cost = st.text_input(
            "商品成本"
        )


        commission = st.text_input(
            "分潤比例"
        )


        specs = st.text_area(
            "商品規格"
        )


        start = st.button(
            "🚀 開始 AI 分析",
            type="primary",
            use_container_width=True
        )



    with right:


        st.subheader(
            "AI 生成結果"
        )


        if start:


            if not image:

                st.warning(
                    "請先上傳圖片"
                )


            elif not name:

                st.warning(
                    "請輸入商品名稱"
                )


            else:


                try:


                    with st.spinner(
                        "AI分析中..."
                    ):


                        img_bytes = prepare_image(
                            image
                        )


                        product={

                            "name":name,

                            "price":price,

                            "cost":cost,

                            "commission":commission,

                            "specs":specs

                        }


                        prompt=create_master_prompt(
                            product
                        )


                        result=ask_gemini(

                            prompt,

                            img_bytes

                        )


                        st.session_state.result=result



                except Exception as e:

                    st.error(
                        str(e)
                    )



        if st.session_state.result:


            st.markdown(
                st.session_state.result
            )


            st.download_button(

                "📥 下載報告",

                st.session_state.result,

                file_name="AI電商報告.txt"

            )



# =====================================================
# 管理員中心
# =====================================================

def admin_page():

    st.title(
        "👑 管理員中心"
    )


    members = load_members()


    st.write(
        "會員數：",
        len(members)
    )


    for m in members:

        st.write(

            m.get("username"),

            "-",

            m.get("role")

        )



# =====================================================
# 主程式
# =====================================================

def main():


    if not st.session_state.login:


        login_page()


    else:


        sidebar()


        if st.session_state.role=="admin":


            menu = st.selectbox(

                "功能",

                [
                    "AI商品分析",
                    "管理員中心"
                ]

            )


            if menu=="管理員中心":

                admin_page()

            else:

                home_page()


        else:

            home_page()



if __name__=="__main__":

    main()


# END OF FILE
    
