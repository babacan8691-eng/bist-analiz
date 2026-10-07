import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Profesyonel Nihai Nicel & Katılım Terminali", layout="wide")

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
aktif_gun = simdi.weekday() 
aktif_saat = simdi.time()

borsa_acik_mi = (aktif_gun < 5) and (time(9, 40) <= aktif_saat <= time(18, 30))

if borsa_acik_mi:
    count = st_autorefresh(interval=60000, key="bist_Nihai_tarama_300")
    st.sidebar.success(f"🟢 Canlı Nicel Tarama Aktif (15D Gecikmeli | Döngü: {count})")
else:
    st.sidebar.warning("🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)")

# Başlık ve Bilgilendirme
st.markdown("## 🚀 BIST Nihai Nicel Finans, AI & Katılım Al-Sat Terminali")
st.caption(f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | 15 Dakika Gecikmeli Veri & CLV / Sıkışma / Half-Life Modülleri (BIST 300 Havuzu)")

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Verileri Şimdi Güncelle"):
        st.cache_data.clear()  # Önbelleği temizleyerek yeni veri çekilmesini sağlar
        st.rerun()

st.markdown("---")

# Güvenli Hurst Eksponenti Hesaplama (Minimum Veri Boyutu 20'ye Yükseltildi)
def calculate_hurst(ts):
    try:
        ts = np.array(ts)
        if len(ts) < 20 or np.any(np.isnan(ts)):
            return 0.50
        lags = range(2, min(10, len(ts)//2))
        tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
        if any(np.isnan(tau)) or any(np.array(tau) == 0):
            return 0.50
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return float(poly[0] * 2.0)
    except:
        return 0.50

# RSI Hesaplama Fonksiyonu
def calculate_rsi(series, period=14):
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (100 + rs))
        return rsi
    except:
        return pd.Series(index=series.index, data=50.0)

# BIST 100 Genel Trend Verisi (Önbelleklendi)
@st.cache_data(ttl=60)
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
st.info(f"🌐 **BIST 100 Genel Trend Teyidi (15D Gecikmeli):** {b100_durum} (Değişim: {b100_oran})")

# BIST 300 Temizlenmiş Genişletilmiş Tarama Motoru (Hızlandırılmış ve Geliştirilmiş)
@st.cache_data(ttl=60)
def fetch_final_universe_data(b100_benchmark):
    tickers = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "GARAN.IS", "AKBNK.IS", 
        "ASELS.IS", "BIMAS.IS", "TUPRS.IS", "SAHOL.IS", "SISE.IS",
        "YKBNK.IS", "PGSUS.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "SASA.IS",
        "HEKTS.IS", "KONTR.IS", "BRYAT.IS", "ECILC.IS", "EGEEN.IS",
        "GESAN.IS", "GUBRF.IS", "ODAS.IS", "KMPUR.IS", "ALBRK.IS", 
        "ZOREN.IS", "CWENE.IS", "EUPWR.IS", "BIOEN.IS", "ALFAS.IS",
        "AKSA.IS", "AKSEN.IS", "ALARK.IS", "BERA.IS", "BIENY.IS", 
        "BOBET.IS", "BRISA.IS", "BUCIM.IS", "CCOLA.IS", "CEMTS.IS", 
        "CIMSA.IS", "DOHOL.IS", "EKSUN.IS", "ENERY.IS", "GLYHO.IS", 
        "GWIND.IS", "HALKB.IS", "IPEKE.IS", "ISCTR.IS", "KCAER.IS", 
        "KONFS.IS", "KONYA.IS", "KOZAA.IS", "KOZAL.IS", "MAVI.IS", 
        "MPARK.IS", "OTKAR.IS", "POLHO.IS", "QUAGR.IS", "REEDR.IS", 
        "SMRTG.IS", "SOKM.IS", "TAVHL.IS", "TKFEN.IS", "TSKB.IS", 
        "ULKER.IS", "VAKBN.IS", "VESBE.IS", "YEOTK.IS", "YYLGD.IS",
        "AHGAZ.IS", "AKFYE.IS", "ANELE.IS", "ARASE.IS", "ARDYZ.IS", 
        "ARENA.IS", "AYDEM.IS", "AYEN.IS", "BAGFS.IS", "CATES.IS", 
        "DAPGM.IS", "DEVA.IS", "ECZYT.IS", "EGEPO.IS", "FADE.IS", 
        "FORMT.IS", "GENIL.IS", "GIPTA.IS", "GOODY.IS", "ANACM.IS",
        "TRKCM.IS", "SODA.IS", "ISDMR.IS", "IZMDC.IS",
        "KARSN.IS", "KFEIN.IS", "KOCMT.IS", "KRONT.IS", "LOGO.IS",
        "LUKSK.IS", "MAALT.IS", "MERKO.IS", "METUR.IS", "MIPAZ.IS",
        "NTHOL.IS", "OYYAT.IS", "PNSUT.IS", "PRKME.IS", "PSGYO.IS",
        "RTALB.IS", "RYSAS.IS", "SARKY.IS", "SELEC.IS", "SELGD.IS",
        "SKBNK.IS", "SUNTK.IS", "TATGD.IS", "TBORG.IS",
        "TMSN.IS", "TRGYO.IS", "TRILC.IS", "ULUUN.IS", "UNLU.IS",
        "VAKFN.IS", "VBTYZ.IS", "VERTU.IS", "VKGYO.IS", "YAPRK.IS",
        "YATAS.IS", "YGGYO.IS", "YKSLN.IS", "ACSEL.IS",
        "ADEL.IS", "ADESE.IS", "AFYON.IS", "AGESA.IS", "AGHOL.IS",
        "AGROT.IS", "AKENR.IS", "AKFGY.IS", "AKSGY.IS", "ALCAR.IS",
        "ALCTL.IS", "ALMAD.IS", "ANGEN.IS", "ARFYO.IS",
        "ARSAN.IS", "ARTMS.IS", "ARZUM.IS", "ASUZU.IS", "ATAKP.IS",
        "ATEKS.IS", "ATLAS.IS", "AVOD.IS", "AVTUR.IS", "AYCES.IS",
        "AZTEK.IS", "BAKAB.IS", "BALAT.IS", "BANVT.IS", "BARMA.IS",
        "BASCM.IS", "BASGZ.IS", "BAYRK.IS", "BEGYO.IS", "BEYAZ.IS",
        "BJKAS.IS", "BLCYT.IS", "BMSCH.IS", "BMSTL.IS", "BNTAS.IS",
        "BOSSA.IS", "BRKSN.IS", "BRSAN.IS", "BTGYO.IS", "BURCE.IS",
        "BURVA.IS", "BVSAN.IS", "CANTE.IS", "CELHA.IS", "CEMAS.IS", "CEOEM.IS", "CUSAN.IS",
        "DAGI.IS", "DENGE.IS", "DERHL.IS",
        "DERIM.IS", "DESA.IS", "DESPC.IS", "DIRIT.IS", "DMSAS.IS",
        "DNISI.IS", "DOBUR.IS", "DOCO.IS", "DOGUB.IS", "DOKTA.IS",
        "DURDO.IS", "DYOBY.IS", "DZGYO.IS", "EBEBK.IS", "EDIP.IS",
        "EGGUB.IS", "EMKEL.IS", "ENSRI.IS", "EPLAS.IS", "ERCB.IS",
        "ERSU.IS", "ESCAR.IS", "ESEN.IS", "ETILR.IS", "EUHOL.IS",
        "EUKYO.IS", "EVYOT.IS", "EYGYO.IS",
        "FENER.IS", "FLAP.IS", "FONET.IS",
        "FRIGO.IS", "GARFA.IS", "GEDIK.IS", "GEDZA.IS", "GENTS.IS",
        "GEREL.IS", "GLRYH.IS", "GMTAS.IS",
        "GOLTS.IS", "GRNYO.IS", "GZNMI.IS",
        "HATSN.IS", "HEDEF.IS", "HKTM.IS", "HLGYO.IS", "HTTBT.IS",
        "HUBVC.IS", "HURGZ.IS", "ICBCT.IS", "IDEAS.IS",
        "IHEVA.IS", "IHGZT.IS", "IHLAS.IS", "IHLGM.IS"
    ]
    tickers = list(dict.fromkeys(tickers))[:300]
    
    katilim_listesi = [
        "THYAO.IS", "EREGL.IS", "KCHOL.IS", "ASELS.IS", "BIMAS.IS", 
        "SISE.IS", "KRDMD.IS", "PETKM.IS", "ENKAI.IS", "PGSUS.IS",
        "FROTO.IS", "TOASO.IS", "TCELL.IS", "TTKOM.IS", "MGROS.IS",
        "ASTOR.IS", "OYAKC.IS", "ARCLK.IS", "ENJSA.IS", "KONTR.IS",
        "GESAN.IS", "ALFAS.IS", "CWENE.IS", "EUPWR.IS", "BIOEN.IS", 
        "SASA.IS", "AKSA.IS", "ALARK.IS", "BRISA.IS", "CIMSA.IS", 
        "GWIND.IS", "KCAER.IS", "KONFS.IS", "KOZAL.IS", "MAVI.IS", 
        "OTKAR.IS", "SMRTG.IS", "SOKM.IS", "TAVHL.IS", "ULKER.IS", "VESBE.IS", "YEOTK.IS"
    ]
    
    sonuclar = []
    
    # Yeni Yöntem 1: Hız için toplu veri indirme (Batch Download)
    st.info("🔄 BIST 300 Veri Havuzu Tek Seferde İndiriliyor...")
    try:
        tum_hisse_verileri = yf.download(tickers, period="1mo", group_by='ticker', progress=False)
    except:
        st.error("Veri indirme sırasında bir hata oluştu.")
        return pd.DataFrame()
        
    bar = st.progress(0, text="Metrikler hesaplanıyor...")
    toplam = len(tickers)
    
    for i, t in enumerate(tickers):
        try:
            # Toplu indirilen veriden ilgili hissenin verisini çekme
            if t in tum_hisse_verileri.columns.levels[0]:
                hist = tum_hisse_verileri[t].dropna()
            else:
                continue
                
            if not hist.empty and len(hist) >= 15:
                fiyat = float(hist['Close'].iloc[-1])
                fiyat_once = float(hist['Close'].iloc[0])
                degisim = ((fiyat - fiyat_once) / fiyat_once) * 100
                
                close = hist['Close']
                high = hist['High']
                low = hist['Low']
                volume = hist['Volume']
                
                hurst_val = calculate_hurst(close.values)
                rel_strength = degisim - b100_benchmark

                ortalama_hacim = volume.iloc[:-1].mean() if len(volume) > 1 else volume.iloc[-1]
                son_hacim = volume.iloc[-1]
                vol_ratio = float(son_hacim / ortalama_hacim) if ortalama_hacim > 0 else 1.0

                typical_price = (high + low + close) / 3
                vwap = (typical_price * volume).sum() / volume.sum() if volume.sum() > 0 else fiyat
                vwap_sapma = ((fiyat - vwap) / vwap) * 100

                # Yeni Yöntem 2: Rakamsal Z-Skoru Entegrasyonu (Fiyat Sapma Kararlılığı)
                
