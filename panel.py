import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="BIST Pro Terminali", layout="wide", initial_sidebar_state="collapsed")

# Karanlık Tema CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stDataFrame { background-color: #1E1E1E; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    .stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 1. OTURUM AÇMA (LOGIN) MODÜLÜ (DÜZELTİLDİ) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 BIST Pro Terminali Girişi")
    
    # st.form kullanarak butona basılana kadar sayfanın yenilenmesini engelliyoruz
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Kullanıcı Adı")
        with col2:
            password = st.text_input("Şifre", type="password")
        
        submit_button = st.form_submit_button("Giriş Yap")

        if submit_button:
            # .strip() komutu başta ve sondaki görünmez boşlukları temizler
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre! Lütfen büyük/küçük harf ve boşluklara dikkat edin.")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- 2. VERİ SİMÜLASYONU ---
def get_mock_data():
    hisseler = ["BRISA.IS", "CCOLA.IS", "HEKTS.IS", "SAHOL.IS", "SASA.IS", "EKSUN.IS", "GLYHO.IS", "ENKAI.IS", "PETKM.IS", "ENERY.IS", "ASELS.IS", "KCHOL.IS", "TUPRS.IS", "BIMAS.IS", "FROTO.IS"]
    data = []
    for h in hisseler:
        net_guc = random.uniform(30, 95)
        vol = random.uniform(0.5, 3.5)
        comp = random.uniform(0.8, 1.8)
        fiyat = random.uniform(10, 100)
        
        if comp > 1.3 and vol > 2.0:
            tahmin = "🚀 YÜKSELİŞ BEKLENİYOR (%78)"
        elif comp < 0.9 and vol < 1.0:
            tahmin = "📉 DÜŞÜŞ BEKLENİYOR (%65)"
        else:
            tahmin = "⏳ BEKLE (%50)"
            
        data.append({
            "Hisse": h,
            "Net Güç Skoru": round(net_guc, 2),
            "Sinyal": "GÜÇLÜ TREND" if net_guc > 70 else "BEKLE",
            "Trend Kararı": "Yükseliş Kanalı" if net_guc > 60 else "Yatay Dar Bant",
            "Olası Haber/Beklenti": "Hacim Genişlemesi Bekleniyor" if vol > 1.5 else "Normal",
            "Trend Projeksiyon": "Güçlü Trend Devamı" if net_guc > 75 else "Bant İçi Toparlanma",
            "Beklenen Getiri": f"%{round(random.uniform(-2, 5), 2)}",
            "Erken Konum": "HACIM & SIKIŞMA" if comp > 1.2 else "NORMAL",
            "Swing Al-Sat": "SWING / İNTEL UYGUN" if net_guc > 60 else "HARİÇ",
            "Al Olasılığı (AI)": f"%{round(random.uniform(50, 90), 1)}",
            "Hacim (Vol)": f"{round(vol, 2)}x",
            "Sıkışma (Comp)": f"{round(comp, 2)}x",
            "Fiyat": f"{round(fiyat, 2)} TL",
            "Dönem Değişimi": f"%{round(random.uniform(-5, 10), 2)}",
            "Endeks RS": f"%{round(random.uniform(-3, 6), 2)}",
            "Hurst": round(random.uniform(0.3, 0.8), 2),
            "VWAP Sapma": f"%{round(random.uniform(-2, 3), 2)}",
            "Net Para Girişi": round(random.uniform(-1000000, 5000000), 2),
            "Güçlü Yükseliş": "EVET" if net_guc > 80 else "HAYIR",
            "15 Dk Sonra Tahmin": tahmin
        })
    return pd.DataFrame(data)

# --- 3. ANA PANEL ARAYÜZÜ ---
st.title("🚀 BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali")
st.caption(f"Son Güncelleme (TRT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 15Dk Gecikmeli Güvenli Trend & Sıkışma Avcısı Modu")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🌐 BIST 100 Trend Teyidi", value="YÜKSELİŞ ONAYLI", delta="%0.02")
with col2:
    st.metric(label="⚖️ Öncü Piyasa Sinyali (VIOP Denge)", value="Denge", delta="Nötr")
with col3:
    st.metric(label="🔄 Trend Tarama Akışı", value="Aktif (30 Sn Döngü)", delta="Sayfa: 34")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Genel Trend & Sıkışma Matrisi", "⚖️ VIOP Denge", "📰 Canlı KAP Haberleri", "📈 Tüm Hisseler Görseli", "🌙 Seans Kapanış Fırsatları"])

with tab1:
    st.subheader("Gelişmiş Nicel Trend Matrisi (Hacim & Sıkışma Odaklı Tarama)")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        strateji = st.radio("Strateji Modu:", ["Tüm Hisseler / Nötr", "Yüksek Güvenli Trend", "İslam'a Uygun Öncüler"], horizontal=True)
    with col_f2:
        st.checkbox("🚀 Erken Sıkışma & Hacim Patlaması")
    with col_f3:
        st.checkbox("Yalnızca İslam'a Uygun (Katılım) Hisseler", value=True)

    df = get_mock_data()
    
    if not df.empty:
        def color_prediction(val):
            if "YÜKSELİŞ" in str(val):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            elif "DÜŞÜŞ" in str(val):
                return 'background-color: #b71c1c; color: white; font-weight: bold;'
            elif "BEKLE" in str(val):
                return 'background-color: #e65100; color: white; font-weight: bold;'
            return ''

        styled_df = df.style.map(color_prediction, subset=["15 Dk Sonra Tahmin"])
        st.dataframe(styled_df, use_container_width=True, height=600)
    else:
        st.warning("Gösterilecek hisse verisi bulunamadı.")

with tab2:
    st.subheader("VIOP Denge Analizi")
    st.info("Vadeli işlemler ile spot piyasa arasındaki dengeyi gösteren öncü sinyal paneli burada yer alacak.")

with tab3:
    st.subheader("Canlı KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    st.write("- [Saat 14:18:40] KAP & Sıkışma Bülteni: 15m-30m Bar Verilerine Göre Hacim Patlamaları Güncellendi.")
    st.write("- [Trend Modu] Comp Ratio (Sıkışma Oranı) ve Vol Ratio (Hacim Çarpanı) Taraması Aktif.")

with tab4:
    st.subheader("Tüm Hisseler Görseli")
    st.info("Tüm hisseleri gösteren grafiksel görünüm burada yer alacak.")

with tab5:
    st.subheader("Seans Kapanışı & Overnight Fırsatları")
    st.success("Overnight Taşınabilecek Katılım Hisseleri Hazırlandı.")
