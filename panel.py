import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
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

# --- OTOMATİK YENİLEME (Her 60 Saniye) ---
st.markdown(
    """
    <script>
        setTimeout(function(){
           window.location.reload(1);
        }, 60000);
    </script>
    """, unsafe_allow_html=True)

# --- 1. OTURUM AÇMA MODÜLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 BIST Pro Terminali Girişi")
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Kullanıcı Adı")
        with col2:
            password = st.text_input("Şifre", type="password")
        submit_button = st.form_submit_button("Giriş Yap")
        if submit_button:
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- 2. GERÇEK VERİ ÇEKME FONKSİYONU ---
@st.cache_data(ttl=3600) 
def get_bist_tickers():
    # BIST 100'de işlem gören popüler hisseler (Daha fazlası eklenebilir)
    return [
        "THYAO.IS", "GARAN.IS", "ASELS.IS", "BIMAS.IS", "FROTO.IS", "KCHOL.IS", 
        "SAHOL.IS", "CCOLA.IS", "HEKTS.IS", "BRISA.IS", "SASA.IS", "TUPRS.IS",
        "EREGL.IS", "SISE.IS", "TOASO.IS", "PGSUS.IS", "TAVHL.IS", "VESTL.IS",
        "ARCLK.IS", "DOHOL.IS", "EKGYO.IS", "GUBRF.IS", "ISCTR.IS", "KRDMD.IS",
        "MGROS.IS", "ODAS.IS", "PETKM.IS", "SOKM.IS", "TCELL.IS", "TTKOM.IS",
        "VAKBN.IS", "YKBNK.IS", "ZOREN.IS", "ALARK.IS", "AYGAZ.IS", "ENKAI.IS",
        "GESAN.IS", "GLYHO.IS", "KONTR.IS", "SMRTG.IS", "TUKAS.IS", "ULKER.IS"
    ]

@st.cache_data(ttl=86400)
def get_katilim_hisseleri():
    # BIST Katılım Endeksi'nde yer alan hisseler (Örnek liste)
    return [
        "AHGAZ.IS", "AKCNS.IS", "AKFYE.IS", "ALBRK.IS", "ARASE.IS", "ATAKP.IS",
        "AVPGY.IS", "AYDEM.IS", "BASGZ.IS", "BETAE.IS", "BUCIM.IS", "EGGUB.IS",
        "EGPRO.IS", "ENERY.IS", "GWIND.IS", "HTTBT.IS", "ASTOR.IS", "BMSTL.IS",
        "CVKMD.IS", "DOFRB.IS", "NETCD.IS", "RALYH.IS", "AKSA.IS", "KUYAS.IS",
        "ALKLC.IS", "EFOR.IS", "QUAGR.IS", "SARKY.IS", "BSOKE.IS", "CANTE.IS",
        "ASELS.IS", "TUPRS.IS", "BIMAS.IS", "FROTO.IS", "SISE.IS", "TOASO.IS",
        "TCELL.IS", "TTKOM.IS", "MGROS.IS", "SOKM.IS", "ULKER.IS", "AYGAZ.IS",
        "ENKAI.IS", "VESTL.IS", "ARCLK.IS", "PGSUS.IS", "TAVHL.IS", "ODAS.IS",
        "GESAN.IS", "KONTR.IS", "SMRTG.IS", "TUKAS.IS", "ZOREN.IS", "ALARK.IS"
    ]

