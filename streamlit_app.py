import io
from datetime import datetime

import streamlit as st
from PIL import Image

APP_NAME = "AI 蝦皮自動化"
APP_VERSION = "2.5 PRO"

st.set_page_config(
    page_title=f"{APP_NAME} {APP_VERSION}",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp{background:radial-gradient(circle at 20% 0%,rgba(255,90,0,.08),transparent 25%),#05080d;color:#f5f7fa}
#MainMenu,footer{visibility:hidden}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0a1018,#070b11);border-right:1px solid rgba(255,255,255,.08)}
.card{background:linear-gradient(145deg,#101923,#090f17);border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:16px;margin-bottom:14px}
.title{font-size:24px;font-weight:800}.sub{color:#8995a4;font-size:12px}
.section{font-size:17px;font-weight:800;margin:10px 0}
.badge{display:inline-block;margin-left:8px;padding:3px 8px;border-radius:6px;font-size:11px;color:#ff9d52;border:1px solid #ff6a00;background:rgba(255,90,0,.1)}
.metric{background:linear-gradient(145deg,#111a25,#0b1119);border:1px solid rgba(255,255,255,.07);border-radius:13px;padding:13px;min-height:80px}
.metric-label{font-size:11px;color:#8995a4}.metric-value{font-size:21px;font-weight:800;margin-top:4px}.orange{color:#ff6a00}.green{color:#50d890}.blue{color:#4ab7ff}.purple{color:#b28cff}
.workflow{display:flex;gap:8px;align-items:center;background:#0b121b;border:1px solid rgba(255,255,255,.07);border-radius:14px;padding:12px;margin-bottom:14px;overflow-x:auto}
.step{min-width:130px;flex:1;background:#101923;border:1px solid rgba(255,255,255,.08);border-radius:11px;padding:10px}.step-icon{font-size:22px}.step-title{font-size:13px;font-weight:800}.step-desc{font-size:10px;color:#7e8a99}.arrow{color:#ff6a00;font-size:20px;font-weight:bold}
.check{color:#49d98c}.tag{display:inline-block;padding:5px 9px;margin:3px;background:#172331;border:1px solid #293a4b;border-radius:7px;color:#b8c5d2;font-size:11px}
.stButton>button{border-radius:8px!important;background:#111a24!important;color:#fff!important;font-weight:700!important;border:1px solid rgba(255,255,255,.12)!important}
.stButton>button:hover{border-color:#ff6a00!important;color:#ff8b42!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#0b121b!important;color:#fff!important;border-radius:8px!important}
</style>
""", unsafe_allow_html=True)

# -------------------- state --------------------
def init_state():
    defaults = {
        "page": "商品上架工作台",
        "product_name": "",
        "category": "保養保健",
        "price": 499,
        "stock": 100,
        "selling_points": "",
        "condition": "全新",
        "images": [],
        "generated": False,
        "published": 0,
        "history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

# -------------------- helpers --------------------
def current_name():
    return st.session_state.product_name.strip() or "玻尿酸保濕精華液"

def title_text():
    return f"{current_name()}｜深層保濕修護｜日常補水保養"

def description_text():
    return f"""{current_name()}\n\n✨ 商品特色\n✓ 深層保濕補水\n✓ 修護日常保養\n✓ 溫和好使用\n✓ 清爽不黏膩\n\n實際商品資訊請以商品包裝及賣場資訊為準。"""

def keywords_text():
    return "保濕,補水,修護,保養,美容,肌膚,日常保養"

def tiktok_text():
    return f"""🔥 {current_name()}\n\n乾燥、缺水怎麼辦？\n用簡單的日常保養方式，維持水嫩感。\n\n✨ 商品特色展示\n🛒 想了解更多商品資訊，立即查看賣場！"""

def jimeng_prompt():
    return f"""9:16 vertical premium commercial product video.\n\nMain subject: {current_name()}\n\nUse the uploaded product image as the ONLY visual source for the product. Preserve original product shape, packaging, logo, label, colors, materials and visible text.\n\nCamera: slow cinematic push-in, subtle orbit movement, premium commercial lighting, clean luxury background.\n\nDo not redesign the product. Do not invent logos. Do not change packaging. Do not add fake text."""

def save_history(action):
    st.session_state.history.insert(0, {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "商品": current_name(),
        "操作": action,
    })

# -------------------- sidebar --------------------
def sidebar():
    with st.sidebar:
        st.markdown('<div class="card"><div style="font-size:19px;font-weight:800">🛍️ AI 蝦皮自動化</div><div class="sub">AI 智能生成・一鍵上架</div></div>', unsafe_allow_html=True)
        menus = [
            ("🏠", "Dashboard"), ("🛍️", "商品上架工作台"), ("📦", "商品管理"),
            ("🧾", "訂單管理"), ("📊", "數據分析"), ("🖼️", "AI 素材庫"),
            ("🕘", "歷史紀錄"), ("🎵", "TikTok 短影音"), ("💰", "蝦皮分潤管理"),
        ]
        for icon, name in menus:
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()
        st.markdown("---")
        for icon, name in [("👤", "會員管理"), ("🛡️", "管理員中心"), ("⚙️", "系統設定"), ("🔑", "API 設定"), ("📚", "使用教學")]:
            if st.button(f"{icon}  {name}", key=f"sys_{name}", use_container_width=True):
                st.session_state.page = name
                st.rerun()
        st.markdown('<div class="card"><b style="color:#ff8a3d">👑 PRO 會員</b><br><span class="check">✓</span> AI 內容生成<br><span class="check">✓</span> 商品圖片分析介面<br><span class="check">✓</span> TikTok 9:16<br><span class="check">✓</span> 即夢 Prompt<br><span class="check">✓</span> 歷史紀錄</div>', unsafe_allow_html=True)

# -------------------- header / metrics --------------------
def header():
    st.markdown('<div class="card"><div class="title">🛍️ AI 蝦皮自動化 <span class="badge">2.5 PRO</span></div><div class="sub">AI 智能生成・商品工作流・蝦皮上架準備</div></div>', unsafe_allow_html=True)

def metrics():
    cols = st.columns(4)
    values = [("今日 AI 使用額度", "86 / 200 次", "orange"), ("AI 剩餘額度", "1,248 Tokens", "green"), ("會員等級", "PRO 會員", "purple"), ("會員期限", "永久會員", "blue")]
    for col, (label, value, cls) in zip(cols, values):
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{label}</div><div class="metric-value {cls}">{value}</div></div>', unsafe_allow_html=True)

# -------------------- dashboard --------------------
def dashboard():
    st.markdown('<div class="section">📊 Dashboard 總覽</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, icon, label, value, delta in zip(cols, ["🛍️", "👁️", "🛒", "💰"], ["今日上架商品", "商品瀏覽數", "成交訂單", "銷售額"], ["12", "5,689", "58", "NT$28,560"], ["+3", "+22%", "+15%", "+25%"]):
        with col:
            st.markdown(f'<div class="metric"><div style="font-size:23px">{icon}</div><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="green">{delta}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section">🚀 AI 自動化流程</div>', unsafe_allow_html=True)
    st.markdown('<div class="workflow">' + '<div class="step"><div class="step-icon">📝</div><div class="step-title">商品輸入</div><div class="step-desc">資料與圖片</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🧠</div><div class="step-title">AI 分析</div><div class="step-desc">分析商品</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">✨</div><div class="step-title">內容生成</div><div class="step-desc">標題與文案</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">⚙️</div><div class="step-title">上架設定</div><div class="step-desc">價格與庫存</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🚀</div><div class="step-title">一鍵上架</div><div class="step-desc">目前為模擬</div></div></div>', unsafe_allow_html=True)
    a, b = st.columns([2, 1])
    with a:
        st.markdown('<div class="card"><b>📈 最近銷售</b></div>', unsafe_allow_html=True)
        st.line_chart({"銷售額": [18000, 21000, 19500, 26000, 24500, 28000, 28560]})
    with b:
        st.markdown('<div class="card"><b>🤖 AI 使用統計</b><h1 style="color:#ff6a00">24.96%</h1>本月使用量<br><br>文案生成：658 次<br>圖片分析：412 次<br>其他功能：178 次</div>', unsafe_allow_html=True)

# -------------------- workspace --------------------
def workflow_header():
    st.markdown('<div class="workflow"><div class="step"><div class="step-icon">📝</div><div class="step-title">商品資訊</div><div class="step-desc">輸入商品</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🧠</div><div class="step-title">AI 分析</div><div class="step-desc">分析圖片與資料</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">✨</div><div class="step-title">內容生成</div><div class="step-desc">文案與 Prompt</div></div><div class="arrow">→</div><div class="step"><div class="step-icon">🚀</div><div class="step-title">上架</div><div class="step-desc">目前為模擬</div></div></div>', unsafe_allow_html=True)

def workspace():
    workflow_header()
    left, middle, right = st.columns([1.05, 1.25, 1.2])
    with left:
        st.markdown('<div class="card"><b>① 商品資訊輸入</b>', unsafe_allow_html=True)
        name = st.text_input("商品名稱", value=st.session_state.product_name, placeholder="例如：玻尿酸保濕精華液 30ml")
        category = st.selectbox("商品分類", ["保養保健", "美妝保養", "3C 電子", "居家生活", "服飾鞋包", "食品飲料", "汽機車", "其他"], index=0)
        price = st.number_input("商品價格", min_value=0, value=int(st.session_state.price), step=10)
        stock = st.number_input("商品庫存", min_value=0, value=int(st.session_state.stock), step=1)
        condition = st.radio("商品狀態", ["全新", "二手"], horizontal=True)
        points = st.text_area("商品賣點", value=st.session_state.selling_points, placeholder="例如：深層保濕、修護、溫和", height=90)
        files = st.file_uploader("上傳商品圖片（可多張）", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
        if files:
            st.session_state.images = files
            st.success(f"已選擇 {len(files)} 張圖片")
        if st.button("🚀 執行 AI 工作流", use_container_width=True):
            st.session_state.product_name = name
            st.session_state.category = category
            st.session_state.price = price
            st.session_state.stock = stock
            st.session_state.condition = condition
            st.session_state.selling_points = points
            st.session_state.generated = True
            save_history("執行 AI 工作流")
            st.success("工作流完成，內容已產生")
        st.markdown('</div>', unsafe_allow_html=True)
    with middle:
        st.markdown('<div class="card"><b>② AI 分析結果</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品分析", "標題建議", "關鍵字", "賣點"])
        with tabs[0]:
            if st.session_state.images:
                try:
                    img = Image.open(st.session_state.images[0])
                    st.image(img, use_container_width=True)
                except Exception:
                    st.warning("圖片無法讀取")
            else:
                st.info("尚未上傳商品圖片")
            st.write(f"商品：{current_name()}")
            st.write("目前為離線展示模式；未連接 Gemini，因此不會虛構真正的圖片分析結果。")
        with tabs[1]:
            for i, text in enumerate([title_text(), f"{current_name()}｜保濕補水｜日常保養", f"高效修護 {current_name()}｜清爽好吸收"]):
                st.checkbox(text, value=(i == 0), key=f"suggest_{i}")
        with tabs[2]:
            st.markdown("".join(f'<span class="tag">#{x}</span>' for x in keywords_text().split(",")), unsafe_allow_html=True)
        with tabs[3]:
            for x in ["深層保濕補水", "日常修護", "溫和好使用", "清爽不黏膩"]:
                st.markdown(f'<div><span class="check">✓</span> {x}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card"><b>③ AI 內容生成</b>', unsafe_allow_html=True)
        tabs = st.tabs(["商品標題", "商品描述", "關鍵字", "TikTok 文案", "即夢 Prompt"])
        with tabs[0]:
            st.text_area("標題", title_text(), height=120)
        with tabs[1]:
            st.text_area("描述", description_text(), height=200)
        with tabs[2]:
            st.text_area("關鍵字", keywords_text(), height=90)
        with tabs[3]:
            st.text_area("TikTok", tiktok_text(), height=170)
        with tabs[4]:
            st.text_area("即夢 AI 2.5 Prompt", jimeng_prompt(), height=260)
        st.markdown('</div>', unsafe_allow_html=True)
    bottom1, bottom2, bottom3 = st.columns([1, 1.2, 1])
    with bottom1:
        st.markdown('<div class="card"><b>④ 蝦皮上架設定</b>', unsafe_allow_html=True)
        st.selectbox("物流", ["蝦皮店到店", "7-11 店到店", "全家店到店", "賣家宅配"])
        st.selectbox("出貨地", ["台灣・新北市", "台灣・台北市", "台灣・桃園市"])
        st.text_input("商品規格", "30ml")
        st.number_input("上架庫存", min_value=0, value=int(st.session_state.stock))
        st.selectbox("出貨天數", ["1 天內出貨", "2 天內出貨", "3 天內出貨", "7 天內出貨"])
        st.toggle("自動回覆買家問題", True)
        st.markdown('</div>', unsafe_allow_html=True)
    with bottom2:
        st.markdown('<div class="card"><b>⑤ 蝦皮上架預覽</b>', unsafe_allow_html=True)
        if st.session_state.images:
            try:
                st.image(Image.open(st.session_state.images[0]), use_container_width=True)
            except Exception:
                st.info("圖片預覽失敗")
        else:
            st.info("尚未上傳商品圖片")
        st.markdown(f'<div style="background:#fff;color:#222;padding:12px;border-radius:9px"><b>{current_name()}</b><div style="color:#ee4d2d;font-size:25px;font-weight:800">NT${st.session_state.price}</div><small>⭐⭐⭐⭐⭐　預覽資料</small></div>', unsafe_allow_html=True)
        if st.button("🚀 一鍵上架蝦皮（模擬）", use_container_width=True):
            st.session_state.published += 1
            save_history("一鍵上架模擬")
            st.success("模擬上架完成；尚未連接蝦皮官方 API，不會真的發布商品。")
        st.markdown('</div>', unsafe_allow_html=True)
    with bottom3:
        st.markdown(f'<div class="card"><b>系統狀態</b><h2>🟢 正常</h2>AI：離線展示模式<br>圖片：{len(st.session_state.images)} 張<br>模擬上架：{st.session_state.published} 次<br>版本：{APP_VERSION}</div>', unsafe_allow_html=True)

# -------------------- generic pages --------------------
def generic_page(page):
    info = {
        "商品管理": ("📦", "管理商品資料與上架狀態"),
        "訂單管理": ("🧾", "管理訂單與出貨流程"),
        "數據分析": ("📊", "查看銷售與使用數據"),
        "AI 素材庫": ("🖼️", "管理圖片、影片與 Prompt"),
        "歷史紀錄": ("🕘", "查看操作歷史"),
        "TikTok 短影音": ("🎵", "建立 9:16 短影音內容"),
        "蝦皮分潤管理": ("💰", "查看分潤資料"),
        "會員管理": ("👤", "管理會員帳號與期限"),
        "管理員中心": ("🛡️", "管理系統權限"),
        "系統設定": ("⚙️", "系統功能設定"),
        "API 設定": ("🔑", "AI 與蝦皮 API 設定"),
        "使用教學": ("📚", "操作說明"),
    }
    icon, desc = info.get(page, ("⚙️", "系統功能"))
    st.markdown(f'<div class="card"><div style="font-size:28px">{icon}</div><div class="title">{page}</div><div class="sub">{desc}</div></div>', unsafe_allow_html=True)
    if page == "商品管理":
        st.dataframe({"商品":["玻尿酸保濕精華液","修護面膜","保濕乳液"],"價格":[499,299,399],"庫存":[100,250,88],"狀態":["上架中","上架中","草稿"]}, use_container_width=True, hide_index=True)
    elif page == "訂單管理":
        st.info("目前為介面展示版，尚未連接蝦皮訂單 API。")
    elif page == "數據分析":
        a,b,c=st.columns(3)
        a.metric("今日銷售額","NT$28,560","+25%")
        b.metric("今日訂單","58","+15%")
        c.metric("瀏覽人次","5,689","+22%")
        st.line_chart({"銷售額":[18000,21000,19500,26000,24500,28000,28560]})
    elif page == "AI 素材庫":
        st.info("素材庫介面已建立；目前資料只保存在本次 Streamlit 工作階段。")
    elif page == "歷史紀錄":
        if st.session_state.history:
            st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
        else:
            st.info("尚無歷史紀錄。")
    elif page == "TikTok 短影音":
        st.text_area("9:16 短影音腳本", tiktok_text(), height=180)
        st.text_area("即夢 AI 2.5 Prompt", jimeng_prompt(), height=230)
        st.info("目前只生成文字 Prompt，尚未連接影片生成服務。")
    elif page == "蝦皮分潤管理":
        st.metric("本月分潤","NT$12,580","+18%")
    elif page == "會員管理":
        st.info("會員管理介面已建立。正式登入與永久會員資料庫可在下一階段接入。")
    elif page == "管理員中心":
        st.warning("目前為展示介面，正式管理員驗證尚未連接資料庫。")
    elif page == "系統設定":
        st.toggle("啟用 AI 自動分析", True)
        st.toggle("自動保存歷史紀錄", True)
        st.toggle("深色科技介面", True)
    elif page == "API 設定":
        st.info("不填 API Key 也可以正常啟動本版本。")
        st.text_input("Gemini API Key", type="password")
        st.text_input("Shopee API Key", type="password")
    elif page == "使用教學":
        st.markdown("""### 使用流程\n1. 輸入商品名稱、分類、價格、庫存。\n2. 上傳一張或多張商品圖片。\n3. 執行 AI 工作流。\n4. 檢查標題、描述、關鍵字、TikTok 文案與即夢 Prompt。\n5. 使用蝦皮預覽確認資料。\n6. 目前一鍵上架為**模擬功能**，尚未真的連接蝦皮。""")

# -------------------- run --------------------
sidebar()
header()

if st.session_state.page == "Dashboard":
    dashboard()
elif st.session_state.page == "商品上架工作台":
    metrics()
    workspace()
else:
    generic_page(st.session_state.page)

st.markdown('<div style="text-align:center;color:#52606e;font-size:10px;padding:25px 0 10px">AI 蝦皮自動化 2.5 PRO ・ Streamlit Cloud Ready</div>', unsafe_allow_html=True)
fe_allow_html=True)
        a,b,c,d,e = st.tabs(["標題","描述","關鍵字","TikTok","即夢 Prompt"])
        with a: st.text_area("商品標題", title_text(), height=110, key="out_title")
        with b: st.text_area("商品描述", description_text(), height=220, key="out_desc")
        with c: st.text_area("關鍵字", "保濕,補水,修護,保養,美容,肌膚,日常保養", height=100, key="out_kw")
        with d: st.text_area("TikTok 文案", f"🔥 {product_name()}\n\n乾燥肌日常保養怎麼做？\n簡單介紹商品特色與使用情境。\n\n立即了解商品資訊！", height=170, key="out_tt")
        with e: st.text_area("即夢 AI 2.5 Prompt", jimeng_prompt(), height=270, key="out_jm")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("###")
    c1,c2,c3 = st.columns([1,1.25,1])
    with c1:
        st.markdown("<div class='card'><div class='ct'>④ 蝦皮上架設定</div>", unsafe_allow_html=True)
        st.selectbox("物流", ["蝦皮店到店","7-11 店到店","全家店到店","賣家宅配"])
        st.selectbox("出貨地", ["新北市","台北市","桃園市","其他"])
        st.text_input("商品規格", "30ml")
        st.number_input("上架庫存", min_value=0, value=int(st.session_state.stock))
        st.selectbox("出貨天數", ["1 天內","2 天內","3 天內","7 天內"])
        st.toggle("自動回覆買家問題", value=True)
        st.button("💾 儲存上架設定", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='card'><div class='ct'>⑤ 蝦皮商品預覽</div>", unsafe_allow_html=True)
        if st.session_state.images:
            try: st.image(Image.open(st.session_state.images[0]), use_container_width=True)
            except Exception: pass
        else: st.info("尚未上傳商品圖片")
        st.markdown(f"<div style='background:white;color:#222;border-radius:8px;padding:12px'><b>{product_name()}</b><div style='color:#ee4d2d;font-size:25px;font-weight:800'>NT$ {st.session_state.price}</div><span style='font-size:10px;color:#777'>⭐⭐⭐⭐⭐　已售 268</span></div>", unsafe_allow_html=True)
        if st.button("🚀 一鍵上架蝦皮（目前為模擬）", use_container_width=True):
            st.session_state.published += 1
            save_history("一鍵上架模擬", product_name())
            st.success("上架資料已完成驗證；目前尚未連接蝦皮官方 API，因此不會真的發布商品。")
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='card'><div class='ct'>📡 系統狀態</div><div style='text-align:center;font-size:40px'>🚀</div><div style='text-align:center;font-weight:800'>系統運行正常</div><div class='check' style='text-align:center'>● 本機 AI 工作流在線</div><hr><div class='small'>版本：2.5 PRO</div><div class='small'>AI：規則生成模式</div><div class='small'>已模擬上架：%d 次</div></div>" % st.session_state.published, unsafe_allow_html=True)
    st.markdown("### ⚡ 快速功能")
    q = [("🧠","AI 圖片分析"),("📄","批量生成"),("🎵","TikTok 短影音"),("🎬","即夢 Prompt"),("📁","素材庫"),("🕘","歷史紀錄"),("📊","數據分析")]
    cols=st.columns(7)
    for col,(icon,title) in zip(cols,q):
        with col: st.markdown(f"<div class='quick'><div class='qicon'>{icon}</div><div class='qtitle'>{title}</div></div>", unsafe_allow_html=True)


def dashboard():
    metrics()
    workflow()
    a,b=st.columns([2,1])
    with a:
        st.markdown("<div class='card'><div class='ct'>📈 電商工作概況</div>", unsafe_allow_html=True)
        st.bar_chart({"上架商品":[8,12,10,15,12,18,20],"AI 工作量":[10,16,14,22,20,28,30]})
        st.markdown("</div>", unsafe_allow_html=True)
    with b:
        st.markdown("<div class='card'><div class='ct'>🤖 AI 使用統計</div><div style='font-size:38px;font-weight:800;color:#ff6a00;text-align:center'>24.96%</div><div class='small' style='text-align:center'>本月使用量</div><hr><div class='small'>文案生成　658 次</div><div class='small'>圖片分析　412 次</div><div class='small'>Prompt　178 次</div></div>", unsafe_allow_html=True)


def generic_page(page):
    info={
        "商品管理":("📦","管理商品資料、價格、庫存與狀態"),"訂單管理":("🧾","查看訂單與出貨資料"),"數據分析":("📊","查看銷售與工作流數據"),
        "AI 素材庫":("🖼️","管理圖片、文案、Prompt 與影片素材"),"歷史紀錄":("🕘","查看本機 AI 工作紀錄"),"TikTok 短影音":("🎵","建立 9:16 短影音腳本與 Prompt"),
        "蝦皮分潤管理":("💰","管理分潤資料"),"會員管理":("👤","會員管理介面"),"管理員中心":("🛡️","管理員控制中心"),"系統設定":("⚙️","系統功能設定"),"API 設定":("🔑","未來接入 API 的設定區"),"使用教學":("📚","系統使用說明")}
    icon,desc=info.get(page,("⚙️","系統功能"))
    st.markdown(f"<div class='card'><div style='font-size:28px'>{icon}</div><div style='font-size:22px;font-weight:800'>{page}</div><div class='small'>{desc}</div></div>",unsafe_allow_html=True)
    if page=="商品管理":
        st.dataframe({"商品":["玻尿酸保濕精華液","修護面膜","保濕乳液"],"價格":[499,299,399],"庫存":[100,250,88],"狀態":["上架中","上架中","草稿"]},use_container_width=True,hide_index=True)
    elif page=="訂單管理": st.info("訂單模組目前為介面版，尚未連接蝦皮官方訂單 API。")
    elif page=="數據分析":
        c=st.columns(3); c[0].metric("今日銷售額","NT$28,560","+25%"); c[1].metric("今日訂單","58","+15%"); c[2].metric("瀏覽人次","5,689","+22%"); st.line_chart([18000,21000,19500,26000,24500,28000,28560])
    elif page=="AI 素材庫": st.info("目前可由商品工作台產生並管理素材；雲端儲存可在下一階段加入。")
    elif page=="歷史紀錄":
        try: st.dataframe(json.loads(HISTORY_FILE.read_text(encoding="utf-8")),use_container_width=True,hide_index=True)
        except Exception: st.info("目前沒有歷史紀錄。")
    elif page=="TikTok 短影音": st.text_area("9:16 腳本", "3 秒吸睛開場\n商品特色\n使用情境\nCTA", height=180); st.text_area("即夢 Prompt", jimeng_prompt(), height=220)
    elif page=="蝦皮分潤管理": st.metric("本月分潤","NT$12,580","+18%")
    elif page=="會員管理": st.info("會員管理介面已建立。後續可加入登入、永久會員、期限與權限資料庫。")
    elif page=="管理員中心": st.warning("管理員中心目前是介面版，正式權限驗證可在下一階段加入。")
    elif page=="系統設定": st.toggle("啟用 AI 自動分析",True); st.toggle("自動保存歷史紀錄",True); st.toggle("深色科技介面",True)
    elif page=="API 設定":
        st.info("這個版本不需要 API 就能啟動。API 欄位先保留，避免因缺少金鑰造成部署失敗。")
        st.text_input("Gemini API Key",type="password"); st.text_input("Shopee API Key",type="password")
    elif page=="使用教學": st.markdown("1. 輸入商品資料 → 2. 上傳圖片 → 3. 執行 AI 工作流 → 4. 檢查標題、描述與 Prompt → 5. 確認上架資料。\n\n**注意：目前一鍵上架是模擬功能，不會真的操作蝦皮。**")


sidebar()
header()

if st.session_state.page == "Dashboard":
    dashboard()
elif st.session_state.page == "商品上架工作台":
    metrics(); workspace()
else:
    generic_page(st.session_state.page)

st.markdown("<div style='text-align:center;color:#52606e;font-size:10px;padding:25px 0'>AI 蝦皮自動化 2.5 PRO ・ Streamlit Cloud Ready</div>",unsafe_allow_html=True)
xt", None)
        if not text:
            raise RuntimeError("Gemini 沒有返回文字內容。")

        st.session_state.gemini_model = GEMINI_MODEL
        st.session_state.gemini_error = ""
        return text.strip()

    except Exception as exc:
        raw = str(exc)

        if "404" in raw:
            msg = "Gemini 模型不存在或目前 API 不支援此模型（404）。"
        elif "401" in raw:
            msg = "Gemini API Key 無效（401）。"
        elif "403" in raw:
            msg = "Gemini API 權限不足（403）。"
        elif "429" in raw:
            msg = "Gemini 額度或頻率限制（429）。"
        elif "400" in raw:
            msg = "Gemini 請求格式錯誤（400）。"
        else:
            msg = f"Gemini 執行失敗：{raw}"

        st.session_state.gemini_error = msg
        raise RuntimeError(msg) from exc


# =========================================================
# Prompt
# =========================================================
SHOPEE_PROMPT_TEMPLATE = """
請輸出：
1. SEO 商品標題
2. 商品賣點 5 點
3. 完整商品描述
4. 關鍵字
5. 長尾關鍵字
6. FAQ 5 題
不得虛構品牌、規格、認證、效果、折扣或贈品。
"""

TIKTOK_PROMPT_TEMPLATE = """
請輸出：
1. 爆款標題
2. 0~3 秒 Hook
3. 15 秒口播
4. 25 秒口播
5. 貼文文案
6. Hashtags
要求前 3 秒抓住注意力，但不得使用無法證實的誇大承諾。
"""

JIMENG_25_RULES = """
上傳商品圖是商品外觀的唯一主要依據。
必須維持品牌、Logo、包裝、文字、顏色、材質、形狀、比例與細節一致。
不得重新設計包裝、改 Logo、改字、改顏色、增加不存在配件。
可改變的是場景、背景、燈光、鏡頭、景深與商業攝影氛圍。
影片預設 9:16 直式。
"""


def build_master_prompt(product):
    p = {key: str(value or "").strip() for key, value in product.items()}

    return f"""
你是「{APP_NAME}」的核心電商 AI。
請使用繁體中文。
只能根據商品圖片與使用者提供的資料回答；不確定的資訊一律寫「待確認」。

==============================
【商品資料】
==============================
商品名稱：{p.get('name')}
商品分類：{p.get('category')}
售價：{p.get('price')}
成本：{p.get('cost')}
分潤比例：{p.get('commission')}
預估月銷量：{p.get('sales')}
商品評分：{p.get('rating')}
商品連結：{p.get('url')}
商品規格：{p.get('specs')}
目標平台：{p.get('platform')}

==============================
【資料真實性規則】
==============================
1. 不得虛構品牌、Logo、規格、認證、成分、功能、價格、折扣、贈品或效果。
2. 圖片看不清楚的文字請寫「待確認」。
3. 使用者沒有提供的數據，不得自行補數字。
4. 不得把 AI 推測寫成確定事實。
5. 行銷文案可以有吸引力，但不能做無法證實的誇大承諾。

==============================
【任務一：商品辨識與 AI 選品分析】
==============================
請分析：
- 商品名稱與分類
- 圖片可確認資訊
- 待確認資訊
- 外觀、包裝、Logo、文字
- 主要賣點
- 目標客群
- 消費需求
- 市場定位
- 優勢
- 劣勢
- 短影音切入點
- 購買誘因
- 合規提醒
- 選品分數 0~100
- 市場吸引力 0~100
- 視覺吸引力 0~100
- TikTok 潛力 0~100
- 蝦皮潛力 0~100

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
{JIMENG_25_RULES}
請輸出：
- 【即夢 AI 2.5 生圖英文 Prompt】
- 【Negative Prompt】
- 【畫面繁體中文文字設計】
- 【9:16 構圖與光影建議】

==============================
【任務五：即夢 AI 2.5 商業影片 Prompt】
==============================
請輸出英文影片 Prompt，必須包含：
Opening、Middle、Camera Motion、Lighting、Product Detail、Ending Freeze。
另外輸出 Negative Prompt。

==============================
【任務六：即夢 AI 2.5 25 秒帶貨分鏡】
==============================
0~3 秒：黃金 Hook
3~8 秒：商品全貌與品質展示
8~15 秒：核心賣點與細節特寫
15~20 秒：使用情境與價值呈現
20~25 秒：CTA 與結尾定格

==============================
【任務七：最終檢查】
==============================
檢查是否有虛構資料、誇大宣稱、錯誤品牌、錯誤規格，
以及是否維持原商品圖片的一致性。

請輸出完整、可直接複製使用的 Markdown 報告。
"""


def detect_category(text):
    text = (text or "").lower()
    groups = {
        "保養美妝": ["洗面", "面膜", "乳液", "精華", "保養", "化妝", "美容", "防曬", "洗髮"],
        "3C": ["手機", "耳機", "充電", "電腦", "鍵盤", "滑鼠", "3c", "平板", "螢幕"],
        "居家生活": ["收納", "清潔", "家居", "廚房", "杯", "居家", "拖把", "用品"],
        "服飾": ["衣服", "褲", "鞋", "帽", "包", "服飾", "外套"],
        "食品": ["食品", "零食", "餅乾", "飲料", "茶", "咖啡", "水果"],
        "汽機車": ["汽車", "機車", "車用", "汽機車", "輪胎"],
    }

    for category, keywords in groups.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "其他"


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
    product_copy.pop("image_bytes", None)

    save_json(folder / "product.json", product_copy)
    (folder / "result.md").write_text(result, encoding="utf-8")

    return history_id


def list_history(limit=30):
    items = []

    for folder in sorted(HISTORY_DIR.glob("*"), reverse=True):
        if not folder.is_dir():
            continue

        product = load_json(folder / "product.json", {})
        result_file = folder / "result.md"

        items.append(
            {
                "id": folder.name,
                "product": product.get("name", "未命名"),
                "result": result_file.read_text(encoding="utf-8") if result_file.exists() else "",
            }
        )

        if len(items) >= limit:
            break

    return items


# =========================================================
# 短影音工具：Edge TTS / Pexels / FFmpeg
# =========================================================
def tool_available(name):
    return shutil.which(name) is not None


def create_tts(text, output_path):
    if not tool_available("edge-tts"):
        raise RuntimeError(
            "找不到 edge-tts。請在 requirements.txt 加入 edge-tts。"
        )

    subprocess.run(
        [
            "edge-tts",
            "--text", text,
            "--voice", "zh-TW-HsiaoChenNeural",
            "--write-media", str(output_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def download_pexels_video(keyword, output_path):
    if not PEXELS_KEY:
        raise RuntimeError("尚未設定 PEXELS_KEY。")

    try:
        import requests
    except ImportError as exc:
        raise RuntimeError("缺少 requests，請加入 requirements.txt。") from exc

    headers = {"Authorization": PEXELS_KEY}
    params = {
        "query": keyword or "product commercial",
        "orientation": "portrait",
        "per_page": 5,
    }

    response = requests.get(
        "https://api.pexels.com/videos/search",
        headers=headers,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    videos = response.json().get("videos", [])

    if not videos:
        params["query"] = "abstract product"
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        videos = response.json().get("videos", [])

    if not videos:
        raise RuntimeError("Pexels 找不到適合的影片素材。")

    files = videos[0].get("video_files", [])
    if not files:
        raise RuntimeError("Pexels 影片沒有可下載檔案。")

    portrait = [
        item for item in files
        if item.get("height", 0) >= item.get("width", 0)
    ]
    files = portrait or files
    files.sort(
        key=lambda item: item.get("width", 0) * item.get("height", 0),
        reverse=True,
    )

    video_response = requests.get(
        files[0]["link"],
        timeout=120,
    )
    video_response.raise_for_status()
    output_path.write_bytes(video_response.content)

    if output_path.stat().st_size > MAX_VIDEO_MB * 1024 * 1024:
        raise RuntimeError(f"影片超過 {MAX_VIDEO_MB}MB。")

    return output_path


def create_video(background, audio, output):
    if not tool_available("ffmpeg"):
        raise RuntimeError(
            "找不到 FFmpeg。Streamlit Cloud 需要額外安裝系統套件。"
        )

    command = [
        "ffmpeg",
        "-y",
        "-stream_loop", "-1",
        "-i", str(background),
        "-i", str(audio),
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-c:a", "aac",
        "-shortest",
        "-movflags", "+faststart",
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
# 登入頁
# =========================================================
def render_login_page():
    st.markdown(
        f'<div class="main-title">🛒 {APP_NAME}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-title">永久會員｜管理員｜Gemini 2.5 Flash｜TikTok｜即夢 AI 2.5</div>',
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["🔐 會員登入", "📝 會員註冊"])

    with login_tab:
        with st.form("login_form"):
            username = st.text_input("會員帳號", key="login_username")
            password = st.text_input("會員密碼", type="password", key="login_password")
            submitted = st.form_submit_button("登入", use_container_width=True)

        if submitted:
            ok, message = login_user(username, password)
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

        st.info(f"預設管理員帳號：admin / 密碼：{DEFAULT_ADMIN_PASSWORD}")

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("新會員帳號", key="reg_username")
            name = st.text_input("姓名 / 暱稱", key="reg_name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("設定密碼", type="password", key="reg_password")
            password2 = st.text_input("再次輸入密碼", type="password", key="reg_password2")
            submitted = st.form_submit_button("註冊永久會員", use_container_width=True)

        if submitted:
            if password != password2:
                st.error("兩次密碼不一致。")
            else:
                ok, message = create_member(
                    username,
                    password,
                    name,
                    email,
                    "member",
                    True,
         
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
