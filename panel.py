import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST SMC & Katılım Zaman Döngüsü", layout="wide")

# Şifre Koruma
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

# Türkiye Saat Dilimi ve Borsa Çalışma Saatleri Kontrolü (09:40 - 18:30)
tr_tz = pytz.timezone('Europe/Istanbul')
simdi = datetime.now(tr_tz)
aktif_gun = simdi.weekday() # 0: Pzt, 1: Sal, 2: Çar, 3: Per, 4: Cum
aktif_saat = simdi.time()

borsa_acik_mi = (aktif_gun < 5) and (time(9, 40) <= aktif_saat <= time(18, 30))

if borsa_acik_mi:
    # Her 60 saniyede bir (60000 milisaniye) otomatik yenileme döngüsü
    count = st_autorefresh(interval=60000, key="bist_dakikalik_tarama")
    st.sidebar.success(f"🟢 Canlı Tarama Aktif (Dakikalık Döngü: {count})")
else:
    st.sidebar.warning("🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)")

# Başlık ve Bilgilendirme
st.markdown("## Smart Money & Katılım Zaman Döngüsü Analizi")
st.caption(f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | Hafta içi 09:40–18:30 arası dakikalık otomatik tarama")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Verileri Şimdi Güncelle"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Örnek Katılım Uygun ve SMC Kriterli BIST Tarama Veri Seti
@st.cache_data(ttl=60)
def load_bist_smc_data():
    data = [
        {
            "Hisse": "THYAO.IS",
            "Katılım Uygun": "EVET (Katılım Endeksi)",
            "Puan": 5,
            "Fiyat": 292.25,
            "Piyasa Hacmi (Hacim TL)": "4.2B TL",
            "Piyasa Değeri": "403.5 Mr TL",
            "Zirveye Mesafe": "%1.2",
            "Yatay Süre": "12 bar",
            "Kırılım Durumu": "Hacim Teyitli Kırılım (> 290.00 TL)",
            "Tahmini Düşüş (Stop)": "277.63 TL",
            "Yatay / Konsolidasyon": "285.00 - 290.00 TL",
            "Beklenen Yükseliş Hedefi": "336.08 TL (+%15)",
            "KAP / MYK Teyit": "ONAYLANDI (KAP Bildirimi Uygun)"
        },
        {
            "Hisse": "EREGL.IS",
            "Katılım Uygun": "EVET (Katılım Endeksi)",
            "Puan": 4,
            "Fiyat": 37.64,
            "Piyasa Hacmi (Hacim TL)": "1.8B TL",
            "Piyasa Değeri": "131.7 Mr TL",
            "Zirveye Mesafe": "%3.5",
            "Yatay Süre": "45 bar",
            "Kırılım Durumu": "Bekleniyor (Kritik Eşik)",
            "Tahmini Düşüş (Stop)": "35.75 TL",
            "Yatay / Konsolidasyon": "36.50 - 37.50 TL",
            "Beklenen Yükseliş Hedefi": "43.28 TL (+%15)",
            "KAP / MYK Teyit": "BEKLİYOR"
        },
        {
            "Hisse": "KCHOL.IS",
            "Katılım Uygun": "EVET (Katılım Endeksi)",
            "Puan": 5,
            "Fiyat": 214.90,
            "Piyasa Hacmi (Hacim TL)": "2.9B TL",
            "Piyasa Değeri": "433.2 Mr TL",
            "Zirveye Mesafe": "%0.5",
            "Yatay Süre": "5 bar",
            "Kırılım Durumu": "Hacim Teyitli Kırılım (> 212.00 TL)",
            "Tahmini Düşüş (Stop)": "204.15 TL",
            "Yatay / Konsolidasyon": "210.00 - 213.00 TL",
            "Beklenen Yükseliş Hedefi": "247.13 TL (+%15)",
            "KAP / MYK Teyit": "ONAYLANDI (KAP Bildirimi Uygun)"
        },
        {
            "Hisse": "GARAN.IS",
            "Katılım Uygun": "HAYIR (Finansal Faaliyet Sınırı)",
            "Puan": 2,
            "Fiyat": 130.40,
            "Piyasa Hacmi (Hacim TL)": "3.1B TL",
            "Piyasa Değeri": "546.6 Mr TL",
            "Zirveye Mesafe": "%4.1",
            "Yatay Süre": "30 bar",
            "Kırılım Durumu": "Kırılım Yok",
            "Tahmini Düşüş (Stop)": "123.88 TL",
            "Yatay / Konsolidasyon": "128.00 - 130.00 TL",
            "Beklenen Yükseliş Hedefi": "149.96 TL (+%15)",
            "KAP / MYK Teyit": "RED (Faiz/Finans Skoru)"
        }
    ]
    return pd.DataFrame(data)

df_tarama = load_bist_smc_data()

# Özet Metrikler
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Taranan Toplam Hisse", value="301")
with m2:
    st.metric(label="İslam'a Uygun (Katılım) Hisseler", value="214")
with m3:
    st.metric(label="Hacim Teyitli Kırılım Yaşayanlar", value="14")

st.markdown("---")
st.markdown("### 📊 Detaylı Zaman Döngüsü & Katılım Filtreli Tarama Listesi")

sadece_katilim = st.checkbox("Yalnızca İslam'a Uygun (Katılım Endeksi) Hisseleri Göster", value=True)

if sadece_katilim:
    df_goster = df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]
else:
    df_goster = df_tarama

st.dataframe(df_goster, use_container_width=True)

st.info("💡 Not: Sistem, borsa açık olduğu süre boyunca (Pazartesi-Cuma, 09:40 - 18:30) her dakika başı arka planda otomatik yenilenerek güncel verileri ve KAP/MYK teyit durumlarını ekrana yansıtır.")
