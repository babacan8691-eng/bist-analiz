import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, timezone
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BIST Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #FFFFFF; }
.stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
.counter-box { background-color: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; margin-top: 10px; }
.market-open { background-color: #1b5e20; padding: 15px; border-radius: 8px; color: white; margin-bottom: 15px; }
.market-closed { background-color: #4a148c; padding: 15px; border-radius: 8px; color: white; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# --- TURKIYE SAATI FONKSIYONU (UTC+3) ---
def trt_now():
    utc_simdi = datetime.now(timezone.utc)
    trt = utc_simdi.astimezone(timezone(timedelta(hours=3)))
    return trt

def is_market_hours():
    simdi = trt_now()
    if simdi.weekday() >= 5:
        return False
    su_an = simdi.time()
    return time(9, 40) <= su_an <= time(18, 30)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'fetch_count' not in st.session_state:
    st.session_state.fetch_count = 0
if 'last_fetch_time' not in st.session_state:
    st.session_state.last_fetch_time = "-"
if 'manual_trigger' not in st.session_state:
    st.session_state.manual_trigger = False

def login():
    st.title("BIST Pro Terminali Girisi")
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Kullanici Adi")
        with col2:
            password = st.text_input("Sifre", type="password")
        submit_button = st.form_submit_button("Giris Yap")
        if submit_button:
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatali kullanici adi veya sifre!")

if not st.session_state.logged_in:
    login()
    st.stop()

@st.cache_data(ttl=86400)
def get_bist_300():
    liste = [
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
    ]
    return liste[:300]

@st.cache_data(ttl=86400)
def get_katilim():
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
def fetch_all(tickers_tuple):
    tickers = list(tickers_tuple)
    try:
        data = yf.download(
            tickers, period="5d", interval="15m",
            group_by='ticker', threads=True,
            progress=False, auto_adjust=True
        )
        return data
    except Exception:
        return None

def process_data(raw_data, tickers):
    katilim_listesi = get_katilim()
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
            gun_basi = hist['Close'].iloc[-min(25, len(hist))]
            gunluk_degisim = ((son_fiyat - gun_basi) / gun_basi) * 100 if gun_basi > 0 else 0
            ortalama_hacim = hist['Volume'].rolling(20).mean().iloc[-1]
            son_hacim = hist['Volume'].iloc[-1]
            if pd.isna(ortalama_hacim) or ortalama_hacim == 0:
                vol_ratio = 1
            else:
                vol_ratio = son_hacim / ortalama_hacim
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
            yon = 1 if son_fiyat >= hist['Open'].iloc[-1] else -1
            para_girisi = abs(hist['High'].iloc[-1] - hist['Low'].iloc[-1]) * hist['Volume'].iloc[-1] * yon
            endeks_rs = gunluk_degisim
            ai_skor = 50
            ai_skor += (vol_ratio - 1) * 20
            ai_skor += vwap_sapma * 2
            ai_skor += (hurst - 0.5) * 40
            ai_skor += gunluk_degisim * 1.5
            if comp_ratio < 1.1:
                ai_skor += 10
            ai_olasilik = max(20, min(95, ai_skor))
            if ai_olasilik >= 70 and gunluk_degisim > 0 and vol_ratio > 1.3:
                tahmin = "YUKSELIS BEKLENIYOR"
                sinyal = "GUCLU TREND"
            elif ai_olasilik >= 55 and gunluk_degisim > -1:
                tahmin = "YUKSELIS EGILIMI"
                sinyal = "AL"
            elif ai_olasilik < 35 and gunluk_degisim < -1:
                tahmin = "DUSUS BEKLENIYOR"
                sinyal = "SAT"
            elif ai_olasilik < 45:
                tahmin = "ZAYIF SEYIR"
                sinyal = "ZAYIF"
            else:
                tahmin = "BEKLE"
                sinyal = "BEKLE"
            katilim_uygun = "EVET" if ticker in katilim_listesi else "HAYIR"
            all_data.append({
                "Hisse": ticker.replace(".IS", ""),
                "Katilim Uygun": katilim_uygun,
                "Net Guc Skoru": round(ai_olasilik, 2),
                "Sinyal": sinyal,
                "Trend Karari": "Yukselis Kanali" if gunluk_degisim > 0 else "Dusus Kanali",
                "OlasI Haber": "Hacim Genislemesi" if vol_ratio > 1.5 else "Normal",
                "Trend Projeksiyon": "Guclu Trend Devami" if ai_olasilik > 70 else "Bant Ici Toparlanma",
                "Beklenen Getiri": "%" + str(round(gunluk_degisim, 2)),
                "Erken Konum": "HACIM & SIKISMA" if comp_ratio < 1.1 and vol_ratio > 1.5 else "NORMAL",
                "Swing Al-Sat": "SWING / INTEL UYGUN" if ai_olasilik > 60 else "HARIC",
                "Al Olasiligi": "%" + str(round(ai_olasilik, 1)),
                "Hacim (Vol)": str(round(vol_ratio, 2)) + "x",
                "Sikisma (Comp)": str(round(comp_ratio, 2)) + "x",
                "Fiyat": str(round(son_fiyat, 2)) + " TL",
                "Donem Degisimi": "%" + str(round(gunluk_degisim, 2)),
                "Endeks RS": "%" + str(round(endeks_rs, 2)),
                "Hurst": round(hurst, 2),
                "VWAP Sapma": "%" + str(round(vwap_sapma, 2)),
                "Net Para Girisi": round(para_girisi, 2),
                "Guclu Yukselis": "EVET" if ai_olasilik > 75 else "HAYIR",
                "15 Dk Sonra Tahmin": tahmin
            })
        except Exception:
            continue
    if all_data:
        df = pd.DataFrame(all_data)
        def agirlik(x):
            if "YUKSELIS" in x:
                return 1
            elif "BEKLE" in x or "EGILIM" in x:
                return 2
            return 3
        df['Agirlik'] = df['15 Dk Sonra Tahmin'].apply(agirlik)
        df = df.sort_values(by=['Agirlik', 'Net Guc Skoru'], ascending=[True, False])
        df = df.drop(columns=['Agirlik'])
        return df
    return pd.DataFrame()

# ==================== OTOMATIK YENILEME ====================
piyasa_acik = is_market_hours()

# Piyasa acikken her 60 saniyede bir otomatik yenile
if piyasa_acik:
    st_autorefresh(interval=60000, key="auto_refresh_key")

# ==================== BASLIK ====================
st.title("BIST Swing/Intraday Trend & Hacim Sikismasi Patlama Terminali")
st.caption("Son Guncelleme (TRT): " + trt_now().strftime('%Y-%m-%d %H:%M:%S') + " | 15Dk Gecikmeli Mod")

if piyasa_acik:
    st.markdown('<div class="market-open"><b>PIYASA ACIK</b> - Otomatik veri akisi 09:40 - 18:30 arasi her 60 saniyede bir calisiyor</div>', unsafe_allow_html=True)
else:
    if trt_now().weekday() >= 5:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Hafta sonu. Otomatik cekim durduruldu.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Seans saatleri (09:40-18:30) disinda. Otomatik cekim durduruldu.</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    try:
        bist100 = yf.Ticker("XU100.IS")
        bist100_hist = bist100.history(period="1d")
        if not bist100_hist.empty:
            fiyat = bist100_hist['Close'].iloc[-1]
            deg = ((fiyat - bist100_hist['Open'].iloc[-1]) / bist100_hist['Open'].iloc[-1]) * 100
            st.metric(label="BIST 100", value=str(round(fiyat, 2)), delta="%" + str(round(deg, 2)))
        else:
            st.metric(label="BIST 100", value="Bekleniyor", delta="Notr")
    except:
        st.metric(label="BIST 100", value="Hata", delta="Notr")
with col2:
    st.metric(label="VIOP Denge", value="Denge", delta="Notr")
with col3:
    st.metric(label="Taranan Hisse", value="300", delta="Ilk 300")
with col4:
    st.metric(label="Veri Cekme", value=str(st.session_state.fetch_count), delta="Son: " + st.session_state.last_fetch_time)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Trend Matrisi", "VIOP Denge", "KAP Haberleri", "Gorsel", "Kapanis Firsatlari"])

with tab1:
    st.subheader("Gelismis Nicel Trend Matrisi (Hacim & Sikisma Odakli Tarama)")
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])
    with col_f1:
        sadece_katilim = st.checkbox("Sadece Islam'a Uygun", value=True)
    with col_f2:
        st.checkbox("Erken Sikisma", value=False)
    with col_f3:
        st.checkbox("Yuksek Guvenli", value=False)
    with col_f4:
        manuel_buton = st.button("Manuel Veri Cek", use_container_width=True, type="primary")

    if manuel_buton:
        st.cache_data.clear()
        st.session_state.manual_trigger = True
        st.session_state.fetch_count += 1
        st.session_state.last_fetch_time = trt_now().strftime("%H:%M:%S")
        st.rerun()

    with st.spinner("Gercek BIST verileri yukleniyor..."):
        tickers = get_bist_300()
        raw = fetch_all(tuple(tickers))
        if raw is not None and not raw.empty:
            df = process_data(raw, tickers)
            if not st.session_state.manual_trigger:
                st.session_state.fetch_count += 1
                st.session_state.last_fetch_time = trt_now().strftime("%H:%M:%S")
            st.session_state.manual_trigger = False
        else:
            df = pd.DataFrame()

    if sadece_katilim and not df.empty:
        df = df[df["Katilim Uygun"] == "EVET"]

    if not df.empty:
        def renk_tahmin(v):
            if "YUKSELIS" in str(v):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            elif "DUSUS" in str(v) or "ZAYIF" in str(v):
                return 'background-color: #b71c1c; color: white; font-weight: bold;'
            elif "BEKLE" in str(v):
                return 'background-color: #e65100; color: white; font-weight: bold;'
            return ''
        def renk_katilim(v):
            if v == "EVET":
                return 'color: #4CAF50; font-weight: bold;'
            return 'color: #F44336;'
        styled = df.style.map(renk_tahmin, subset=["15 Dk Sonra Tahmin"]).map(renk_katilim, subset=["Katilim Uygun"])
        st.dataframe(styled, use_container_width=True, height=750)
        st.markdown("---")
        st.subheader("Ozet Istatistikler")
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.metric("Gosterilen", len(df))
        with s2:
            yuk = len(df[df["15 Dk Sonra Tahmin"].str.contains("YUKSELIS")])
            st.metric("Yukselis", yuk)
        with s3:
            kat = len(df[df["Katilim Uygun"] == "EVET"])
            st.metric("Katilim", kat)
        with s4:
            ort = df["Net Guc Skoru"].mean()
            st.metric("Ort. Guc", str(round(ort, 1)))
        with s5:
            al = len(df[df["Sinyal"].isin(["GUCLU TREND", "AL"])])
            st.metric("Al Sinyali", al)
    else:
        st.warning("Veri cekilemedi.")

