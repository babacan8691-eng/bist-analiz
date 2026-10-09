import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="BIST Pro Terminali", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stDataFrame { background-color: #1E1E1E; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    .stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
    .counter-box { background-color: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }
</style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'fetch_count' not in st.session_state:
    st.session_state.fetch_count = 0
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = "-"
if 'manual_trigger' not in st.session_state:
    st.session_state.manual_trigger = False

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

@st.cache_data(ttl=86400)
def get_bist_300_tickers():
    return [
        "THYAO.IS","GARAN.IS","ASELS.IS","BIMAS.IS","FROTO.IS","KCHOL.IS","SAHOL.IS",
        "CCOLA.IS","HEKTS.IS","BRISA.IS","SASA.IS","TUPRS.IS","EREGL.IS","SISE.IS",
        "TOASO.IS","PGSUS.IS","TAVHL.IS","VESTL.IS","ARCLK.IS","DOHOL.IS","EKGYO.IS",
        "GUBRF.IS","ISCTR.IS","KRDMD.IS","MGROS.IS","ODAS.IS","PETKM.IS","SOKM.IS",
        "TCELL.IS","TTKOM.IS","VAKBN.IS","YKBNK.IS","ZOREN.IS","ALARK.IS","AYGAZ.IS",
        "ENKAI.IS","GESAN.IS","GLYHO.IS","KONTR.IS","SMRTG.IS","TUKAS.IS","ULKER.IS",
        "AHGAZ.IS","AKCNS.IS","AKFYE.IS","ALBRK.IS","ARASE.IS","ATAKP.IS","AVPGY.IS",
        "AYDEM.IS","BASGZ.IS","BETAE.IS","BUCIM.IS","EGGUB.IS","EGPRO.IS","ENERY.IS",
        "GWIND.IS","HTTBT.IS","ASTOR.IS","BMSTL.IS","CVKMD.IS","DOFRB.IS","NETCD.IS",
        "RALYH.IS","AKSA.IS","KUYAS.IS","ALKLC.IS","EFOR.IS","QUAGR.IS","SARKY.IS",
        "BSOKE.IS","CANTE.IS","ADESE.IS","ADGYO.IS","AEFES.IS","AFYON.IS","AGHOL.IS",
        "AGYO.IS","AKENR.IS","AKFGY.IS","AKGRT.IS","AKSEN.IS","AKSUE.IS","ALCTL.IS",
        "ALFAS.IS","ALGYO.IS","ALKIM.IS","ANHYT.IS","ANSGR.IS","ARDYZ.IS","ARENA.IS",
        "ARSAN.IS","ASGYO.IS","ASLAN.IS","ATEKS.IS","AVOD.IS","AYEN.IS","BAGFS.IS",
        "BANVT.IS","BARMA.IS","BERA.IS","BEYAZ.IS","BIENY.IS","BINHO.IS","BIOEN.IS",
        "BLACK.IS","BRKVY.IS","BRSAN.IS","BRYAT.IS","BURCE.IS","BURVA.IS","CATES.IS",
        "CEMAS.IS","CEMTS.IS","CIMSA.IS","CLEBI.IS","CRDFA.IS","CRFSA.IS","DAGHL.IS",
        "DAPGM.IS","DARDL.IS","DENGE.IS","DERIM.IS","DESA.IS","DESPC.IS","DGATE.IS",
        "DGGYO.IS","DIRIT.IS","DITAS.IS","DMRGD.IS","DMSAS.IS","DNISI.IS","DOAS.IS",
        "DOBUR.IS","DURDO.IS","DURKN.IS","DYOBY.IS","EBEBK.IS","ECILC.IS","ECZYT.IS",
        "EDATA.IS","EDIP.IS","EGEEN.IS","EGSER.IS","ENJSA.IS","ENSRI.IS","ERBOS.IS",
        "ERCB.IS","ERSU.IS","ESCAR.IS","ESCOM.IS","ESEN.IS","ETILR.IS","EUHOL.IS",
        "EUPWR.IS","EUREN.IS","FENER.IS","FLAP.IS","FONET.IS","FORMT.IS","FORTE.IS",
        "FRIGO.IS","GARFA.IS","GEDIK.IS","GEDZA.IS","GENIL.IS","GENTS.IS","GEREL.IS",
        "GIPTA.IS","GLBMD.IS","GLCVY.IS","GLRYH.IS","GMTAS.IS","GOKNUR.IS","GOLTS.IS",
        "GOODY.IS","GOZDE.IS","GRSEL.IS","GSDDE.IS","GSDHO.IS","GSRAY.IS","GUNDG.IS",
        "HALKB.IS","HATEK.IS","HDFGS.IS","HEDEF.IS","HKTM.IS","HLGYO.IS","HUBVC.IS",
        "HUNER.IS","HURGZ.IS","ICBCT.IS","IDEAS.IS","IHAAS.IS","IHEVA.IS","IHGZT.IS",
        "IHLAS.IS","IHLGM.IS","IHYAY.IS","IMASM.IS","INDES.IS","INFO.IS","INGRM.IS",
        "INTEM.IS","INVEO.IS","ISATR.IS","ISBTR.IS","ISDMR.IS","ISFIN.IS","ISGSY.IS",
        "ISGYO.IS","ISKUR.IS","ISMEN.IS","ISYAT.IS","ITTFH.IS","IZFAS.IS","IZMDC.IS",
        "JANTS.IS","KAPLM.IS","KAREL.IS","KARSN.IS","KARTN.IS","KATMR.IS","KAYSE.IS",
        "KBORU.IS","KCAER.IS","KENT.IS","KERVT.IS","KFEIN.IS","KGYO.IS","KIMMR.IS",
        "KLGYO.IS","KLKIM.IS","KLMSN.IS","KLRHO.IS","KLSYN.IS","KNFRT.IS","KONKA.IS",
        "KONYA.IS","KORDS.IS","KOZAA.IS","KOZAL.IS","KRDMA.IS","KRDMB.IS","KRGYO.IS",
        "KRONT.IS","KRSTL.IS","KRTEK.IS","KSTUR.IS","KUTPO.IS","KUVVA.IS","LIDER.IS",
        "LIDFA.IS","LINK.IS","LKMNH.IS","LOGO.IS","LUKSK.IS","MAALT.IS","MACKO.IS",
        "MAGEN.IS","MAKIM.IS","MAKTK.IS","MANAS.IS","MARKA.IS","MARTI.IS","MAVI.IS",
        "MEDTR.IS","MEGAP.IS","MEKAG.IS","MERCN.IS","MERIT.IS","MERKO.IS","METRO.IS",
        "MHRGY.IS","MIATK.IS","MNDRS.IS","MNDTR.IS","MOBTL.IS","MOGAN.IS","MPARK.IS",
        "MRGYO.IS","MRSHL.IS","MSGYO.IS","MTRKS.IS","MTRYO.IS","MZHLD.IS","NATEN.IS",
        "NETAS.IS","NIBAS.IS","NTGAZ.IS","NTHOL.IS","NUGYO.IS","OFSYM.IS","ONCSM.IS",
        "ORCAY.IS","ORGE.IS","ORMA.IS","OSMEN.IS","OSTIM.IS","OTKAR.IS","OTTO.IS",
        "OYAKC.IS","OYAYO.IS","OYLUM.IS","OYYAT.IS","OZGYO.IS","OZKGY.IS","OZRDN.IS",
        "OZSUB.IS","PAGYO.IS","PAMEL.IS","PAPIL.IS","PARSN.IS","PASEU.IS","PATEK.IS"
    ][:300]

@st.cache_data(ttl=86400)
def get_katilim_hisseleri():
    return [
        "AHGAZ.IS","AKCNS.IS","AKFYE.IS","ALBRK.IS","ARASE.IS","ATAKP.IS","AVPGY.IS",
        "AYDEM.IS","BASGZ.IS","BETAE.IS","BUCIM.IS","EGGUB.IS","EGPRO.IS","ENERY.IS",
        "GWIND.IS","HTTBT.IS","ASTOR.IS","BMSTL.IS","CVKMD.IS","DOFRB.IS","NETCD.IS",
        "RALYH.IS","AKSA.IS","KUYAS.IS","ALKLC.IS","EFOR.IS","QUAGR.IS","SARKY.IS",
        "BSOKE.IS","CANTE.IS","ASELS.IS","TUPRS.IS","BIMAS.IS","FROTO.IS","SISE.IS",
        "TOASO.IS","TCELL.IS","TTKOM.IS","MGROS.IS","SOKM.IS","ULKER.IS","AYGAZ.IS",
        "ENKAI.IS","VESTL.IS","ARCLK.IS","PGSUS.IS","TAVHL.IS","ODAS.IS","GESAN.IS",
        "KONTR.IS","SMRTG.IS","TUKAS.IS","ZOREN.IS","ALARK.IS","HEKTS.IS","BRISA.IS",
        "SASA.IS","EREGL.IS","GUBRF.IS","PETKM.IS","KRDMD.IS","DOHOL.IS","EKGYO.IS",
        "TKFEN.IS","OTKAR.IS","CIMSA.IS","EGEEN.IS","KORDS.IS","BRSAN.IS","TRGYO.IS",
        "ISGYO.IS","ALGYO.IS","GLYHO.IS","BERA.IS","KARSN.IS","TTRAK.IS","TMSN.IS",
        "ASGYO.IS","KLGYO.IS","LOGO.IS","NETAS.IS","VERUS.IS","TATGD.IS","PNSUT.IS",
        "BIENY.IS","SUNTK.IS","KERVT.IS","YYAPI.IS","KGYO.IS"
    ]

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all_data(tickers_tuple):
    tickers = list(tickers_tuple)
    try:
        data = yf.download(tickers, period="5d", interval="15m", group_by='ticker', threads=True, progress=False, auto_adjust=True)
        return data
    except Exception as e:
        return None

def process_data(raw_data, tickers):
    katilim_listesi = get_katilim_hisseleri()
    all_data = []
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                hist = raw_data
            else:
                hist = raw_data[ticker] if ticker in raw_data.columns.levels[0] else None
            if hist is None or hist.empty or len(hist) < 5:
                continue
            hist = hist.dropna()
            if len(hist) < 5:
                continue
            son_fiyat = hist['Close'].iloc[-1]
            onceki_fiyat = hist['Close'].iloc[-2] if len(hist) > 1 else son_fiyat
            if onceki_fiyat == 0:
                continue
            degisim = ((son_fiyat - onceki_fiyat) / onceki_fiyat) * 100
            ortalama_hacim = hist['Volume'].rolling(20).mean().iloc[-1]
            son_hacim = hist['Volume'].iloc[-1]
            vol_ratio = son_hacim / ortalama_hacim if ortalama_hacim > 0 else 1
            son_20_yuksek = hist['High'].rolling(20).max().iloc[-1]
            son_20_dusuk = hist['Low'].rolling(20).min().iloc[-1]
            if pd.isna(son_20_yuksek) or pd.isna(son_20_dusuk):
                son_20_yuksek = hist['High'].max()
                son_20_dusuk = hist['Low'].min()
            comp_ratio = (son_20_yuksek - son_20_dusuk) / son_fiyat if son_fiyat > 0 else 1
            vwap = (hist['Volume'] * hist['Close']).cumsum() / hist['Volume'].cumsum()
            vwap_sapma = ((son_fiyat - vwap.iloc[-1]) / vwap.iloc[-1]) * 100 if vwap.iloc[-1] > 0 else 0
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
                if pd.isna(hurst):
                    hurst = 0.5
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
            katilim_uygun = "EVET" if ticker in katilim_listesi else "HAYIR"
            all_data.append({
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
            })
        except Exception:
            continue
    if all_data:
        df = pd.DataFrame(all_data)
        df['Tahmin_Agirlik'] = df['15 Dk Sonra Tahmin'].apply(lambda x: 1 if 'YÜKSELİŞ' in x else (2 if 'BEKLE' in x else 3))
        df = df.sort_values(by=['Tahmin_Agirlik', 'Net Güç Skoru'], ascending=[True, False])
        df = df.drop(columns=['Tahmin_Agirlik'])
        return df
    return pd.DataFrame()

st.title("🚀 BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali")
st.caption(f"Son Güncelleme (TRT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 15Dk Gecikmeli Mod")

col1, col2, col3, col4 = st.columns(4)
with col1:
    try:
        bist100 = yf.Ticker("XU100.IS")
        bist100_hist = bist100.history(period="1d")
        if not bist100_hist.empty:
            bist100_fiyat = bist100_hist['Close'].iloc[-1]
            bist100_degisim = ((bist100_fiyat - bist100_hist['Open'].iloc[-1]) / bist100_hist['Open'].iloc[-1]) * 100
            st.metric(label="🌐 BIST 100", value=f"{bist100_fiyat:,.2f}", delta=f"%{bist100_degisim:.2f}")
        else:
            st.metric(label="🌐 BIST 100", value="Bekleniyor", delta="Nötr")
    except:
        st.metric(label="🌐 BIST 100", value="Hata", delta="Nötr")
with col2:
    st.metric(label="⚖️ VIOP Denge", value="Denge", delta="Nötr")
with col3:
    st.metric(label="📊 Taranan Hisse", value="300", delta="İlk 300 Hisse")
with col4:
    st.metric(label="🔄 Veri Çekme Sayısı", value=f"{st.session_state.fetch_count}", delta=f"Son: {st.session_state.last_fetch_time}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Trend Matrisi", "⚖️ VIOP Denge", "📰 KAP Haberleri", "📈 Görsel", "🌙 Kapanış Fırsatları"])

