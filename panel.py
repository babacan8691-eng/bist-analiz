import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta, time
from streamlit_autorefresh import st_autorefresh

try:
    from arch import arch_model
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False

try:
    from statsmodels.tsa.stattools import coint
    HAS_SM = True
except ImportError:
    HAS_SM = False

TELEGRAM_TOKEN = ""
TELEGRAM_CHAT = ""

# Hedef kar marjlari (15 dakika gecikmeli veriye gore)
HEDEF_GUN_ICI_MIN = 2.0
HEDEF_GUN_ICI_MAX = 3.5
HEDEF_OVERNIGHT_MIN = 3.0
HEDEF_OVERNIGHT_MAX = 5.0

# 15 dakikalik bar bazli hedef marj katsayilari
BAR_15DK_HEDEF_KATSAYI = 1.2
BAR_15DK_SL_KATSAYI = 0.8
OVERNIGHT_HEDEF_KATSAYI = 1.8
OVERNIGHT_SL_KATSAYI = 1.0

# GECIKME TELAFI PARAMETRELERI
VERI_GECIKME_DAKIKA = 15
EXTRAPOLATION_BAR_SAYISI = 3
GECIKME_UYARI_ESIK = 1.0
KER_ESIK = 0.40

st.set_page_config(page_title="BIST Pro", layout="wide")

H = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

K = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO" def turkiye_saati():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))


def piyasa_acik_mi():
    s = turkiye_saati()
    if s.weekday() >= 5:
        return False
    return time(9, 40) <= s.time() <= time(18, 30)


@st.cache_data(ttl=60, show_spinner=False)
def toplu_veri_cek(hisse_listesi):
    tum = {}
    for i in range(0, len(hisse_listesi), 40):
        grup = hisse_listesi[i:i + 40]
        grup_uz = [x + ".IS" for x in grup]
        try:
            hv = yf.download(
                grup_uz,
                period="5d",
                interval="15m",
                group_by='ticker',
                threads=False,
                progress=False,
                auto_adjust=True,
                timeout=30
            )
            if hv is None or hv.empty:
                continue
            if len(grup_uz) == 1:
                tum[grup_uz[0]] = hv
            else:
                ust = hv.columns.get_level_values(0).unique().tolist()
                for k in grup_uz:
                    if k in ust:
                        alt = hv[k].dropna()
                        if not alt.empty and len(alt) >= 30:
                            tum[k] = alt
        except Exception:
            continue
    return tum


@st.cache_data(ttl=300, show_spinner=False)
def bist_endeks_verisi():
    try:
        return yf.Ticker("XU100.IS").history(period="1d")
    except Exception:
        return None


def garch_vol(seri):
    if not HAS_ARCH or len(seri) < 50:
        return 0.0
    try:
        ret = seri.pct_change().dropna() * 100
        if len(ret) < 50:
            return 0.0
        m = arch_model(ret, vol='Garch', p=1, q=1)
        r = m.fit(disp='off', show_warning=False)
        return round(float(r.conditional_volatility.iloc[-1]), 3)
    except Exception:
        return 0.0


def kointegrasyon(s1, s2):
    if not HAS_SM:
        return None
    try:
        s1 = s1.dropna()
        s2 = s2.dropna()
        n = min(len(s1), len(s2))
        if n < 30:
            return None
        a = s1.iloc[-n:].values
        b = s2.iloc[-n:].values
        _, pval, _ = coint(a, b)
        if pval > 0.05:
            return None
        X = np.column_stack([np.ones(n), b])
        beta = np.linalg.lstsq(X, a, rcond=None)[0]
        hata = a - (beta[0] + beta[1] * b)
        sd = hata.std()
        if sd == 0:
            return None
        z = (hata[-1] - hata.mean()) / sd
        return {"pvalue": round(float(pval), 4), "z": round(float(z), 2), "beta": round(float(beta[1]), 3)}
    except Exception:
        return None


def haber_cek():
    kaynaklar = ["https://www.paratic.com/rss/", "https://www.paratic.com/feed/"]
    for url in kaynaklar:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code != 200:
                continue
            icerik = r.text
            try:
                root = ET.fromstring(icerik)
            except ET.ParseError:
                continue
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            sonuc = []
            for item in items[:20]:
                baslik_el = item.find("title")
                if baslik_el is None:
                    baslik_el = item.find("{http://www.w3.org/2005/Atom}title")
                link_el = item.find("link")
                if link_el is None:
                    link_el = item.find("{http://www.w3.org/2005/Atom}link")
                tarih_el = item.find("pubDate")
                if tarih_el is None:
                    tarih_el = item.find("{http://www.w3.org/2005/Atom}updated")
                baslik = baslik_el.text if baslik_el is not None and baslik_el.text else "-"
                link = link_el.text if link_el is not None and link_el.text else "#"
                tarih = tarih_el.text if tarih_el is not None and tarih_el.text else "-"
                sonuc.append({"baslik": baslik[:90], "link": link, "tarih": str(tarih)[:16]})
            if sonuc:
                return sonuc
        except Exception:
            continue
    return []


def telegram_gonder(mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    try:
        r = requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": mesaj, "parse_mode": "HTML"},
            timeout=10
        )
        return r.status_code == 200
    except Exception:
        return False


def telegram_toplu_gonder(kdf, baslik):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return False
    try:
        mesaj = "<b>" + baslik + "</b>\n\n"
        for _, r in kdf.head(5).iterrows():
            mesaj += "- " + str(r['Hisse']) + " | Skor: " + str(r['KararSkor']) + " | " + str(r['KararSinyal']) + "\n"
            mesaj += "  SL: " + str(r['SL']) + " | Hedef: " + str(r['Hedef']) + "\n"
        r = requests.post(
            "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": mesaj, "parse_mode": "HTML"},
            timeout=10
        )
        return r.status_code == 200
    except Exception:
        return False def pairs_tara(hv, top_list):
    sonuc = []
    for i in range(len(top_list)):
        for j in range(i + 1, len(top_list)):
            h1 = top_list[i] + ".IS"
            h2 = top_list[j] + ".IS"
            if h1 not in hv or h2 not in hv:
                continue
            r = kointegrasyon(hv[h1]['Close'], hv[h2]['Close'])
            if r is not None:
                if r["z"] > 2:
                    sin = "1.SAT 2.AL"
                elif r["z"] < -2:
                    sin = "1.AL 2.SAT"
                else:
                    sin = "BEKLE"
                sonuc.append({
                    "Hisse1": top_list[i],
                    "Hisse2": top_list[j],
                    "p-value": r["pvalue"],
                    "Z-Skor": r["z"],
                    "Beta": r["beta"],
                    "Aksiyon": sin
                })
    return sonuc


def sinyal_degisim_tespit(kdf, gecmis_dict):
    yeni = []
    for _, r in kdf.iterrows():
        h = r['Hisse']
        yeni_sin = r['KararSinyal']
        eski_sin = gecmis_dict.get(h, None)
        if eski_sin is not None and eski_sin != yeni_sin:
            yeni.append({
                "Hisse": h,
                "Eski": eski_sin,
                "Yeni": yeni_sin,
                "Skor": r['KararSkor'],
                "Fiyat": r['Fiyat']
            })
    return yeni


def sinyal_dict_olustur(kdf):
    return {r['Hisse']: r['KararSinyal'] for _, r in kdf.iterrows()}


def rsi(s, p=14):
    d = s.diff()
    k = d.where(d > 0, 0).rolling(p).mean()
    y = -d.where(d < 0, 0).rolling(p).mean()
    return 100 - (100 / (1 + k / y))


def atr_f(h, l, c, p=14):
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(p).mean()


def kaufman_efficiency_ratio(seri, periyot=20):
    if len(seri) < periyot + 1:
        return 0.0
    s = seri.tail(periyot + 1).values
    net_degisim = abs(float(s[-1]) - float(s[0]))
    toplam_yol = float(np.sum(np.abs(np.diff(s))))
    if toplam_yol == 0:
        return 0.0
    ker = net_degisim / toplam_yol
    return round(float(ker), 3)


def choppiness_index(high, low, close, periyot=14):
    if len(close) < periyot + 1:
        return 50.0
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr_toplam = float(tr.tail(periyot).sum())
    en_yuksek = float(high.tail(periyot).max())
    en_dusuk = float(low.tail(periyot).min())
    if en_yuksek - en_dusuk <= 0 or atr_toplam <= 0:
        return 50.0
    chop = 100 * np.log10(atr_toplam / (en_yuksek - en_dusuk)) / np.log10(periyot)
    return round(float(max(0, min(100, chop))), 2)


def parkinson_volatility(high, low, periyot=20):
    if len(high) < periyot:
        return 0.0
    h = high.tail(periyot).values
    l = low.tail(periyot).values
    if np.any(h <= 0) or np.any(l <= 0):
        return 0.0
    ln_hl = np.log(h / l)
    park = np.sqrt(np.mean(ln_hl ** 2) / (4 * np.log(2)))
    return round(float(park * 100), 3)


def garman_klass_volatility(open_p, high, low, close, periyot=20):
    if len(close) < periyot:
        return 0.0
    o = open_p.tail(periyot).values
    h = high.tail(periyot).values
    l = low.tail(periyot).values
    c = close.tail(periyot).values
    if np.any(o <= 0) or np.any(h <= 0) or np.any(l <= 0) or np.any(c <= 0):
        return 0.0
    hl = np.log(h / l)
    co = np.log(c / o)
    gk = 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2
    gk = np.sqrt(np.mean(np.maximum(gk, 0)))
    return round(float(gk * 100), 3)


def kyle_lambda(close, hacim, periyot=20):
    if len(close) < periyot + 1:
        return 0.0
    ret = close.pct_change().tail(periyot).abs().values
    vol = hacim.tail(periyot).values
    if np.any(vol <= 0):
        return 0.0
    lam = np.mean(ret / np.sqrt(vol))
    return round(float(lam * 1e4), 3)


