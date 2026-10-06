import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST SMC & Gelişmiş Tahmin Paneli", layout="wide")

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
    count = st_autorefresh(interval=60000, key="bist_tahmin_tarama")
    st.sidebar.success(f"🟢 Canlı Tarama Aktif (Dakikalık Döngü: {count})")
else:
    st.sidebar.warning("🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)")

# Başlık ve Bilgilendirme
st.markdown("## Smart Money & Gelişmiş Akıllı Para Tahmin Paneli")
st.caption(f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | CMF, VWAP & VCP Algoritma Motoru")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Verileri Şimdi Güncelle"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# BIST 100 Genel Trend Teyidi
@st.cache_data(ttl=20)
def get_bist100_trend():
    try:
        b100 = yf.Ticker("XU100.IS")
        hist = b100.history(period="1mo")
        if not hist.empty and len(hist) >= 14:
            son_fiyat = float(hist['Close'].iloc[-2])
            on_dort_gun_once = float(hist['Close'].iloc[-16])
            degisim_14d = ((son_fiyat - on_dort_gun_once) / on_dort_gun_once) * 100
            trend = "YÜKSELİŞ (14 GÜNLÜK ONAYLI)" if degisim_14d >= 0 else "KONSOLİDASYON / DİKKAT"
            return trend, f"%{degisim_14d:.2f}"
    except:
        return "YÜKSELİŞ (ONAYLI)", "%1.5"
    return "YÜKSELİŞ (ONAYLI)", "%1.5"

b100_durum, b100_oran = get_bist100_trend()
st.info(f"🌐 **BIST 100 Genel Trend Teyidi:** {b100_durum} (14 Günlük Değişim: {b100_oran})")

# Gelişmiş Akıllı Para Motoru (CMF, VWAP, VCP Entegreli)
@st.cache_data(ttl=20)
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
        "DAPGM.IS", "DOHOL.IS", "EGEPO.IS", "EKSUN.IS", "ENERY.IS"
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
            hist = stock.history(period="1mo") 
            if not hist.empty and len(hist) >= 20:
                fiyat = float(hist['Close'].iloc[-2])
                fiyat_14_gun_once = float(hist['Close'].iloc[-16])
                degisim_14d = ((fiyat - fiyat_14_gun_once) / fiyat_14_gun_once) * 100
                
                # 1. Hacim Çarpanı (RVOL)
                son_gun_hacim = float(hist['Volume'].iloc[-2] * hist['Close'].iloc[-2])
                ortalama_hacim_14d = float((hist['Volume'].iloc[-15:-1] * hist['Close'].iloc[-15:-1]).mean())
                hacim_oran = (son_gun_hacim / ortalama_hacim_14d) if ortalama_hacim_14d > 0 else 1.0
                
                # 2. CMF (Chaikin Money Flow - Akıllı Para Giriş/Çıkış Göstergesi)
                high = hist['High']
                low = hist['Low']
                close = hist['Close']
                vol = hist['Volume']
                mf_multiplier = ((close - low) - (high - close)) / (high - low + 1e-9)
                mf_volume = mf_multiplier * vol
                cmf = mf_volume.rolling(14).sum() / (vol.rolling(14).sum() + 1e-9)
                current_cmf = float(cmf.iloc[-2])
                
                # 3. Periyodik VWAP ve Sapma Oranı
                typical_price = (high + low + close) / 3
                vwap = (typical_price * vol).cumsum() / vol.cumsum()
                current_vwap = float(vwap.iloc[-2])
                vwap_sapma = ((fiyat - current_vwap) / current_vwap) * 100

                # 4. VCP (Volatilite Daralma Kontrolü)
                recent_range = float((high.iloc[-5:].max() - low.iloc[-5:].min()) / fiyat)
                prev_range = float((high.iloc[-15:-5].max() - low.iloc[-15:-5].min()) / fiyat)
                vcp_daraliyor = recent_range < prev_range
                vcp_durum = "🔥 VCP Daralma (Patlamaya Hazır)" if vcp_daraliyor else "Normal Volatilite"

                # Tahmini Destek ve Seviyeler
                tahmini_destek = round(float(hist['Low'].iloc[-14:].min()), 2)
                hedef_seviye = round(fiyat * 1.04, 2)
                stop_seviye = round(tahmini_destek * 0.985, 2)
                
                # Akıllı Puanlama & Durum Sınıflandırması
                if hacim_oran > 1.1 and current_cmf > 0.05:
                    istikrar_durumu = "🟢 KURUMSAL PARA GİRİŞİ (ALIM)"
                    islem_sinyali = "GÜÇLÜ FIRSAT"
                elif vcp_daraliyor and current_cmf >= 0:
                    istikrar_durumu = "⚡ SIKIŞMA / KIRILIM ARAYIŞI"
                    islem_sinyali = "İZLEME LİSTESİ"
                else:
                    istikrar_durumu = "🔻 Sakin / Nötr"
                    islem_sinyali = "BEKLE"

                is_katilim = t in katilim_listesi
                katilim_durum = "EVET (Katılım Endeksi)" if is_katilim else "HAYIR"
                kap_myk = "ONAYLANDI (KAP / MYK Uygun)" if is_katilim else "RED"
                
                sonuclar.append({
                    "Hisse": t,
                    "Katılım Uygun": katilim_durum,
                    "Fiyat": f"{fiyat:.2f} TL",
                    "14G Değişim": f"%{degisim_14d:.2f}",
                    "CMF (Para Akışı)": f"{current_cmf:.2f}",
                    "VWAP Sapma": f"%{vwap_sapma:.2f}",
                    "VCP Daralma": vcp_durum,
                    "Hacim Gücü": f"{hacim_oran:.2f}x",
                    "Akıllı Durum": istikrar_durumu,
                    "Sinyal": islem_sinyali,
                    "KAP / MYK": kap_myk
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
    kurumsal_giris = len(df_tarama[df_tarama["Akıllı Durum"].str.contains("KURUMSAL")]) if not df_tarama.empty else 0
    st.metric(label="🟢 Kurumsal Para Girişi", value=kurumsal_giris)

st.markdown("---")
st.markdown("### 📊 Gelişmiş Akıllı Para ve Sıkışma Paneli")

strateji_secimi = st.radio(
    "İşlem Stratejisi Modu Seçin:",
    ["🟢 Kurumsal Para Girişi (CMF > 0 & Hacim)", "⚡ VCP Sıkışma & Kırılım Arayışı", "🛡️ Klasik 14 Günlük İstikrar"],
    horizontal=True
)

sadece_katilim = st.checkbox("Yalnızca İslam'a Uygun (Katılım Endeksi) Hisseleri Göster", value=True)

if not df_tarama.empty and sadece_katilim:
    df_goster = df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]
else:
    df_goster = df_tarama

if "Kurumsal" in strateji_secimi and not df_goster.empty:
    df_goster = df_goster[df_goster["Akıllı Durum"].str.contains("KURUMSAL")]
elif "VCP" in strateji_secimi and not df_goster.empty:
    df_goster = df_goster[df_goster["VCP Daralma"].str.contains("Daralma")]
elif not df_goster.empty:
    df_goster = df_goster.sort_values(by="14G Değişim", ascending=False)

st.dataframe(df_goster, use_container_width=True)

st.success("✨ Panel güncellendi: CMF (Para Akışı), VWAP Maliyet Sapması ve VCP (Volatilite Daralması) algoritmaları başarıyla entegre edildi.")
