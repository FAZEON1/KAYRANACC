import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import os
from datetime import datetime, date, timedelta
from io import BytesIO

from database import (
    initialize_db, get_tum_haftalar, get_aktif_hafta,
    hafta_ekle, hafta_aktif_yap, hafta_sil,
    get_hafta_odemeler, odeme_ekle_bulk, odeme_ekle_manuel,
    odeme_durum_guncelle, odeme_sil, get_hafta_ozet,
    get_bankalar, banka_ekle, banka_guncelle, banka_sil,
    get_cekler, cek_ekle_bulk,
)
from excel_islemler import (
    excel_yukle_odeme_listesi, excel_yukle_cek_listesi,
    export_excel, create_sample_excel
)
from rapor import haftalik_excel_raporu, haftalik_html_raporu, nakit_akis_excel
from bildirim import (
    get_bildirim_ayarlari, email_gonder, baglanti_test,
    vade_bildirimi_olustur, ozet_bildirimi_olustur,
)

# ── Sayfa ayarları ──────────────────────────────────────────────────
st.set_page_config(
    page_title="KAYRANACC | Ödeme Takip",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_db()

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── GLOBAL ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.main {
    background: linear-gradient(135deg, #F0F4FF 0%, #F8FAFF 50%, #EFF6FF 100%);
    min-height: 100vh;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1629 0%, #1A2540 40%, #0F1629 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}
section[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}
section[data-testid="stSidebar"] .stRadio > label {
    color: #94A3B8 !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: .8px !important;
    text-transform: uppercase !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
    color: #CBD5E1 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    padding: 6px 8px !important;
    border-radius: 8px !important;
    transition: all .15s !important;
}
section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label:hover {
    background: rgba(255,255,255,0.07) !important;
    color: #F1F5F9 !important;
}
section[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: #F1F5F9 !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: rgba(59, 130, 246, 0.15) !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
    color: #93C5FD !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    transition: all .2s !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(59, 130, 246, 0.25) !important;
    color: #BFDBFE !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
}
section[data-testid="stSidebar"] a {
    color: #60A5FA !important;
}

/* ── METRİK KARTLARI ── */
[data-testid="metric-container"] {
    background: white !important;
    border-radius: 14px !important;
    padding: 20px 22px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04) !important;
    transition: transform .2s, box-shadow .2s !important;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: .6px !important;
    text-transform: uppercase !important;
    color: #64748B !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -.5px !important;
}

/* ── BUTONLAR ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-radius: 10px !important;
    padding: 10px 20px !important;
    transition: all .2s !important;
    letter-spacing: .1px !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #1D4ED8) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #1D4ED8, #1E40AF) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.4) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    color: #475569 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #CBD5E1 !important;
    background: #F8FAFC !important;
}

/* ── INPUT ALANLARI ── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
.stDateInput input, .stTextArea textarea {
    font-family: 'Inter', sans-serif !important;
    border-radius: 10px !important;
    border: 1.5px solid #E2E8F0 !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
    transition: border-color .2s, box-shadow .2s !important;
    background: white !important;
    color: #0F172A !important;
}
.stTextInput input:focus, .stNumberInput input:focus,
.stSelectbox select:focus, .stDateInput input:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label,
.stDateInput label, .stTextArea label {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #475569 !important;
    letter-spacing: .3px !important;
    margin-bottom: 4px !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: #334155 !important;
    background: white !important;
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    padding: 14px 18px !important;
}
.streamlit-expanderContent {
    background: #FAFBFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 16px !important;
}

/* ── DATAFRAME ── */
div[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F1F5F9 !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: #64748B !important;
    padding: 8px 18px !important;
    transition: all .2s !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #1E40AF !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── BAŞLIKLAR ── */
.baslik {
    font-family: 'Inter', sans-serif !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -1px !important;
    margin-bottom: 4px !important;
    line-height: 1.2 !important;
}
.alt-baslik {
    font-size: 14px !important;
    color: #64748B !important;
    font-weight: 400 !important;
    margin-bottom: 24px !important;
    letter-spacing: .1px !important;
}

/* ── BADGE / TAG ── */
.tag-kirmizi { background:#FEE2E2; color:#991B1B; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.3px; border:1px solid #FECACA; }
.tag-turuncu { background:#FEF3C7; color:#92400E; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.3px; border:1px solid #FDE68A; }
.tag-sari    { background:#FEF9C3; color:#854D0E; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.3px; border:1px solid #FEF08A; }
.tag-yesil   { background:#DCFCE7; color:#166534; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.3px; border:1px solid #BBF7D0; }
.tag-mavi    { background:#DBEAFE; color:#1E40AF; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:700; letter-spacing:.3px; border:1px solid #BFDBFE; }
.tag-gri     { background:#F1F5F9; color:#475569; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:600; border:1px solid #E2E8F0; }

/* ── ALERT KUTULARI ── */
.uyari-box {
    background: linear-gradient(135deg, #FFFBEB, #FEF3C7);
    border-left: 4px solid #F59E0B;
    padding: 12px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
    font-size: 13px;
    font-weight: 500;
    color: #78350F;
    box-shadow: 0 1px 4px rgba(245,158,11,0.1);
}
.info-box {
    background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
    border-left: 4px solid #3B82F6;
    padding: 12px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
    font-size: 13px;
    font-weight: 500;
    color: #1E3A8A;
    box-shadow: 0 1px 4px rgba(59,130,246,0.1);
}
.ok-box {
    background: linear-gradient(135deg, #F0FDF4, #DCFCE7);
    border-left: 4px solid #22C55E;
    padding: 12px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
    font-size: 13px;
    font-weight: 500;
    color: #14532D;
    box-shadow: 0 1px 4px rgba(34,197,94,0.1);
}
.alarm-box {
    background: linear-gradient(135deg, #FFF1F2, #FFE4E6);
    border-left: 4px solid #EF4444;
    padding: 12px 18px;
    border-radius: 0 10px 10px 0;
    margin: 8px 0;
    font-size: 13px;
    font-weight: 500;
    color: #7F1D1D;
    box-shadow: 0 1px 4px rgba(239,68,68,0.1);
}

/* ── FORM ALANLARI ── */
div[data-testid="stForm"] {
    background: white !important;
    border-radius: 16px !important;
    padding: 24px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid #F1F5F9 !important;
    margin: 20px 0 !important;
}

/* ── SUCCESS / ERROR / WARNING ── */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ── SPINNER ── */
.stSpinner > div {
    border-top-color: #3B82F6 !important;
}

/* ── MONO FONT ── */
.mono {
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important;
    letter-spacing: -.3px !important;
}

/* ── KART ── */
.pro-kart {
    background: white;
    border-radius: 16px;
    padding: 20px 24px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04);
    transition: all .2s;
    margin-bottom: 12px;
}
.pro-kart:hover {
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}

/* ── DOWNLOAD BUTON ── */
.stDownloadButton button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
}

/* ── MARKDOWN ── */
.stMarkdown p {
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    color: #334155 !important;
    line-height: 1.6 !important;
}

/* ── STREAMLIT HEADER GİZLE ── */
header[data-testid="stHeader"] {
    background: rgba(240,244,255,0.95) !important;
    backdrop-filter: blur(10px) !important;
    border-bottom: 1px solid #E2E8F0 !important;
}

/* ── DARK MODE OVERRIDE — TÜM YAZILARI ZORLA DÜZELT ── */
.stApp, .stApp * {
    color-scheme: light !important;
}
.stApp {
    background: linear-gradient(135deg, #F0F4FF 0%, #F8FAFF 50%, #EFF6FF 100%) !important;
}
/* Ana içerik yazıları */
.stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown div,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
p, span, div, label, h1, h2, h3, h4 {
    color: #0F172A !important;
}
/* Tab yazıları */
.stTabs [data-baseweb="tab"] span { color: #64748B !important; }
.stTabs [aria-selected="true"] span { color: #1E40AF !important; }
/* Info / success / warning / error kutuları */
div[data-testid="stAlert"] p { color: inherit !important; }
/* DataFrame içi */
.stDataFrame * { color: #0F172A !important; }
/* Expander */
.streamlit-expanderHeader p, .streamlit-expanderHeader span { color: #334155 !important; }
/* Selectbox, input */
.stSelectbox div, .stTextInput div, .stNumberInput div { color: #0F172A !important; }

/* ── FILE UPLOADER — KARANLIK ALAN DÜZELTMESİ ── */
[data-testid="stFileUploader"] {
    background: white !important;
    border-radius: 14px !important;
}
[data-testid="stFileUploader"] > div,
[data-testid="stFileUploader"] section,
[data-testid="stFileUploader"] section > div {
    background: white !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] section {
    border: 2px dashed #CBD5E1 !important;
    padding: 16px !important;
}
[data-testid="stFileUploader"] button {
    background: #EFF6FF !important;
    color: #1E40AF !important;
    border: 1.5px solid #BFDBFE !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small,
[data-testid="stFileUploaderDropzone"] span,
[data-testid="stFileUploaderDropzone"] p {
    color: #64748B !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: white !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 12px !important;
}

/* ── DOWNLOAD BUTONU ── */
[data-testid="stDownloadButton"] button {
    background: white !important;
    border: 1.5px solid #E2E8F0 !important;
    color: #334155 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #F8FAFC !important;
    border-color: #CBD5E1 !important;
}

/* ── SELECTBOX DROPDOWN ── */
[data-baseweb="select"] > div { background: white !important; color: #0F172A !important; }
[data-baseweb="popover"], [data-baseweb="menu"] { background: white !important; }
[data-baseweb="option"] { background: white !important; color: #0F172A !important; }
[data-baseweb="option"]:hover { background: #EFF6FF !important; }
[data-baseweb="select"] span { color: #0F172A !important; }

/* ── NUMBER / TEXT / DATE INPUT ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stDateInput"] input,
textarea {
    background: white !important;
    color: #0F172A !important;
}

/* ── CHECKBOX ── */
[data-testid="stCheckbox"] span { color: #0F172A !important; }

/* ── SIDEBAR HARİÇ TUT ── */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] label {
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] [data-testid="stFileUploader"] * {
    color: #E2E8F0 !important;
    background: rgba(255,255,255,0.08) !important;
}
</style>
""", unsafe_allow_html=True)

# ── GİRİŞ SİSTEMİ ────────────────────────────────────────────────────
def giris_kontrol():
    if "giris_yapildi" not in st.session_state:
        st.session_state.giris_yapildi = False
    if "aktif_kullanici" not in st.session_state:
        st.session_state.aktif_kullanici = ""
    return st.session_state.giris_yapildi


def giris_ekrani():
    st.markdown("""
    <div style="max-width:400px;margin:80px auto 0;background:white;border-radius:16px;
                padding:40px;box-shadow:0 4px 24px rgba(0,0,0,0.10);border:1px solid #E0E0E0;">
        <div style="font-size:28px;font-weight:800;color:#0B1437;margin-bottom:4px;">💳 KAYRANACC</div>
        <div style="font-size:13px;color:#757575;margin-bottom:24px;">Ödeme Takip Sistemi</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.form("giris_form"):
            st.markdown("### 🔐 Giriş Yap")
            kullanici = st.text_input("Kullanıcı Adı", placeholder="kullanici_adi")
            sifre = st.text_input("Şifre", type="password", placeholder="••••••••")
            giris_btn = st.form_submit_button("Giriş Yap", type="primary", use_container_width=True)

            if giris_btn:
                try:
                    kullanicilar = st.secrets.get("kullanicilar", {})
                    if not kullanicilar:
                        st.warning("⚠️ Kullanıcı ayarları yapılandırılmamış.")
                        st.code("""
# Streamlit Secrets'a ekle:
[kullanicilar]
ibrahim = "sifreniz"
""")
                        return
                    if kullanici in kullanicilar and kullanicilar[kullanici] == sifre:
                        st.session_state.giris_yapildi = True
                        st.session_state.aktif_kullanici = kullanici
                        st.rerun()
                    else:
                        st.error("❌ Kullanıcı adı veya şifre hatalı.")
                except Exception as e:
                    st.error(f"Giriş hatası: {e}")


if not giris_kontrol():
    giris_ekrani()
    st.stop()

# ── YARDIMCI FONKSİYONLAR ────────────────────────────────────────────
GUNLER = ["Pazar", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi"]

KATEGORILER = {
    "cek":   {"label": "Çek",         "oncelik": 1, "renk": "#dc2626"},
    "kredi": {"label": "Kredi",        "oncelik": 2, "renk": "#ea580c"},
    "kart":  {"label": "K.Kartı",      "oncelik": 3, "renk": "#d97706"},
    "vergi": {"label": "Vergi",        "oncelik": 4, "renk": "#7c3aed"},
    "sgk":   {"label": "SGK",          "oncelik": 5, "renk": "#0891b2"},
    "kira":  {"label": "Kira",         "oncelik": 6, "renk": "#059669"},
    "sabit": {"label": "Sabit Gider",  "oncelik": 7, "renk": "#2563eb"},
    "cari":  {"label": "Cari Hesap",   "oncelik": 8, "renk": "#be185d"},
    "diger": {"label": "Diğer",        "oncelik": 9, "renk": "#6b7280"},
}


def fmt(n):
    if n is None or (isinstance(n, float) and pd.isna(n)):
        return "-"
    return f"{float(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_tarih(s):
    if not s:
        return ""
    try:
        d = pd.to_datetime(s)
        return d.strftime("%d %B %Y")
    except Exception:
        return str(s)


def today_iso():
    return date.today().isoformat()


def tomorrow_iso():
    return (date.today() + timedelta(days=1)).isoformat()


def get_kur():
    if "kur" not in st.session_state:
        st.session_state.kur = 38.50
    return st.session_state.kur


def fetch_kur_live():
    """Birden fazla API kaynağından USD/TL kurunu çeker."""
    apis = [
        ("https://open.er-api.com/v6/latest/USD", lambda d: round(d["rates"]["TRY"], 2)),
        ("https://api.exchangerate-api.com/v4/latest/USD", lambda d: round(d["rates"]["TRY"], 2)),
        ("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json", lambda d: round(d["usd"]["try"], 2)),
        ("https://api.frankfurter.app/latest?from=USD&to=TRY", lambda d: round(d["rates"]["TRY"], 2)),
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    for url, parser in apis:
        try:
            r = requests.get(url, timeout=8, headers=headers)
            d = r.json()
            kur = parser(d)
            if kur and kur > 1:
                st.session_state.kur = kur
                return kur, True
        except Exception:
            continue
    return get_kur(), False


def get_aktif_odemeler():
    hafta = get_aktif_hafta()
    if not hafta:
        return [], None
    return get_hafta_odemeler(hafta["id"]), hafta


def vade_durumu(vade_str):
    """Vade tarihine göre alarm durumu döndürür."""
    if not vade_str:
        return "normal"
    try:
        v = pd.to_datetime(vade_str).date()
        today = date.today()
        if v < today:
            return "gecmis"
        elif v == today:
            return "bugun"
        elif v == today + timedelta(days=1):
            return "yarin"
        return "normal"
    except Exception:
        return "normal"


# ── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(37,99,235,0.15), rgba(99,102,241,0.1));
        border: 1px solid rgba(59,130,246,0.2);
        border-radius: 14px;
        padding: 18px 16px;
        margin-bottom: 16px;
        text-align: center;
    ">
        <div style="font-size:28px;margin-bottom:6px;">💳</div>
        <div style="font-size:18px;font-weight:800;color:#F1F5F9;letter-spacing:-0.5px;">KAYRANACC</div>
        <div style="font-size:11px;color:#64748B;font-weight:500;margin-top:2px;letter-spacing:.5px;">ÖDEME TAKİP SİSTEMİ</div>
    </div>
    """, unsafe_allow_html=True)

    aktif_kullanici = st.session_state.get("aktif_kullanici", "")
    if aktif_kullanici:
        st.markdown(f"""
        <div style="
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        ">
            <div style="
                width:32px;height:32px;
                background:linear-gradient(135deg,#3B82F6,#6366F1);
                border-radius:50%;
                display:flex;align-items:center;justify-content:center;
                font-size:14px;font-weight:700;color:white;flex-shrink:0;
            ">{aktif_kullanici[0].upper()}</div>
            <div>
                <div style="font-size:11px;color:#64748B;font-weight:500;">Giriş yapan</div>
                <div style="font-size:13px;color:#F1F5F9;font-weight:700;">{aktif_kullanici}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state.giris_yapildi = False
            st.session_state.aktif_kullanici = ""
            st.rerun()

    st.markdown("---")

    # Aktif hafta göster
    hafta = get_aktif_hafta()
    if hafta:
        st.markdown(f"""
        <div style="
            background: rgba(37,99,235,0.12);
            border: 1px solid rgba(59,130,246,0.25);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 12px;
        ">
            <div style="font-size:10px;color:#60A5FA;font-weight:700;letter-spacing:.5px;text-transform:uppercase;margin-bottom:3px;">📅 Aktif Hafta</div>
            <div style="font-size:12px;color:#E2E8F0;font-weight:600;line-height:1.3;">{hafta['hafta_adi']}</div>
        </div>
        """, unsafe_allow_html=True)

    sayfa = st.radio("", [
        "📊 Dashboard",
        "💳 Bu Hafta",
        "🏦 Banka Bakiyeleri",
        "💸 Nakit Akış",
        "📋 Firma Çekleri",
        "✅ Ödenenler",
        "🕐 Geçmiş",
        "📂 Veri Yükleme",
        "📄 Raporlar",
        "🔔 Bildirim Ayarları",
    ], label_visibility="collapsed")

    st.markdown("---")

    # Kur paneli
    st.markdown("**💱 USD/TL Kur**")

    if "kur" not in st.session_state:
        st.session_state.kur = 38.50

    yeni_kur = st.number_input(
        "",
        value=float(st.session_state.kur),
        step=0.01,
        min_value=1.0,
        format="%.2f",
        label_visibility="collapsed",
    )
    st.session_state.kur = yeni_kur

    if st.button("🔄 Güncel Kur", use_container_width=True):
        with st.spinner("Alınıyor..."):
            kur_cekilen, basarili = fetch_kur_live()
        if basarili:
            st.session_state.kur = kur_cekilen
            st.success(f"✅ {kur_cekilen} ₺")
            st.rerun()
        else:
            st.error("❌ Bağlanamadı, manuel girin.")

    st.markdown(f"<small>🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}</small>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# 1) DASHBOARD
# ════════════════════════════════════════════════════════════════════
if sayfa == "📊 Dashboard":
    st.markdown('<div class="baslik">📊 KAYRANACC — Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">Haftalık ödeme durumu ve finansal özet</div>', unsafe_allow_html=True)

    kur = get_kur()
    odemeler, hafta = get_aktif_odemeler()
    bankalar = get_bankalar()

    if not odemeler:
        st.info("📂 Henüz veri yüklenmemiş. **'Veri Yükleme'** sekmesinden Excel dosyanızı yükleyin veya manuel ödeme ekleyin.")
        st.stop()

    # Alarmlar
    alarmlar = [o for o in odemeler if o["durum"] == "bekliyor" and vade_durumu(o.get("vade")) in ("bugun", "yarin", "gecmis")]
    bugun_alarmlar = [o for o in alarmlar if vade_durumu(o.get("vade")) == "bugun"]
    yarin_alarmlar = [o for o in alarmlar if vade_durumu(o.get("vade")) == "yarin"]
    gecmis_alarmlar = [o for o in alarmlar if vade_durumu(o.get("vade")) == "gecmis"]

    if gecmis_alarmlar:
        isimler = ", ".join(o["firma"] for o in gecmis_alarmlar[:3])
        st.error(f"🚨 **GECİKMİŞ ÖDEME!** {len(gecmis_alarmlar)} ödeme vadesi geçmiş: {isimler}")
    if bugun_alarmlar:
        isimler = ", ".join(o["firma"] for o in bugun_alarmlar[:3])
        st.warning(f"⚠️ **BUGÜN VADELİ:** {len(bugun_alarmlar)} ödeme — {isimler}")
    if yarin_alarmlar:
        isimler = ", ".join(o["firma"] for o in yarin_alarmlar[:3])
        st.info(f"📅 **YARIN VADELİ:** {len(yarin_alarmlar)} ödeme — {isimler}")

    # Özet metrikler
    tl_toplam = sum(o["tutar_tl"] or 0 for o in odemeler)
    usd_toplam = sum(o["tutar_usd"] or 0 for o in odemeler)
    odendi_tl = sum(o["tutar_tl"] or 0 for o in odemeler if o["durum"] == "odendi")
    odendi_usd = sum(o["tutar_usd"] or 0 for o in odemeler if o["durum"] == "odendi")
    bekleyen_tl = tl_toplam - odendi_tl
    bekleyen_usd = usd_toplam - odendi_usd
    odendi_cnt = sum(1 for o in odemeler if o["durum"] == "odendi")
    banka_tl = sum(b["bakiye"] for b in bankalar if b["para_birimi"] == "TL")
    banka_usd = sum(b["bakiye"] for b in bankalar if b["para_birimi"] == "USD")
    hafta_sonu_tl = banka_tl - bekleyen_tl - (bekleyen_usd * kur)
    ilerleme_pct = int((odendi_cnt / len(odemeler)) * 100) if odemeler else 0

    # ── Profesyonel Metrik Kartları (Koyu Stil) ──
    nakit_bg    = "#064E3B" if hafta_sonu_tl >= 0 else "#7F1D1D"
    nakit_renk  = "#34D399" if hafta_sonu_tl >= 0 else "#FCA5A5"
    nakit_label = "✅ Hafta Sonu Kalan" if hafta_sonu_tl >= 0 else "⚠️ Nakit Açığı"
    nakit_alt   = "Tahmini bakiye" if hafta_sonu_tl >= 0 else "Tahmini açık"

    st.markdown(f"""
    <style>
    .kart-grid {{
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }}
    .kart {{
        background: #1E293B;
        border-radius: 14px;
        padding: 22px 20px 18px;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        text-align: center;
    }}
    .kart-label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: #94A3B8;
        margin-bottom: 14px;
    }}
    .kart-deger {{
        font-size: 24px;
        font-weight: 800;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }}
    .kart-alt {{
        font-size: 12px;
        margin-top: 10px;
        color: #64748B;
        font-weight: 500;
    }}
    </style>

    <div class="kart-grid">

      <div class="kart">
        <div class="kart-label">Toplam TL</div>
        <div class="kart-deger" style="color:#60A5FA">₺{fmt(tl_toplam)}</div>
        <div class="kart-alt">Bu haftaki yükümlülük</div>
      </div>

      <div class="kart">
        <div class="kart-label">Toplam USD</div>
        <div class="kart-deger" style="color:#A78BFA">${fmt(usd_toplam)}</div>
        <div class="kart-alt">≈ ₺{fmt(usd_toplam * kur)}</div>
      </div>

      <div class="kart">
        <div class="kart-label">İlerleme</div>
        <div class="kart-deger" style="color:#F1F5F9">{odendi_cnt} <span style="font-size:16px;color:#475569;font-weight:600">/ {len(odemeler)}</span></div>
        <div style="background:#0F172A;border-radius:6px;height:6px;margin-top:12px;overflow:hidden">
          <div style="background:linear-gradient(90deg,#22C55E,#16A34A);height:100%;width:{ilerleme_pct}%"></div>
        </div>
        <div class="kart-alt">%{ilerleme_pct} tamamlandı</div>
      </div>

      <div class="kart">
        <div class="kart-label">Bekleyen TL</div>
        <div class="kart-deger" style="color:#FBBF24">₺{fmt(bekleyen_tl)}</div>
        <div class="kart-alt">Ödenmesi gereken</div>
      </div>

      <div class="kart" style="background:{nakit_bg};border-color:rgba(255,255,255,0.12)">
        <div class="kart-label" style="color:rgba(255,255,255,0.6)">{nakit_label}</div>
        <div class="kart-deger" style="color:{nakit_renk}">₺{fmt(abs(hafta_sonu_tl))}</div>
        <div class="kart-alt" style="color:rgba(255,255,255,0.4)">{nakit_alt}</div>
      </div>

    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Kategori dağılımı ve durum grafikleri
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Kategori Bazında Ödeme Dağılımı**")
        kat_data = {}
        for o in odemeler:
            kat = o.get("kategori") or "diger"
            label = KATEGORILER.get(kat, {}).get("label", "Diğer")
            tl = (o.get("tutar_tl") or 0) + (o.get("tutar_usd") or 0) * kur
            kat_data[label] = kat_data.get(label, 0) + tl

        if kat_data:
            fig = go.Figure(go.Pie(
                labels=list(kat_data.keys()),
                values=list(kat_data.values()),
                hole=0.5,
                marker_colors=[KATEGORILER.get(k, {}).get("renk", "#888")
                                for k in [next((key for key, v in KATEGORILER.items() if v["label"] == lab), "diger")
                                          for lab in kat_data.keys()]],
                textfont=dict(family="Inter, sans-serif", size=12),
                hovertemplate="<b>%{label}</b><br>₺%{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(
                height=320, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="white", plot_bgcolor="white",
                showlegend=True,
                legend=dict(font=dict(family="Inter, sans-serif", size=11), orientation="v"),
                font=dict(family="Inter, sans-serif"),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**📈 Ödeme Durumu**")
        odendi_tutar = sum((o.get("tutar_tl") or 0) + (o.get("tutar_usd") or 0) * kur
                           for o in odemeler if o["durum"] == "odendi")
        bekleyen_tutar = sum((o.get("tutar_tl") or 0) + (o.get("tutar_usd") or 0) * kur
                             for o in odemeler if o["durum"] == "bekliyor")
        fig2 = go.Figure(go.Pie(
            labels=["Ödendi", "Bekliyor"],
            values=[odendi_tutar, bekleyen_tutar],
            hole=0.55,
            marker_colors=["#22C55E", "#F59E0B"],
            textfont=dict(family="Inter, sans-serif", size=12),
            hovertemplate="<b>%{label}</b><br>₺%{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig2.add_annotation(
            text=f"%{ilerleme_pct}", x=0.5, y=0.5,
            font=dict(size=22, family="JetBrains Mono, monospace", color="#0F172A"),
            showarrow=False,
        )
        fig2.update_layout(
            height=320, margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="white", plot_bgcolor="white",
            font=dict(family="Inter, sans-serif"),
            legend=dict(font=dict(family="Inter, sans-serif", size=12)),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Günlük ödeme takvimi özeti
    st.markdown("**📅 Günlük Ödeme Takvimi**")
    from collections import defaultdict
    by_day = defaultdict(list)
    for o in odemeler:
        day = (o.get("vade") or "")[:10] or "?"
        by_day[day].append(o)

    tablo_rows = []
    for day in sorted(by_day.keys()):
        try:
            d = pd.to_datetime(day)
            gun_adi = GUNLER[d.dayofweek + 1] if d.dayofweek < 6 else GUNLER[0]
            tarih_str = d.strftime("%d.%m.%Y")
        except Exception:
            gun_adi = ""
            tarih_str = day

        gun_odemeler = by_day[day]
        gun_tl = sum(o.get("tutar_tl") or 0 for o in gun_odemeler)
        gun_usd = sum(o.get("tutar_usd") or 0 for o in gun_odemeler)
        gun_odendi = sum(1 for o in gun_odemeler if o["durum"] == "odendi")
        vd = vade_durumu(day)

        tablo_rows.append({
            "Gün": gun_adi,
            "Tarih": tarih_str,
            "Ödeme Sayısı": len(gun_odemeler),
            "Ödendi": gun_odendi,
            "Bekliyor": len(gun_odemeler) - gun_odendi,
            "Tutar TL (₺)": f"₺{fmt(gun_tl)}" if gun_tl else "-",
            "Tutar USD ($)": f"${fmt(gun_usd)}" if gun_usd else "-",
            "Durum": "⏰ BUGÜN" if vd == "bugun" else ("📅 YARIN" if vd == "yarin" else ("🚨 GECİKMİŞ" if vd == "gecmis" else "—")),
        })

    df_tablo = pd.DataFrame(tablo_rows)
    st.dataframe(df_tablo, use_container_width=True, hide_index=True, height=280)


# ════════════════════════════════════════════════════════════════════
# 2) BU HAFTA
# ════════════════════════════════════════════════════════════════════
elif sayfa == "💳 Bu Hafta":
    st.markdown('<div class="baslik">💳 Bu Hafta Ödemeleri</div>', unsafe_allow_html=True)

    kur = get_kur()
    odemeler, hafta = get_aktif_odemeler()
    bankalar = get_bankalar()

    # Manuel ödeme ekleme formu
    with st.expander("➕ Manuel Ödeme Ekle"):
        with st.form("manuel_form"):
            col1, col2 = st.columns(2)
            with col1:
                firma = st.text_input("Firma / Kişi Adı *")
                aciklama = st.text_input("Açıklama")
                vade = st.date_input("Vade Tarihi *", value=date.today())
            with col2:
                kategori = st.selectbox("Kategori", list(KATEGORILER.keys()),
                                        format_func=lambda k: KATEGORILER[k]["label"])
                tutar_tl = st.number_input("Tutar TL (₺)", min_value=0.0, step=100.0)
                tutar_usd = st.number_input("Tutar USD ($)", min_value=0.0, step=100.0)

            ekle_btn = st.form_submit_button("➕ Ekle", type="primary")
            if ekle_btn:
                if not firma:
                    st.error("Firma adı zorunludur.")
                elif tutar_tl == 0 and tutar_usd == 0:
                    st.error("En az bir tutar girilmelidir.")
                else:
                    if not hafta:
                        hafta_id = hafta_ekle("Manuel Girişler")
                    else:
                        hafta_id = hafta["id"]
                    odeme_ekle_manuel(
                        hafta_id, firma, aciklama,
                        vade.isoformat(),
                        tutar_tl if tutar_tl > 0 else None,
                        tutar_usd if tutar_usd > 0 else None,
                        kategori
                    )
                    st.success(f"✅ {firma} ödeme olarak eklendi.")
                    st.rerun()

    if not odemeler:
        st.info("Veri yok. Veri Yükleme sekmesinden Excel yükleyin veya manuel ödeme ekleyin.")
        st.stop()

    # Alarmlar
    for o in odemeler:
        vd = vade_durumu(o.get("vade"))
        if o["durum"] == "bekliyor" and vd in ("bugun", "gecmis"):
            renk = "#FFCCCC" if vd == "gecmis" else "#FFF3E0"
            emoji = "🚨" if vd == "gecmis" else "⚠️"
            etiket = "GECİKMİŞ" if vd == "gecmis" else "BUGÜN"
            tl_str = f"₺{fmt(o['tutar_tl'])}" if o.get("tutar_tl") else f"${fmt(o['tutar_usd'])}"
            st.markdown(f'<div class="alarm-box">{emoji} <b>{etiket}</b> — {o["firma"]} — {tl_str}</div>', unsafe_allow_html=True)

    # Özet
    tl_toplam = sum(o.get("tutar_tl") or 0 for o in odemeler)
    usd_toplam = sum(o.get("tutar_usd") or 0 for o in odemeler)
    odendi_tl = sum(o.get("tutar_tl") or 0 for o in odemeler if o["durum"] == "odendi")
    odendi_usd = sum(o.get("tutar_usd") or 0 for o in odemeler if o["durum"] == "odendi")
    odendi_cnt = sum(1 for o in odemeler if o["durum"] == "odendi")
    kalan_tl = tl_toplam - odendi_tl
    ilerleme = int((odendi_cnt / len(odemeler)) * 100) if odemeler else 0

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px">
      <div style="background:#1E2A3A;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748B;margin-bottom:12px">Toplam TL</div>
        <div style="font-size:26px;font-weight:800;color:#60A5FA;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">₺{fmt(tl_toplam)}</div>
        <div style="font-size:11px;margin-top:8px;color:#475569">Ödendi: ₺{fmt(odendi_tl)}</div>
      </div>
      <div style="background:#1E2A3A;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748B;margin-bottom:12px">Toplam USD</div>
        <div style="font-size:26px;font-weight:800;color:#818CF8;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">${fmt(usd_toplam)}</div>
        <div style="font-size:11px;margin-top:8px;color:#475569">Ödendi: ${fmt(odendi_usd)}</div>
      </div>
      <div style="background:#1E2A3A;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748B;margin-bottom:12px">İlerleme</div>
        <div style="font-size:26px;font-weight:800;color:#F1F5F9;font-family:'JetBrains Mono',monospace">{odendi_cnt} <span style="font-size:15px;color:#475569">/ {len(odemeler)}</span></div>
        <div style="background:#0F172A;border-radius:6px;height:6px;margin-top:10px;overflow:hidden">
          <div style="background:linear-gradient(90deg,#22C55E,#16A34A);height:100%;width:{ilerleme}%"></div>
        </div>
      </div>
      <div style="background:#1a3a2a;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:rgba(255,255,255,0.4);margin-bottom:12px">Kalan TL</div>
        <div style="font-size:26px;font-weight:800;color:#4ade80;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">₺{fmt(kalan_tl)}</div>
        <div style="font-size:11px;margin-top:8px;color:rgba(255,255,255,0.3)">Ödenmesi gereken</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Gün bazında grupla
    from collections import defaultdict
    by_day = defaultdict(list)
    for o in odemeler:
        day = (o.get("vade") or "")[:10] or "?"
        by_day[day].append(o)

    # Öncelik sırala
    def oncelik_sirala(o):
        kat = o.get("kategori") or "diger"
        return KATEGORILER.get(kat, {"oncelik": 9})["oncelik"]

    for day in sorted(by_day.keys()):
        try:
            d = pd.to_datetime(day)
            gun_adi = GUNLER[d.dayofweek + 1] if d.dayofweek < 6 else GUNLER[0]
            tarih_str = d.strftime("%d %B %Y")
        except Exception:
            gun_adi = ""
            tarih_str = day

        gun_odemeler = sorted(by_day[day], key=oncelik_sirala)
        gun_tl = sum(o.get("tutar_tl") or 0 for o in gun_odemeler)
        gun_usd = sum(o.get("tutar_usd") or 0 for o in gun_odemeler)
        vd = vade_durumu(day)

        renk_header = "#EFF6FF" if vd == "bugun" else ("#FFFBEB" if vd == "yarin" else ("#FEF2F2" if vd == "gecmis" else "#F8F9FB"))

        etiket = ""
        if vd == "bugun":
            etiket = " 🔵 BUGÜN"
        elif vd == "yarin":
            etiket = " 🟡 YARIN"
        elif vd == "gecmis":
            etiket = " 🔴 GECİKMİŞ"

        with st.expander(f"**{gun_adi}{etiket}** — {tarih_str}  |  {'₺' + fmt(gun_tl) if gun_tl else ''}  {'$' + fmt(gun_usd) if gun_usd else ''}  ({len(gun_odemeler)} ödeme)", expanded=(vd in ("bugun", "yarin", "gecmis"))):
            for o in gun_odemeler:
                kat = o.get("kategori") or "diger"
                kat_info = KATEGORILER.get(kat, KATEGORILER["diger"])
                is_odendi = o["durum"] == "odendi"

                col1, col2, col3, col4, col5 = st.columns([0.3, 3, 2, 2, 2])

                with col1:
                    st.markdown(
                        f'<div style="width:8px;height:40px;background:{kat_info["renk"]};'
                        f'border-radius:4px;margin-top:4px;opacity:{"0.3" if is_odendi else "1"}"></div>',
                        unsafe_allow_html=True
                    )

                with col2:
                    opacity = "opacity:0.4;" if is_odendi else ""
                    st.markdown(
                        f'<div style="{opacity}"><b style="font-size:13px">{o["firma"]}</b><br>'
                        f'<small style="color:#6b7280">{o.get("aciklama") or ""}</small></div>',
                        unsafe_allow_html=True
                    )

                with col3:
                    st.markdown(
                        f'<span style="background:{kat_info["renk"]};color:white;font-size:11px;'
                        f'padding:2px 8px;border-radius:10px;font-weight:600">{kat_info["label"]}</span>',
                        unsafe_allow_html=True
                    )

                with col4:
                    if o.get("tutar_tl"):
                        st.markdown(f'<b style="color:#065F46;font-size:14px">₺{fmt(o["tutar_tl"])}</b>', unsafe_allow_html=True)
                    elif o.get("tutar_usd"):
                        st.markdown(f'<b style="color:#1E40AF;font-size:14px">${fmt(o["tutar_usd"])}</b>', unsafe_allow_html=True)

                with col5:
                    if is_odendi:
                        if st.button(f"↩ Geri Al", key=f"geri_{o['id']}"):
                            odeme_durum_guncelle(o["id"], "bekliyor")
                            st.rerun()
                    else:
                        banka_options = {f"{b['hesap_adi']} ({b['para_birimi']})": b["id"] for b in bankalar}
                        banka_options = {"— Seçiniz —": None} | banka_options
                        sec_banka = st.selectbox("", list(banka_options.keys()),
                                                 key=f"banka_{o['id']}", label_visibility="collapsed")
                        if st.button(f"✅ Ödendi", key=f"od_{o['id']}", type="primary"):
                            banka_id = banka_options.get(sec_banka)
                            odeme_durum_guncelle(o["id"], "odendi", banka_id, kur)
                            st.rerun()

                st.divider()

    # Export butonları
    col1, col2 = st.columns(2)
    with col1:
        excel_buf = export_excel(odemeler, hafta["hafta_adi"] if hafta else "", kur)
        st.download_button(
            "📥 Excel İndir",
            data=excel_buf,
            file_name=f"odeme_listesi_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════════
# 3) BANKA BAKİYELERİ
# ════════════════════════════════════════════════════════════════════
elif sayfa == "🏦 Banka Bakiyeleri":
    st.markdown('<div class="baslik">🏦 Banka Bakiyeleri</div>', unsafe_allow_html=True)

    kur = get_kur()
    bankalar = get_bankalar()
    odemeler, hafta = get_aktif_odemeler()

    bekleyen_tl = sum(o.get("tutar_tl") or 0 for o in odemeler if o["durum"] == "bekliyor")
    bekleyen_usd = sum(o.get("tutar_usd") or 0 for o in odemeler if o["durum"] == "bekliyor")

    # Hesap kartları
    if bankalar:
        cols = st.columns(min(len(bankalar), 3))
        for i, b in enumerate(bankalar):
            sym = "$" if b["para_birimi"] == "USD" else ("€" if b["para_birimi"] == "EUR" else "₺")
            with cols[i % 3]:
                if b["para_birimi"] == "TL":
                    net = b["bakiye"] - bekleyen_tl - (bekleyen_usd * kur)
                    net_str = f"{'🟢' if net >= 0 else '🔴'} Hafta sonu: ₺{fmt(net)}"
                elif b["para_birimi"] == "USD":
                    net = b["bakiye"] - bekleyen_usd
                    net_str = f"{'🟢' if net >= 0 else '🔴'} Hafta sonu: ${fmt(net)}"
                else:
                    net_str = ""

                st.markdown(f"""
                <div style="background:white;border:1.5px solid #E5E7EB;border-radius:12px;
                            padding:20px;box-shadow:0 1px 4px rgba(0,0,0,0.07);margin-bottom:12px">
                    <div style="font-size:11px;color:#9CA3AF;font-weight:700;text-transform:uppercase;
                                letter-spacing:.5px;margin-bottom:8px">{b['hesap_adi']}</div>
                    <div style="font-size:28px;font-weight:700;color:#0F1117;font-family:monospace">
                        {sym}{fmt(b['bakiye'])}
                        <span style="font-size:12px;color:#9CA3AF;margin-left:4px">{b['para_birimi']}</span>
                    </div>
                    <div style="font-size:12px;color:#6B7280;margin-top:8px">{net_str}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Henüz banka hesabı eklenmemiş.")

    st.markdown("---")

    # Hesap ekle / düzenle
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**➕ Yeni Hesap Ekle**")
        with st.form("banka_ekle"):
            hesap_adi = st.text_input("Hesap Adı", placeholder="Örn: YKB TL Hesabı")
            bakiye = st.number_input("Bakiye", min_value=0.0, step=1000.0)
            para_birimi = st.selectbox("Para Birimi", ["TL", "USD", "EUR"])
            if st.form_submit_button("➕ Ekle", type="primary"):
                if hesap_adi:
                    banka_ekle(hesap_adi, bakiye, para_birimi)
                    st.success("✅ Hesap eklendi.")
                    st.rerun()

    with col2:
        if bankalar:
            st.markdown("**✏️ Hesap Düzenle / Sil**")
            secim = st.selectbox("Hesap seçin", [f"{b['hesap_adi']} ({b['para_birimi']})" for b in bankalar])
            sec_idx = [f"{b['hesap_adi']} ({b['para_birimi']})" for b in bankalar].index(secim)
            sec_banka = bankalar[sec_idx]

            with st.form("banka_duzenle"):
                yeni_ad = st.text_input("Hesap Adı", value=sec_banka["hesap_adi"])
                yeni_bakiye = st.number_input("Bakiye", value=float(sec_banka["bakiye"]), step=1000.0)
                yeni_pb = st.selectbox("Para Birimi", ["TL", "USD", "EUR"],
                                       index=["TL", "USD", "EUR"].index(sec_banka["para_birimi"]))
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("💾 Kaydet", type="primary"):
                        banka_guncelle(sec_banka["id"], yeni_ad, yeni_bakiye, yeni_pb)
                        st.success("✅ Güncellendi.")
                        st.rerun()
                with col_b:
                    if st.form_submit_button("🗑 Sil"):
                        banka_sil(sec_banka["id"])
                        st.success("Silindi.")
                        st.rerun()


# ════════════════════════════════════════════════════════════════════
# 4) NAKİT AKIŞ
# ════════════════════════════════════════════════════════════════════
elif sayfa == "💸 Nakit Akış":
    st.markdown('<div class="baslik">💸 Nakit Akış Analizi</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">Bekleyen ödemeler baz alınmıştır</div>', unsafe_allow_html=True)

    kur = get_kur()
    odemeler, hafta = get_aktif_odemeler()
    bankalar = get_bankalar()

    if not odemeler:
        st.info("Veri yok.")
        st.stop()

    banka_tl = sum(b["bakiye"] for b in bankalar if b["para_birimi"] == "TL")
    banka_usd = sum(b["bakiye"] for b in bankalar if b["para_birimi"] == "USD")

    from collections import defaultdict
    by_day = defaultdict(list)
    for o in odemeler:
        if o["durum"] == "bekliyor":
            day = (o.get("vade") or "")[:10] or "?"
            by_day[day].append(o)

    kum_tl = 0
    kum_usd = 0
    tablo_rows = []

    for day in sorted(by_day.keys()):
        gun_tl = sum(o.get("tutar_tl") or 0 for o in by_day[day])
        gun_usd = sum(o.get("tutar_usd") or 0 for o in by_day[day])
        kum_tl += gun_tl
        kum_usd += gun_usd
        kalan = banka_tl - kum_tl - (kum_usd * kur)

        tablo_rows.append({
            "Tarih": day,
            "Günlük TL (₺)": gun_tl or None,
            "Günlük USD ($)": gun_usd or None,
            "Kümülatif TL (₺)": kum_tl,
            "Kümülatif USD ($)": kum_usd,
            "TL Bakiye Kalan (₺)": kalan,
            "_kalan": kalan,
        })

    net_tl = banka_tl - kum_tl - (kum_usd * kur)
    tablo_rows.append({
        "Tarih": "TOPLAM",
        "Günlük TL (₺)": kum_tl,
        "Günlük USD ($)": kum_usd,
        "Kümülatif TL (₺)": kum_tl,
        "Kümülatif USD ($)": kum_usd,
        "TL Bakiye Kalan (₺)": net_tl,
        "_kalan": net_tl,
    })

    df_nakit = pd.DataFrame(tablo_rows)

    def nakit_rengi(row):
        k = row.get("_kalan", 0)
        if row["Tarih"] == "TOPLAM":
            return ["background-color:#C8E6C9" if k >= 0 else "background-color:#FFCCCC"] * len(row)
        return ["background-color:#FEF2F2" if k < 0 else ""] * len(row)

    goster = ["Tarih", "Günlük TL (₺)", "Günlük USD ($)", "Kümülatif TL (₺)", "Kümülatif USD ($)", "TL Bakiye Kalan (₺)"]
    styled = df_nakit[goster + ["_kalan"]].style.apply(nakit_rengi, axis=1)
    styled = styled.hide(axis="columns", subset=["_kalan"])
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Grafik
    df_grafik = pd.DataFrame([r for r in tablo_rows if r["Tarih"] != "TOPLAM"])
    if len(df_grafik) > 1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_grafik["Tarih"],
            y=df_grafik["Günlük TL (₺)"].fillna(0),
            name="Günlük TL Ödemesi",
            marker_color="#2D6BE4",
        ))
        fig.add_trace(go.Scatter(
            x=df_grafik["Tarih"],
            y=df_grafik["TL Bakiye Kalan (₺)"],
            name="Kalan Bakiye",
            mode="lines+markers",
            line=dict(color="#059669", width=3),
            marker=dict(size=8),
            yaxis="y2",
        ))
        fig.update_layout(
            title="Günlük Ödeme ve Kalan Bakiye",
            xaxis_title="Tarih",
            yaxis_title="Ödeme TL (₺)",
            yaxis2=dict(title="Kalan Bakiye (₺)", overlaying="y", side="right"),
            height=380, plot_bgcolor="white", paper_bgcolor="white",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
# 5) FİRMA ÇEKLERİ
# ════════════════════════════════════════════════════════════════════
elif sayfa == "📋 Firma Çekleri":
    st.markdown('<div class="baslik">📋 Firma Çekleri</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">TL ve USD bazında çek takibi</div>', unsafe_allow_html=True)

    def cek_tablo(cekler, cur):
        if not cekler:
            st.info(f"{cur} çeki bulunamadı.")
            return
        sym = "$" if cur == "USD" else "₺"
        rows = []
        for c in cekler:
            vd = vade_durumu(c.get("vade"))
            rows.append({
                "Ref No": c.get("ref_no") or c.get("ref", ""),
                "Vade": fmt_tarih(c.get("vade")),
                f"Meblağ ({sym})": c.get("meblagh", 0),
                f"Kalan ({sym})": c.get("kalan", 0),
                "Alıcı": c.get("alici", ""),
                "Durum": c.get("durum", "Bekliyor"),
                "_vd": vd,
            })
        df = pd.DataFrame(rows)
        def renk(row):
            vd = row.get("_vd", "")
            if vd == "gecmis": return ["background-color:#FFCCCC"] * len(row)
            if vd == "bugun":  return ["background-color:#FFF3E0"] * len(row)
            if row.get("Durum") == "Ödendi": return ["background-color:#D1FAE5"] * len(row)
            return [""] * len(row)
        goster = [k for k in rows[0].keys() if k != "_vd"]
        styled = df[goster + ["_vd"]].style.apply(renk, axis=1).hide(axis="columns", subset=["_vd"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

    tab1, tab2 = st.tabs(["💴 TL Çekleri", "💵 USD Çekleri"])
    with tab1:
        cek_tablo(get_cekler("TL"), "TL")
    with tab2:
        cek_tablo(get_cekler("USD"), "USD")


# ════════════════════════════════════════════════════════════════════
# 6) ÖDENENLEr
# ════════════════════════════════════════════════════════════════════
elif sayfa == "✅ Ödenenler":
    st.markdown('<div class="baslik">✅ Ödenen Ödemeler</div>', unsafe_allow_html=True)

    odemeler, hafta = get_aktif_odemeler()
    odenenler = [o for o in odemeler if o["durum"] == "odendi"]

    if not odenenler:
        st.info("Bu haftada henüz ödendi olarak işaretlenmiş ödeme yok.")
        st.stop()

    tl_top = sum(o.get("tutar_tl") or 0 for o in odenenler)
    usd_top = sum(o.get("tutar_usd") or 0 for o in odenenler)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px">
      <div style="background:#1a3a2a;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:rgba(255,255,255,0.4);margin-bottom:12px">Ödenen TL</div>
        <div style="font-size:28px;font-weight:800;color:#4ade80;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">₺{fmt(tl_top)}</div>
      </div>
      <div style="background:#1a2a3a;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:rgba(255,255,255,0.4);margin-bottom:12px">Ödenen USD</div>
        <div style="font-size:28px;font-weight:800;color:#60A5FA;font-family:'JetBrains Mono',monospace;letter-spacing:-1px">${fmt(usd_top)}</div>
      </div>
      <div style="background:#1E2A3A;border-radius:14px;padding:20px 18px;border:1px solid rgba(255,255,255,0.07);
                  box-shadow:0 4px 20px rgba(0,0,0,0.25);text-align:center">
        <div style="font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:#64748B;margin-bottom:12px">Ödeme Adedi</div>
        <div style="font-size:28px;font-weight:800;color:#F1F5F9;font-family:'JetBrains Mono',monospace">{len(odenenler)}</div>
        <div style="font-size:11px;margin-top:8px;color:#475569">tamamlanan ödeme</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    rows = []
    for o in sorted(odenenler, key=lambda x: x.get("vade") or ""):
        kat = KATEGORILER.get(o.get("kategori") or "diger", KATEGORILER["diger"])
        rows.append({
            "Firma": o["firma"],
            "Açıklama": o.get("aciklama") or "",
            "Kategori": kat["label"],
            "Vade": fmt_tarih(o.get("vade")),
            "Tutar TL (₺)": o.get("tutar_tl"),
            "Tutar USD ($)": o.get("tutar_usd"),
            "Ödendi Tarihi": o.get("odendi_tarih") or "",
            "ID": o["id"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True, height=400)

    st.markdown("---")
    st.markdown("**Geri almak istediğin ödeme:**")
    geri_sec = st.selectbox("Ödeme seç", [f"{o['firma']} — {fmt_tarih(o.get('vade'))}" for o in odenenler])
    if st.button("↩ Geri Al", type="secondary"):
        idx = [f"{o['firma']} — {fmt_tarih(o.get('vade'))}" for o in odenenler].index(geri_sec)
        odeme_durum_guncelle(odenenler[idx]["id"], "bekliyor")
        st.success("Geri alındı.")
        st.rerun()


# ════════════════════════════════════════════════════════════════════
# 7) GEÇMİŞ
# ════════════════════════════════════════════════════════════════════
elif sayfa == "🕐 Geçmiş":
    st.markdown('<div class="baslik">🕐 Geçmiş Haftalar</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">Geçmiş haftaya tıklayarak o haftanın ödemelerini görüntüleyin</div>', unsafe_allow_html=True)

    haftalar = get_tum_haftalar()

    if not haftalar:
        st.info("Henüz geçmiş hafta yok.")
        st.stop()

    aktif = get_aktif_hafta()
    aktif_id = aktif["id"] if aktif else None

    for h in haftalar:
        ozet = get_hafta_ozet(h["id"])
        is_aktif = h["id"] == aktif_id

        renk = "#EFF6FF" if is_aktif else "white"
        border = "2px solid #2563EB" if is_aktif else "1px solid #E5E7EB"

        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"""
            <div style="background:{renk};border:{border};border-radius:10px;
                        padding:14px 18px;margin-bottom:8px;cursor:pointer">
                <div style="font-size:15px;font-weight:700;color:#0F1117">
                    {h['hafta_adi']}
                    {'<span style="background:#2563EB;color:white;font-size:10px;padding:2px 8px;border-radius:4px;margin-left:8px">AKTİF</span>' if is_aktif else ''}
                </div>
                <div style="font-size:12px;color:#6B7280;margin-top:4px">
                    {ozet['toplam']} ödeme · {ozet['odendi']}/{ozet['toplam']} ödendi · 
                    Yüklendi: {h['yuklendi_tarih']}
                </div>
                <div style="margin-top:6px">
                    <span class="tag-yesil">₺{fmt(ozet['tl_toplam'])}</span>&nbsp;
                    <span class="tag-mavi">${fmt(ozet['usd_toplam'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if not is_aktif:
                if st.button("📂 Aç", key=f"ac_{h['id']}"):
                    hafta_aktif_yap(h["id"])
                    st.success(f"'{h['hafta_adi']}' aktif yapıldı.")
                    st.rerun()
            if st.button("🗑 Sil", key=f"sil_{h['id']}"):
                hafta_sil(h["id"])
                st.success("Silindi.")
                st.rerun()


# ════════════════════════════════════════════════════════════════════
# 8) VERİ YÜKLEME
# ════════════════════════════════════════════════════════════════════
elif sayfa == "📂 Veri Yükleme":
    st.markdown('<div class="baslik">📂 Veri Yükleme</div>', unsafe_allow_html=True)

    # Son yüklenenler (Recents)
    haftalar = get_tum_haftalar()
    if haftalar:
        st.markdown("### 🕐 Son Yüklenenler")
        aktif = get_aktif_hafta()
        aktif_id = aktif["id"] if aktif else None

        cols = st.columns(min(len(haftalar), 4))
        for i, h in enumerate(haftalar[:8]):
            ozet = get_hafta_ozet(h["id"])
            is_aktif = h["id"] == aktif_id
            with cols[i % 4]:
                renk = "#EFF6FF" if is_aktif else "white"
                border = "2px solid #2563EB" if is_aktif else "1px solid #E5E7EB"
                st.markdown(f"""
                <div style="background:{renk};border:{border};border-radius:10px;
                            padding:12px 14px;margin-bottom:10px;min-height:100px">
                    <div style="font-size:12px;font-weight:700;color:#0F1117;line-height:1.3">
                        {h['hafta_adi']}
                        {'<br><span style="background:#2563EB;color:white;font-size:9px;padding:1px 6px;border-radius:3px">AKTİF</span>' if is_aktif else ''}
                    </div>
                    <div style="font-size:10px;color:#9CA3AF;margin:4px 0">{ozet['odendi']}/{ozet['toplam']} ödendi</div>
                    <div style="font-size:11px"><span style="color:#065F46">₺{fmt(ozet['tl_toplam'])}</span></div>
                    <div style="font-size:10px;color:#9CA3AF">{h['yuklendi_tarih']}</div>
                </div>
                """, unsafe_allow_html=True)
                if not is_aktif:
                    if st.button("Aç", key=f"recent_ac_{h['id']}", use_container_width=True):
                        hafta_aktif_yap(h["id"])
                        st.success(f"'{h['hafta_adi']}' aktif yapıldı.")
                        st.rerun()

        st.markdown("---")

    st.markdown("### 📤 Yeni Hafta Yükle")
    st.markdown("""
    <div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;padding:12px 14px;margin-bottom:14px;font-size:12px;color:#78350F">
        <b>Excel sütun sırası:</b> A=HAFTA · B=FİRMA · C=AÇIKLAMA · D=(boş) · E=VADE · F=TUTAR TL · G=TUTAR USD · <b>H=KATEGORİ (opsiyonel)</b>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**1. Haftalık Ödeme Listesi (XLSX)**")
        odeme_file = st.file_uploader("", type=["xlsx", "xls"], key="odeme_upload")
        if odeme_file:
            st.success(f"✅ {odeme_file.name} seçildi")

    with col2:
        st.markdown("**2. Firma Çekleri Dökümü (XLSX) — Opsiyonel**")
        cek_file = st.file_uploader("", type=["xlsx", "xls"], key="cek_upload")
        if cek_file:
            st.success(f"✅ {cek_file.name} seçildi")

    col_a, col_b = st.columns(2)
    with col_a:
        yukle_btn = st.button("✅ Verileri İşle ve Yükle", type="primary", use_container_width=True)
    with col_b:
        ornek = create_sample_excel()
        st.download_button(
            "📥 Örnek Excel İndir",
            data=ornek,
            file_name="ornek_odeme_listesi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if yukle_btn:
        if not odeme_file and not cek_file:
            st.error("Lütfen en az bir dosya seçin.")
        else:
            mesajlar = []

            if odeme_file:
                file_bytes = odeme_file.read()
                hafta_adi, odemeler, hatalar = excel_yukle_odeme_listesi(file_bytes)

                if hatalar:
                    for h in hatalar:
                        st.warning(h)

                if odemeler:
                    hafta_id = hafta_ekle(hafta_adi or f"Hafta {len(get_tum_haftalar()) + 1}")
                    odeme_ekle_bulk(hafta_id, odemeler)
                    mesajlar.append(f"✅ {len(odemeler)} ödeme yüklendi — '{hafta_adi}'")
                else:
                    mesajlar.append("⚠️ Ödeme listesinde işlenebilir veri bulunamadı.")

            if cek_file:
                file_bytes = cek_file.read()
                tl_cekler, usd_cekler, hatalar = excel_yukle_cek_listesi(file_bytes)
                aktif = get_aktif_hafta()
                hafta_id = aktif["id"] if aktif else None

                if hatalar:
                    for h in hatalar:
                        st.warning(h)

                if tl_cekler or usd_cekler:
                    if tl_cekler and hafta_id:
                        cek_ekle_bulk(hafta_id, tl_cekler, "TL")
                    if usd_cekler and hafta_id:
                        cek_ekle_bulk(hafta_id, usd_cekler, "USD")
                    mesajlar.append(f"✅ Çekler yüklendi: TL {len(tl_cekler)} · USD {len(usd_cekler)}")
                else:
                    mesajlar.append("⚠️ Çek dosyasında veri bulunamadı.")

            for m in mesajlar:
                st.success(m) if m.startswith("✅") else st.warning(m)

            if any(m.startswith("✅") for m in mesajlar):
                st.balloons()
                st.rerun()


# ════════════════════════════════════════════════════════════════════
# 9) RAPORLAR
# ════════════════════════════════════════════════════════════════════
elif sayfa == "📄 Raporlar":
    st.markdown('<div class="baslik">📄 Raporlar</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">Excel ve PDF formatında haftalık raporlar</div>', unsafe_allow_html=True)

    kur      = get_kur()
    odemeler, hafta = get_aktif_odemeler()
    bankalar = get_bankalar()

    if not odemeler:
        st.info("Rapor oluşturmak için önce veri yükleyin.")
        st.stop()

    hafta_adi = hafta["hafta_adi"] if hafta else "Haftalık Rapor"

    st.markdown(f"**Aktif hafta:** `{hafta_adi}` — {len(odemeler)} ödeme")
    st.markdown("---")

    # ── TAB: Excel / HTML ──
    tab1, tab2, tab3 = st.tabs(["📊 Tam Excel Raporu", "🖨️ PDF / Yazdır", "💸 Nakit Akış Excel"])

    with tab1:
        st.markdown("**Özet + Günlük Detay + Kategori Analizi** üç sayfalı Excel dosyası.")
        st.markdown("")

        col1, col2, col3 = st.columns(3)
        with col1:
            tl_top = sum(o.get("tutar_tl")  or 0 for o in odemeler)
            st.metric("Toplam TL", f"₺{fmt(tl_top)}")
        with col2:
            usd_top = sum(o.get("tutar_usd") or 0 for o in odemeler)
            st.metric("Toplam USD", f"${fmt(usd_top)}")
        with col3:
            odendi = sum(1 for o in odemeler if o.get("durum") == "odendi")
            st.metric("Ödendi", f"{odendi}/{len(odemeler)}")

        st.markdown("")
        try:
            excel_buf = haftalik_excel_raporu(odemeler, hafta_adi, bankalar, kur)
            st.download_button(
                label="📥 Excel Raporu İndir",
                data=excel_buf,
                file_name=f"KAYRANACC_{hafta_adi.replace(' ','_')}_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Excel oluşturulamadı: {e}")

    with tab2:
        st.markdown("Tarayıcınızda açılır — **Ctrl+P / Cmd+P** ile yazdırabilir ya da PDF olarak kaydedebilirsiniz.")
        st.markdown("")

        try:
            html_bytes = haftalik_html_raporu(odemeler, hafta_adi, bankalar, kur)
            st.download_button(
                label="🖨️ HTML Rapor İndir (Yazdır/PDF)",
                data=html_bytes,
                file_name=f"KAYRANACC_{hafta_adi.replace(' ','_')}_{date.today()}.html",
                mime="text/html",
                type="primary",
                use_container_width=True,
            )
            st.markdown("")
            st.markdown("""
            <div class="info-box">
            💡 <b>Nasıl PDF yapılır?</b><br>
            HTML dosyasını indirip tarayıcıda açın → <b>Ctrl+P</b> (veya Cmd+P) →
            "Hedef" olarak <b>PDF Olarak Kaydet</b> seçin → Kaydet.
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"HTML rapor oluşturulamadı: {e}")

        # Önizleme
        with st.expander("👁️ Rapor Önizleme"):
            try:
                preview = haftalik_html_raporu(odemeler, hafta_adi, bankalar, kur)
                st.components.v1.html(preview.decode("utf-8"), height=500, scrolling=True)
            except Exception as e:
                st.warning(f"Önizleme yüklenemedi: {e}")

    with tab3:
        st.markdown("Nakit akış tablosunu Excel dosyası olarak indirin.")
        st.markdown("")
        try:
            nakit_buf = nakit_akis_excel(odemeler, bankalar, hafta_adi, kur)
            st.download_button(
                label="📥 Nakit Akış Excel İndir",
                data=nakit_buf,
                file_name=f"KAYRANACC_NakitAkis_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Nakit akış raporu oluşturulamadı: {e}")


# ════════════════════════════════════════════════════════════════════
# 10) BİLDİRİM AYARLARI
# ════════════════════════════════════════════════════════════════════
elif sayfa == "🔔 Bildirim Ayarları":
    st.markdown('<div class="baslik">🔔 Bildirim Ayarları</div>', unsafe_allow_html=True)
    st.markdown('<div class="alt-baslik">Vade yaklaşan ödemeler için email bildirimleri</div>', unsafe_allow_html=True)

    ayarlar  = get_bildirim_ayarlari()
    odemeler, hafta = get_aktif_odemeler()
    bankalar = get_bankalar()

    # Secrets konfigürasyonu
    with st.expander("⚙️ SMTP Ayarları (Streamlit Secrets)", expanded=not ayarlar.get("smtp_user")):
        st.markdown("""
        Email bildirimleri için Streamlit Cloud → **Settings → Secrets** bölümüne ekleyin:

        ```toml
        [bildirim]
        smtp_host    = "smtp.gmail.com"
        smtp_port    = 587
        smtp_user    = "sizin@gmail.com"
        smtp_pass    = "uygulama-sifresi"   # Gmail Uygulama Şifresi
        alici_email  = "alici@firma.com"
        aktif        = true
        ```
        """)
        st.markdown("""
        <div class="info-box">
        💡 <b>Gmail Uygulama Şifresi nasıl alınır?</b><br>
        Google Hesabım → Güvenlik → 2 Adımlı Doğrulama (aktif olmalı) →
        Uygulama Şifreleri → Yeni oluştur → "Posta" seçin → Kopyalayın.
        </div>
        """, unsafe_allow_html=True)

    # Mevcut ayar durumu
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Mevcut Konfigürasyon**")
        if ayarlar.get("smtp_user"):
            st.markdown(f'<div class="ok-box">✅ SMTP: {ayarlar["smtp_host"]}:{ayarlar["smtp_port"]}<br>👤 Kullanıcı: {ayarlar["smtp_user"]}<br>📧 Alıcı: {ayarlar["alici_email"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="uyari-box">⚠️ SMTP ayarları henüz yapılandırılmamış.<br>Secrets bölümünden ekleyin.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("**Bağlantı Testi**")
        if ayarlar.get("smtp_user"):
            if st.button("🔌 Bağlantıyı Test Et", use_container_width=True):
                with st.spinner("Test ediliyor..."):
                    basarili, mesaj = baglanti_test(ayarlar)
                if basarili:
                    st.success(mesaj)
                else:
                    st.error(mesaj)
        else:
            st.info("Önce SMTP ayarlarını yapılandırın.")

    st.markdown("---")
    st.markdown("### 📨 Manuel Bildirim Gönder")

    if not ayarlar.get("smtp_user"):
        st.warning("Email göndermek için önce SMTP ayarlarını yapılandırın.")
    elif not odemeler:
        st.info("Göndermek için önce veri yükleyin.")
    else:
        hafta_adi = hafta["hafta_adi"] if hafta else "Bu Hafta"

        tab1, tab2 = st.tabs(["⚠️ Vade Uyarısı", "📊 Haftalık Özet"])

        with tab1:
            konu, html_icerik = vade_bildirimi_olustur(odemeler, hafta_adi)
            if not konu:
                st.markdown('<div class="ok-box">✅ Bugün ve yarın vadeli bekleyen ödeme yok. Bildirim gönderilecek bir durum yok.</div>', unsafe_allow_html=True)
            else:
                bugun_cnt  = sum(1 for o in odemeler if o.get("durum") != "odendi" and (o.get("vade") or "")[:10] == date.today().isoformat())
                yarin_cnt  = sum(1 for o in odemeler if o.get("durum") != "odendi" and (o.get("vade") or "")[:10] == (date.today() + timedelta(days=1)).isoformat())
                gecmis_cnt = sum(1 for o in odemeler if o.get("durum") != "odendi" and (o.get("vade") or "")[:10] < date.today().isoformat() and (o.get("vade") or "")[:10])

                if gecmis_cnt:
                    st.markdown(f'<div class="alarm-box">🚨 {gecmis_cnt} gecikmiş ödeme!</div>', unsafe_allow_html=True)
                if bugun_cnt:
                    st.markdown(f'<div class="uyari-box">⚠️ Bugün vadeli: {bugun_cnt} ödeme</div>', unsafe_allow_html=True)
                if yarin_cnt:
                    st.markdown(f'<div class="info-box">📅 Yarın vadeli: {yarin_cnt} ödeme</div>', unsafe_allow_html=True)

                st.markdown(f"**Konu:** `{konu}`")
                st.markdown(f"**Alıcı:** `{ayarlar['alici_email']}`")

                with st.expander("👁️ Email Önizleme"):
                    st.components.v1.html(html_icerik, height=400, scrolling=True)

                if st.button("📨 Vade Uyarısı Gönder", type="primary", use_container_width=True):
                    with st.spinner("Gönderiliyor..."):
                        basarili, mesaj = email_gonder(konu, html_icerik, ayarlar)
                    if basarili:
                        st.success(mesaj)
                    else:
                        st.error(mesaj)

        with tab2:
            konu_ozet, html_ozet = ozet_bildirimi_olustur(odemeler, bankalar, hafta_adi)
            st.markdown(f"**Konu:** `{konu_ozet}`")
            st.markdown(f"**Alıcı:** `{ayarlar['alici_email']}`")

            with st.expander("👁️ Email Önizleme"):
                st.components.v1.html(html_ozet, height=400, scrolling=True)

            if st.button("📨 Haftalık Özet Gönder", type="primary", use_container_width=True):
                with st.spinner("Gönderiliyor..."):
                    basarili, mesaj = email_gonder(konu_ozet, html_ozet, ayarlar)
                if basarili:
                    st.success(mesaj)
                else:
                    st.error(mesaj)
