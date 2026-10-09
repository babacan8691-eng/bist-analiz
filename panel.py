import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, timezone, time
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="BIST Pro", layout="wide")

HISSELER = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

KATILIM = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"

def trt():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))

def market_open():
    s = trt()
    if s.weekday() >= 5:
        return False
    return time(9, 40) <= s.time() <= time(18, 30)

def rsi(s, p=14):
    d = s.diff()
    k = d.where(d > 0, 0).rolling(p).mean()
    y = -d.where(d < 0, 0).rolling(p).mean()
    return 100 - (100 / (1 + k / y))

for k, v in [('logged_in', False), ('cnt', 0), ('last', '-'), ('man', False)]:
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
def fetch_batch(tks_tuple):
    try:
        return yf.download(list(tks_tuple), period="5d", interval="15m",
                          group_by='ticker', threads=True, progress=False,
                          auto_adjust=True, timeout=30)
    except:
        return None

def fetch_all(tks):
    result = {}
    for i in range(0, len(tks), 40):
        batch = tks[i:i+40]
        batch_ws = [t + ".IS" for t in batch]
        data = fetch_batch(tuple(batch_ws))
        if data is None or data.empty:
            continue
        try:
            if len(batch_ws) == 1:
                result[batch_ws[0]] = data
            else:
                lvl0 = data.columns.get_level_values(0).unique().tolist()
                for tk in batch_ws:
                    if tk in lvl0:
                        sub = data[tk].dropna()
                        if not sub.empty and len(sub) >= 30:
                            result[tk] = sub
        except:
            continue
    return result