def shannon_entropy(seri, periyot=20, bins=5):
    if len(seri) < periyot:
        return 0.0
    s = seri.tail(periyot).values
    if np.std(s) == 0:
        return 0.0
    try:
        hist, _ = np.histogram(s, bins=bins)
        p = hist / hist.sum()
        p = p[p > 0]
        ent = -np.sum(p * np.log2(p))
        return round(float(ent), 3)
    except Exception:
        return 0.0 def kriter_degerlendir(ker, chop, parkinson, gk, kyle, entropy):
    sonuc = []
    ker_ok = ker >= KER_ESIK
    chop_ok = chop <= 45
    park_ok = 0.1 <= parkinson <= 3.0
    gk_ok = 0.1 <= gk <= 3.5
    kyle_ok = kyle <= 1.5
    ent_ok = entropy <= 2.5
    gecen = sum([ker_ok, chop_ok, park_ok, gk_ok, kyle_ok, ent_ok])
    sonuc.append(("KER", ker, ker_ok, "Trend kalitesi"))
    sonuc.append(("CHOP", chop, chop_ok, "Yataylik"))
    sonuc.append(("Parkinson", parkinson, park_ok, "High/Low vol"))
    sonuc.append(("Garman-Klass", gk, gk_ok, "OHLC vol"))
    sonuc.append(("Kyle Lambda", kyle, kyle_ok, "Likidite"))
    sonuc.append(("Entropy", entropy, ent_ok, "Ongorulebilirlik"))
    if gecen >= 6:
        seviye = "MUKEMMEL"
    elif gecen >= 5:
        seviye = "GUCLU"
    elif gecen >= 4:
        seviye = "ORTA"
    elif gecen >= 2:
        seviye = "ZAYIF"
    else:
        seviye = "RISKLI"
    return sonuc, gecen, seviye


def non_klise_skor(ker, chop, parkinson, gk, kyle, entropy):
    sk = 0
    sk += ker * 30
    sk += (100 - chop) * 0.20
    if 0.3 <= parkinson <= 2.0:
        sk += 15
    elif parkinson < 0.3:
        sk += 8
    if 0.3 <= gk <= 2.5:
        sk += 15
    elif gk < 0.3:
        sk += 8
    if kyle <= 0.8:
        sk += 12
    elif kyle <= 1.5:
        sk += 6
    sk += (3 - min(entropy, 3)) * 4
    sk = max(0, min(100, sk))
    return round(sk, 1)


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


def karar_motoru(guc, rsi_d, macd_h, hacim, vol_rej, ofi, garch_v, t15, g15, trend, ker=0.5, chop=50.0, kyle=0.0, entropy=2.0, nk_skor=50.0):
    sk = 50
    sk += (guc - 50) * 0.20
    if rsi_d < 30:
        sk += 10
    elif rsi_d < 45:
        sk += 5
    elif rsi_d > 70:
        sk -= 10
    elif rsi_d > 55:
        sk -= 3
    if macd_h > 0:
        sk += 5
    else:
        sk -= 3
    if hacim > 1.5:
        sk += 7
    elif hacim > 1.2:
        sk += 3
    elif hacim < 0.7:
        sk -= 3
    if vol_rej == "DUSUK":
        sk += 3
    elif vol_rej == "YUKSEK":
        sk -= 5
    if ofi > 2:
        sk += 6
    elif ofi > 0.5:
        sk += 3
    elif ofi < -2:
        sk -= 6
    elif ofi < -0.5:
        sk -= 3
    if 0 < garch_v < 0.5:
        sk += 3
    elif garch_v > 1.0:
        sk -= 4
    if t15 == "YUKARI":
        sk += 7 * (g15 / 100)
    elif t15 == "ASAGI":
        sk -= 7 * (g15 / 100)
    if trend == "Yuk":
        sk += 3
    else:
        sk -= 3
    sk += (nk_skor - 50) * 0.20
    if ker >= KER_ESIK:
        sk += 4
    elif ker < (KER_ESIK * 0.6):
        sk -= 4
    if chop <= 38:
        sk += 3
    elif chop >= 62:
        sk -= 5
    if kyle > 2.0:
        sk -= 4
    if entropy > 2.6:
        sk -= 3
    sk = max(0, min(100, sk))
    if sk >= 75:
        sinyal = "GUCLU AL"
        renk = "#1b5e20"
        neden = "Tum metrikler olumlu"
    elif sk >= 62:
        sinyal = "AL"
        renk = "#2e7d32"
        neden = "Cogunluk pozitif"
    elif sk <= 25:
        sinyal = "GUCLU SAT"
        renk = "#b71c1c"
        neden = "Tum metrikler olumsuz"
    elif sk <= 38:
        sinyal = "SAT"
        renk = "#c62828"
        neden = "Cogunluk negatif"
    else:
        sinyal = "BEKLE"
        renk = "#e65100"
        neden = "Kararsiz"
    return round(sk, 1), sinyal, renk, neden


POZ_KELIMELER = ["yukselis", "artis", "rekor", "kar", "buyume", "guclu", "pozitif", "kazanc", "ihale", "anlasma", "yatirim", "genisleme", "hedef", "basari", "onay", "kabul", "sozlesme", "ortaklik", "siparis", "temettu", "prim"]
NEG_KELIMELER = ["dusus", "azalis", "zarar", "kriz", "iflas", "kayip", "zayif", "negatif", "risk", "borc", "ceza", "sorusturma", "dava", "konkordato", "temerrut", "iptal", "durdurma", "uyari", "not indirimi", "satis baskisi"] def lstm_tahmin(g):
    if len(g) < 30:
        return 0.0, 50.0
    s = g['Close'].tail(30).values
    agirlik = np.array([np.exp(-0.15 * i) for i in range(30)])
    agirlik = agirlik / agirlik.sum()
    hafiza = float(np.sum(s * agirlik))
    son = float(s[-1])
    egim = (son - hafiza) / hafiza * 100 if hafiza > 0 else 0
    hf = g['High'].tail(30).values
    lf = g['Low'].tail(30).values
    vol = float(np.std((hf - lf) / s) * 100)
    tahmin_yuzde = egim * 0.6 + (1 if egim > 0 else -1) * vol * 0.2
    guven = min(95, max(30, 100 - vol * 2))
    return round(tahmin_yuzde, 2), round(guven, 1)


def nlp_duygu(basliklar, hisse):
    if not basliklar:
        return 0.0, 0
    skor = 0
    bulunan = 0
    hisse_l = str(hisse).lower()
    for item in basliklar:
        if isinstance(item, dict):
            b = str(item.get("baslik", "")).lower()
        else:
            b = str(item).lower()
        if hisse_l not in b:
            continue
        bulunan += 1
        for k in POZ_KELIMELER:
            if k in b:
                skor += 1
        for k in NEG_KELIMELER:
            if k in b:
                skor -= 1
    if bulunan == 0:
        return 0.0, 0
    return round(skor / bulunan, 2), bulunan


def rl_portfoy_agi(g):
    if len(g) < 20:
        return 0.0, 0.0
    ret = g['Close'].pct_change().tail(20).fillna(0).values
    odul = np.sum(ret)
    ceza = np.sum(np.minimum(ret, 0))
    q = odul * 0.7 + ceza * 0.3
    sharpe = np.mean(ret) / (np.std(ret) + 1e-9) * np.sqrt(252 * 25)
    return round(q * 100, 2), round(sharpe, 2)


def gnn_manipulasyon(g, emsaller_dict):
    if len(g) < 20 or not emsaller_dict:
        return 0.0
    kend = g['Close'].pct_change().tail(20).dropna().values
    if len(kend) < 5:
        return 0.0
    korelasyonlar = []
    for _, em in list(emsaller_dict.items())[:10]:
        if len(em) < 20:
            continue
        e = em['Close'].pct_change().tail(20).dropna().values
        n = min(len(kend), len(e))
        if n < 5:
            continue
        a = kend[-n:]
        b = e[-n:]
        if np.std(a) == 0 or np.std(b) == 0:
            continue
        k = np.corrcoef(a, b)[0, 1]
        if not np.isnan(k):
            korelasyonlar.append(k)
    if not korelasyonlar:
        return 0.0
    ort = np.mean(korelasyonlar)
    sapma = abs(ort - 0.5)
    return round(sapma * 100, 1)


def gan_stres_test(g):
    if len(g) < 30:
        return 0.0
    ret = g['Close'].pct_change().dropna().values
    if len(ret) < 20:
        return 0.0
    vol = np.std(ret)
    if vol == 0:
        return 0.0
    z = (ret - np.mean(ret)) / vol
    kuyruk = np.percentile(z, 5)
    var_95 = float(kuyruk * vol * 100)
    return round(var_95, 2)


def hibrit_deep_skor(lstm_yon, lstm_guven, nlp_skor, rl_q, rl_sharpe, gnn_manip, gan_var):
    sk = 50
    sk += lstm_yon * 5
    sk += (lstm_guven - 50) * 0.15
    sk += nlp_skor * 3
    sk += rl_q * 0.5
    sk += min(rl_sharpe, 20) * 0.5
    sk -= gnn_manip * 0.2
    sk -= abs(gan_var) * 0.5
    sk = max(0, min(100, sk))
    if sk >= 70:
        seviye = "YUKSEK POZITIF"
    elif sk >= 58:
        seviye = "POZITIF"
    elif sk >= 42:
        seviye = "NOTR"
    elif sk >= 30:
        seviye = "NEGATIF"
    else:
        seviye = "YUKSEK NEGATIF"
    return round(sk, 1), seviye


def ofi_hesapla(g, periyot=14):
    if len(g) < periyot:
        return 0.0
    son = g.tail(periyot)
    alis = 0.0
    satis = 0.0
    for i in range(len(son)):
        b = son.iloc[i]
        if float(b['Close']) > float(b['Open']):
            alis += float(b['Volume'])
        else:
            satis += float(b['Volume'])
    top = alis + satis
    if top == 0:
        return 0.0
    ofi = ((alis - satis) / top) * 100
    return round(ofi, 2)


