import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from data.fetcher import toplu_veri_cek, piyasa_acik_mi, turkiye_saati

st.set_page_config(page_title="BIST Pro", layout="wide")

HISSELER = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

KATILIM = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"


def rsi(s, p=14):
    d = s.diff()
    k = d.where(d > 0, 0).rolling(p).mean()
    y = -d.where(d < 0, 0).rolling(p).mean()
    return 100 - (100 / (1 + k / y))


def hesapla(hisse, veri, katilim_set):
    if veri is None or len(veri) < 30:
        return None
    g = veri.dropna()
    if len(g) < 30:
        return None
    sf = float(g['Close'].iloc[-1])
    gb = float(g['Close'].iloc[-25])
    gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
    sma = float(g['Close'].rolling(20).mean().iloc[-1])
    rv = rsi(g['Close']).iloc[-1]
    r = float(rv) if not pd.isna(rv) else 50
    hm = float(g['Volume'].rolling(20).mean().iloc[-1])
    ho = float(g['Volume'].iloc[-1]) / hm if hm > 0 else 1

    skor = 50
    if sf > sma: skor += 15
    if gd > 0: skor += 10
    if r < 40: skor += 10
    elif r > 70: skor -= 15
    if ho > 1.3: skor += 10
    skor = max(20, min(95, skor))

    if skor >= 70 and gd > 0 and ho > 1.2:
        sn, tp = "GUCLU AL", "YUKSELIS BEKLENIYOR"
    elif skor >= 55 and gd > -1:
        sn, tp = "AL", "YUKSELIS EGILIMI"
    elif skor < 35 and gd < -1:
        sn, tp = "SAT", "DUSUS BEKLENIYOR"
    elif skor < 45:
        sn, tp = "ZAYIF", "ZAYIF SEYIR"
    else:
        sn, tp = "BEKLE", "BEKLE"

    s25 = g.iloc[-25:]
    gh = float(s25['High'].max())
    gl = float(s25['Low'].min())
    kp = (sf - gl) / (gh - gl) if gh > gl else 0.5
    gap = 50
    if kp > 0.75: gap += 20
    elif kp < 0.25: gap -= 15
    if gd > 1: gap += 10
    if ho > 1.5: gap += 10
    if r < 35: gap += 10
    elif r > 65: gap -= 5
    gap = max(0, min(100, gap))

    if gap >= 70:
        osig, bg = "GECE TASI", "YUKARI"
    elif gap >= 55:
        osig, bg = "ZAYIF TASI", "NOTR"
    elif gap < 35:
        osig, bg = "GECE TASIMA", "ASAGI"
    else:
        osig, bg = "BEKLE", "NOTR"

    av = (g['High'] - g['Low']).rolling(14).mean().iloc[-1]
    a = float(av) if not pd.isna(av) else 0
    if a > 0:
        sl = round(sf - a * 2, 2)
        hd = round(sf + a * 3, 2)
        ro = round((hd - sf) / (sf - sl), 2) if (sf - sl) > 0 else 0
    else:
        sl, hd, ro = 0, 0, 0

    return {
        "Hisse": hisse,
        "Katilim": "EVET" if (hisse + ".IS") in katilim_set else "HAYIR",
        "Guc": round(skor, 1),
        "Sinyal": sn,
        "RSI": round(r, 1),
        "Trend": "Yuk" if gd > 0 else "Dus",
        "Getiri": "%" + str(round(gd, 2)),
        "Hacim": str(round(ho, 2)) + "x",
        "Fiyat": str(round(sf, 2)) + " TL",
        "SL": str(sl) + " TL",
        "Hedef": str(hd) + " TL",
        "R/O": ro,
        "Tahmin": tp,
        "GapSkor": round(gap, 1),
        "Overnight": osig,
        "GapYon": bg
    }


varsayilanlar = {'giris': False, 'sayac': 0, 'son': '-', 'man': False}
for k, v in varsayilanlar.items():
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.giris:
    st.title("BIST Pro Giris")
    with st.form("giris_formu"):
        c1, c2 = st.columns(2)
        u = c1.text_input("Kullanici Adi")
        p = c2.text_input("Sifre", type="password")
        if st.form_submit_button("Giris Yap"):
            if u.strip() == "Cuma Babacan" and p.strip() == "784512":
                st.session_state.giris = True
                st.rerun()
            else:
                st.error("Hatali giris!")
    st.stop()

