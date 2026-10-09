import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone, time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BIST Pro", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
.stApp { background-color: #0E1117; color: #FFFFFF; }
.stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
.counter-box { background-color: #1E1E1E; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }
.market-open { background-color: #1b5e20; padding: 15px; border-radius: 8px; color: white; }
.market-closed { background-color: #4a148c; padding: 15px; border-radius: 8px; color: white; }
</style>""", unsafe_allow_html=True)

HISSELER = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

KATILIM = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"

def trt():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))

def piyasa_acik():
    s = trt()
    if s.weekday() >= 5:
        return False
    return time(9, 40) <= s.time() <= time(18, 30)

def rsi(s, p=14):
    d = s.diff()
    k = d.where(d > 0, 0).rolling(p).mean()
    y = -d.where(d < 0, 0).rolling(p).mean()
    return 100 - (100 / (1 + k / y))

def macd(s):
    e1 = s.ewm(span=12, adjust=False).mean()
    e2 = s.ewm(span=26, adjust=False).mean()
    m = e1 - e2
    sig = m.ewm(span=9, adjust=False).mean()
    return m, sig, m - sig

def bb(s, p=20):
    sma = s.rolling(p).mean()
    sd = s.rolling(p).std()
    return sma + sd * 2, sma, sma - sd * 2

def atr(h, l, c, p=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()

def stoch(h, l, c, p=14):
    hi = h.rolling(p).max()
    lo = l.rolling(p).min()
    k = 100 * (c - lo) / (hi - lo)
    return k, k.rolling(3).mean()

def obv(c, v):
    return (np.sign(c.diff()) * v).fillna(0).cumsum()

def sinyal(h, sf):
    if len(h) < 30:
        return 50, "BEKLE", "Yetersiz veri", 0.5, 0
    sma20 = h['SMA20'].iloc[-1] if not pd.isna(h['SMA20'].iloc[-1]) else sf
    sma50 = h['SMA50'].iloc[-1] if not pd.isna(h['SMA50'].iloc[-1]) else sf
    t = 0.5
    if sf > sma20: t += 0.25
    if sf > sma50: t += 0.25
    if sma20 > sma50: t += 0.15
    t = min(1.0, t)
    r = h['RSI'].iloc[-1] if not pd.isna(h['RSI'].iloc[-1]) else 50
    mh = h['MACD_H'].iloc[-1] if not pd.isna(h['MACD_H'].iloc[-1]) else 0
    sk = h['STOCH_K'].iloc[-1] if not pd.isna(h['STOCH_K'].iloc[-1]) else 50
    m = 0.5
    if 40 < r < 70: m += 0.15
    elif r < 30: m += 0.3
    elif r > 70: m -= 0.2
    if mh > 0: m += 0.2
    if sk < 20: m += 0.15
    elif 20 < sk < 80: m += 0.1
    m = max(0, min(1.0, m))
    vr = h['VR'].iloc[-1] if not pd.isna(h['VR'].iloc[-1]) else 1
    ot = 1 if h['OBV'].iloc[-1] > h['OBV'].iloc[-5] else 0
    hc = 0.5
    if vr > 1.5: hc += 0.3
    elif vr > 1.2: hc += 0.15
    if ot: hc += 0.2
    hc = min(1.0, hc)
    bu = h['BB_U'].iloc[-1] if not pd.isna(h['BB_U'].iloc[-1]) else sf * 1.05
    ba = h['BB_A'].iloc[-1] if not pd.isna(h['BB_A'].iloc[-1]) else sf * 0.95
    bp = (sf - ba) / (bu - ba) if (bu - ba) > 0 else 0.5
    ai = (t * 0.35 + m * 0.35 + hc * 0.20 + (1 - bp) * 0.10) * 100
    ai = max(20, min(95, ai))
    if ai >= 70 and t > 0.6 and m > 0.5: sn = "GUCLU AL"
    elif ai >= 55 and t > 0.4: sn = "AL"
    elif ai < 35 and t < 0.4: sn = "SAT"
    elif ai < 45: sn = "ZAYIF"
    else: sn = "BEKLE"
    y = []
    if t > 0.6: y.append("Trend+")
    if mh > 0: y.append("MACD+")
    if vr > 1.5: y.append("Hacim+")
    if r < 35: y.append("RSI dipsiz")
    if r > 70: y.append("RSI zirve")
    return ai, sn, " | ".join(y) if y else "Notr", bp, h['ATR'].iloc[-1] if not pd.isna(h['ATR'].iloc[-1]) else 0

def risk(sf, ai, a):
    if a == 0:
        return None, None, None, None
    if ai >= 70: cs, ch, rk = 1.5, 3.0, "Dusuk"
    elif ai >= 55: cs, ch, rk = 2.0, 2.5, "Orta"
    else: cs, ch, rk = 2.5, 2.0, "Yuksek"
    sl = sf - a * cs
    hd = sf + a * ch
    rr = (hd - sf) / (sf - sl) if (sf - sl) > 0 else 0
    return round(sl, 2), round(hd, 2), round(rr, 2), rk

for k, v in [('logged_in', False), ('fetch_count', 0), ('last_fetch', '-'), ('manual', False)]:
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.logged_in:
    st.title("BIST Pro Giris")
    with st.form("l"):
        c1, c2 = st.columns(2)
        u = c1.text_input("Kullanici Adi")
        p = c2.text_input("Sifre", type="password")
        if st.form_submit_button("Giris"):
            if u.strip() == "Cuma Babacan" and p.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatali giris!")
    st.stop()

@st.cache_data(ttl=60, show_spinner=False)
def fetch(tks):
    try:
        return yf.download(list(tks), period="5d", interval="15m", group_by='ticker', threads=True, progress=False, auto_adjust=True)
    except:
        return None

def isle(raw, tks, kset):
    rows = []
    for t in tks:
        try:
            tk = t + ".IS"
            if len(tks) == 1: h = raw.copy()
            else: h = raw[tk].copy() if tk in raw.columns.levels[0] else None
            if h is None or h.empty or len(h) < 30: continue
            h = h.dropna()
            if len(h) < 30: continue
            h['RSI'] = rsi(h['Close'])
            h['MACD'], h['MACD_S'], h['MACD_H'] = macd(h['Close'])
            h['BB_U'], h['BB_O'], h['BB_A'] = bb(h['Close'])
            h['ATR'] = atr(h['High'], h['Low'], h['Close'])
            h['STOCH_K'], h['STOCH_D'] = stoch(h['High'], h['Low'], h['Close'])
            h['OBV'] = obv(h['Close'], h['Volume'])
            h['SMA20'] = h['Close'].rolling(20).mean()
            h['SMA50'] = h['Close'].rolling(50).mean()
            h['VR'] = h['Volume'] / h['Volume'].rolling(20).mean()
            sf = h['Close'].iloc[-1]
            gb = h['Close'].iloc[-min(25, len(h))]
            gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
            ai, sn, yr, bp, at = sinyal(h, sf)
            sl, hd, rr, rk = risk(sf, ai, at)
            vw = (h['Volume'] * h['Close']).cumsum() / h['Volume'].cumsum()
            vs = ((sf - vw.iloc[-1]) / vw.iloc[-1]) * 100 if vw.iloc[-1] > 0 else 0
            rt = h['Close'].pct_change().dropna()
            if len(rt) > 10:
                n = len(rt)
                dv = rt - rt.mean()
                cs = dv.cumsum()
                R = cs.max() - cs.min()
                S = rt.std()
                hu = np.log(R/S) / np.log(n) if S > 0 else 0.5
                hu = max(0.1, min(0.9, hu))
                if pd.isna(hu): hu = 0.5
            else: hu = 0.5
            y20 = h['High'].rolling(20).max().iloc[-1]
            d20 = h['Low'].rolling(20).min().iloc[-1]
            if pd.isna(y20) or pd.isna(d20): y20, d20 = h['High'].max(), h['Low'].min()
            cr = (y20 - d20) / sf if sf > 0 else 1
            yon = 1 if sf >= h['Open'].iloc[-1] else -1
            pg = abs(h['High'].iloc[-1] - h['Low'].iloc[-1]) * h['Volume'].iloc[-1] * yon
            if ai >= 70: tp = "YUKSELIS BEKLENIYOR"
            elif ai >= 55: tp = "YUKSELIS EGILIMI"
            elif ai < 35: tp = "DUSUS BEKLENIYOR"
            elif ai < 45: tp = "ZAYIF SEYIR"
            else: tp = "BEKLE"
            rows.append({
                "Hisse": t, "Katilim": "EVET" if tk in kset else "HAYIR",
                "Guc": round(ai, 2), "Sinyal": sn, "Yorum": yr,
                "RSI": round(h['RSI'].iloc[-1], 1) if not pd.isna(h['RSI'].iloc[-1]) else 50,
                "MACD_H": round(h['MACD_H'].iloc[-1], 3) if not pd.isna(h['MACD_H'].iloc[-1]) else 0,
                "Stoch": round(h['STOCH_K'].iloc[-1], 1) if not pd.isna(h['STOCH_K'].iloc[-1]) else 50,
                "BB_Poz": round(bp, 2),
                "Trend": "Yukselis" if gd > 0 else "Dusus",
                "Getiri": "%" + str(round(gd, 2)),
                "Erken": "HACIM+SIKISMA" if cr < 1.1 else "NORMAL",
                "Swing": "SWING UYGUN" if ai > 60 else "HARIC",
                "Al_Olas": "%" + str(round(ai, 1)),
                "Vol": str(round(h['VR'].iloc[-1], 2)) + "x" if not pd.isna(h['VR'].iloc[-1]) else "1x",
                "Comp": str(round(cr, 2)) + "x",
                "Fiyat": str(round(sf, 2)) + " TL",
                "SL": str(sl) + " TL" if sl else "-",
                "Hedef": str(hd) + " TL" if hd else "-",
                "R/O": str(rr) if rr else "-",
                "Risk": rk if rk else "-",
                "EndeksRS": "%" + str(round(gd, 2)),
                "Hurst": round(hu, 2),
                "VWAP": "%" + str(round(vs, 2)),
                "Para": round(pg, 2),
                "Tahmin": tp
            })
        except: continue
    if not rows: return pd.DataFrame()
    df = pd.DataFrame(rows)
    df['A'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
    return df.sort_values(by=['A', 'Guc'], ascending=[True, False]).drop(columns=['A'])

@st.cache_data(ttl=300, show_spinner=False)
def grafik(tk):
    try:
        h = yf.Ticker(tk).history(period="5d", interval="15m")
        if h.empty: return None
        h['RSI'] = rsi(h['Close'])
        h['MACD'], h['MACD_S'], h['MACD_H'] = macd(h['Close'])
        h['BB_U'], h['BB_O'], h['BB_A'] = bb(h['Close'])
        return h
    except: return None

pk = piyasa_acik()
if pk:
    st_autorefresh(interval=60000, key="r")

st.title("BIST Swing/Intraday Trend & Hacim Sikismasi Terminali")
st.caption("Son Guncelleme (TRT): " + trt().strftime('%Y-%m-%d %H:%M:%S') + " | 15Dk Gecikmeli | 20+ Gosterge")

if pk:
    st.markdown('<div class="market-open"><b>PIYASA ACIK</b> - Otomatik veri 09:40-18:30 arasi 60 sn</div>', unsafe_allow_html=True)
else:
    if trt().weekday() >= 5:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Hafta sonu.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Seans disi (09:40-18:30).</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    try:
        bh = yf.Ticker("XU100.IS").history(period="1d")
        if not bh.empty:
            f = bh['Close'].iloc[-1]
            d = ((f - bh['Open'].iloc[-1]) / bh['Open'].iloc[-1]) * 100
            st.metric("BIST 100", str(round(f, 2)), "%" + str(round(d, 2)))
        else: st.metric("BIST 100", "Bekleniyor", "Notr")
    except: st.metric("BIST 100", "Hata", "Notr")
with c2: st.metric("VIOP Denge", "Denge", "Notr")
with c3: st.metric("Taranan", "300", "Ilk 300")
with c4: st.metric("Cekim", str(st.session_state.fetch_count), "Son: " + st.session_state.last_fetch)

t1, t2, t3, t4 = st.tabs(["Trend Matrisi", "Mum Grafigi", "Risk Analizi", "KAP+VIOP"])

with t1:
    st.subheader("Nicel Trend Matrisi (20+ Gosterge)")
    cf1, cf2, cf3 = st.columns([3, 2, 2])
    with cf1: sk = st.checkbox("Sadece Islam'a Uygun", value=True)
    with cf2: mb = st.button("Manuel Cek", use_container_width=True, type="primary")
    with cf3: st.write("")
    if mb:
        st.cache_data.clear()
        st.session_state.manual = True
        st.session_state.fetch_count += 1
        st.session_state.last_fetch = trt().strftime("%H:%M:%S")
        st.rerun()
    with st.spinner("Yukleniyor..."):
        tks = HISSELER.split(",")
        kset = set((k + ".IS") for k in KATILIM.split(","))
        rw = fetch(tuple(tks))
        if rw is not None and not rw.empty:
            df = isle(rw, tks, kset)
            if not st.session_state.manual:
                st.session_state.fetch_count += 1
                st.session_state.last_fetch = trt().strftime("%H:%M:%S")
            st.session_state.manual = False
        else: df = pd.DataFrame()
    if sk and not df.empty:
        df = df[df["Katilim"] == "EVET"]
    if not df.empty:
        def rt(v):
            if "YUKSELIS" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "DUSUS" in str(v) or "ZAYIF" in str(v): return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "BEKLE" in str(v): return 'background-color:#e65100;color:white;font-weight:bold;'
            return ''
        def rs(v):
            if "GUCLU AL" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AL" in str(v): return 'background-color:#2e7d32;color:white;'
            if "SAT" in str(v) or "ZAYIF" in str(v): return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'
        def rk2(v): return 'color:#4CAF50;font-weight:bold;' if v == "EVET" else 'color:#F44336;'
        st.dataframe(df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk2, subset=["Katilim"]), use_container_width=True, height=700)
        st.markdown("---")
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        s1.metric("Gosterilen", len(df))
        s2.metric("Yukselis", len(df[df["Tahmin"].str.contains("YUKSELIS")]))
        s3.metric("Katilim", len(df[df["Katilim"] == "EVET"]))
        s4.metric("Ort Guc", str(round(df["Guc"].mean(), 1)))
        s5.metric("Guclu AL", len(df[df["Sinyal"] == "GUCLU AL"]))
        s6.metric("SAT", len(df[df["Sinyal"] == "SAT"]))
    else: st.warning("Veri cekilemedi.")

with t2:
    st.subheader("Interaktif Mum Grafigi")
    try:
        hs = st.selectbox("Hisse", [h for h in HISSELER.split(",")[:100]])
        h = grafik(hs + ".IS")
        if h is not None and not h.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Fiyat", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'))
            fig.add_trace(go.Scatter(x=h.index, y=h['BB_U'], name="BB Ust", line=dict(color='#9c27b0', width=1, dash='dot')))
            fig.add_trace(go.Scatter(x=h.index, y=h['BB_A'], name="BB Alt", line=dict(color='#9c27b0', width=1, dash='dot')))
            fig.add_trace(go.Scatter(x=h.index, y=h['Close'].rolling(20).mean(), name="SMA20", line=dict(color='#FFC107', width=1)))
            fig.update_layout(title=hs + " - 15 Dakikalik", xaxis_rangeslider_visible=False, template='plotly_dark', height=500, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E')
            st.plotly_chart(fig, use_container_width=True)
            cr, cm = st.columns(2)
            with cr:
                fr = go.Figure()
                fr.add_trace(go.Scatter(x=h.index, y=h['RSI'], name="RSI", line=dict(color='#4CAF50')))
                fr.add_hline(y=70, line_dash="dash", line_color="red")
                fr.add_hline(y=30, line_dash="dash", line_color="green")
                fr.update_layout(title="RSI (14)", template='plotly_dark', height=250, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E', showlegend=False)
                st.plotly_chart(fr, use_container_width=True)
            with cm:
                fm = go.Figure()
                fm.add_trace(go.Bar(x=h.index, y=h['MACD_H'], name="Hist", marker_color='#FFC107'))
                fm.add_trace(go.Scatter(x=h.index, y=h['MACD'], name="MACD", line=dict(color='#4CAF50')))
                fm.add_trace(go.Scatter(x=h.index, y=h['MACD_S'], name="Signal", line=dict(color='#F44336')))
                fm.update_layout(title="MACD", template='plotly_dark', height=250, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E')
                st.plotly_chart(fm, use_container_width=True)
        else: st.warning("Grafik alinamadi.")
    except Exception as e: st.error("Hata: " + str(e))

with t3:
    st.subheader("ATR Bazli Risk Yonetimi")
    try:
        tks = HISSELER.split(",")
        kset = set((k + ".IS") for k in KATILIM.split(","))
        rw = fetch(tuple(tks))
        if rw is not None and not rw.empty:
            df_r = isle(rw, tks, kset)
            if not df_r.empty:
                df_r = df_r[df_r["Katilim"] == "EVET"]
                def rn(x):
                    try: return float(x) > 1.5
                    except: return False
                rdf = df_r[df_r["R/O"].apply(rn)]
                st.markdown("**Risk/Odul > 1.5 olan " + str(len(rdf)) + " hisse:**")
                if not rdf.empty:
                    st.dataframe(rdf[["Hisse", "Fiyat", "SL", "Hedef", "R/O", "Risk", "Sinyal", "Guc"]], use_container_width=True, height=500)
                else: st.info("Uygun risk/odul oraninda hisse yok.")
                st.markdown("---")
                st.info("Stop-Loss = Fiyat - (ATR x Carpan) | Hedef = Fiyat + (ATR x Carpan)")
    except: st.warning("Risk analizi yapilamadi.")

with t4:
    st.subheader("KAP Haberleri")
    st.warning("KAP entegrasyonu yakinda eklenecek.")
    st.write("**[14:18:40] ASELS** - Yeni Siparis Anlasmasi (Pozitif)")
    st.write("**[14:15:20] TUPRS** - Uretim Verileri (Notr)")
    st.markdown("---")
    st.subheader("VIOP Denge")
    v1, v2, v3 = st.columns(3)
    v1.metric("VIOP 30", "11.450", "%0.45")
    v2.metric("Spot", "11.420", "%0.40")
    v3.metric("Fark", "+30", "Pozitif")

st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    st.markdown('<div class="counter-box"><h4>Veri Cekme</h4><p><b>Toplam:</b> ' + str(st.session_state.fetch_count) + '</p><p><b>Son:</b> ' + st.session_state.last_fetch + '</p><p><b>Hisse:</b> 300</p></div>', unsafe_allow_html=True)
with b2:
    dm = "ACIK" if pk else "KAPALI"
    st.markdown('<div class="counter-box"><h4>Sistem</h4><p><b>Yenileme:</b> 60 sn</p><p><b>Gecikme:</b> 15 dk</p><p><b>TRT:</b> ' + trt().strftime('%H:%M:%S') + '</p><p><b>Piyasa:</b> ' + dm + '</p></div>', unsafe_allow_html=
