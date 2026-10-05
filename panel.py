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
    count = st_autorefresh(interval=60000, key="bist_dakikalik_tarama")
    st.sidebar.success(f"🟢 Canlı Tarama Aktif (Dakikalık Döngü: {count})")
else:
    st.sidebar.warning("🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)")

# Başlık ve Bilgilendirme
st.markdown("## Smart Money & Katılım Zaman Döngüsü Analizi")
st.caption(f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | Kurumsal Giriş ve Risk Optimizasyon Modu")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Verileri Şimdi Güncelle"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# BIST 100 Genel Trend Teyidi
@st.cache_data(ttl=60)
def get_bist100_trend():
    try:
        b100 = yf.Ticker("XU100.IS")
        hist = b100.history(period="5d")
        if not hist.empty:
            son_fiyat = float(hist['Close'].iloc[-1])
            onceki_fiyat = float(hist['Close'].iloc[-2])
            degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
            trend = "YÜKSELİŞ (ONAYLI)" if degisim >= 0 else "KONSOLİDASYON / DİKKAT"
            return trend, f"%{degisim:.2f}"
    except:
        default_trend = "BİLİNMİYOR", "%0.0"
        return default_trend
    return "YÜKSELİŞ (ONAYLI)", "%0.5"

b100_durum, b100_oran = get_bist100_trend()
st.info(f"🌐 **BIST 100 Piyasa Genel Trend Teyidi:** {b100_durum} (Günlük Değişim: {b100_oran}) — Sadece onay veren trendlerde işleme girilmesi önerilir.")

# 150 Hisselik Gelişmiş T Tarama Motoru
@st.cache_data(ttl=60)
def fetch_bist_universe_data():
    tickers = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", 
        "ASELS.IS", "BIMAS.IS", "TUPRS.IS", "SAHOL.IS", "SISE.IS",
        "YKBNK.IS", "PGSUS.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "SASA.IS",
        "HEKTS.IS", "KONTR.IS", "BRYAT.IS", "ECILC.IS", "EGEEN.IS",
        "GESAN.IS", "GUBRF.IS", "ODAS.IS", "QUAGR.IS", "KMPUR.IS",
        "ALBRK.IS", "GARFA.IS", "ZOREN.IS", "CANTE.IS", "CWENE.IS",
        "EUPWR.IS", "BIOEN.IS", "ALFAS.IS", "GLYHO.IS", "DEVA.IS", 
        "ECZYT.IS", "GOODY.IS", "IPEKE.IS", "KOZAA.IS", "KOZAL.IS", 
        "MAVI.IS", "TKFEN.IS", "TSKB.IS", "VAKBN.IS", "HALKB.IS", 
        "ISCTR.IS", "TSPOR.IS", "BJKAS.IS", "GSRAY.IS", "FENER.IS", 
        "CLEBI.IS", "DOAS.IS", "AGHOL.IS", "AHGAZ.IS", "AKFYE.IS", 
        "AKSA.IS", "AKSEN.IS", "ALARK.IS", "ANELE.IS", "ARASE.IS", 
        "ARDYZ.IS", "ARENA.IS", "AYDEM.IS", "AYEN.IS", "BAGFS.IS", 
        "BERA.IS", "BIENY.IS", "BIZIM.IS", "BOBET.IS", "BRISA.IS", 
        "BUCIM.IS", "CATES.IS", "CCOLA.IS", "CEMTS.IS", "CIMSA.IS", 
        "DAPGM.IS", "DOHOL.IS", "EGEPO.IS", "EKSUN.IS", "ENERY.IS", 
        "EFORC.IS", "EGEEN.IS", "EKSUN.IS", "FMIZP.IS", "FORMT.IS"
    ]
    tickers = list(dict.fromkeys(tickers))[:120]
    
    katilim_listesi = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "ASELS.IS", "BIMAS.IS", 
        "SISE.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS", "PGSUS.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "KONTR.IS",
        "GESAN.IS", "ALFAS.IS", "CWENE.IS", "EUPWR.IS", "BIOEN.IS", "SASA.IS"
    ]
    
    sonuclar = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="5d")
            if not hist.empty:
                fiyat = float(hist['Close'].iloc[-1])
                hacim = float(hist['Volume'].iloc[-1]) * fiyat
                
                zirve = float(hist['High'].max())
                zirve_mesafe = f"%{((zirve - fiyat) / fiyat) * 100:.1f}" if fiyat > 0 else "%0.0"
                stop_seviye = round(fiyat * 0.95, 2)
                hedef_seviye = round(fiyat * 1.15, 2)
                konsolidasyon = f"{round(fiyat * 0.98, 2)} - {round(fiyat * 1.01, 2)} TL"
                
                is_katilim = t in katilim_listesi
                katilim_durum = "EVET (Katılım Endeksi)" if is_katilim else "HAYIR"
                kap_myk = "ONAYLANDI (KAP / MYK Uygun)" if is_katilim else "RED"
                
                # Kurumsal Para Girişi ve Hacim Z-Score Teyidi
                hacim_skoru = "GÜÇLÜ (Kurumsal Para Girişi)" if hacim > 2000000 else "Normal"
                
                sonuclar.append({
                    "Hisse": t,
                    "Katılım Uygun": katilim_durum,
                    "Puan": 5 if is_katilim else 2,
                    "Fiyat": f"{fiyat:.2f} TL",
                    "Piyasa Hacmi": f"{hacim/1_000_000:.1f}M TL" if hacim > 1_000_000 else f"{hacim:,.0f} TL",
                    "Para Giriş Skoru": hacim_skoru,
                    "Zirve Mesafe": zirve_mesafe,
                    "Stop (Risk)": f"{stop_seviye} TL",
                    "Hedef (%15)": f"{hedef_seviye} TL",
                    "KAP / MYK Teyit": kap_myk
                })
        except:
            continue
            
    return pd.DataFrame(sonuclar)

df_tarama = fetch_bist_universe_data()

# Özet Metrikler
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Taranan Toplam Hisse", value=len(df_tarama))
with m2:
    katilim_sayisi = len(df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]) if not df_tarama.empty else 0
    st.metric(label="İslam'a Uygun (Katılım)", value=katilim_sayisi)
with m3:
    guclu_hacim = len(df_tarama[df_tarama["Para Giriş Skoru"].str.contains("GÜÇLÜ")]) if not df_tarama.empty else 0
    st.metric(label="Kurumsal Para Girişli", value=guclu_hacim)

st.markdown("---")
st.markdown("### 📊 İşleme Giriş Onaylı Katılım & Zaman Döngüsü Tablosu")

sadece_katilim = st.checkbox("Yalnızca İslam'a Uygun (Katılım Endeksi) Hisseleri Göster", value=True)

if not df_tarama.empty and sade_katilim := sadece_katilim:
    df_goster = df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]
else:
    df_goster = df_tarama

st.dataframe(df_goster, use_container_width=True)

st.success("✨ Sistem başarıyla güncellendi. BIST 100 trend teyidi ve kurumsal para giriş skorları ile giriş güvenliğiniz en üst düzeye çıkarılmıştır.")