pk = piyasa_acik_mi()
if pk:
    st_autorefresh(interval=60000, key="yenile")

st.title("BIST Pro Terminali")
st.caption("Son: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 Dakika Gecikmeli")

if pk:
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

with st.spinner("Veriler yukleniyor..."):
    hl = HISSELER.split(",")
    ks = set(k + ".IS" for k in KATILIM.split(","))
    hv = toplu_veri_cek(hl)
    rows = []
    for h in hl:
        kod = h + ".IS"
        if kod in hv:
            r = hesapla(h, hv[kod], ks)
            if r:
                rows.append(r)
    if not st.session_state.man:
        st.session_state.sayac += 1
        st.session_state.son = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.man = False

c1, c2, c3, c4 = st.columns(4)
c1.metric("Taranan", "300")
c2.metric("Bulunan", len(rows))
c3.metric("Cekim", st.session_state.sayac)
c4.metric("Son", st.session_state.son)

sk = st.checkbox("Sadece Islam'a Uygun", value=True)
mb = st.button("Manuel Cek", type="primary")
if mb:
    st.cache_data.clear()
    st.session_state.man = True
    st.session_state.sayac += 1
    st.session_state.son = turkiye_saati().strftime("%H:%M:%S")
    st.rerun()

t1, t2 = st.tabs(["Trend Matrisi", "Overnight Gap"])

with t1:
    if not rows:
        st.warning("Veri yok")
    else:
        df = pd.DataFrame(rows)
        df['O'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
        df = df.sort_values(by=['O', 'Guc'], ascending=[True, False]).drop(columns=['O'])
        if sk:
            df = df[df["Katilim"] == "EVET"]

        def rt(v):
            if "YUKSELIS" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "DUSUS" in str(v) or "ZAYIF" in str(v): return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "BEKLE" in str(v): return 'background-color:#e65100;color:white;font-weight:bold;'
            return ''

        def rs(v):
            if "GUCLU" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AL" in str(v): return 'background-color:#2e7d32;color:white;'
            if "SAT" in str(v) or "ZAYIF" in str(v): return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'

        def rk(v):
            return 'color:#4CAF50;font-weight:bold;' if v == "EVET" else 'color:#F44336;'

        sty = df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk, subset=["Katilim"])
        st.dataframe(sty, use_container_width=True, height=650)

        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Gosterilen", len(df))
        o2.metric("Yukselis", len(df[df["Tahmin"].str.contains("YUKSELIS")]))
        o3.metric("Guclu AL", len(df[df["Sinyal"] == "GUCLU AL"]))
        o4.metric("Ort Guc", f"{df['Guc'].mean():.1f}")

with t2:
    st.subheader("Overnight Gap Stratejisi")
    if not rows:
        st.warning("Veri yok")
    else:
        df = pd.DataFrame(rows)
        if sk:
            df = df[df["Katilim"] == "EVET"]
        df = df.sort_values(by="GapSkor", ascending=False).reset_index(drop=True)

        def ro(v):
            if "GECE TASI" in str(v): return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ZAYIF" in str(v): return 'background-color:#2e7d32;color:white;'
            if "GECE TASIMA" in str(v): return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'

        def rg(v):
            if "YUKARI" in str(v): return 'color:#4CAF50;font-weight:bold;'
            if "ASAGI" in str(v): return 'color:#F44336;font-weight:bold;'
            return 'color:#FFC107;'

        sty = df.style.map(ro, subset=["Overnight"]).map(rg, subset=["GapYon"])
        st.dataframe(sty[["Hisse", "Fiyat", "GapSkor", "Overnight", "GapYon", "Hacim", "RSI"]], use_container_width=True, height=600)

        c1, c2, c3 = st.columns(3)
        c1.metric("GECE TASI", len(df[df["Overnight"] == "GECE TASI"]))
        c2.metric("ZAYIF TASI", len(df[df["Overnight"] == "ZAYIF TASI"]))
        c3.metric("Ort Gap", f"{df['GapSkor'].mean():.1f}")

        st.caption("Strateji: 17:50-18:30 arasi GECE TASI sinyali veren hisseler alinir, ertesi gun 09:40-10:00 arasi satilir.")

st.caption("Veriler 15 dakika gecikmelidir. Yatirim tavsiyesi degildir.")
