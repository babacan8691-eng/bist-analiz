import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from data.fetcher import toplu_veri_cek, piyasa_acik_mi, turkiye_saati, bist_endeks_verisi

st.set_page_config(page_title="BIST Pro", layout="wide")

H = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"
K = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"

for k, v in [('g', False), ('s', 0), ('l', '-'), ('m', False)]:
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.g:
    st.title("BIST Pro Giris")
    with st.form("f"):
        c1, c2 = st.columns(2)
        u = c1.text_input("Kullanici")
        p = c2.text_input("Sifre", type="password")
        if st.form_submit_button("Gir"):
            if u.strip() == "Cuma Babacan" and p.strip() == "784512":
                st.session_state.g = True
                st.rerun()
            else:
                st.error("Hatali!")
    st.stop()

def rsi(s, p=14):
    d = s.diff()
    k = d.where(d > 0, 0).rolling(p).mean()
    y = -d.where(d < 0, 0).rolling(p).mean()
    return 100 - (100 / (1 + k / y))

def atr_f(h, l, c, p=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()

def tahmin_15(g):
    if len(g) < 20:
        return "YATAY", 50.0, 0.0
    s5 = g.iloc[-5:]
    s10 = g.iloc[-10:]
    f0 = float(s5['Close'].iloc[0])
    f1 = float(s5['Close'].iloc[-1])
    mom = ((f1 - f0) / f0) * 100 if f0 > 0 else 0
    yh, dh = 0.0, 0.0
    for i in range(len(s10)):
        b = s10.iloc[i]
        if float(b['Close']) > float(b['Open']):
            yh += float(b['Volume'])
        else:
            dh += float(b['Volume'])
    top = yh + dh
    hb = ((yh / top) - 0.5) * 100 if top > 0 else 0
    vw = (g['Volume'] * g['Close']).cumsum() / g['Volume'].cumsum()
    sf = float(g['Close'].iloc[-1])
    vwl = float(vw.iloc[-1])
    vu = ((sf - vwl) / vwl) * 100 if vwl > 0 else 0
    sb = g.iloc[-1]
    sh = float(sb['High'])
    sl = float(sb['Low'])
    kp = (float(sb['Close']) - sl) / (sh - sl) if (sh - sl) > 0 else 0.5
    a5 = float((g['High'] - g['Low']).iloc[-5:].mean())
    a20 = float((g['High'] - g['Low']).iloc[-20:].mean())
    vr = ((a5 / a20) - 1) * 50 if a20 > 0 else 0
    s = 50 + mom * 3 + hb * 0.4 + vu * 2 + (kp - 0.5) * 20 + vr * 0.2
    s = max(0, min(100, s))
    if s >= 65:
        yon, gv = "YUKARI", s
    elif s <= 35:
        yon, gv = "ASAGI", 100 - s
    else:
        yon, gv = "YATAY", 100 - abs(s - 50) * 2
    bkl = (s - 50) / 10
    return yon, round(gv, 1), round(bkl, 2)

def hesapla(hs, v, kset):
    if v is None or v.empty or len(v) < 30:
        return None, None
    g = v.dropna()
    if len(g) < 30:
        return None, None
    sf = float(g['Close'].iloc[-1])
    gb = float(g['Close'].iloc[-min(25, len(g))])
    gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
    sma20 = float(g['Close'].rolling(20).mean().iloc[-1])
    rv = rsi(g['Close']).iloc[-1]
    r = float(rv) if not pd.isna(rv) else 50
    e1 = g['Close'].ewm(span=12, adjust=False).mean()
    e2 = g['Close'].ewm(span=26, adjust=False).mean()
    mh = float((e1 - e2 - (e1 - e2).ewm(span=9, adjust=False).mean()).iloc[-1])
    hm = g['Volume'].rolling(20).mean().iloc[-1]
    ho = float(hm) if not pd.isna(hm) else 1
    hr = float(g['Volume'].iloc[-1]) / ho if ho > 0 else 1
    av = atr_f(g['High'], g['Low'], g['Close']).iloc[-1]
    a = float(av) if not pd.isna(av) else 0
    sk = 50
    yr = []
    if sf > sma20:
        sk += 12
        yr.append("SMA20+")
    if gd > 0:
        sk += 10
    if r < 40:
        sk += 10
        yr.append("RSI dusuk")
    elif r > 70:
        sk -= 12
        yr.append("RSI yuksek")
    if mh > 0:
        sk += 10
        yr.append("MACD+")
    if hr > 1.3:
        sk += 8
        yr.append("Hacim+")
    sk = max(20, min(95, sk))
    if sk >= 70 and gd > 0:
        sn, tp = "GUCLU AL", "YUKSELIS BEKLENIYOR"
    elif sk >= 55:
        sn, tp = "AL", "YUKSELIS EGILIMI"
    elif sk < 35:
        sn, tp = "SAT", "DUSUS BEKLENIYOR"
    elif sk < 45:
        sn, tp = "ZAYIF", "ZAYIF"
    else:
        sn, tp = "BEKLE", "BEKLE"
    if a > 0:
        sl = round(sf - a * 2, 2)
        hd = round(sf + a * 3, 2)
        ro = round((hd - sf) / (sf - sl), 2) if (sf - sl) > 0 else 0
    else:
        sl, hd, ro = 0, 0, 0
    hz = hs + ".IS"
    y15, g15, b15 = tahmin_15(g)
    pct20 = g['Close'].pct_change().iloc[-20:].fillna(0).abs()
    dn20 = (g['Volume'].iloc[-20:] * g['Close'].iloc[-20:]).replace(0, np.nan).fillna(1)
    amh = float((pct20 / dn20).sum() / 20)
    lik = max(0, min(100, 100 - amh * 1e8))
    v5 = float((g['High'] - g['Low']).iloc[-5:].mean())
    v20 = float((g['High'] - g['Low']).iloc[-20:].mean())
    vrej = "YUKSEK" if v5 > v20 * 1.3 else ("DUSUK" if v5 < v20 * 0.7 else "NORMAL")
    obv_s = (np.sign(g['Close'].diff()) * g['Volume']).fillna(0).cumsum()
    ofi = float(obv_s.iloc[-1] - obv_s.iloc[-5]) / 1e6 if len(obv_s) >= 5 else 0
    ana = {"Hisse": hs, "Katilim": "EVET" if hz in kset else "HAYIR", "Guc": round(sk, 1), "Sinyal": sn, "Yorum": " | ".join(yr) if yr else "Notr", "RSI": f"{r:.1f}", "MACD": f"{mh:.3f}", "Trend": "Yuk" if gd > 0 else "Dus", "Getiri": f"%{gd:.2f}", "Hacim": f"{hr:.2f}x", "Fiyat": f"{sf:.2f} TL", "SL": f"{sl} TL", "Hedef": f"{hd} TL", "RO": f"{ro:.2f}", "Tahmin": tp, "Tahmin15": y15, "Guven15": f"%{g15}", "Beklenti15": f"%{b15}", "Likidite": round(lik, 1), "VolRejim": vrej, "OFI": round(ofi, 2)}
    s25 = g.iloc[-min(25, len(g)):]
    gh = float(s25['High'].max())
    gl = float(s25['Low'].min())
    kp = (sf - gl) / (gh - gl) if (gh - gl) > 0 else 0.5
    ay = (a / sf) * 100 if sf > 0 else 0
    gs = 50
    if kp > 0.75:
        gs += 15
    elif kp < 0.25:
        gs -= 10
    if gd > 2:
        gs += 10
    elif gd < -2:
        gs -= 10
    if hr > 1.5:
        gs += 8
    if mh > 0:
        gs += 7
    if r > 65:
        gs -= 5
    elif r < 35:
        gs += 8
    gs = max(0, min(100, gs))
    if gs >= 70:
        os, bg, tg = "GECE TASI", "YUKARI", round(ay * 0.6, 2)
    elif gs >= 55:
        os, bg, tg = "ZAYIF TASI", "NOTR", round(ay * 0.3, 2)
    elif gs < 35:
        os, bg, tg = "GECE TASIMA", "ASAGI", round(-ay * 0.5, 2)
    else:
        os, bg, tg = "BEKLE", "NOTR", 0
    onc = {"Hisse": hs, "Kapanis": f"{sf:.2f} TL", "GapSkor": round(gs, 1), "Overnight": os, "GapYon": bg, "Gap%": f"%{tg}", "Yorum": "Zirve" if kp > 0.75 else ("Dip" if kp < 0.25 else "Notr")}
    return ana, onc

pk = piyasa_acik_mi()
if pk:
    st_autorefresh(interval=60000, key="y")

st.title("BIST Pro Terminali")
st.caption("Son: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 dk Gecikmeli | Pro Analiz Aktif")

if pk:
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

with st.spinner("Veri yukleniyor..."):
    hl = H.split(",")
    ks = set(x + ".IS" for x in K.split(","))
    hv = toplu_veri_cek(hl)
    sat, onc = [], []
    for x in hl:
        kod = x + ".IS"
        if kod in hv:
            a, o = hesapla(x, hv[kod], ks)
            if a:
                sat.append(a)
            if o:
                onc.append(o)
    if not st.session_state.m:
        st.session_state.s += 1
        st.session_state.l = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.m = False

bd, bdeg = "-", "0"
try:
    bv = bist_endeks_verisi()
    if bv is not None and not bv.empty:
        bf = float(bv['Close'].iloc[-1])
        bd = f"{bf:.2f}"
        bdeg = f"%{((bf - float(bv['Open'].iloc[-1])) / float(bv['Open'].iloc[-1])) * 100:.2f}"
except Exception:
    pass

c1, c2, c3, c4 = st.columns(4)
c1.metric("BIST 100", bd, bdeg)
c2.metric("VIOP", "Denge", "0")
c3.metric("Taranan", str(len(hl)), "0")
c4.metric("Cekim", str(st.session_state.s), "Son: " + st.session_state.l)

cc1, cc2 = st.columns([3, 1])
with cc1:
    sd = st.checkbox("Sadece Islam'a Uygun", value=True)
with cc2:
    mb = st.button("Manuel Cek", use_container_width=True, type="primary")
if mb:
    st.cache_data.clear()
    st.session_state.m = True
    st.session_state.s += 1
    st.session_state.l = turkiye_saati().strftime("%H:%M:%S")
    st.rerun()

t1, t2, t3, t4 = st.tabs(["Trend", "Mum", "Risk", "Overnight"])

with t1:
    if not sat:
        st.warning("Veri yok.")
    else:
        df = pd.DataFrame(sat)
        df['O'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
        df = df.sort_values(by=['O', 'Guc'], ascending=[True, False]).drop(columns=['O'])
        if sd:
            df = df[df["Katilim"] == "EVET"]
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
        def rk(v): return 'color:#4CAF50;font-weight:bold;' if v == "EVET" else 'color:#F44336;'
        def r15(v):
            if "YUKARI" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ASAGI" in str(v): return 'background-color:#b71c1c;color:white;font-weight:bold;'
            return 'background-color:#e65100;color:white;font-weight:bold;'
        def rv(v):
            if "DUSUK" in str(v): return 'color:#4CAF50;font-weight:bold;'
            if "YUKSEK" in str(v): return 'color:#F44336;font-weight:bold;'
            return 'color:#FFC107;'
        st.dataframe(df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk, subset=["Katilim"]).map(r15, subset=["Tahmin15"]).map(rv, subset=["VolRejim"]), use_container_width=True, height=600)
        st.markdown("---")
        st.subheader("15-25 Dakika Sonrasi Yon Dagilimi")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("YUKARI KIRILIM", len(df[df["Tahmin15"] == "YUKARI"]))
        m2.metric("ASAGI KIRILIM", len(df[df["Tahmin15"] == "ASAGI"]))
        m3.metric("YATAY", len(df[df["Tahmin15"] == "YATAY"]))
        gvv = pd.to_numeric(df['Guven15'].str.replace('%', ''), errors='coerce').mean()
        m4.metric("Ort Guven", f"%{round(gvv, 1) if not pd.isna(gvv) else 0}")
        st.markdown("---")
        st.subheader("Pro Analiz - Likidite, Volatilite, OFI")
        pdf = df.copy()
        pdf['GV'] = pd.to_numeric(pdf['Guven15'].str.replace('%', ''), errors='coerce')
        pdf = pdf.sort_values('GV', ascending=False)
        st.dataframe(pdf[["Hisse", "Fiyat", "Likidite", "VolRejim", "OFI", "Tahmin15", "Guven15"]].head(15), use_container_width=True)
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("Likidite En Yuksek 5")
            st.dataframe(pdf.sort_values("Likidite", ascending=False)[["Hisse", "Likidite", "VolRejim", "OFI"]].head(5), use_container_width=True)
        with colB:
            st.subheader("OFI En Yuksek 5")
            st.dataframe(pdf.sort_values("OFI", ascending=False)[["Hisse", "OFI", "Likidite", "Guven15"]].head(5), use_container_width=True)
        st.caption("Likidite: Amihud (yuksek=iyi) | VolRejim: ATR oranina gore (DUSUK/NORMAL/YUKSEK) | OFI: OBV proxy emir akis (pozitif=alim baskisi)")

with t2:
    st.subheader("Mum Grafigi")
    try:
        hs = st.selectbox("Hisse", hl[:80])
        kod = hs + ".IS"
        if kod in hv:
            h = hv[kod].dropna()
            h['SMA20'] = h['Close'].rolling(20).mean()
            h['BBU'] = h['Close'].rolling(20).mean() + 2 * h['Close'].rolling(20).std()
            h['BBA'] = h['Close'].rolling(20).mean() - 2 * h['Close'].rolling(20).std()
            h['RSI'] = rsi(h['Close'])
            f = go.Figure()
            f.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Fiyat", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'))
            f.add_trace(go.Scatter(x=h.index, y=h['BBU'], name="BBU", line=dict(color='#9c27b0', width=1, dash='dot')))
            f.add_trace(go.Scatter(x=h.index, y=h['BBA'], name="BBA", line=dict(color='#9c27b0', width=1, dash='dot')))
            f.add_trace(go.Scatter(x=h.index, y=h['SMA20'], name="SMA20", line=dict(color='#FFC107', width=1)))
            f.update_layout(title=hs, xaxis_rangeslider_visible=False, template='plotly_dark', height=450, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E')
            st.plotly_chart(f, use_container_width=True)
            fr = go.Figure()
            fr.add_trace(go.Scatter(x=h.index, y=h['RSI'], name="RSI", line=dict(color='#4CAF50')))
            fr.add_hline(y=70, line_dash="dash", line_color="red")
            fr.add_hline(y=30, line_dash="dash", line_color="green")
            fr.update_layout(title="RSI", template='plotly_dark', height=220, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E', showlegend=False)
            st.plotly_chart(fr, use_container_width=True)
    except Exception:
        st.error("Grafik yuklenemedi")

with t3:
    st.subheader("ATR Bazli Risk")
    if sat:
        dfr = pd.DataFrame(sat)
        if sd:
            dfr = dfr[dfr["Katilim"] == "EVET"]
        def rok(x):
            try: return float(x) > 1.5
            except: return False
        rdf = dfr[dfr["RO"].apply(rok)]
        st.markdown(f"**R/O > 1.5 olan {len(rdf)} hisse:**")
        if not rdf.empty:
            st.dataframe(rdf[["Hisse", "Fiyat", "SL", "Hedef", "RO", "Sinyal", "Guc"]], use_container_width=True, height=500)
    else:
        st.warning("Veri yok.")

with t4:
    st.subheader("Overnight Gap Stratejisi")
    st.info("Kapanista al, acilista sat")
    if onc:
        odf = pd.DataFrame(onc)
        if sd:
            odf = odf[odf["Hisse"].apply(lambda x: (x + ".IS") in ks)]
        odf = odf.sort_values(by="GapSkor", ascending=False).reset_index(drop=True)
        def ron(v):
            if "GECE TASI" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ZAYIF TASI" in str(v): return 'background-color:#2e7d32;color:white;'
            if "GECE TASIMA" in str(v): return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'
        def rg(v):
            if "YUKARI" in str(v): return 'color:#4CAF50;font-weight:bold;'
            if "ASAGI" in str(v): return 'color:#F44336;font-weight:bold;'
            return 'color:#FFC107;'
        st.dataframe(odf.style.map(ron, subset=["Overnight"]).map(rg, subset=["GapYon"]), use_container_width=True, height=450)
        st.markdown("---")
        st.subheader("En Guclu 10")
        st.dataframe(odf.head(10)[["Hisse", "Kapanis", "GapSkor", "Overnight", "GapYon", "Gap%"]], use_container_width=True)
    else:
        st.warning("Veri yok.")
    st.markdown("---")
    st.subheader("VIOP Denge")
    v1, v2, v3 = st.columns(3)
    v1.metric("VIOP 30", "11.450", "%0.45")
    v2.metric("Spot", "11.420", "%0.40")
    v3.metric("Fark", "+30", "Pozitif")

st.markdown("---")
st.caption("15 dk gecikmeli. Yatirim tavsiyesi degildir.")