def isle(all_data, tks, kset):
    rows = []
    for t in tks:
        try:
            tk = t + ".IS"
            if tk not in all_data:
                continue
            h = all_data[tk].copy()
            if h.empty or len(h) < 30:
                continue
            h = h.dropna()
            if len(h) < 30:
                continue
            sf = h['Close'].iloc[-1]
            gb = h['Close'].iloc[-min(25, len(h))]
            gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
            sma20 = h['Close'].rolling(20).mean().iloc[-1]
            r_ser = rsi(h['Close'])
            r = r_ser.iloc[-1] if not pd.isna(r_ser.iloc[-1]) else 50
            vm = h['Volume'].rolling(20).mean().iloc[-1]
            vr = h['Volume'].iloc[-1] / vm if vm > 0 else 1
            ai = 50
            if sf > sma20: ai += 15
            if gd > 0: ai += 10
            if r < 40: ai += 10
            elif r > 70: ai -= 15
            if vr > 1.3: ai += 10
            ai = max(20, min(95, ai))
            if ai >= 70 and gd > 0 and vr > 1.2:
                sn, tp = "GUCLU AL", "YUKSELIS BEKLENIYOR"
            elif ai >= 55 and gd > -1:
                sn, tp = "AL", "YUKSELIS EGILIMI"
            elif ai < 35 and gd < -1:
                sn, tp = "SAT", "DUSUS BEKLENIYOR"
            elif ai < 45:
                sn, tp = "ZAYIF", "ZAYIF SEYIR"
            else:
                sn, tp = "BEKLE", "BEKLE"
            atr_v = (h['High'] - h['Low']).rolling(14).mean().iloc[-1]
            sl = round(sf - atr_v * 2, 2) if not pd.isna(atr_v) and atr_v > 0 else 0
            hd = round(sf + atr_v * 3, 2) if not pd.isna(atr_v) and atr_v > 0 else 0
            rr = round((hd - sf) / (sf - sl), 2) if (sf - sl) > 0 else 0
            rows.append({
                "Hisse": t, "Katilim": "EVET" if tk in kset else "HAYIR",
                "Guc": round(ai, 2), "Sinyal": sn, "RSI": round(r, 1),
                "Trend": "Yukselis" if gd > 0 else "Dusus",
                "Getiri": "%" + str(round(gd, 2)),
                "Vol": str(round(vr, 2)) + "x",
                "Fiyat": str(round(sf, 2)) + " TL",
                "SL": str(sl) + " TL", "Hedef": str(hd) + " TL",
                "R/O": rr, "Tahmin": tp
            })
        except:
            continue
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df['A'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
    return df.sort_values(by=['A', 'Guc'], ascending=[True, False]).drop(columns=['A'])

pk = market_open()
if pk:
    st_autorefresh(interval=60000, key="r")

st.title("BIST Pro Terminali")
st.caption("Son: " + trt().strftime('%Y-%m-%d %H:%M:%S') + " | 15Dk Gecikmeli")

if pk:
    st.success("PIYASA ACIK - Otomatik veri 60 sn")
else:
    st.warning("PIYASA KAPALI - Seans disi")

c1, c2, c3, c4 = st.columns(4)
with c1:
    try:
        bh = yf.Ticker("XU100.IS").history(period="1d")
        if not bh.empty:
            f = bh['Close'].iloc[-1]
            d = ((f - bh['Open'].iloc[-1]) / bh['Open'].iloc[-1]) * 100
            st.metric("BIST 100", str(round(f, 2)), "%" + str(round(d, 2)))
        else:
            st.metric("BIST 100", "-", "0")
    except:
        st.metric("BIST 100", "-", "0")
with c2:
    st.metric("VIOP", "Denge", "0")
with c3:
    st.metric("Hisse", str(len(HISSELER.split(","))), "0")
with c4:
    st.metric("Cekim", str(st.session_state.cnt), "Son: " + st.session_state.last)

sk = st.checkbox("Sadece Islam'a Uygun", value=True)
mb = st.button("Manuel Veri Cek", type="primary")

if mb:
    st.cache_data.clear()
    st.session_state.man = True
    st.session_state.cnt += 1
    st.session_state.last = trt().strftime("%H:%M:%S")
    st.rerun()

with st.spinner("Veri yukleniyor (40'lik gruplar halinde)..."):
    tks = HISSELER.split(",")
    kset = set((k + ".IS") for k in KATILIM.split(","))
    all_data = fetch_all(tks)
    if all_data:
        df = isle(all_data, tks, kset)
        if not st.session_state.man:
            st.session_state.cnt += 1
            st.session_state.last = trt().strftime("%H:%M:%S")
        st.session_state.man = False
    else:
        df = pd.DataFrame()

if sk and not df.empty:
    df = df[df["Katilim"] == "EVET"]

if not df.empty:
    def rt(v):
        if "YUKSELIS" in str(v):
            return 'background-color:#1b5e20;color:white;font-weight:bold;'
        if "DUSUS" in str(v) or "ZAYIF" in str(v):
            return 'background-color:#b71c1c;color:white;font-weight:bold;'
        if "BEKLE" in str(v):
            return 'background-color:#e65100;color:white;font-weight:bold;'
        return ''
    def rs(v):
        if "GUCLU AL" in str(v):
            return 'background-color:#1b5e20;color:white;font-weight:bold;'
        if "AL" in str(v):
            return 'background-color:#2e7d32;color:white;'
        if "SAT" in str(v) or "ZAYIF" in str(v):
            return 'background-color:#b71c1c;color:white;'
        return 'background-color:#e65100;color:white;'
    def rk2(v):
        return 'color:#4CAF50;font-weight:bold;' if v == "EVET" else 'color:#F44336;'
    st.dataframe(df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk2, subset=["Katilim"]), use_container_width=True, height=700)
    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Gosterilen", len(df))
    s2.metric("Yukselis", len(df[df["Tahmin"].str.contains("YUKSELIS")]))
    s3.metric("Guclu AL", len(df[df["Sinyal"] == "GUCLU AL"]))
    s4.metric("Ort Guc", str(round(df["Guc"].mean(), 1)))
else:
    st.warning("Veri cekilemedi. Lutfen 'Manuel Veri Cek' butonuna basin.")

st.caption("15 dk gecikmeli. Yatirim tavsiyesi degildir.")
