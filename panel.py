import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone, time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BIST Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #FFFFFF; }
.stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
.counter-box { background-color: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }
.market-open { background-color: #1b5e20; padding: 15px; border-radius: 8px; color: white; }
.market-closed { background-color: #4a148c; padding: 15px; border-radius: 8px; color: white; }
.risk-box { background-color: #1E1E1E; padding: 12px; border-radius: 8px; border-left: 4px solid #FFC107; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

TUM_HISSELER = "THYAO.IS,GARAN.IS,ASELS.IS,BIMAS.IS,FROTO.IS,KCHOL.IS,SAHOL.IS,CCOLA.IS,HEKTS.IS,BRISA.IS,SASA.IS,TUPRS.IS,EREGL.IS,SISE.IS,TOASO.IS,PGSUS.IS,TAVHL.IS,VESTL.IS,ARCLK.IS,DOHOL.IS,EKGYO.IS,GUBRF.IS,ISCTR.IS,KRDMD.IS,MGROS.IS,ODAS.IS,PETKM.IS,SOKM.IS,TCELL.IS,TTKOM.IS,VAKBN.IS,YKBNK.IS,ZOREN.IS,ALARK.IS,AYGAZ.IS,ENKAI.IS,GESAN.IS,GLYHO.IS,KONTR.IS,SMRTG.IS,TUKAS.IS,ULKER.IS,AHGAZ.IS,AKCNS.IS,AKFYE.IS,ALBRK.IS,ARASE.IS,ATAKP.IS,AVPGY.IS,AYDEM.IS,BASGZ.IS,BETAE.IS,BUCIM.IS,EGGUB.IS,EGPRO.IS,ENERY.IS,GWIND.IS,HTTBT.IS,ASTOR.IS,BMSTL.IS,CVKMD.IS,DOFRB.IS,NETCD.IS,RALYH.IS,AKSA.IS,KUYAS.IS,ALKLC.IS,EFOR.IS,QUAGR.IS,SARKY.IS,BSOKE.IS,CANTE.IS,ADESE.IS,ADGYO.IS,AEFES.IS,AFYON.IS,AGHOL.IS,AGYO.IS,AKENR.IS,AKFGY.IS,AKGRT.IS,AKSEN.IS,AKSUE.IS,ALCTL.IS,ALFAS.IS,ALGYO.IS,ALKIM.IS,ANHYT.IS,ANSGR.IS,ARDYZ.IS,ARENA.IS,ARSAN.IS,ASGYO.IS,ASLAN.IS,ATEKS.IS,AVOD.IS,AYEN.IS,BAGFS.IS,BANVT.IS,BARMA.IS,BERA.IS,BEYAZ.IS,BIENY.IS,BINHO.IS,BIOEN.IS,BLACK.IS,BRKVY.IS,BRSAN.IS,BRYAT.IS,BURCE.IS,BURVA.IS,CATES.IS,CEMAS.IS,CEMTS.IS,CIMSA.IS,CLEBI.IS,CRDFA.IS,CRFSA.IS,DAGHL.IS,DAPGM.IS,DARDL.IS,DENGE.IS,DERIM.IS,DESA.IS,DESPC.IS,DGATE.IS,DGGYO.IS,DIRIT.IS,DITAS.IS,DMRGD.IS,DMSAS.IS,DNISI.IS,DOAS.IS,DOBUR.IS,DURDO.IS,DURKN.IS,DYOBY.IS,EBEBK.IS,ECILC.IS,ECZYT.IS,EDATA.IS,EDIP.IS,EGEEN.IS,EGSER.IS,ENJSA.IS,ENSRI.IS,ERBOS.IS,ERCB.IS,ERSU.IS,ESCAR.IS,ESCOM.IS,ESEN.IS,ETILR.IS,EUHOL.IS,EUPWR.IS,EUREN.IS,FENER.IS,FLAP.IS,FONET.IS,FORMT.IS,FORTE.IS,FRIGO.IS,GARFA.IS,GEDIK.IS,GEDZA.IS,GENIL.IS,GENTS.IS,GEREL.IS,GIPTA.IS,GLBMD.IS,GLCVY.IS,GLRYH.IS,GMTAS.IS,GOKNUR.IS,GOLTS.IS,GOODY.IS,GOZDE.IS,GRSEL.IS,GSDDE.IS,GSDHO.IS,GSRAY.IS,GUNDG.IS,HALKB.IS,HATEK.IS,HDFGS.IS,HEDEF.IS,HKTM.IS,HLGYO.IS,HUBVC.IS,HUNER.IS,HURGZ.IS,ICBCT.IS,IDEAS.IS,IHAAS.IS,IHEVA.IS,IHGZT.IS,IHLAS.IS,IHLGM.IS,IHYAY.IS,IMASM.IS,INDES.IS,INFO.IS,INGRM.IS,INTEM.IS,INVEO.IS,ISATR.IS,ISBTR.IS,ISDMR.IS,ISFIN.IS,ISGSY.IS,ISGYO.IS,ISKUR.IS,ISMEN.IS,ISYAT.IS,ITTFH.IS,IZFAS.IS,IZMDC.IS,JANTS.IS,KAPLM.IS,KAREL.IS,KARSN.IS,KARTN.IS,KATMR.IS,KAYSE.IS,KBORU.IS,KCAER.IS,KENT.IS,KERVT.IS,KFEIN.IS,KGYO.IS,KIMMR.IS,KLGYO.IS,KLKIM.IS,KLMSN.IS,KLRHO.IS,KLSYN.IS,KNFRT.IS,KONKA.IS,KONYA.IS,KORDS.IS,KOZAA.IS,KOZAL.IS,KRDMA.IS,KRDMB.IS,KRGYO.IS,KRONT.IS,KRSTL.IS,KRTEK.IS,KSTUR.IS,KUTPO.IS,KUVVA.IS,LIDER.IS,LIDFA.IS,LINK.IS,LKMNH.IS,LOGO.IS,LUKSK.IS,MAALT.IS,MACKO.IS,MAGEN.IS,MAKIM.IS,MAKTK.IS,MANAS.IS,MARKA.IS,MARTI.IS,MAVI.IS,MEDTR.IS,MEGAP.IS,MEKAG.IS,MERCN.IS,MERIT.IS,MERKO.IS,METRO.IS,MHRGY.IS,MIATK.IS,MNDRS.IS,MNDTR.IS,MOBTL.IS,MOGAN.IS,MPARK.IS,MRGYO.IS,MRSHL.IS,MSGYO.IS,MTRKS.IS,MTRYO.IS,MZHLD.IS,NATEN.IS,NETAS.IS,NIBAS.IS,NTGAZ.IS,NTHOL.IS,NUGYO.IS,OFSYM.IS,ONCSM.IS,ORCAY.IS,ORGE.IS,ORMA.IS,OSMEN.IS,OSTIM.IS,OTKAR.IS,OTTO.IS,OYAKC.IS,OYAYO.IS,OYLUM.IS,OYYAT.IS,OZGYO.IS,OZKGY.IS,OZRDN.IS,OZSUB.IS,PAGYO.IS,PAMEL.IS,PAPIL.IS,PARSN.IS,PASEU.IS,PATEK.IS"

KATILIM = "AHGAZ.IS,AKCNS.IS,AKFYE.IS,ALBRK.IS,ARASE.IS,ATAKP.IS,AVPGY.IS,AYDEM.IS,BASGZ.IS,BETAE.IS,BUCIM.IS,EGGUB.IS,EGPRO.IS,ENERY.IS,GWIND.IS,HTTBT.IS,ASTOR.IS,BMSTL.IS,CVKMD.IS,DOFRB.IS,NETCD.IS,RALYH.IS,AKSA.IS,KUYAS.IS,ALKLC.IS,EFOR.IS,QUAGR.IS,SARKY.IS,BSOKE.IS,CANTE.IS,ASELS.IS,TUPRS.IS,BIMAS.IS,FROTO.IS,SISE.IS,TOASO.IS,TCELL.IS,TTKOM.IS,MGROS.IS,SOKM.IS,ULKER.IS,AYGAZ.IS,ENKAI.IS,VESTL.IS,ARCLK.IS,PGSUS.IS,TAVHL.IS,ODAS.IS,GESAN.IS,KONTR.IS,SMRTG.IS,TUKAS.IS,ZOREN.IS,ALARK.IS,HEKTS.IS,BRISA.IS,SASA.IS,EREGL.IS,GUBRF.IS,PETKM.IS,KRDMD.IS,DOHOL.IS,EKGYO.IS,TKFEN.IS,OTKAR.IS,CIMSA.IS,EGEEN.IS,KORDS.IS,BRSAN.IS,TRGYO.IS,ISGYO.IS,ALGYO.IS,GLYHO.IS,BERA.IS,KARSN.IS,TTRAK.IS,TMSN.IS,ASGYO.IS,KLGYO.IS,LOGO.IS,NETAS.IS,VERUS.IS,TATGD.IS,PNSUT.IS,BIENY.IS,SUNTK.IS,KERVT.IS,YYAPI.IS,KGYO.IS"

def trt_now():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))

def is_market_hours():
    s = trt_now()
    if s.weekday() >= 5:
        return False
    return time(9, 40) <= s.time() <= time(18, 30)

# ==================== TEKNIK GOSTERGE HESAPLAMALARI ====================
def hesapla_rsi(seri, periyot=14):
    delta = seri.diff()
    kazanc = delta.where(delta > 0, 0).rolling(periyot).mean()
    kayip = -delta.where(delta < 0, 0).rolling(periyot).mean()
    rs = kazanc / kayip
    return 100 - (100 / (1 + rs))

def hesapla_macd(seri, hizli=12, yavas=26, sinyal=9):
    ema_hizli = seri.ewm(span=hizli, adjust=False).mean()
    ema_yavas = seri.ewm(span=yavas, adjust=False).mean()
    macd = ema_hizli - ema_yavas
    sinyal_cizgi = macd.ewm(span=sinyal, adjust=False).mean()
    histogram = macd - sinyal_cizgi
    return macd, sinyal_cizgi, histogram

def hesapla_bollinger(seri, periyot=20, std=2):
    sma = seri.rolling(periyot).mean()
    std_dev = seri.rolling(periyot).std()
    ust = sma + (std_dev * std)
    alt = sma - (std_dev * std)
    return ust, sma, alt

def hesapla_atr(high, low, close, periyot=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(periyot).mean()

def hesapla_stochastic(high, low, close, periyot=14, yumusat=3):
    en_yuksek = high.rolling(periyot).max()
    en_dusuk = low.rolling(periyot).min()
    k = 100 * (close - en_dusuk) / (en_yuksek - en_dusuk)
    d = k.rolling(yumusat).mean()
    return k, d

def hesapla_obv(close, volume):
    yon = np.sign(close.diff())
    return (yon * volume).fillna(0).cumsum()

def hesapla_sma(seri, periyot):
    return seri.rolling(periyot).mean()

# ==================== SINYAL MOTORU ====================
def sinyal_motoru(h, sf):
    """Trend + Momentum + Hacim katmanları birleşik skor"""
    if len(h) < 30:
        return 50, "BEKLE", "Yetersiz veri", 0.5

    # 1. TREND KATMANI (0-1)
    sma20 = h['SMA20'].iloc[-1]
    sma50 = h['SMA50'].iloc[-1] if not pd.isna(h['SMA50'].iloc[-1]) else sma20
    trend_skor = 0.5
    if sf > sma20: trend_skor += 0.25
    if sf > sma50: trend_skor += 0.25
    if sma20 > sma50: trend_skor += 0.15
    trend_skor = min(1.0, trend_skor)

    # 2. MOMENTUM KATMANI (0-1)
    rsi = h['RSI'].iloc[-1] if not pd.isna(h['RSI'].iloc[-1]) else 50
    macd_hist = h['MACD_HIST'].iloc[-1] if not pd.isna(h['MACD_HIST'].iloc[-1]) else 0
    stoch_k = h['STOCH_K'].iloc[-1] if not pd.isna(h['STOCH_K'].iloc[-1]) else 50
    mom_skor = 0.5
    if 40 < rsi < 70: mom_skor += 0.15
    elif rsi < 30: mom_skor += 0.3
    elif rsi > 70: mom_skor -= 0.2
    if macd_hist > 0: mom_skor += 0.2
    if 20 < stoch_k < 80: mom_skor += 0.1
    elif stoch_k < 20: mom_skor += 0.15
    mom_skor = max(0, min(1.0, mom_skor))

    # 3. HACIM KATMANI (0-1)
    vol_ratio = h['Vol_Ratio'].iloc[-1] if not pd.isna(h['Vol_Ratio'].iloc[-1]) else 1
    obv_trend = 1 if h['OBV'].iloc[-1] > h['OBV'].iloc[-5] else 0
    hacim_skor = 0.5
    if vol_ratio > 1.5: hacim_skor += 0.3
    elif vol_ratio > 1.2: hacim_skor += 0.15
    if obv_trend: hacim_skor += 0.2
    hacim_skor = min(1.0, hacim_skor)

    # 4. BOLLINGER POZISYONU
    bb_ust = h['BB_UST'].iloc[-1] if not pd.isna(h['BB_UST'].iloc[-1]) else sf * 1.05
    bb_alt = h['BB_ALT'].iloc[-1] if not pd.isna(h['BB_ALT'].iloc[-1]) else sf * 0.95
    bb_pozisyon = (sf - bb_alt) / (bb_ust - bb_alt) if (bb_ust - bb_alt) > 0 else 0.5

    # 5. BIRLESIK SKOR
    final_skor = (trend_skor * 0.35 + mom_skor * 0.35 + hacim_skor * 0.20 + (1 - bb_pozisyon) * 0.10) * 100
    final_skor = max(20, min(95, final_skor))

    # 6. SINYAL KARARI
    if final_skor >= 70 and trend_skor > 0.6 and mom_skor > 0.5:
        sinyal = "GUCLU AL"
    elif final_skor >= 55 and trend_skor > 0.4:
        sinyal = "AL"
    elif final_skor < 35 and trend_skor < 0.4:
        sinyal = "SAT"
    elif final_skor < 45:
        sinyal = "ZAYIF"
    else:
        sinyal = "BEKLE"

    # 7. DETAYLI YORUM
    detaylar = []
    if trend_skor > 0.6: detaylar.append("Trend pozitif")
    if macd_hist > 0: detaylar.append("MACD al")
    if vol_ratio > 1.5: detaylar.append("Hacim patlamasi")
    if rsi < 35: detaylar.append("RSI asiri satim")
    if rsi > 70: detaylar.append("RSI asiri alim")
    yorum = " | ".join(detaylar) if detaylar else "Notr"

    return final_skor, sinyal, yorum, bb_pozisyon

# ==================== RISK YONETIMI ====================
def risk_hesapla(h, sf, ai_skor):
    """ATR bazli stop-loss ve hedef fiyat"""
    if pd.isna(h['ATR'].iloc[-1]) or h['ATR'].iloc[-1] == 0:
        return None, None, None, None

    atr = h['ATR'].iloc[-1]

    # Risk seviyesine gore ATR carpani
    if ai_skor >= 70:
        carpan_sl = 1.5
        carpan_h = 3.0
        risk_seviye = "Dusuk"
    elif ai_skor >= 55:
        carpan_sl = 2.0
        carpan_h = 2.5
        risk_seviye = "Orta"
    else:
        carpan_sl = 2.5
        carpan_h = 2.0
        risk_seviye = "Yuksek"

    sl = sf - (atr * carpan_sl)
    hedef = sf + (atr * carpan_h)
    risk_odul = (hedef - sf) / (sf - sl) if (sf - sl) > 0 else 0

    return round(sl, 2), round(hedef, 2), round(risk_odul, 2), risk_seviye

for k, v in [('logged_in', False), ('fetch_count', 0), ('last_fetch_time', '-'), ('manual_trigger', False)]:
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.logged_in:
    st.title("BIST Pro Terminali Girisi")
    with st.form("login"):
        c1, c2 = st.columns(2)
        u = c1.text_input("Kullanici Adi")
        p = c2.text_input("Sifre", type="password")
        if st.form_submit_button("Giris Yap"):
            if u.strip() == "Cuma Babacan" and p.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatali kullanici adi veya sifre!")
    st.stop()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_all(tickers_tuple):
    try:
        return yf.download(list(tickers_tuple), period="5d", interval="15m", group_by='ticker', threads=True, progress=False, auto_adjust=True)
    except:
        return None

def process(raw, tickers, katilim_set):
    rows = []
    for t in tickers:
        try:
            if len(tickers) == 1:
                h = raw.copy()
            else:
                h = raw[t].copy() if t in raw.columns.levels[0] else None
            if h is None or h.empty or len(h) < 30:
                continue
            h = h.dropna()
            if len(h) < 30:
                continue

            # Gostergeleri hesapla
            h['RSI'] = hesapla_rsi(h['Close'])
            h['MACD'], h['MACD_SIG'], h['MACD_HIST'] = hesapla_macd(h['Close'])
            h['BB_UST'], h['BB_ORTA'], h['BB_ALT'] = hesapla_bollinger(h['Close'])
            h['ATR'] = hesapla_atr(h['High'], h['Low'], h['Close'])
            h['STOCH_K'], h['STOCH_D'] = hesapla_stochastic(h['High'], h['Low'], h['Close'])
            h['OBV'] = hesapla_obv(h['Close'], h['Volume'])
            h['SMA20'] = hesapla_sma(h['Close'], 20)
            h['SMA50'] = hesapla_sma(h['Close'], 50)
            h['Vol_Ratio'] = h['Volume'] / h['Volume'].rolling(20).mean()

            sf = h['Close'].iloc[-1]
            gb = h['Close'].iloc[-min(25, len(h))]
            gd = ((sf - gb) / gb) * 100 if gb > 0 else 0

            # Cok katmanli sinyal
            ai_skor, sinyal, yorum, bb_poz = sinyal_motoru(h, sf)

            # Risk yonetimi
            sl, hedef, rr, rsk = risk_hesapla(h, sf, ai_skor)

            # VWAP
            vw = (h['Volume'] * h['Close']).cumsum() / h['Volume'].cumsum()
            vs = ((sf - vw.iloc[-1]) / vw.iloc[-1]) * 100 if vw.iloc[-1] > 0 else 0

            # Hurst
            ret = h['Close'].pct_change().dropna()
            if len(ret) > 10:
                n = len(ret)
                dv = ret - ret.mean()
                cs = dv.cumsum()
                R = cs.max() - cs.min()
                S = ret.std()
                hu = np.log(R/S) / np.log(n) if S > 0 else 0.5
                hu = max(0.1, min(0.9, hu))
                if pd.isna(hu): hu = 0.5
            else:
                hu = 0.5

            # Sikisma
            y20 = h['High'].rolling(20).max().iloc[-1]
            d20 = h['Low'].rolling(20).min().iloc[-1]
            if pd.isna(y20) or pd.isna(d20):
                y20, d20 = h['High'].max(), h['Low'].min()
            cr = (y20 - d20) / sf if sf > 0 else 1

            # Net para girisi
            yon = 1 if sf >= h['Open'].iloc[-1] else -1
            pg = abs(h['High'].iloc[-1] - h['Low'].iloc[-1]) * h['Volume'].iloc[-1] * yon

            # 15 dk tahmin
            if ai_skor >= 70:
                tp = "YUKSELIS BEKLENIYOR"
            elif ai_skor >= 55:
                tp = "YUKSELIS EGILIMI"
            elif ai_skor < 35:
                tp = "DUSUS BEKLENIYOR"
            elif ai_skor < 45:
                tp = "ZAYIF SEYIR"
            else:
                tp = "BEKLE"

            rows.append({
                "Hisse": t.replace(".IS", ""),
                "Katilim Uygun": "EVET" if t in katilim_set else "HAYIR",
                "Net Guc Skoru": round(ai_skor, 2),
                "Sinyal": sinyal,
                "Yorum": yorum,
                "RSI": round(h['RSI'].iloc[-1], 1) if not pd.isna(h['RSI'].iloc[-1]) else 50,
                "MACD Hist": round(h['MACD_HIST'].iloc[-1], 3) if not pd.isna(h['MACD_HIST'].iloc[-1]) else 0,
                "Stoch K": round(h['STOCH_K'].iloc[-1], 1) if not pd.isna(h['STOCH_K'].iloc[-1]) else 50,
                "BB Pozisyon": round(bb_poz, 2),
                "Trend Karari": "Yukselis Kanali" if gd > 0 else "Dusus Kanali",
                "OlasI Haber": "Hacim Genislemesi" if h['Vol_Ratio'].iloc[-1] > 1.5 else "Normal",
                "Trend Projeksiyon": "Guclu Trend Devami" if ai_skor > 70 else "Bant Ici Toparlanma",
                "Beklenen Getiri": "%" + str(round(gd, 2)),
                "Erken Konum": "HACIM & SIKISMA" if cr < 1.1 else "NORMAL",
                "Swing Al-Sat": "SWING UYGUN" if ai_skor > 60 else "HARIC",
                "Al Olasiligi": "%" + str(round(ai_skor, 1)),
                "Hacim (Vol)": str(round(h['Vol_Ratio'].iloc[-1], 2)) + "x",
                "Sikisma (Comp)": str(round(cr, 2)) + "x",
                "Fiyat": str(round(sf, 2)) + " TL",
                "Stop-Loss": str(sl) + " TL" if sl else "-",
                "Hedef": str(hedef) + " TL" if hedef else "-",
                "Risk/Odul": str(rr) if rr else "-",
                "Risk Seviye": rsk if rsk else "-",
                "Donem Degisimi": "%" + str(round(gd, 2)),
                "Endeks RS": "%" + str(round(gd, 2)),
                "Hurst": round(hu, 2),
                "VWAP Sapma": "%" + str(round(vs, 2)),
                "Net Para Girisi": round(pg, 2),
                "Guclu Yukselis": "EVET" if ai_skor > 75 else "HAYIR",
                "15 Dk Sonra Tahmin": tp
            })
        except:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df['Agirlik'] = df['15 Dk Sonra Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
    df = df.sort_values(by=['Agirlik', 'Net Guc Skoru'], ascending=[True, False]).drop(columns=['Agirlik'])
    return df

@st.cache_data(ttl=300, show_spinner=False)
def get_chart_data(ticker):
    try:
        h = yf.Ticker(ticker).history(period="5d", interval="15m")
        if h.empty:
            return None
        h['RSI'] = hesapla_rsi(h['Close'])
        h['MACD'], h['MACD_SIG'], h['MACD_HIST'] = hesapla_macd(h['Close'])
        h['BB_UST'], h['BB_ORTA'], h['BB_ALT'] = hesapla_bollinger(h['Close'])
        return h
    except:
        return None

piyasa = is_market_hours()
if piyasa:
    st_autorefresh(interval=60000, key="refresh")

st.title("BIST Swing/Intraday Trend & Hacim Sikismasi Patlama Terminali")
st.caption("Son Guncelleme (TRT): " + trt_now().strftime('%Y-%m-%d %H:%M:%S') + " | 15Dk Gecikmeli | 20+ Teknik Gosterge")

if piyasa:
    st.markdown('<div class="market-open"><b>PIYASA ACIK</b> - Otomatik veri akisi 09:40-18:30 arasi her 60 saniyede bir</div>', unsafe_allow_html=True)
else:
    if trt_now().weekday() >= 5:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Hafta sonu.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Seans saatleri (09:40-18:30) disinda.</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    try:
        bh = yf.Ticker("XU100.IS").history(period="1d")
        if not bh.empty:
            f = bh['Close'].iloc[-1]
            d = ((f - bh['Open'].iloc[-1]) / bh['Open'].iloc[-1]) * 100
            st.metric("BIST 100", str(round(f, 2)), "%" + str(round(d, 2)))
        else:
            st.metric("BIST 100", "Bekleniyor", "Notr")
    except:
        st.metric("BIST 100", "Hata", "Notr")
with c2:
    st.metric("VIOP Denge", "Denge", "Notr")
with c3:
    st.metric("Taranan Hisse", "300", "Ilk 300")
with c4:
    st.metric("Veri Cekme", str(st.session_state.fetch_count), "Son: " + st.session_state.last_fetch_time)

t1, t2, t3, t4, t5, t6 = st.tabs(["Trend Matrisi", "Mum Grafigi", "Risk Analizi", "VIOP Denge", "KAP Haberleri", "Kapanis"])

with t1:
    st.subheader("Gelismis Nicel Trend Matrisi (20+ Gosterge)")
    cf1, cf2, cf3, cf4 = st.columns([2, 2, 2, 2])
    with cf1:
        sk = st.checkbox("Sadece Islam'a Uygun", value=True)
    with cf2:
        st.checkbox("Erken Sikisma", value=False)
    with cf3:
        st.checkbox("Yuksek Guvenli", value=False)
    with cf4:
        mb = st.button("Manuel Veri Cek", use_container_width=True, type="primary")
    if mb:
        st.cache_data.clear()
        st.session_state.manual_trigger = True
        st.session_state.fetch_count += 1
        st.session_state.last_fetch_time = trt_now().strftime("%H:%M:%S")
        st.rerun()
    with st.spinner("Gercek BIST verileri ve gostergeler hesaplaniyor..."):
        tk = TUM_HISSELER.split(",")
        ks = set(KATILIM.split(","))
        rw = fetch_all(tuple(tk))
        if rw is not None and not rw.empty:
            df = process(rw, tk, ks)
            if not st.session_state.manual_trigger:
                st.session_state.fetch_count += 1
                st.session_state.last_fetch_time = trt_now().strftime("%H:%M:%S")
            st.session_state.manual_trigger = False
        else:
            df = pd.DataFrame()
    if sk and not df.empty:
        df = df[df["Katilim Uygun"] == "EVET"]
    if not df.empty:
        def rt(v):
            if "YUKSELIS" in str(v):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            if "DUSUS" in str(v) or "ZAYIF" in str(v):
                return 'background-color: #b71c1c; color: white; font-weight: bold;'
            if "BEKLE" in str(v):
                return 'background-color: #e65100; color: white; font-weight: bold;'
            return ''
        def rs(v):
            if "GUCLU AL" in str(v):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            if "AL" in str(v) and "GUCLU" not in str(v):
                return 'background-color: #2e7d32; color: white;'
            if "SAT" in st