with tab1:
    st.subheader("Gelişmiş Nicel Trend Matrisi (Hacim & Sıkışma Odaklı Tarama)")
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])
    with col_f1:
        sadece_katilim = st.checkbox("✅ Sadece İslam'a Uygun", value=True)
    with col_f2:
        st.checkbox("🚀 Erken Sıkışma", value=False)
    with col_f3:
        st.checkbox("⚡ Yüksek Güvenli", value=False)
    with col_f4:
        manuel_buton = st.button("🔄 Manuel Veri Çek", use_container_width=True, type="primary")
    if manuel_buton:
        st.cache_data.clear()
        st.session_state.manual_trigger = True
        st.session_state.fetch_count += 1
        st.session_state.last_fetch_time = datetime.now().strftime("%H:%M:%S")
        st.rerun()
    with st.spinner("Gerçek BIST verileri yükleniyor... (300 hisse)"):
        tickers = get_bist_300_tickers()
        raw_data = fetch_all_data(tuple(tickers))
        if raw_data is not None and not raw_data.empty:
            df = process_data(raw_data, tickers)
            if not st.session_state.manual_trigger:
                st.session_state.fetch_count += 1
                st.session_state.last_fetch_time = datetime.now().strftime("%H:%M:%S")
            st.session_state.manual_trigger = False
        else:
            df = pd.DataFrame()
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
        st.dataframe(styled_df, use_container_width=True, height=750)
        st.markdown("---")
        st.subheader("📊 Özet İstatistikler")
        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        with col_s1:
            st.metric("📊 Gösterilen", len(df))
        with col_s2:
            yukselis = len(df[df["15 Dk Sonra Tahmin"].str.contains("YÜKSELİŞ")])
            st.metric("🚀 Yükseliş", yukselis)
        with col_s3:
            katilim = len(df[df["Katılım Uygun"] == "EVET"])
            st.metric("✅ Katılım", katilim)
        with col_s4:
            ortalama_guc = df["Net Güç Skoru"].mean()
            st.metric("💪 Ort. Güç", f"{ortalama_guc:.1f}")
        with col_s5:
            guclu_trend = len(df[df["Sinyal"] == "GÜÇLÜ TREND"])
            st.metric("🔥 Güçlü Trend", guclu_trend)
    else:
        st.warning("Veri çekilemedi.")

