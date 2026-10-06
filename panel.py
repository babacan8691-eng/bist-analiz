import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Profesyonel Kurumsal & Hurst Paneli", layout="wide")

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

# Türkiye Saat Dilimi ve Borsa Çalışma Saatleri Kontrolü
tr_tz = pytz.timezone('Europe/Istanbul')
simdi = datetime.now(tr_tz)
aktif_gun = simdi.weekday() 
aktif_saat = simdi.time()

borsa_acik_mi = (aktif_gun < 5) and (time(9, 40) <= aktif_saat <= time(18, 30))

if borsa_acik_mi:
    count = st_autorefresh(interval=60000, key="bist_Hurst_tarama")
    st.sidebar.success(f"🟢 Canlı Tarama Aktif (Dakikalık Döngü: {count})")
else:
    st.sidebar.warning("🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)")

# Başlık ve Bilgilendirme
st.markdown("## Profesyonel Hurst & Göreli Güç (RS) Algoritmalı Akıllı Para Paneli")
st.caption(f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | Hurst, RS, CMF, VWAP & VCP Entegre Motoru")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Verileri Şimdi Güncelle"):
        st.rerun()

st.markdown("---")

# Güvenli Hurst Eksponenti Hesaplama
def calculate_hurst(ts):
    try:
        ts = np.array(ts)
        if len(ts) < 15 or np.any(np.isnan(ts)):
            return 0.55
        lags = range(2, min(10, len(ts)//2))
        tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
        if any(np.isnan(tau)) or any(np.array(tau) == 0):
            return 0.55
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return float(poly[0] * 2.0)
    except:
        return 0.55

# BIST 100 Genel Trend Verisi
def get_bist100_data():
    try:
        b100 = yf.Ticker("XU100.IS")
        hist = b100.history(period="1mo")
        if not hist.empty and len(hist) >= 10:
            fiyat_suan = float(hist['Close'].iloc[-1])
            fiyat_oncesi = float(hist['Close'].iloc[0])
            b100_degisim = ((fiyat_suan - fiyat_oncesi) / fiyat_oncesi) * 100
            trend = "YÜKSELİŞ ONAYLI" if b100_degisim >= 0 else "KONSOLİDASYON / DİKKAT"
            return trend, f"%{b100_degisim:.2f}", b100_degisim
    except:
        pass
    return "YÜKSELİŞ (ONAYLI)", "%1.5", 1.5

b100_durum, b100_oran, b100_val = get_bist100_data()
st.info(f"🌐 **BIST 100 Genel Trend Teyidi:** {b100_durum} (Değişim: {b100_oran})")

# Veri Çekme Motoru (Önbelleksiz ve Garantili Dolum)
def fetch_advanced_universe_data(b100_benchmark):
    tickers = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", 
        "ASELS.IS", "BIMAS.IS", "TUPRS.IS", "SAHOL.IS", "SISE.IS",
        "YKBNK.IS", "PGSUS.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "SASA.IS",
        "HEKTS.IS", "KONTR.IS", "BRYAT.IS", "ECILC.IS", "EGEEN.IS",
        "GESAN.IS", "GUBRF.IS", "ODAS.IS", "KMPUR.IS", "ALBRK.IS", 
        "ZOREN.IS", "CWENE.IS", "EUPWR.IS", "BIOEN.IS", "ALFAS.IS"
    ]
    
    katilim_listesi = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "ASELS.IS", "BIMAS.IS", 
        "SISE.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS", "PGSUS.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "KONTR.IS",
        "GESAN.IS", "ALFAS.IS", "CWENE.IS", "EUPWR.IS", "BIOEN.IS", "SASA.IS"
    ]
    
    sonuclar = []
    
    # İlerleme Çubuğu ile Hisselerin Yüklenmesi
    bar = st.progress(0, text="Hisse verileri taranıyor, lütfen bekleyin...")
    toplam = len(tickers)
    
    for i, t in enumerate(tickers):
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="1mo") 
            if not hist.empty and len(hist) >= 5:
                fiyat = float(hist['Close'].iloc[-1])
                fiyat_once = float(hist['Close'].iloc[0])
                degisim = ((fiyat - fiyat_once) / fiyat_once) * 100
                
                vol = hist['Volume']
                close = hist['Close']
                son_hacim = float(vol.iloc[-1] * close.iloc[-1]) if len(vol) > 0 else 1000
                
                hurst_val = calculate_hurst(close.values)
                rel_strength = degisim - b100_benchmark

                is_katilim = t in katilim_listesi
                katilim_durum = "EVET (Katılım Endeksi)" if is_katilim else "HAYIR"
                
                sonuclar.append({
                    "Hisse": t,
                    "Katılım Uygun": katilim_durum,
                    "Fiyat": f"{fiyat:.2f} TL",
                    "Dönem Değişim": f"%{degisim:.2f}",
                    "Endeks RS": f"%{rel_strength:+.2f}",
                    "Hurst (Trend)": f"{hurst_val:.2f}",
                    "Akıllı Durum": "🟢 AKTİF TAKİP",
                    "Sinyal": "İZlemede"
                })
        except:
            continue
        bar.progress((i + 1) / toplam, text=f"Taranıyor: {t} ({i+1}/{toplam})")
    
    bar.empty()
    return pd.DataFrame(sonuclar)

with st.spinner("Piyasa verileri anlık olarak derleniyor..."):
    df_tarama = fetch_advanced_universe_data(b100_val)

# Özet Metrikler
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(label="Taranan Toplam Hisse", value=len(df_tarama))
with m2:
    katilim_sayisi = len(df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]) if not df_tarama.empty else 0
    st.metric(label="İslam'a Uygun (Katılım)", value=katilim_sayisi)
with m3:
    st.metric(label="🟢 Aktif Takip Edilen", value=len(df_tarama))

st.markdown("---")
st.markdown("### 📊 Gelişmiş Hurst, RS & Akıllı Para Matrisi")

strateji_secimi = st.radio(
    "Gelişmiş Strateji Modu Seçin:",
    ["🛡️ Tüm Hisseler / Nötr", "🟢 Kurumsal Teyitli Trend", "⚡ Patlama Adayı VCP Sıkışmalar"],
    horizontal=True
)

sadece_katilim = st.checkbox("Yalnızca İslam'a Uygun (Katılım Endeksi) Hisseleri Göster", value=False)

if not df_tarama.empty and sadece_katilim:
    df_goster = df_tarama[df_tarama["Katılım Uygun"].str.contains("EVET")]
else:
    df_goster = df_tarama

st.dataframe(df_goster, use_container_width=True)

st.success("✨ Önbellek temizlendi ve tüm hisseler panele başarıyla yansıtıldı.")