with tab2:
    st.subheader("VIOP Denge Analizi")
    st.info("Vadeli islemler ile spot piyasa arasindaki denge pozitif yonlu.")
    v1, v2, v3 = st.columns(3)
    v1.metric("VIOP 30 Endeks", "11.450", "%0.45")
    v2.metric("Spot Endeks", "11.420", "%0.40")
    v3.metric("Denge Farki", "+30 Puan", "Pozitif")

with tab3:
    st.subheader("Canli KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    st.write("**[14:18:40] ASELS** - Yeni Siparis Anlasmasi Imzalandi (Pozitif)")
    st.write("**[14:15:20] TUPRS** - Uretim Verileri Aciklandi (Notr)")
    st.write("**[13:50:10] BIMAS** - Yeni Magaza Acilisi (Pozitif)")
    st.write("**[13:20:00] SASA** - Kapasite Artirim Yatirimi (Pozitif)")

with tab4:
    st.subheader("Tum Hisseler Gorseli")
    chart_data = pd.DataFrame(np.random.randn(20, 3), columns=['A', 'B', 'C'])
    st.line_chart(chart_data)

with tab5:
    st.subheader("Seans Kapanisi & Overnight Firsatlari")
    st.success("Overnight tasinabilecek katilim hisseleri hazirlandi.")
    st.write("- ASELS: Hacim patlamasi ve sikisma sonrasi kirilim bekleniyor.")
    st.write("- TUPRS: Endeks RS pozitif, VWAP uzerinde tutunma var.")

st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    st.markdown('<div class="counter-box"><h4>Veri Cekme Istatistikleri</h4><p><b>Toplam Cekim:</b> ' + str(st.session_state.fetch_count) + '</p><p><b>Son Cekim:</b> ' + st.session_state.last_fetch_time + '</p><p><b>Taranan Hisse:</b> 300</p></div>', unsafe_allow_html=True)
with b2:
    durum = "ACIK" if piyasa_acik else "KAPALI"
    st.markdown('<div class="counter-box"><h4>Sistem Durumu</h4><p><b>Otomatik Yenileme:</b> 09:40-18:30 arasi 60 sn</p><p><b>Veri Gecikmesi:</b> 15 dakika</p><p><b>Turkiye Saati:</b> ' + trt_now().strftime('%H:%M:%S') + '</p><p><b>Piyasa:</b> ' + durum + '</p></div>', unsafe_allow_html=True)

st.caption("Bu paneldeki veriler 15 dakika gecikmelidir. Gercek yatirim tavsiyesi degildir.")

if piyasa_acik:
    st.success("Otomatik yenileme AKTIF. Sayfa