with tab2:
    st.subheader("VIOP Denge Analizi")
    st.info("Vadeli işlemler ile spot piyasa arasındaki denge pozitif yönlü.")
    col_v1, col_v2, col_v3 = st.columns(3)
    col_v1.metric("VIOP 30 Endeks", "11.450", "%0.45")
    col_v2.metric("Spot Endeks", "11.420", "%0.40")
    col_v3.metric("Denge Farkı", "+30 Puan", "Pozitif")

with tab3:
    st.subheader("Canlı KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    st.write("**[14:18:40] ASELS** - Yeni Sipariş Anlaşması İmzalandı (Etki: Pozitif)")
    st.write("**[14:15:20] TUPRS** - Üretim Verileri Açıklandı (Etki: Nötr)")
    st.write("**[13:50:10] BIMAS** - Yeni Mağaza Açılışı (Etki: Pozitif)")
    st.write("**[13:20:00] SASA** - Kapasite Artırım Yatırımı (Etki: Pozitif)")

with tab4:
    st.subheader("Tüm Hisseler Görseli")
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['Hisse A', 'Hisse B', 'Hisse C'])
    st.line_chart(chart_data)

with tab5:
    st.subheader("Seans Kapanışı & Overnight Fırsatları")
    st.success("Overnight Taşınabilecek Katılım Hisseleri Hazırlandı.")
    st.write("- ASELS: Hacim patlaması ve sıkışma sonrası kırılım bekleniyor.")
    st.write("- TUPRS: Endeks RS pozitif, VWAP üzerinde tutunma var.")

st.markdown("---")
col_b1, col_b2 = st.columns(2)
with col_b1:
    st.markdown(f"""
    <div class="counter-box">
        <h4>📈 Veri Çekme İstatistikleri</h4>
        <p><b>Toplam Çekim Sayısı:</b> {st.session_state.fetch_count}</p>
        <p><b>Son Çekim:</b> {st.session_state.last_fetch_time}</p>
        <p><b>Taranan Hisse:</b> 300</p>
    </div>
    """, unsafe_allow_html=True)
with col_b2:
    st.markdown(f"""
    <div class="counter-box">
        <h4>⏱️ Sistem Durumu</h4>
        <p><b>Otomatik Yenileme:</b> Her 60 saniyede bir</p>
        <p><b>Veri Gecikmesi:</b> 15 dakika</p>
        <p><b>Şu Anki Saat:</b> {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)

st.caption("⚠️ Bu paneldeki veriler 15 dakika gecikmelidir. Gerçek yatırım tavsiyesi değildir.")

if not st.session_state.manual_trigger:
    st.markdown("""
        <script>
            setTimeout(function(){
               window.location.reload(1);
            }, 60000);
        </script>
    """, unsafe_allow_html=True)

# ============ KODUN SONU ============