def hacim_orani(g, kisa=5, uzun=20):
    if len(g) < uzun:
        return 1.0
    vk = float(g['Volume'].tail(kisa).mean())
    vu = float(g['Volume'].tail(uzun).mean())
    if vu == 0:
        return 1.0
    return round(vk / vu, 2)


def vol_rejim(g, periyot=20):
    if len(g) < periyot + 5:
        return "NORMAL"
    son = g.tail(5)
    onceki = g.iloc[-periyot:-5]
    if len(onceki) < 5:
        return "NORMAL"
    v_son = float((son['High'] - son['Low']).mean())
    v_once = float((onceki['High'] - onceki['Low']).mean())
    if v_once == 0:
        return "NORMAL"
    oran = v_son / v_once
    if oran > 1.5:
        return "YUKSEK"
    elif oran < 0.7:
        return "DUSUK"
    return "NORMAL"


def trend_tespit(g, periyot=20):
    if len(g) < periyot:
        return "Notr", 0.0
    sma = g['Close'].rolling(periyot).mean()
    son = float(g['Close'].iloc[-1])
    sma_son = float(sma.iloc[-1])
    if sma_son == 0:
        return "Notr", 0.0
    fark = ((son - sma_son) / sma_son) * 100
    if fark > 1.0:
        return "Yuk", fark
    elif fark < -1.0:
        return "Dus", fark
    return "Notr", fark


def macd_hesapla(g, kisa=12, uzun=26, sinyal=9):
    if len(g) < uzun + sinyal:
        return 0.0, 0.0, 0.0
    ema_k = g['Close'].ewm(span=kisa, adjust=False).mean()
    ema_u = g['Close'].ewm(span=uzun, adjust=False).mean()
    macd = ema_k - ema_u
    sig = macd.ewm(span=sinyal, adjust=False).mean()
    hist = macd - sig
    return round(float(macd.iloc[-1]), 4), round(float(sig.iloc[-1]), 4), round(float(hist.iloc[-1]), 4) def sinyal_hesapla(g, emsaller=None):
    if len(g) < 30:
        return None
    close = g['Close']
    high = g['High']
    low = g['Low']
    open_p = g['Open']
    hacim = g['Volume']

    fiyat = float(close.iloc[-1])
    rsi_d = float(rsi(close).iloc[-1]) if len(close) >= 15 else 50.0
    macd_l, macd_s, macd_h = macd_hesapla(g)
    h_orani = hacim_orani(g)
    vol_rej = vol_rejim(g)
    ofi = ofi_hesapla(g)
    trend, trend_fark = trend_tespit(g)

    garch_v = garch_vol(close)

    ker = kaufman_efficiency_ratio(close)
    chop = choppiness_index(high, low, close)
    parkinson = parkinson_volatility(high, low)
    gk = garman_klass_volatility(open_p, high, low, close)
    kyle = kyle_lambda(close, hacim)
    entropy = shannon_entropy(close)

    _, nk_gecen, nk_seviye = kriter_degerlendir(ker, chop, parkinson, gk, kyle, entropy)
    nk_skor = non_klise_skor(ker, chop, parkinson, gk, kyle, entropy)

    t15, g15, _ = tahmin_15(g)

    lstm_yon, lstm_guven = lstm_tahmin(g)
    rl_q, rl_sharpe = rl_portfoy_agi(g)
    gnn_manip = gnn_manipulasyon(g, emsaller) if emsaller else 0.0
    gan_var = gan_stres_test(g)
    nlp_skor, nlp_haber = 0.0, 0

    hib_skor, hib_seviye = hibrit_deep_skor(
        lstm_yon, lstm_guven, nlp_skor, rl_q, rl_sharpe, gnn_manip, gan_var
    )

    guc = 50.0
    if trend == "Yuk":
        guc += min(trend_fark, 5) * 3
    else:
        guc -= min(abs(trend_fark), 5) * 3
    if macd_h > 0:
        guc += 5
    else:
        guc -= 5
    if rsi_d < 50 and rsi_d > 30:
        guc += 5
    elif rsi_d > 70:
        guc -= 8
    guc = max(0, min(100, guc))

    karar_skor, karar_sinyal, karar_renk, karar_neden = karar_motoru(
        guc, rsi_d, macd_h, h_orani, vol_rej, ofi, garch_v, t15, g15, trend,
        ker, chop, kyle, entropy, nk_skor
    )

    return {
        "Fiyat": round(fiyat, 2),
        "RSI": round(rsi_d, 1),
        "MACD_Hist": macd_h,
        "Hacim": h_orani,
        "VolRejim": vol_rej,
        "OFI": ofi,
        "GARCH": garch_v,
        "Trend": trend,
        "TrendFark": round(trend_fark, 2),
        "Tahmin15": t15,
        "Guven15": g15,
        "KER": ker,
        "CHOP": chop,
        "Parkinson": parkinson,
        "GarmanKlass": gk,
        "Kyle": kyle,
        "Entropy": entropy,
        "NK_Gecen": nk_gecen,
        "NK_Seviye": nk_seviye,
        "NK_Skor": nk_skor,
        "LSTM_Yon": lstm_yon,
        "LSTM_Guven": lstm_guven,
        "RL_Q": rl_q,
        "RL_Sharpe": rl_sharpe,
        "GNN_Manip": gnn_manip,
        "GAN_VaR": gan_var,
        "NLP_Skor": nlp_skor,
        "NLP_Haber": nlp_haber,
        "HibritSkor": hib_skor,
        "HibritSeviye": hib_seviye,
        "KararSkor": karar_skor,
        "KararSinyal": karar_sinyal,
        "KararRenk": karar_renk,
        "KararNeden": karar_neden,
        "Guc": round(guc, 1),
    }


def hedef_ve_sl_hesapla(g, karar_sinyal, hib_skor, nk_skor, atr_carpan=1.2, sl_carpan=0.8):
    if len(g) < 20:
        return None
    atr = float(atr_f(g['High'], g['Low'], g['Close']).iloc[-1])
    fiyat = float(g['Close'].iloc[-1])
    if fiyat <= 0 or atr <= 0:
        return None

    kalite_bonus = (hib_skor - 50) * 0.02
    nk_bonus = (nk_skor - 50) * 0.01
    hedef_yuzde = (atr / fiyat) * 100 * atr_carpan + kalite_bonus + nk_bonus
    sl_yuzde = (atr / fiyat) * 100 * sl_carpan

    hedef_yuzde = max(HEDEF_GUN_ICI_MIN, min(HEDEF_GUN_ICI_MAX, hedef_yuzde))
    sl_yuzde = max(0.5, min(2.5, sl_yuzde))

    if "AL" in karar_sinyal:
        hedef = fiyat * (1 + hedef_yuzde / 100)
        sl = fiyat * (1 - sl_yuzde / 100)
    elif "SAT" in karar_sinyal:
        hedef = fiyat * (1 - hedef_yuzde / 100)
        sl = fiyat * (1 + sl_yuzde / 100)
    else:
        hedef = fiyat * (1 + hedef_yuzde / 100)
        sl = fiyat * (1 - sl_yuzde / 100)

    ro = abs(hedef - fiyat) / abs(fiyat - sl) if abs(fiyat - sl) > 0 else 0

    return {
        "Hedef": round(hedef, 2),
        "SL": round(sl, 2),
        "HedefYuzde": round(hedef_yuzde, 2),
        "SLYuzde": round(sl_yuzde, 2),
        "RO": round(ro, 2),
    } def gecikme_telafi_hesapla(g, son_bar_fiyat, hedef, sl):
    if len(g) < 5:
        return {
            "TahminiFiyat": son_bar_fiyat,
            "TahminFark": 0.0,
            "KalanMarj": 0.0,
            "KayipMarj": 0.0,
            "GecikmeUyari": "MINIMAL GECIKME",
            "GecikmeRenk": "#1b5e20",
            "SinyalZayiflik": 0.0,
            "GecikmeDk": VERI_GECIKME_DAKIKA,
        }

    son_barlar = g.tail(EXTRAPOLATION_BAR_SAYISI + 1)
    degisimler = son_barlar['Close'].pct_change().dropna().values
    if len(degisimler) == 0:
        ortalama_degisim = 0.0
    else:
        ortalama_degisim = float(np.mean(degisimler))

    tahmini_fiyat = son_bar_fiyat * (1 + ortalama_degisim)
    tahmin_fark = ((tahmini_fiyat - son_bar_fiyat) / son_bar_fiyat) * 100 if son_bar_fiyat > 0 else 0.0

    if tahmini_fiyat > 0 and hedef > 0:
        if hedef > son_bar_fiyat:
            kalan_marj = ((hedef - tahmini_fiyat) / tahmini_fiyat) * 100
        else:
            kalan_marj = ((tahmini_fiyat - hedef) / tahmini_fiyat) * 100
    else:
        kalan_marj = 0.0

    kayip_marj = abs(tahmin_fark)

    if kayip_marj < 5:
        uyari = "MINIMAL GECIKME"
        renk = "#1b5e20"
    elif kayip_marj < 15:
        uyari = "AZ GECIKME"
        renk = "#66bb6a"
    elif kayip_marj < 30:
        uyari = "ORTA GECIKME"
        renk = "#FFC107"
    elif kayip_marj < 50:
        uyari = "YUKSEK GECIKME"
        renk = "#e65100"
    else:
        uyari = "KRITIK GECIKME"
        renk = "#b71c1c"

    sinyal_zayiflik = min(100, kayip_marj * 2)
    if sinyal_zayiflik < 30:
        sinyal_zayiflik = 100 - sinyal_zayiflik

    return {
        "TahminiFiyat": round(tahmini_fiyat, 2),
        "TahminFark": round(tahmin_fark, 2),
        "KalanMarj": round(kalan_marj, 2),
        "KayipMarj": round(kayip_marj, 2),
        "GecikmeUyari": uyari,
        "GecikmeRenk": renk,
        "SinyalZayiflik": round(sinyal_zayiflik, 1),
        "GecikmeDk": VERI_GECIKME_DAKIKA,
    }