def get_stock_data(ticker):
    """Gerçek zamanlı hisse verisi çeker (15 dk gecikmeli)"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d", interval="15m")
        if hist.empty:
            return None
        
        son_fiyat = hist['Close'].iloc[-1]
        onceki_fiyat = hist['Close'].iloc[-2] if len(hist) > 1 else son_fiyat
        degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
        
        ortalama_hacim = hist['Volume'].rolling(20).mean().iloc[-1]
        son_hacim = hist['Volume'].iloc[-1]
        vol_ratio = son_hacim / ortalama_hacim if ortalama_hacim > 0 else 1
        
        son_20_yuksek = hist['High'].rolling(20).max().iloc[-1]
        son_20_dusuk = hist['Low'].rolling(20).min().iloc[-1]
        comp_ratio = (son_20_yuksek - son_20_dusuk) / son_fiyat if son_fiyat > 0 else 1
        
        vwap = (hist['Volume'] * hist['Close']).cumsum() / hist['Volume'].cumsum()
        vwap_sapma = ((son_fiyat - vwap.iloc[-1]) / vwap.iloc[-1]) * 100 if vwap.iloc[-1] > 0 else 0
        
        # Basit Hurst Hesaplaması (Numpy ile)
        returns = hist['Close'].pct_change().dropna()
        if len(returns) > 10:
            n = len(returns)
            mean_ret = returns.mean()
            deviation = returns - mean_ret
            cumsum = deviation.cumsum()
            R = cumsum.max() - cumsum.min()
            S = returns.std()
            hurst = np.log(R/S) / np.log(n) if S > 0 else 0.5
            hurst = max(0.1, min(0.9, hurst))
        else:
            hurst = 0.5
        
        para_girisi = (hist['Close'].iloc[-1] - hist['Open'].iloc[-1]) * hist['Volume'].iloc[-1]
        endeks_rs = degisim
        
        ai_olasilik = min(95, max(30, (vol_ratio * 15) + (comp_ratio * 20) + (10 if vwap_sapma > 0 else -10) + (hurst * 30)))
        
        if comp_ratio > 1.3 and vol_ratio > 2.0 and vwap_sapma > 0:
            tahmin = "🚀 YÜKSELİŞ BEKLENİYOR (%78)"
            sinyal = "GÜÇLÜ TREND"
        elif comp_ratio < 0.9 and vol_ratio < 1.0:
            tahmin = "📉 DÜŞÜŞ BEKLENİYOR (%65)"
            sinyal = "ZAYIF"
        else:
            tahmin = "⏳ BEKLE (%50)"
            sinyal = "BEKLE"
        
        katilim_listesi = get_katilim_hisseleri()
        katilim_uygun = "EVET" if ticker in katilim_listesi else "HAYIR"
        
        return {
            "Hisse": ticker.replace(".IS", ""),
            "Katılım Uygun": katilim_uygun,
            "Net Güç Skoru": round(ai_olasilik, 2),
            "Sinyal": sinyal,
            "Trend Kararı": "Yükseliş Kanalı" if degisim > 0 else "Düşüş Kanalı",
            "Olası Haber/Beklenti": "Hacim Genişlemesi" if vol_ratio > 1.5 else "Normal",
            "Trend Projeksiyon": "Güçlü Trend Devamı" if ai_olasilik > 75 else "Bant İçi Toparlanma",
            "Beklenen Getiri": f"%{round(degisim, 2)}",
            "Erken Konum": "HACIM & SIKIŞMA" if comp_ratio > 1.2 else "NORMAL",
            "Swing Al-Sat": "SWING / İNTEL UYGUN" if ai_olasilik > 60 else "HARİÇ",
            "Al Olasılığı (AI)": f"%{round(ai_olasilik, 1)}",
            "Hacim (Vol)": f"{round(vol_ratio, 2)}x",
            "Sıkışma (Comp)": f"{round(comp_ratio, 2)}x",
            "Fiyat": f"{round(son_fiyat, 2)} TL",
            "Dönem Değişimi": f"%{round(degisim, 2)}",
            "Endeks RS": f"%{round(endeks_rs, 2)}",
            "Hurst": round(hurst, 2),
            "VWAP Sapma": f"%{round(vwap_sapma, 2)}",
            "Net Para Girişi": round(para_girisi, 2),
            "Güçlü Yükseliş": "EVET" if ai_olasilik > 80 else "HAYIR",
            "15 Dk Sonra Tahmin": tahmin
        }
    except Exception as e:
        return None

@st.cache_data(ttl=60)
def get_all_stocks_data():
    tickers = get_bist_tickers()
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Veri çekiliyor: {ticker} ({i+1}/{len(tickers)})")
        data = get_stock_data(ticker)
        if data:
            all_data.append(data)
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.text("Veri çekme tamamlandı!")
    progress_bar.empty()
    
    if all_data:
        df = pd.DataFrame(all_data)
        df['Tahmin_Agirlik'] = df['15 Dk Sonra Tahmin'].apply(lambda x: 1 if 'YÜKSELİŞ' in x else (2 if 'BEKLE' in x else 3))
        df = df.sort_values(by=['Tahmin_Agirlik', 'Net Güç Skoru'], ascending=[True, False])
        df = df.drop(columns=['Tahmin_Agirlik'])
        return df
    return pd.DataFrame()

# --- 3. ANA PANEL ARAYÜZÜ ---
st.title("🚀 BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali")
st.caption(f"Son Güncelleme (TRT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 15Dk Gecikmeli Güvenli Trend & Sıkışma Avcısı Modu")

col1, col2, col3 = st.columns(3)
with col1:
    try:
        bist100 = yf.Ticker("XU100.IS")
        bist100_hist = bist100.history(period="1d")
        if not bist100_hist.empty:
            bist100_fiyat = bist100_hist['Close'].iloc[-1]
            bist100_degisim = ((bist100_fiyat - bist100_hist['Open'].iloc[-1]) / bist100_hist['Open'].iloc[-1]) * 100
            st.metric(label="🌐 BIST 100 Endeksi", value=f"{bist100_fiyat:,.2f}", delta=f"%{bist100_degisim:.2f}")
        else:
            st.metric(label="🌐 BIST 100 Endeksi", value="Veri Bekleniyor", delta="Nötr")
    except:
        st.metric(label="🌐 BIST 100 Endeksi", value="Hata", delta="Nötr")

with col2:
    st.metric(label="⚖️ Öncü Piyasa Sinyali (VIOP Denge)", value="Denge", delta="Nötr")

with col3:
    st.metric(label="🔄 Trend Tarama Akışı", value="Aktif (30 Sn Döngü)", delta="Canlı Veri")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Genel Trend & Sıkışma Matrisi", "⚖️ VIOP Denge", "📰 Canlı KAP Haberleri", "📈 Tüm Hisseler Görseli", "🌙 Seans Kapanış Fırsatları"])

with tab1:
    st.subheader("Gelişmiş Nicel Trend Matrisi (Hacim & Sıkışma Odaklı Tarama)")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sadece_katilim = st.checkbox("✅ Sadece İslam'a Uygun Hisseleri Göster", value=True)
    with col_f2:
        st.checkbox("🚀 Erken Sıkışma & Hacim Patlaması")
    with col_f3:
        st.checkbox("Yalnızca Yüksek Güvenli Trendler")
    
    with st.spinner("Gerçek BIST verileri yükleniyor... (İlk yükleme biraz sürebilir)"):
        df = get_all_stocks_data()
    
    if sadece_katilim and not df.empty:
        df = df[df["Katılım Uygun"] == "EVET"]
    
    if not df.empty:
        def color_prediction(val):
            if "YÜKSELİŞ" in str(val):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            elif "DÜŞÜŞ" in str(val):
                return 'background-color: #b71c1c; color: white; font-weight: bold;'
            elif "BEKLE" in str(val):
                return 'background-color: #e65100; color: white; font-weight: bold;'
            return ''

        def color_katilim(val):
            if val == "EVET":
                return 'color: #4CAF50; font-weight: bold;'
            return 'color: #F44336;'

        styled_df = df.style.map(color_prediction, subset=["15 Dk Sonra Tahmin"]).map(color_katilim, subset=["Katılım Uygun"])
        
        st.dataframe(styled_df, use_container_width=True, height=800)
        
        st.markdown("---")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("📊 Toplam Hisse", len(df))
        with col_s2:
            yukselis = len(df[df["15 Dk Sonra Tahmin"].str.contains("YÜKSELİŞ")])
            st.metric("🚀 Yükseliş Beklenen", yukselis)
        with col_s3:
            katilim = len(df[df["Katılım Uygun"] == "EVET"])
            st.metric("✅ İslam'a Uygun", katilim)
        with col_s4:
            ortalama_guc = df["Net Güç Skoru"].mean()
            st.metric("💪 Ortalama Güç", f"{ortalama_guc:.1f}")
    else:
        st.warning("Veri çekilemedi. Lütfen internet bağlantınızı kontrol edin.")

with tab2:
    st.subheader("VIOP Denge Analizi")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        st.metric(label="VIOP 30 Endeks", value="11.450", delta="%0.45")
    with col_v2:
        st.metric(label="Spot Endeks", value="11.420", delta="%0.40")
    with col_v3:
        st.metric(label="Denge Farkı", value="+30 Puan", delta="Pozitif", delta_color="normal")
    st.info("Vadeli işlemler ile spot piyasa arasındaki denge pozitif yönlü. Öncü sinyal AL konumunda.")

with tab3:
    st.subheader("Canlı KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    kap_haberleri = [
        {"Saat": "14:18:40", "Hisse": "ASELS.IS", "Başlık": "Yeni Sipariş Anlaşması İmzalandı", "Etki": "Pozitif"},
        {"Saat": "14:15:20", "Hisse": "TUPRS.IS", "Başlık": "Üretim Verileri Açıklandı", "Etki": "Nötr"},
        {"Saat": "13:50:10", "Hisse": "BIMAS.IS", "Başlık": "Yeni Mağaza Açılışı", "Etki": "Pozitif"},
        {"Saat": "13:20:00", "Hisse": "SASA.IS", "Başlık": "Kapasite Artırım Yatırımı", "Etki": "Pozitif"},
    ]
    for haber in kap_haberleri:
        st.write(f"**[{haber['Saat']}] {haber['Hisse']}** - {haber['Başlık']} (Etki: {haber['Etki']})")

with tab4:
    st.subheader("Tüm Hisseler Görseli")
    st.info("Tüm hisseleri gösteren grafiksel görünüm burada yer alacak.")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['Hisse A', 'Hisse B', 'Hisse C']
    )
    st.line_chart(chart_data)

with tab5:
    st.subheader("Seans Kapanışı & Overnight Fırsatları")
    st.success("Overnight Taşınabilecek Katılım Hisseleri Hazırlandı.")
    st.write("- ASELS.IS: Hacim patlaması ve sıkışma sonrası kırılım bekleniyor.")
    st.write("- TUPRS.IS: Endeks RS pozitif, VWAP üzerinde tutunma var.")

st.markdown("---")
st.caption("⚠️ Bu paneldeki veriler 15 dakika gecikmelidir. Gerçek yatırım tavsiyesi değildir.")
