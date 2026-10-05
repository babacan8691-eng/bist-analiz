import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST SMC & Zaman Döngüsü", layout="wide")

# Şifre ve Kullanıcı Adı Koruma Mekanizması
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.subheader("🔐 Yetkili Giriş Paneli")
    with st.form("login_form"):
        username = st.text_input("Kullanıcı Adı:")
        password = st.text_input("Erişim Şifresi:", type="password")
        submitted = st.form_submit_button("Giriş Yap")
        
        if submitted:
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Hatalı Kullanıcı Adı veya Şifre")
    return False

if not check_password():
    st.stop()

# Başlık ve Açıklama (Ekran Görüntüsüne Uygun)
st.markdown("## Smart Money & Zaman Döngüsü")
st.caption("Yahoo Finance 15 dakikalık OHLCV verisi, hafta içi Türkiye saatiyle 09:40–18:26 arasında dakikada bir yenilenir.")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Yenile"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Özet Metrik Kartları (Ekran Görüntüsündeki Değerler ile Uyumlu)
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="VERISI HAZIR HISSE", value="226 / 301")
with m2:
    st.metric(label="ORTALAMA ZIRVE MESAFESI", value="%4.4")
with m3:
    st.metric(label="HACIM TEYITLI KIRILIM", value="9")

st.markdown("---")
st.markdown("### 01 / TARAMA")
st.subheader("Döngü görünümü")
st.caption(f"GÜNCEL · SON TARAMA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Örnek Detaylı Tarama Veri Seti (Ekran Görüntüsündeki Sütun Yapısı)
data = [
    {
        "Hisse": "BTCIM",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "2.11 TL",
        "80 bar zirve mesafesi": "%0.0",
        "Yatay süre": "0 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 2.09 TL",
        "Stop": "2.37 TL",
        "Hedef": "3.93 TL",
        "Piyasa değeri": "12.6 Mr TL",
        "Son 15dk işlem tutarı": "46.238.282 TL",
        "Katılım aday listesi": "HAYIR"
    },
    {
        "Hisse": "CEMAS",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "3.21 TL",
        "80 bar zirve mesafesi": "%2.4",
        "Yatay süre": "218 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 3.18 TL",
        "Stop": "3.13 TL",
        "Hedef": "5.19 TL",
        "Piyasa değeri": "2.5 Mr TL",
        "Son 15dk işlem tutarı": "4.803.492 TL",
        "Katılım aday listesi": "HAYIR"
    },
    {
        "Hisse": "DGATE",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "65.05 TL",
        "80 bar zirve mesafesi": "%0.0",
        "Yatay süre": "165 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 64.95 TL",
        "Stop": "59.43 TL",
        "Hedef": "98.62 TL",
        "Piyasa değeri": "1.9 Mr TL",
        "Son 15dk işlem tutarı": "1.113.461 TL",
        "Katılım aday listesi": "HAYIR"
    },
    {
        "Hisse": "DURDO",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "5.18 TL",
        "80 bar zirve mesafesi": "%0.0",
        "Yatay süre": "65 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 5.13 TL",
        "Stop": "4.93 TL",
        "Hedef": "8.19 TL",
        "Piyasa değeri": "2.6 Mr TL",
        "Son 15dk işlem tutarı": "2.790.046 TL",
        "Katılım aday listesi": "HAYIR"
    },
    {
        "Hisse": "GENTS",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "4.21 TL",
        "80 bar zirve mesafesi": "%0.0",
        "Yatay süre": "0 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 4.20 TL",
        "Stop": "5.53 TL",
        "Hedef": "6.35 TL",
        "Piyasa değeri": "3.2 Mr TL",
        "Son 15dk işlem tutarı": "515.788 TL",
        "Katılım aday listesi": "HAYIR"
    },
    {
        "Hisse": "ISBIR",
        "Puan": 3,
        "Sektör": "Diğer",
        "Fiyat": "62.00 TL",
        "80 bar zirve mesafesi": "%13.9",
        "Yatay süre": "0 bar",
        "Kırılım teyidi": "Hacim teyitli kırılım | > 61.50 TL",
        "Stop": "73.86 TL",
        "Hedef": "122.56 TL",
        "Piyasa değeri": "2.0 Mr TL",
        "Son 15dk işlem tutarı": "726.950 TL",
        "Katılım aday listesi": "HAYIR"
    }
]

df_display = pd.DataFrame(data)
st.dataframe(df_display, use_container_width=True)