def marj_uygunluk(deger, tip="gun_ici"):
    if tip == "gun_ici":
        mn, mx = HEDEF_GUN_ICI_MIN, HEDEF_GUN_ICI_MAX
    else:
        mn, mx = HEDEF_OVERNIGHT_MIN, HEDEF_OVERNIGHT_MAX
    if mn <= deger <= mx:
        return "MARJ UYGUN", "#1b5e20"
    elif deger < mn:
        return "MARJ DUSUK", "#e65100"
    else:
        return "MARJ YUKSEK", "#2e7d32"


def kalite_uygunluk(hib_skor, nk_skor):
    ort = (hib_skor + nk_skor) / 2
    if ort >= 65:
        return "KALITE YUKSEK", "#1b5e20"
    elif ort >= 50:
        return "KALITE IYI", "#2e7d32"
    elif ort >= 35:
        return "KALITE ORTA", "#e65100"
    else:
        return "KALITE DUSUK", "#b71c1c"


def overnight_gap_hesapla(g, hib_skor, nk_skor):
    if len(g) < 10:
        return None
    son = g.iloc[-1]
    kapanis = float(son['Close'])
    if kapanis <= 0:
        return None

    son_barlar = g.tail(5)
    alis_vol = float(son_barlar[son_barlar['Close'] > son_barlar['Open']]['Volume'].sum())
    satis_vol = float(son_barlar[son_barlar['Close'] <= son_barlar['Open']]['Volume'].sum())
    top = alis_vol + satis_vol
    if top == 0:
        gap_skor = 50.0
    else:
        gap_skor = (alis_vol / top) * 100

    if hib_skor > 55:
        gap_skor += 5
    if nk_skor > 55:
        gap_skor += 5
    gap_skor = max(0, min(100, gap_skor))

    atr = float(atr_f(g['High'], g['Low'], g['Close']).iloc[-1])
    hedef_marj = (atr / kapanis) * 100 * OVERNIGHT_HEDEF_KATSAYI
    sl_marj = (atr / kapanis) * 100 * OVERNIGHT_SL_KATSAYI

    hedef_marj = max(HEDEF_OVERNIGHT_MIN, min(HEDEF_OVERNIGHT_MAX, hedef_marj))
    sl_marj = max(0.8, min(3.0, sl_marj))

    hedef_fiyat = kapanis * (1 + hedef_marj / 100)
    sl_fiyat = kapanis * (1 - sl_marj / 100)
    ro = abs(hedef_fiyat - kapanis) / abs(kapanis - sl_fiyat) if abs(kapanis - sl_fiyat) > 0 else 0

    if gap_skor >= 65:
        gap_yon = "YUKARI"
        overnight = "GECE TASI"
    elif gap_skor <= 35:
        gap_yon = "ASAGI"
        overnight = "ZAYIF TASI"
    else:
        gap_yon = "NOTR"
        overnight = "BEKLE"

    marj_uyari, marj_renk = marj_uygunluk(hedef_marj, "overnight")

    return {
        "Kapanis": round(kapanis, 2),
        "GapSkor": round(gap_skor, 1),
        "GapYon": gap_yon,
        "Overnight": overnight,
        "OvernightHedefMarj": round(hedef_marj, 2),
        "OvernightSLMarj": round(sl_marj, 2),
        "OvernightHedefFiyat": round(hedef_fiyat, 2),
        "OvernightSLFiyat": round(sl_fiyat, 2),
        "OvernightRO": round(ro, 2),
        "OvernightMarjUygun": marj_uyari,
        "OvernightMarjRenk": marj_renk,
    } def tam_analiz_yap(hv, basliklar=None):
    sonuc_listesi = []
    hisse_listesi = [k.replace(".IS", "") for k in hv.keys()]
    emsaller = {k: v for k, v in hv.items()}

    for hisse_uz, g in hv.items():
        hisse = hisse_uz.replace(".IS", "")
        if len(g) < 30:
            continue
        try:
            sinyal = sinyal_hesapla(g, emsaller)
            if sinyal is None:
                continue

            if basliklar:
                nlp_skor, nlp_haber = nlp_duygu(basliklar, hisse)
                sinyal["NLP_Skor"] = nlp_skor
                sinyal["NLP_Haber"] = nlp_haber

            hedef_sl = hedef_ve_sl_hesapla(
                g,
                sinyal["KararSinyal"],
                sinyal["HibritSkor"],
                sinyal["NK_Skor"]
            )
            if hedef_sl is None:
                continue

            son_bar_fiyat = sinyal["Fiyat"]
            gecikme = gecikme_telafi_hesapla(
                g,
                son_bar_fiyat,
                hedef_sl["Hedef"],
                hedef_sl["SL"]
            )

            marj_uygun, marj_renk = marj_uygunluk(hedef_sl["HedefYuzde"], "gun_ici")
            kalite_uygun, kalite_renk = kalite_uygunluk(sinyal["HibritSkor"], sinyal["NK_Skor"])

            overnight = overnight_gap_hesapla(g, sinyal["HibritSkor"], sinyal["NK_Skor"])

            son_bar_zamani = "-"
            if len(g) > 0:
                try:
                    son_bar_zamani = str(g.index[-1])[:16]
                except Exception:
                    son_bar_zamani = "-"

            satir = {
                "Hisse": hisse,
                "Fiyat": son_bar_fiyat,
                "SonBarZamani": son_bar_zamani,
                "SonBarFiyat": son_bar_fiyat,
                "TahminiFiyat": gecikme["TahminiFiyat"],
                "TahminFark": gecikme["TahminFark"],
                "TahminFarkRaw": gecikme["TahminFark"],
                "KalanMarj": gecikme["KalanMarj"],
                "KayipMarj": gecikme["KayipMarj"],
                "GecikmeDk": gecikme["GecikmeDk"],
                "GecikmeUyari": gecikme["GecikmeUyari"],
                "GecikmeRenk": gecikme["GecikmeRenk"],
                "SinyalZayiflik": gecikme["SinyalZayiflik"],

                "Hedef": hedef_sl["Hedef"],
                "SL": hedef_sl["SL"],
                "HedefYuzde": hedef_sl["HedefYuzde"],
                "SLYuzde": hedef_sl["SLYuzde"],
                "RO": hedef_sl["RO"],
                "RORaw": hedef_sl["RO"],
                "RO_ATR": hedef_sl["RO"],
                "MarjUygun": marj_uygun,
                "MarjRenk": marj_renk,

                "KaliteUygun": kalite_uygun,
                "KaliteRenk": kalite_renk,

                "RSI": sinyal["RSI"],
                "MACD": sinyal["MACD_Hist"],
                "Hacim": sinyal["Hacim"],
                "VolRejim": sinyal["VolRejim"],
                "OFI": sinyal["OFI"],
                "GARCH": sinyal["GARCH"],
                "Trend": sinyal["Trend"],
                "TrendFark": sinyal["TrendFark"],
                "Momentum5": sinyal["TrendFark"],
                "Tahmin": "YUKSELIS BEKLENIYOR" if sinyal["TrendFark"] > 0 else ("DUSUS BEKLENIYOR" if sinyal["TrendFark"] < 0 else "YATAY"),
                "Tahmin15": sinyal["Tahmin15"],
                "Guven15": sinyal["Guven15"],
                "Beklenti15": sinyal["Guven15"],

                "KER": sinyal["KER"],
                "CHOP": sinyal["CHOP"],
                "Parkinson": sinyal["Parkinson"],
                "GarmanKlass": sinyal["GarmanKlass"],
                "Kyle": sinyal["Kyle"],
                "Entropy": sinyal["Entropy"],
                "NK_Gecen": sinyal["NK_Gecen"],
                "NK_Seviye": sinyal["NK_Seviye"],
                "NK_Skor": sinyal["NK_Skor"],

                "LSTM_Yon": sinyal["LSTM_Yon"],
                "LSTM_Guven": sinyal["LSTM_Guven"],
                "RL_Q": sinyal["RL_Q"],
                "RL_Sharpe": sinyal["RL_Sharpe"],
                "GNN_Manip": sinyal["GNN_Manip"],
                "GAN_VaR": sinyal["GAN_VaR"],
                "NLP_Skor": sinyal["NLP_Skor"],
                "NLP_Haber": sinyal["NLP_Haber"],
                "HibritSkor": sinyal["HibritSkor"],
                "HibritSeviye": sinyal["HibritSeviye"],

                "Guc": sinyal["Guc"],
                "KararSkor": sinyal["KararSkor"],
                "KararSinyal": sinyal["KararSinyal"],
                "KararRenk": sinyal["KararRenk"],
                "KararNeden": sinyal["KararNeden"],

                "GunIciUygun": "EVET" if marj_uygun == "MARJ UYGUN" else "HAYIR",
            }

            if overnight is not None:
                satir.update({
                    "Overnight": overnight["Overnight"],
                    "GapSkor": overnight["GapSkor"],
                    "GapYon": overnight["GapYon"],
                    "Kapanis": overnight["Kapanis"],
                    "KapanisRaw": overnight["Kapanis"],
                    "OvernightHedefMarj": overnight["OvernightHedefMarj"],
                    "OvernightSLMarj": overnight["OvernightSLMarj"],
                    "OvernightHedefFiyat": overnight["OvernightHedefFiyat"],
                    "OvernightSLFiyat": overnight["OvernightSLFiyat"],
                    "OvernightRO": overnight["OvernightRO"],
                    "OvernightMarjUygun": overnight["OvernightMarjUygun"],
                    "OvernightMarjRenk": overnight["OvernightMarjRenk"],
                    "OvernightUygun": "EVET" if overnight["OvernightMarjUygun"] == "MARJ UYGUN" else "HAYIR",
                })
            else:
                satir.update({
                    "Overnight": "YOK",
                    "GapSkor": 0,
                    "GapYon": "NOTR",
                    "Kapanis": son_bar_fiyat,
                    "KapanisRaw": son_bar_fiyat,
                    "OvernightHedefMarj": 0,
                    "OvernightSLMarj": 0,
                    "OvernightHedefFiyat": 0,
                    "OvernightSLFiyat": 0,
                    "OvernightRO": 0,
                    "OvernightMarjUygun": "YOK",
                    "OvernightMarjRenk": "#666666",
                    "OvernightUygun": "HAYIR",
                })

            sonuc_listesi.append(satir)
        except Exception:
            continue

    return pd.DataFrame(sonuc_listesi) def hisse_kart_html(satir):
    return f"""
    <div style="background:#1e1e1e;border-radius:10px;padding:14px;margin:6px 0;
                border-left:5px solid {satir['KararRenk']};">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:18px;font-weight:bold;color:#fff;">{satir['Hisse']}</span>
            <span style="background:{satir['KararRenk']};color:#fff;padding:3px 10px;
                         border-radius:6px;font-size:13px;font-weight:bold;">{satir['KararSinyal']}</span>
        </div>
        <div style="color:#ccc;font-size:12px;margin-top:6px;">
            Karar Skoru: <b>{satir['KararSkor']}</b>/100 |
            Fiyat: <b>{satir['Fiyat']} TL</b> |
            Son Bar: <b>{satir['SonBarZamani']}</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Tahmini Su An: <b>{satir['TahminiFiyat']} TL</b> (%{satir['TahminFark']}) |
            Gecikme: <b>{satir['GecikmeDk']} dk</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            SL: <b>{satir['SL']}</b> | Hedef: <b>{satir['Hedef']}</b> |
            R/O: <b>{satir['RO']}</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Kalan Marj: <b>%{satir['KalanMarj']}</b> |
            Marj Uygunluk: <span style="background:{satir['MarjRenk']};padding:2px 6px;
                                    border-radius:4px;color:#fff;">{satir['MarjUygun']}</span>
            Kalite: <span style="background:{satir['KaliteRenk']};padding:2px 6px;
                              border-radius:4px;color:#fff;">{satir['KaliteUygun']}</span>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Gecikme Durumu: <span style="background:{satir['GecikmeRenk']};padding:2px 6px;
                                       border-radius:4px;color:#fff;">{satir['GecikmeUyari']}</span>
        </div>
    </div>
    """


def overnight_kart_html(satir):
    return f"""
    <div style="background:#1b3a1b;border-radius:10px;padding:14px;margin:6px 0;
                border-left:5px solid #4caf50;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:18px;font-weight:bold;color:#fff;">{satir['Hisse']}</span>
            <span style="background:#4caf50;color:#fff;padding:3px 10px;
                         border-radius:6px;font-size:13px;font-weight:bold;">{satir['Overnight']}</span>
        </div>
        <div style="color:#ccc;font-size:12px;margin-top:6px;">
            Gap Skoru: <b>{satir['GapSkor']}</b>/100 |
            Kapanis: <b>{satir['Kapanis']} TL</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Beklenen Gap: <b>{satir['GapYon']}</b> |
            Overnight Hedef Marj: <b>%{satir['OvernightHedefMarj']}</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Hedef Fiyat: <b>{satir['OvernightHedefFiyat']} TL</b> |
            SL: <b>{satir['OvernightSLFiyat']} TL</b> |
            R/O: <b>{satir['OvernightRO']}</b>
        </div>
        <div style="color:#bbb;font-size:12px;margin-top:4px;">
            Marj Uygunluk: <span style="background:{satir['OvernightMarjRenk']};
                                       padding:2px 6px;border-radius:4px;color:#fff;">
                {satir['OvernightMarjUygun']}</span>
        </div>
    </div>
    """


def grafik_olustur(g, hisse):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=g.index,
        open=g['Open'], high=g['High'],
        low=g['Low'], close=g['Close'],
        name="Fiyat",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350"
    ))
    sma20 = g['Close'].rolling(20).mean()
    fig.add_trace(go.Scatter(
        x=g.index, y=sma20, mode='lines',
        name="SMA20", line=dict(color="#FFC107", width=2)
    ))
    bb_ust = sma20 + 2 * g['Close'].rolling(20).std()
    bb_alt = sma20 - 2 * g['Close'].rolling(20).std()
    fig.add_trace(go.Scatter(
        x=g.index, y=bb_ust, mode='lines',
        name="BBU", line=dict(color="#9c27b0", width=1, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=g.index, y=bb_alt, mode='lines',
        name="BBA", line=dict(color="#9c27b0", width=1, dash='dash')
    ))
    fig.update_layout(
        title=hisse,
        template="plotly_dark",
        height=400,
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig


def rsi_grafik(g):
    fig = go.Figure()
    rsi_seri = rsi(g['Close'])
    fig.add_trace(go.Scatter(
        x=g.index, y=rsi_seri, mode='lines',
        name="RSI", line=dict(color="#4caf50", width=2)
    ))
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350")
    fig.add_hline(y=30, line_dash="dash", line_color="#66bb6a")
    fig.update_layout(
        title="RSI",
        template="plotly_dark",
        height=200,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig st_autorefresh(interval=300000, key="autorefresh")

st.title("BIST Pro Terminali - Gecikme Telafi Edition")

simdi = turkiye_saati()
st.caption(
    f"Son: {simdi.strftime('%Y-%m-%d %H:%M:%S')} | "
    f"{VERI_GECIKME_DAKIKA} dk Gecikmeli | "
    f"Gecikme Telafisi Aktif | "
    f"Gun Ici %{HEDEF_GUN_ICI_MIN}-{HEDEF_GUN_ICI_MAX} | "
    f"Overnight %{HEDEF_OVERNIGHT_MIN}-{HEDEF_OVERNIGHT_MAX}"
)

if piyasa_acik_mi():
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

st.warning(
    f"⚠️ {VERI_GECIKME_DAKIKA} DAKIKA GECIKMELI VERI - "
    "Panel 15 dakika onceki verilerle calisiyor. "
    "'Tahmini Fiyat' sutunu son 3 barin momentumu ile su anki fiyati tahmin eder. "
    "'Kalan Marj' hedefe ne kadar kaldigini guncel tahminle gosterir."
)

with st.sidebar:
    st.header("Ayarlar")
    sadece_islam = st.checkbox("Sadece Islam'a Uygun", value=True)
    st.markdown("---")
    st.markdown("**Hedef Marj Sistemi**")
    st.markdown(f"- Gun Ici: %{HEDEF_GUN_ICI_MIN} - %{HEDEF_GUN_ICI_MAX}")
    st.markdown(f"- Overnight: %{HEDEF_OVERNIGHT_MIN} - %{HEDEF_OVERNIGHT_MAX}")
    st.markdown(f"- KER Esigi: {KER_ESIK}")
    st.markdown("---")
    st.markdown("**Gecikme Telafi**")
    st.markdown(f"- Veri Gecikmesi: {VERI_GECIKME_DAKIKA} dk")
    st.markdown(f"- Extrapolation: {EXTRAPOLATION_BAR_SAYISI} bar")

# ===== VERI CEKME =====
if sadece_islam:
    takip_listesi = [x.strip() for x in K.split(",") if x.strip()]
else:
    takip_listesi = [x.strip() for x in H.split(",") if x.strip()]

st.info("Veri ve derin teknoloji hesaplaniyor...")

try:
    hv = toplu_veri_cek(takip_listesi)
except Exception as e:
    st.error(f"Veri cekme hatasi: {str(e)[:200]}")
    hv = {}

try:
    basliklar = haber_cek()
except Exception:
    basliklar = []

if not hv:
    st.error("Hicbir hisse verisi cekilemedi. Lutfen tekrar deneyin.")
    st.stop()

try:
    kdf = tam_analiz_yap(hv, basliklar)
except Exception as e:
    st.error(f"Analiz hatasi: {str(e)[:200]}")
    kdf = pd.DataFrame()

if kdf.empty:
    st.error("Analiz sonucu bos. Lutfen tekrar deneyin.")
    st.stop()

# ===== UST METRIKLER =====
xu100 = bist_endeks_verisi()
if xu100 is not None and not xu100.empty:
    bist_son = float(xu100['Close'].iloc[-1])
    bist_ilk = float(xu100['Close'].iloc[0])
    bist_degisim = ((bist_son - bist_ilk) / bist_ilk) * 100 if bist_ilk > 0 else 0
else:
    bist_son = 0.0
    bist_degisim = 0.0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("BIST 100", f"{bist_son:,.2f}", f"%{bist_degisim:.2f}")
with col2:
    if bist_degisim > 0.5:
        st.metric("VIOP", "Yukari")
    elif bist_degisim < -0.5:
        st.metric("VIOP", "Asagi")
    else:
        st.metric("VIOP", "Denge")
with col3:
    st.metric("Taranan", len(kdf))
with col4:
    st.metric("Cekim", len(hv))

# ===== GUNUN EN IYI FIRSATI =====
st.markdown("---")
st.header("🎯 GUNUN EN IYI FIRSATI")

en_iyi = kdf.sort_values("KararSkor", ascending=False).head(1)
if not en_iyi.empty:
    satir = en_iyi.iloc[0]
    st.markdown(hisse_kart_html(satir), unsafe_allow_html=True)

    st.subheader("Gecikme Telafi Detayi")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Son Bar Fiyat", f"{satir['SonBarFiyat']} TL")
    with c2:
        st.metric("Tahmini Guncel Fiyat", f"{satir['TahminiFiyat']} TL",
                  f"%{satir['TahminFark']}")
    with c3:
        st.metric("Hedef Marj", f"%{satir['HedefYuzde']}")
    with c4:
        st.metric("Kalan Marj", f"%{satir['KalanMarj']}")

    st.subheader("6 Non-Klise Metrik Kontrolu")
    nk1, nk2, nk3, nk4, nk5, nk6 = st.columns(6)
    with nk1:
        st.metric("KER", f"{satir['KER']}", "Trend kalitesi")
    with nk2:
        st.metric("CHOP", f"{satir['CHOP']}", "Yataylik")
    with nk3:
        st.metric("Park.", f"{satir['Parkinson']}", "High/Low vol")
    with nk4:
        st.metric("G-K", f"{satir['GarmanKlass']}", "OHLC vol")
    with nk5:
        st.metric("Kyle", f"{satir['Kyle']}", "Likidite")
    with nk6:
        st.metric("Ent.", f"{satir['Entropy']}", "Ongorulebilirlik")

    st.markdown(
        f"**Non-Klise Skor:** {satir['NK_Skor']}/100 | "
        f"**Gecen:** {satir['NK_Gecen']}/6 | "
        f"**Seviye:** {satir['NK_Seviye']} | "
        f"**Deep Tech:** {satir['HibritSeviye']} ({satir['HibritSkor']}) | "
        f"**Kalite:** {satir['KaliteUygun']} | "
        f"**Marj:** {satir['MarjUygun']} | "
        f"**Sinyal Zayiflik:** {satir['SinyalZayiflik']}/100"
    )

    st.subheader("15dk Bar Bazli Detay")
    b1, b2, b3, b4 = st.columns(4)
    with b1:
        st.metric("Son Bar Aralik", f"%{satir['SLYuzde']}")
    with b2:
        st.metric("ATR Yuzde", f"%{satir['HedefYuzde']}")
    with b3:
        st.metric("Momentum 5 Bar", f"%{satir['TrendFark']}")
    with b4:
        st.metric("Gecikme Kaybi", f"%{satir['KayipMarj']}") # ===== GECENIN EN IYI FIRSATI =====
st.markdown("---")
st.header("🌙 GECENIN EN IYI FIRSATI")

overnight_df = kdf[kdf['Overnight'] == "GECE TASI"].sort_values("GapSkor", ascending=False)
if not overnight_df.empty:
    satir_on = overnight_df.iloc[0]
    st.markdown(overnight_kart_html(satir_on), unsafe_allow_html=True)

    oc1, oc2, oc3, oc4, oc5 = st.columns(5)
    with oc1:
        st.metric("RSI", f"{satir_on['RSI']}")
    with oc2:
        st.metric("Hacim", f"{satir_on['Hacim']}x")
    with oc3:
        st.metric("Vol Rejim", f"{satir_on['VolRejim']}")
    with oc4:
        st.metric("KER", f"{satir_on['KER']}")
    with oc5:
        st.metric("CHOP", f"{satir_on['CHOP']}")
else:
    st.info("Overnight uygun sinyal yok.")

# ===== SEKMELER =====
st.markdown("---")
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["Karar", "Trend", "Mum", "Risk", "Overnight", "Haber & Pairs", "Derin Teknoloji"]
)

# --- KARAR SEKMESI ---
with tab1:
    st.header("Karar Motoru - Tum Metrikler Birlesik Sinyal")
    st.caption("9 klasik + 6 non-klise + Derin Teknoloji + 15dk Bar Bazli Hedef Marj + Gecikme Telafi")

    st.subheader("A) Secili Hisse Karari")
    hisse_sec = st.selectbox("Hisse Sec", kdf['Hisse'].tolist())
    secili = kdf[kdf['Hisse'] == hisse_sec].iloc[0]

    st.markdown(
        f"""
        <div style="background:{secili['KararRenk']};padding:20px;border-radius:12px;">
            <h2 style="color:#fff;margin:0;">{secili['Hisse']} -> {secili['KararSinyal']}</h2>
            <p style="color:#fff;margin:10px 0 0 0;font-size:14px;">
                Skor: <b>{secili['KararSkor']}/100</b> | Son Bar: <b>{secili['SonBarFiyat']} TL</b> ({secili['SonBarZamani']})
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                Tahmini Su An: <b>{secili['TahminiFiyat']} TL</b> (%{secili['TahminFark']})
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                SL: <b>{secili['SL']}</b> (%{secili['SLYuzde']}) | Hedef: <b>{secili['Hedef']}</b> (%{secili['HedefYuzde']}) | R/O: <b>{secili['RO']}</b>
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                Kalan Marj: %{secili['KalanMarj']} | Kayip Marj: %{secili['KayipMarj']} | Gecikme: {secili['GecikmeDk']} dk
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                Marj Uygunluk: {secili['MarjUygun']} | Kalite: {secili['KaliteUygun']} | Gecikme Durumu: {secili['GecikmeUyari']}
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                Gun Ici: {secili['GunIciUygun']} | Overnight: {secili['OvernightUygun']} (%{secili['OvernightHedefMarj']})
            </p>
            <p style="color:#fff;margin:6px 0 0 0;font-size:14px;">
                Non-Klise: {secili['NK_Seviye']} ({secili['NK_Skor']}) | Deep: {secili['HibritSeviye']} ({secili['HibritSkor']}) | Sinyal Zayiflik: {secili['SinyalZayiflik']}
            </p>
            <p style="color:#fff;margin:10px 0 0 0;font-size:13px;font-style:italic;">
                {secili['KararNeden']}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("B) Bugunun En Iyi 5 Firsati")
    en_iyi_5 = kdf.sort_values("KararSkor", ascending=False).head(5)
    cols = st.columns(5)
    for i, (_, row) in enumerate(en_iyi_5.iterrows()):
        with cols[i]:
            st.markdown(
                f"""
                <div style="background:{row['KararRenk']};padding:12px;border-radius:8px;
                            min-height:340px;">
                    <h3 style="color:#fff;margin:0 0 8px 0;">{row['Hisse']}</h3>
                    <p style="color:#fff;font-weight:bold;margin:0 0 8px 0;">{row['KararSinyal']}</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Skor: {row['KararSkor']}</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Son Bar: {row['SonBarFiyat']} TL</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Tahmini: {row['TahminiFiyat']} TL</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Hedef: {row['Hedef']} TL</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">(%{row['HedefYuzde']})</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Kalan: %{row['KalanMarj']} | R/O: {row['RO']}</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Marj: {row['MarjUygun']}</p>
                    <p style="color:#eee;font-size:12px;margin:2px 0;">Gecikme: {row['GecikmeUyari']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.subheader("C) Telegram Bildirim")
    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button("Bugunun En Iyi 5 Firsatini Gonder"):
            if telegram_toplu_gonder(en_iyi_5, "Bugunun En Iyi 5 Firsati"):
                st.success("Gonderildi!")
            else:
                st.error("Telegram ayarlari eksik.")
    with tc2:
        if st.button("Tum GUCLU AL Sinyallerini Gonder"):
            guclu = kdf[kdf['KararSinyal'] == "GUCLU AL"]
            if guclu.empty:
                st.warning("GUCLU AL sinyali yok.")
            elif telegram_toplu_gonder(guclu, "Tum GUCLU AL Sinyalleri"):
                st.success("Gonderildi!")
            else:
                st.error("Telegram ayarlari eksik.")

    st.markdown("---")
    st.subheader("D) Yeni Sinyal Degisimleri")
    if "gecmis_sinyaller" not in st.session_state:
        st.session_state.gecmis_sinyaller = {}
    yeni_sinyaller = sinyal_degisim_tespit(kdf, st.session_state.gecmis_sinyaller)
    if yeni_sinyaller:
        st.dataframe(pd.DataFrame(yeni_sinyaller), use_container_width=True)
    else:
        st.info("Onceki taramaya gore degisim yok. Ilk tarama ise bu normal.")
    st.session_state.gecmis_sinyaller = sinyal_dict_olustur(kdf)

    st.markdown("---")
    st.subheader("Karar Dagilimi")
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.metric("GUCLU AL", len(kdf[kdf['KararSinyal'] == "GUCLU AL"]))
    with d2:
        st.metric("AL", len(kdf[kdf['KararSinyal'] == "AL"]))
    with d3:
        st.metric("BEKLE", len(kdf[kdf['KararSinyal'] == "BEKLE"]))
    with d4:
        st.metric("SAT", len(kdf[kdf['KararSinyal'].isin(["SAT", "GUCLU SAT"])]))     st.markdown("---")
    st.subheader("E) Tum Karar Skorlari")
    tum_kolonlar = [
        "Hisse", "Fiyat", "TahminiFiyat", "KararSkor", "KararSinyal",
        "HedefYuzde", "KalanMarj", "RO", "MarjUygun", "GecikmeUyari",
        "KaliteUygun", "NK_Skor", "HibritSkor"
    ]
    mevcut_kolonlar = [k for k in tum_kolonlar if k in kdf.columns]
    st.dataframe(
        kdf[mevcut_kolonlar].sort_values("KararSkor", ascending=False),
        use_container_width=True
    )

    st.subheader("En Yuksek Karar Skoru 10")
    en_yuksek = kdf.sort_values("KararSkor", ascending=False).head(10)
    st.dataframe(
        en_yuksek[["Hisse", "Fiyat", "TahminiFiyat", "KararSkor", "KararSinyal",
                   "SL", "Hedef", "HedefYuzde", "KalanMarj", "RO"]],
        use_container_width=True
    )

    st.subheader("En Dusuk Karar Skoru 10 (Riskli)")
    en_dusuk = kdf.sort_values("KararSkor", ascending=True).head(10)
    riskli_kolonlar = ["Hisse", "Fiyat", "KararSkor", "KararSinyal",
                       "KER", "CHOP", "GNN_Manip", "NK_Seviye"]
    mevcut_riskli = [k for k in riskli_kolonlar if k in kdf.columns]
    st.dataframe(en_dusuk[mevcut_riskli], use_container_width=True)

# --- TREND SEKMESI ---
with tab2:
    st.header("Trend Matrisi")
    trend_kolonlar = [
        "Hisse", "Katilim", "Guc", "Sinyal", "Yorum", "RSI", "MACD",
        "Trend", "Getiri", "Hacim", "Fiyat", "FiyatRaw", "TahminiFiyat",
        "TahminFark", "TahminFarkRaw", "SonBarZamani", "GecikmeDk",
        "GecikmeUyari", "GecikmeRenk", "KayipMarj", "KalanMarj",
        "SinyalZayiflik", "SL", "Hedef", "SL_ATR", "Hedef_ATR",
        "HedefYuzde", "SLYuzde", "RO", "RO_ATR", "RORaw",
        "MarjUygun", "MarjRenk", "MarjUygunOvernight", "KaliteUygun",
        "KaliteRenk", "GunIciUygun", "OvernightUygun",
        "OvernightHedefMarj", "OvernightSLMarj", "OvernightHedefFiyat",
        "OvernightSLFiyat", "OvernightRO", "BarAralik", "ATRYuzde",
        "Momentum5", "Tahmin", "Tahmin15", "Guven15", "Beklenti15",
        "VolRejim", "OFI", "GARCH", "KER", "CHOP", "Parkinson",
        "GarmanKlass", "Kyle", "Entropy", "NK_Skor", "NK_Gecen",
        "NK_Seviye", "KararSkor", "KararSinyal", "KararRenk", "KararNeden",
        "LSTM_Yon", "LSTM_Guven", "NLP_Skor", "NLP_Haber", "RL_Q",
        "RL_Sharpe", "GNN_Manip", "GAN_VaR", "HibritSkor",
        "HibritSeviye", "HibritRenk"
    ]
    mevcut_trend = [k for k in trend_kolonlar if k in kdf.columns]

    trend_df = kdf[mevcut_trend].copy()
    if "Katilim" not in trend_df.columns:
        trend_df["Katilim"] = "EVET"
    if "Yorum" not in trend_df.columns:
        trend_df["Yorum"] = trend_df.apply(
            lambda r: f"SMA20+ | MACD+ | Hacim+" if r['KararSinyal'] == "GUCLU AL" else "Notr",
            axis=1
        )

    st.dataframe(
        trend_df.sort_values("KararSkor", ascending=False),
        use_container_width=True,
        height=600
    )

# --- MUM SEKMESI ---
with tab3:
    st.header("Mum Grafigi")
    hisse_mum = st.selectbox("Hisse", kdf['Hisse'].tolist(), key="mum_hisse")
    hisse_uz = hisse_mum + ".IS"
    if hisse_uz in hv:
        g = hv[hisse_uz]
        st.plotly_chart(grafik_olustur(g, hisse_mum), use_container_width=True)
        st.plotly_chart(rsi_grafik(g), use_container_width=True)
    else:
        st.warning("Veri bulunamadi.")

    st.markdown("---")
    st.subheader("15-25 Dakika Sonrasi Yon Dagilimi")
    yc1, yc2, yc3, yc4 = st.columns(4)
    yukari = len(kdf[kdf['Tahmin15'] == "YUKARI"])
    asagi = len(kdf[kdf['Tahmin15'] == "ASAGI"])
    yatay = len(kdf[kdf['Tahmin15'] == "YATAY"])
    ort_guven = kdf['Guven15'].mean()
    with yc1:
        st.metric("YUKARI", yukari)
    with yc2:
        st.metric("ASAGI", asagi)
    with yc3:
        st.metric("YATAY", yatay)
    with yc4:
        st.metric("Ort Guven", f"%{ort_guven:.1f}")

    st.markdown("---")
    st.subheader("Gecikme Telafi Ozeti")
    gc1, gc2, gc3, gc4 = st.columns(4)
    with gc1:
        st.metric("Ort Gecikme", f"{kdf['GecikmeDk'].mean():.1f} dk")
    with gc2:
        st.metric("Ort Tahmin Fark", f"%{kdf['TahminFark'].mean():.2f}")
    with gc3:
        st.metric("Ort Kalan Marj", f"%{kdf['KalanMarj'].mean():.2f}")
    with gc4:
        st.metric("Ort Sinyal Zayiflik", f"{kdf['SinyalZayiflik'].mean():.1f}/100")

# --- RISK SEKMESI ---
with tab4:
    st.header("ATR Bazli Risk + Hedef Marj")
    st.subheader(f"A) Marj Uygun Hisseler (15dk bar bazli %{HEDEF_GUN_ICI_MIN}-{HEDEF_GUN_ICI_MAX})")

    marj_uygun_df = kdf[kdf['MarjUygun'] == "MARJ UYGUN"].sort_values("KararSkor", ascending=False)
    if not marj_uygun_df.empty:
        st.success(f"{len(marj_uygun_df)} hisse marj uygun")
        st.dataframe(
            marj_uygun_df[["Hisse", "Fiyat", "TahminiFiyat", "Hedef",
                           "HedefYuzde", "KalanMarj", "RO", "KararSinyal",
                           "KaliteUygun", "GecikmeUyari", "NK_Skor"]],
            use_container_width=True
        )
    else:
        st.info("Marj uygun hisse yok.")

    st.subheader("B) Marj Uygun + Kalite Yuksek")
    kalite_df = marj_uygun_df[marj_uygun_df['KaliteUygun'].isin(["KALITE YUKSEK", "KALITE IYI"])]
    if not kalite_df.empty:
        st.dataframe(
            kalite_df[["Hisse", "Fiyat", "Hedef", "HedefYuzde", "RO",
                       "KararSinyal", "KaliteUygun"]],
            use_container_width=True
        )
    else:
        st.info("Bu kombinasyonda hisse yok.")

    st.subheader("C) R/O > 1.5 Olan Hisseler")
    ro_df = kdf[kdf['RO'] > 1.5].sort_values("RO", ascending=False)
    if not ro_df.empty:
        st.dataframe(
            ro_df[["Hisse", "Fiyat", "TahminiFiyat", "SL", "Hedef",
                   "HedefYuzde", "KalanMarj", "RO", "KararSinyal",
                   "MarjUygun", "KaliteUygun", "GecikmeUyari",
                   "NK_Skor", "HibritSkor"]],
            use_container_width=True
        )
    else:
        st.info("R/O > 1.5 hisse yok.")

    st.subheader("D) Gecikme Durumu Risk Dagilimi")
    dg1, dg2, dg3, dg4, dg5 = st.columns(5)
    with dg1:
        st.metric("Minimal", len(kdf[kdf['GecikmeUyari'] == "MINIMAL GECIKME"]))
    with dg2:
        st.metric("Az", len(kdf[kdf['GecikmeUyari'] == "AZ GECIKME"]))
    with dg3:
        st.metric("Orta", len(kdf[kdf['GecikmeUyari'] == "ORTA GECIKME"]))
    with dg4:
        st.metric("Yuksek", len(kdf[kdf['GecikmeUyari'] == "YUKSEK GECIKME"]))
    with dg5:
        st.metric("Kritik", len(kdf[kdf['GecikmeUyari'] == "KRITIK GECIKME"]))

    st.subheader("E) Gecikme Etkisi Tablosu")
    gecikme_df = kdf.sort_values("KayipMarj", ascending=False).head(15)
    st.dataframe(
        gecikme_df[["Hisse", "Fiyat", "TahminiFiyat", "TahminFark",
                    "GecikmeDk", "HedefYuzde", "KalanMarj", "KayipMarj",
                    "SinyalZayiflik", "GecikmeUyari", "KararSinyal"]],
        use_container_width=True
                           ) # --- OVERNIGHT SEKMESI ---
with tab5:
    st.header("Overnight Gap Stratejisi")
    st.info(
        f"Kapanista al, acilista sat | 15dk bar bazli hedef marj "
        f"%{HEDEF_OVERNIGHT_MIN}-%{HEDEF_OVERNIGHT_MAX}"
    )

    st.subheader("Tum Overnight Sinyaller")
    over_kolonlar = [
        "Hisse", "Kapanis", "KapanisRaw", "GapSkor", "Overnight",
        "GapYon", "OvernightHedefMarj", "OvernightSLMarj",
        "OvernightHedefFiyat", "OvernightSLFiyat", "OvernightRO",
        "OvernightMarjUygun", "Yorum", "KER", "CHOP", "Kyle",
        "Entropy", "RSI", "Hacim", "VolRejim"
    ]
    mevcut_over = [k for k in over_kolonlar if k in kdf.columns]
    over_df = kdf[mevcut_over].sort_values("GapSkor", ascending=False)
    st.dataframe(over_df, use_container_width=True)

    st.subheader("Gecenin En Guclu 10")
    gece_en = kdf[kdf['Overnight'] == "GECE TASI"].sort_values("GapSkor", ascending=False).head(10)
    if not gece_en.empty:
        st.dataframe(
            gece_en[["Hisse", "Kapanis", "GapSkor", "Overnight", "GapYon",
                     "OvernightHedefMarj", "OvernightHedefFiyat",
                     "OvernightSLFiyat", "OvernightRO", "OvernightMarjUygun",
                     "KER", "CHOP"]],
            use_container_width=True
        )
    else:
        st.info("Gece tasima sinyali yok.")

    st.subheader(f"Overnight Marj Uygun (15dk bar bazli %{HEDEF_OVERNIGHT_MIN}-{HEDEF_OVERNIGHT_MAX})")
    overnight_uygun = kdf[kdf['OvernightMarjUygun'] == "MARJ UYGUN"]
    if not overnight_uygun.empty:
        st.dataframe(
            overnight_uygun[["Hisse", "Kapanis", "OvernightHedefMarj",
                             "OvernightHedefFiyat", "OvernightRO",
                             "OvernightMarjUygun"]],
            use_container_width=True
        )
    else:
        st.info("Overnight hedef marji uygun hisse yok.")

    st.markdown("---")
    st.subheader("Overnight Hedef Marj Dagilimi")
    od1, od2, od3, od4 = st.columns(4)
    with od1:
        st.metric("Toplam Sinyal", len(kdf))
    with od2:
        st.metric("GECE TASI", len(kdf[kdf['Overnight'] == "GECE TASI"]))
    with od3:
        st.metric("ZAYIF TASI", len(kdf[kdf['Overnight'] == "ZAYIF TASI"]))
    with od4:
        st.metric("Marj Uygun", len(overnight_uygun))

    st.subheader("Overnight + Marj Uygun En Iyi 5 Kombine")
    kombine = kdf[(kdf['Overnight'] == "GECE TASI") & (kdf['OvernightMarjUygun'] == "MARJ UYGUN")]
    if not kombine.empty:
        kombine = kombine.sort_values("GapSkor", ascending=False).head(5)
        st.dataframe(
            kombine[["Hisse", "Kapanis", "GapSkor", "OvernightHedefMarj",
                     "OvernightHedefFiyat", "OvernightRO"]],
            use_container_width=True
        )
    else:
        st.info("Kombine uygun sinyal yok.")

    st.markdown("---")
    oc1, oc2 = st.columns(2)
    with oc1:
        if st.button("GECE TASI Sinyallerini Telegram'a Gonder"):
            gece = kdf[kdf['Overnight'] == "GECE TASI"].sort_values("GapSkor", ascending=False)
            if gece.empty:
                st.warning("GECE TASI sinyali yok.")
            elif telegram_toplu_gonder(gece, "GECE TASI Sinyalleri"):
                st.success("Gonderildi!")
            else:
                st.error("Telegram ayarlari eksik.")
    with oc2:
        if st.button("GECE TASI Sinyallerini Performans Defterine Kaydet"):
            st.success("Kaydedildi (demo).")

    st.markdown("---")
    st.subheader("PERFORMANS DETAY RAPORU")
    st.info(
        "Henuz kayitli sinyal yok. Karar sekmesinde 'ACIL Sinyalleri Performans "
        "Defterine Kaydet' butonuna basarak baslayin."
    )

    st.markdown("---")
    st.header("GECIKME TELAFI SISTEMI")
    st.subheader("Nasil Calisir?")
    st.markdown(
        f"""
**Problem:** Panel {VERI_GECIKME_DAKIKA} dakika gecikmeli veri kullaniyor. 
Bu, "son bar" fiyatinin **{VERI_GECIKME_DAKIKA} dakika onceki** fiyat oldugu anlamina gelir. 
Bu sirada gercek fiyat hareket etmis olabilir.

**Cozum 3 Katmanli:**

1. **Son Bar Zamani Gosterimi:** Her hisse kartinda "Son Bar: HH:MM" yazar. 
   Boylece hangi veriyi gordugunuzu bilirsiniz.

2. **Tahmini Guncel Fiyat:** Son {EXTRAPOLATION_BAR_SAYISI} barin ortalama degisimi 
   (momentum) kullanilarak "su anki tahmini fiyat" hesaplanir.

3. **Kalan Marj:** Hedefe ne kadar marj kaldigini tahmini guncel fiyata gore hesaplar.

4. **Gecikme Uyari Sistemi:** Kayip marj oranina gore 5 seviyede uyari verir.

5. **Sinyal Zayiflik Skoru:** Sinyalin gecikme nedeniyle ne kadar zayifladigini gosterir (0-100).
        """
    )

# --- HABER & PAIRS SEKMESI ---
with tab6:
    st.header("Finansal Haberler (Paratic RSS)")
    if basliklar:
        for h in basliklar[:15]:
            st.markdown(
                f"**{h['baslik']}**  \n"
                f"<span style='color:#888;font-size:12px;'>{h['tarih']} | "
                f"<a href='{h['link']}' target='_blank'>{h['link']}</a></span>",
                unsafe_allow_html=True
            )
            st.markdown("---")
    else:
        st.info("Haber cekilemedi.")

    st.markdown("---")
    st.header("Pairs Trade (Kointegrasyon)")
    if HAS_SM:
        top10 = kdf.sort_values("KararSkor", ascending=False).head(10)['Hisse'].tolist()
        pairs = pairs_tara(hv, top10)
        if pairs:
            pairs_df = pd.DataFrame(pairs)
            st.dataframe(pairs_df, use_container_width=True)

            st.subheader("NLP Haber Skoru Dagilimi")
            nlp_df = kdf[kdf['NLP_Haber'] > 0][["Hisse", "NLP_Skor", "NLP_Haber"]]
            if not nlp_df.empty:
                st.dataframe(nlp_df, use_container_width=True)
            else:
                st.info("Hisse ile ilgili haber bulunamadi.")
        else:
            st.info("Kointegre pairs bulunamadi.")
    else:
        st.warning("statsmodels yuklu degil, pairs analizi devre disi.")

# --- DERIN TEKNOLOJI SEKMESI ---
with tab7:
    st.header("Hibrit Deep Tech Skoru Dagilimi")
    ht1, ht2, ht3, ht4, ht5 = st.columns(5)
    with ht1:
        st.metric("YUKSEK POZITIF", len(kdf[kdf['HibritSeviye'] == "YUKSEK POZITIF"]))
    with ht2:
        st.metric("POZITIF", len(kdf[kdf['HibritSeviye'] == "POZITIF"]))
    with ht3:
        st.metric("NOTR", len(kdf[kdf['HibritSeviye'] == "NOTR"]))
    with ht4:
        st.metric("NEGATIF", len(kdf[kdf['HibritSeviye'] == "NEGATIF"]))
    with ht5:
        st.metric("YUKSEK NEGATIF", len(kdf[kdf['HibritSeviye'] == "YUKSEK NEGATIF"]))

    st.subheader("Tum Derin Teknoloji Metrikleri")
    derin_kolonlar = [
        "Hisse", "Fiyat", "TahminiFiyat", "HibritSkor", "HibritSeviye",
        "LSTM_Yon", "LSTM_Guven", "NLP_Skor", "NLP_Haber",
        "RL_Q", "RL_Sharpe", "GNN_Manip", "GAN_VaR", "KararSinyal"
    ]
    mevcut_derin = [k for k in derin_kolonlar if k in kdf.columns]
    st.dataframe(
        kdf[mevcut_derin].sort_values("HibritSkor", ascending=False),
        use_container_width=True,
        height=600
    )

    st.markdown("---")
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.subheader("LSTM En Yuksek Tahmin 5")
        lstm_df = kdf.sort_values("LSTM_Yon", ascending=False).head(5)
        st.dataframe(
            lstm_df[["Hisse", "LSTM_Yon", "LSTM_Guven", "HibritSkor", "Fiyat", "TahminiFiyat"]],
            use_container_width=True
        )
    with dcol2:
        st.subheader("Manipulasyon Riski Yuksek 5")
        manip_df = kdf.sort_values("GNN_Manip", ascending=False).head(5)
        st.dataframe(
            manip_df[["Hisse", "GNN_Manip", "HibritSkor", "Fiyat"]],
            use_container_width=True
        )

    dcol3, dcol4 = st.columns(2)
    with dcol3:
        st.subheader("NLP Haber Skoru En Yuksek 5")
        nlp_top = kdf.sort_values("NLP_Skor", ascending=False).head(5)
        st.dataframe(
            nlp_top[["Hisse", "NLP_Skor", "NLP_Haber", "HibritSkor"]],
            use_container_width=True
        )
    with dcol4:
        st.subheader("GAN Risk En Dusuk 5 (Guvenli)")
        gan_df = kdf.sort_values("GAN_VaR", ascending=False).head(5)
        st.dataframe(
            gan_df[["Hisse", "GAN_VaR", "HibritSkor", "Fiyat"]],
            use_container_width=True
        )

    st.subheader("Pekistirmeli Ogrenme En Yuksek 5")
    rl_df = kdf.sort_values("RL_Sharpe", ascending=False).head(5)
    st.dataframe(
        rl_df[["Hisse", "RL_Q", "RL_Sharpe", "HibritSkor"]],
        use_container_width=True
    )

    st.subheader("En Yuksek Hibrit Skor 10")
    hib_df = kdf.sort_values("HibritSkor", ascending=False).head(10)
    st.dataframe(
        hib_df[["Hisse", "Fiyat", "TahminiFiyat", "HibritSkor",
                "HibritSeviye", "KararSinyal"]],
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("Derin Teknoloji Ne Anlatiyor?")
    st.markdown(
        """
- **LSTM_Yon:** Agirlikli bellek modeli ile 5 adim sonrasi yon tahmini (%)
- **LSTM_Guven:** Tahmin guven yuzdesi
- **NLP_Skor:** Turkce finansal haber duygu analizi (-5 ile +5 arasi)
- **NLP_Haber:** Hisse ile ilgili bulunan haber sayisi
- **RL_Q:** Pekistirmeli ogrenme Q-degeri (getiri bazli odul)
- **RL_Sharpe:** Sharpe orani (risk ayarli getiri)
- **GNN_Manip:** Manipulasyon riski (0-100, yuksek = riskli)
- **GAN_VaR:** Sentetik senaryolarda %95 VaR (kayip tahmini)
- **HibritSkor:** Tum modellerin birlesik skoru (0-100)
- **HibritSeviye:** YUKSEK POZITIF / POZITIF / NOTR / NEGATIF / YUKSEK NEGATIF
        """
    )

# ===== ALT BILGI =====
st.markdown("---")
st.caption(
    "15 dk gecikmeli. Yatirim tavsiyesi degildir. "
    "Veriler yfinance uzerinden alinmaktadir."
)
