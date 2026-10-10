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

K = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"


def turkiye_saati():
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
            hv = yf.download(grup_uz, period="5d", interval="15m", group_by='ticker', threads=True, progress=False, auto_adjust=True, timeout=30)
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
        r = requests.post("https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage", json={"chat_id": TELEGRAM_CHAT, "text": mesaj, "parse_mode": "HTML"}, timeout=10)
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
        r = requests.post("https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage", json={"chat_id": TELEGRAM_CHAT, "text": mesaj, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def pairs_tara(hv, top_list):
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
                sonuc.append({"Hisse1": top_list[i], "Hisse2": top_list[j], "p-value": r["pvalue"], "Z-Skor": r["z"], "Beta": r["beta"], "Aksiyon": sin})
    return sonuc


def sinyal_degisim_tespit(kdf, gecmis_dict):
    yeni = []
    for _, r in kdf.iterrows():
        h = r['Hisse']
        yeni_sin = r['KararSinyal']
        eski_sin = gecmis_dict.get(h, None)
        if eski_sin is not None and eski_sin != yeni_sin:
            yeni.append({"Hisse": h, "Eski": eski_sin, "Yeni": yeni_sin, "Skor": r['KararSkor'], "Fiyat": r['Fiyat']})
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
        return 0.0


def kriter_degerlendir(ker, chop, parkinson, gk, kyle, entropy):
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
NEG_KELIMELER = ["dusus", "azalis", "zarar", "kriz", "iflas", "kayip", "zayif", "negatif", "risk", "borc", "ceza", "sorusturma", "dava", "konkordato", "temerrut", "iptal", "durdurma", "uyari", "not indirimi", "satis baskisi"]


def lstm_tahmin(g):
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
    ret = g['Close'].pct_change().dropna().tail(50).values
    if len(ret) < 10:
        return 0.0
    np.random.seed(42)
    ornek = np.random.choice(ret, size=(100, 10), replace=True)
    yol = np.prod(1 + ornek, axis=1)
    var_95 = np.percentile(yol, 5) - 1
    return round(var_95 * 100, 2)


def hibrit_skor(lstm_y, lstm_g, nlp_s, rl_q, rl_sh, gnn, gan):
    sk = 50
    sk += lstm_y * 5
    if lstm_y > 0:
        sk += (lstm_g - 50) * 0.15
    sk += nlp_s * 8
    sk += min(15, max(-15, rl_q * 0.3))
    sk += min(10, max(-10, rl_sh * 2))
    sk -= gnn * 0.3
    sk += gan * 2 if gan > -3 else 0
    sk = max(0, min(100, sk))
    if sk >= 72:
        seviye = "YUKSEK POZITIF"
    elif sk >= 58:
        seviye = "POZITIF"
    elif sk <= 28:
        seviye = "YUKSEK NEGATIF"
    elif sk <= 42:
        seviye = "NEGATIF"
    else:
        seviye = "NOTR"
    return round(sk, 1), seviye


def derin_teknoloji_hesapla(hs, g, tum_veriler, haber_listesi):
    lstm_y, lstm_g = lstm_tahmin(g)
    nlp_s, nlp_adet = nlp_duygu(haber_listesi, hs)
    rl_q, rl_sh = rl_portfoy_agi(g)
    emsaller = {}
    idx = -1
    anahtar_listesi = list(tum_veriler.keys())
    for i, k in enumerate(anahtar_listesi):
        if k == hs + ".IS":
            idx = i
            break
    if idx >= 0:
        bas = max(0, idx - 3)
        son = min(len(anahtar_listesi), idx + 4)
        for h2 in anahtar_listesi[bas:son]:
            if h2 != hs + ".IS":
                emsaller[h2] = tum_veriler[h2]
    gnn = gnn_manipulasyon(g, emsaller)
    gan = gan_stres_test(g)
    hb_sk, hb_sv = hibrit_skor(lstm_y, lstm_g, nlp_s, rl_q, rl_sh, gnn, gan)
    return {
        "LSTM_Yon": lstm_y,
        "LSTM_Guven": lstm_g,
        "NLP_Skor": nlp_s,
        "NLP_Haber": nlp_adet,
        "RL_Q": rl_q,
        "RL_Sharpe": rl_sh,
        "GNN_Manip": gnn,
        "GAN_VaR": gan,
        "HibritSkor": hb_sk,
        "HibritSeviye": hb_sv
    } 

def son_bar_zamani_hesapla(g):
    """Son 15dk barin zamanini TRT olarak dondurur + kac dakika gecikmeli oldugunu hesaplar."""
    try:
        son_bar_index = g.index[-1]
        if hasattr(son_bar_index, 'tz_localize'):
            try:
                son_bar_trt = son_bar_index.tz_localize('UTC').tz_convert('Europe/Istanbul')
            except Exception:
                try:
                    son_bar_trt = son_bar_index.tz_convert('Europe/Istanbul')
                except Exception:
                    son_bar_trt = son_bar_index
        else:
            son_bar_trt = son_bar_index
        if hasattr(son_bar_trt, 'strftime'):
            bar_str = son_bar_trt.strftime("%H:%M")
        else:
            bar_str = "-"
        try:
            su_an = turkiye_saati()
            if hasattr(son_bar_trt, 'to_pydatetime'):
                son_dt = son_bar_trt.to_pydatetime()
                if son_dt.tzinfo is None:
                    son_dt = son_dt.replace(tzinfo=timezone(timedelta(hours=3)))
                gecikme = (su_an - son_dt).total_seconds() / 60
            else:
                gecikme = VERI_GECIKME_DAKIKA
        except Exception:
            gecikme = VERI_GECIKME_DAKIKA
        return bar_str, round(gecikme, 1)
    except Exception:
        return "-", VERI_GECIKME_DAKIKA


def tahmini_guncel_fiyat(g, son_fiyat):
    """Son N barin momentumunu kullanarak su anki fiyati tahmin eder.
    Gecikmeyi kapatmaya yonelik basit lineer ekstrapolasyon."""
    if len(g) < EXTRAPOLATION_BAR_SAYISI + 1:
        return son_fiyat, 0.0
    try:
        son_barlar = g['Close'].tail(EXTRAPOLATION_BAR_SAYISI + 1).values
        degisimler = np.diff(son_barlar)
        ort_degisim = float(np.mean(degisimler))
        tahmini_fiyat = float(son_fiyat) + ort_degisim
        fark_yuzde = ((tahmini_fiyat - son_fiyat) / son_fiyat) * 100 if son_fiyat > 0 else 0
        return round(tahmini_fiyat, 2), round(fark_yuzde, 2)
    except Exception:
        return son_fiyat, 0.0


def gecikme_kalan_marj(hedef_fiyat, son_fiyat, tahmini_fiyat):
    """Gecikme sonrasi hedefe ne kadar marj kaldigini hesaplar.
    Tahmini guncel fiyat ile hedef arasindaki fark."""
    if tahmini_fiyat <= 0 or hedef_fiyat <= 0:
        return 0.0, 0.0
    kalan_marj = ((hedef_fiyat - tahmini_fiyat) / tahmini_fiyat) * 100
    kayip_marj = ((tahmini_fiyat - son_fiyat) / son_fiyat) * 100 if son_fiyat > 0 else 0
    return round(kalan_marj, 2), round(kayip_marj, 2)


def gecikme_uyari_mesaji(kayip_marj, hedef_marj):
    """Gecikme nedeniyle kayip marj yuksekse uyari dondurur."""
    if hedef_marj <= 0:
        return "NORMAL", "#4CAF50"
    kayip_orani = abs(kayip_marj) / hedef_marj * 100 if hedef_marj > 0 else 0
    if kayip_orani >= 50:
        return "KRITIK GECIKME", "#b71c1c"
    elif kayip_orani >= 30:
        return "YUKSEK GECIKME", "#e65100"
    elif kayip_orani >= 15:
        return "ORTA GECIKME", "#FFC107"
    elif kayip_orani >= 5:
        return "AZ GECIKME", "#66bb6a"
    else:
        return "MINIMAL GECIKME", "#1b5e20"


def sinyal_zayiflik_skoru(kayip_marj, hedef_marj, sinyal):
    """Gecikme nedeniyle sinyalin ne kadar zayifladigini skorlar (0-100).
    Yuksek = sinyal guclu, Dusuk = sinyal zayifladi."""
    if hedef_marj <= 0:
        return 50
    kayip_orani = abs(kayip_marj) / hedef_marj * 100 if hedef_marj > 0 else 0
    skor = 100 - kayip_orani
    skor = max(0, min(100, skor))
    if sinyal == "GUCLU AL" and skor >= 70:
        return int(skor)
    elif sinyal == "AL" and skor >= 60:
        return int(skor)
    return int(skor)


def hedef_marj_15dk_hesapla(g, atr_deger, guc, rsi_d, macd_h, hacim, vol_rej, ker, chop):
    sf = float(g['Close'].iloc[-1])
    son_bar = g.iloc[-1]
    son_bar_yuksek = float(son_bar['High'])
    son_bar_dusuk = float(son_bar['Low'])
    son_bar_aralik = ((son_bar_yuksek - son_bar_dusuk) / sf) * 100 if sf > 0 else 0
    son5 = g.iloc[-5:]
    mom5 = ((float(son5['Close'].iloc[-1]) - float(son5['Close'].iloc[0])) / float(son5['Close'].iloc[0])) * 100 if float(son5['Close'].iloc[0]) > 0 else 0
    atr_yuzde = (atr_deger / sf) * 100 if sf > 0 else 0
    taban_marj = atr_yuzde * BAR_15DK_HEDEF_KATSAYI
    if atr_yuzde < 0.3:
        taban_marj = 1.8
    elif atr_yuzde > 2.0:
        taban_marj = 4.5
    kalite_bonus = 0
    if guc >= 75:
        kalite_bonus += 0.4
    elif guc >= 65:
        kalite_bonus += 0.2
    if ker >= KER_ESIK:
        kalite_bonus += 0.3
    if chop <= 40:
        kalite_bonus += 0.2
    if rsi_d < 40:
        kalite_bonus += 0.2
    elif rsi_d > 70:
        kalite_bonus -= 0.3
    if macd_h > 0:
        kalite_bonus += 0.15
    if hacim > 1.5:
        kalite_bonus += 0.25
    if vol_rej == "YUKSEK":
        kalite_bonus -= 0.3
    elif vol_rej == "DUSUK":
        kalite_bonus += 0.15
    momentum_bonus = mom5 * 0.15
    hedef_marj = taban_marj + kalite_bonus + momentum_bonus
    hedef_marj = max(1.5, min(5.5, hedef_marj))
    sl_marj = -(atr_yuzde * BAR_15DK_SL_KATSAYI + 0.3)
    sl_marj = max(-4.0, min(-0.8, sl_marj))
    hedef_fiyat = round(sf * (1 + hedef_marj / 100), 2)
    sl_fiyat = round(sf * (1 + sl_marj / 100), 2)
    ro = round(abs(hedef_marj) / abs(sl_marj), 2) if abs(sl_marj) > 0 else 0
    return {
        "HedefMarj": round(hedef_marj, 2),
        "SLMarj": round(sl_marj, 2),
        "HedefFiyat": hedef_fiyat,
        "SLFiyat": sl_fiyat,
        "RO_15dk": ro,
        "BarAralik": round(son_bar_aralik, 2),
        "ATRYuzde": round(atr_yuzde, 2),
        "Momentum5": round(mom5, 2)
    }


def overnight_marj_15dk_hesapla(g, atr_deger, guc, ker, chop, kp, hr):
    sf = float(g['Close'].iloc[-1])
    atr_yuzde = (atr_deger / sf) * 100 if sf > 0 else 0
    taban = atr_yuzde * OVERNIGHT_HEDEF_KATSAYI
    if kp > 0.75:
        taban += 0.5
    elif kp < 0.25:
        taban -= 0.5
    if guc >= 75:
        taban += 0.4
    elif guc >= 65:
        taban += 0.2
    if ker >= KER_ESIK:
        taban += 0.3
    if chop <= 40:
        taban += 0.2
    if hr > 1.5:
        taban += 0.3
    hedef_marj = max(2.5, min(6.0, taban))
    sl_marj = -(atr_yuzde * OVERNIGHT_SL_KATSAYI + 0.5)
    sl_marj = max(-4.5, min(-1.0, sl_marj))
    hedef_fiyat = round(sf * (1 + hedef_marj / 100), 2)
    sl_fiyat = round(sf * (1 + sl_marj / 100), 2)
    ro = round(abs(hedef_marj) / abs(sl_marj), 2) if abs(sl_marj) > 0 else 0
    return {
        "OvernightHedefMarj": round(hedef_marj, 2),
        "OvernightSLMarj": round(sl_marj, 2),
        "OvernightHedefFiyat": hedef_fiyat,
        "OvernightSLFiyat": sl_fiyat,
        "OvernightRO": ro
    }


def marj_uygunluk_belirle(hedef_marj, tip="gun_ici"):
    if tip == "gun_ici":
        if HEDEF_GUN_ICI_MIN <= hedef_marj <= HEDEF_GUN_ICI_MAX:
            return "MARJ UYGUN", "#1b5e20"
        elif hedef_marj < HEDEF_GUN_ICI_MIN:
            return "MARJ DUSUK", "#e65100"
        elif hedef_marj > HEDEF_GUN_ICI_MAX:
            return "MARJ YUKSEK", "#FFC107"
        return "MARJ GECERSIZ", "#b71c1c"
    else:
        if HEDEF_OVERNIGHT_MIN <= hedef_marj <= HEDEF_OVERNIGHT_MAX:
            return "OVERNIGHT UYGUN", "#1b5e20"
        elif hedef_marj < HEDEF_OVERNIGHT_MIN:
            return "OVERNIGHT DUSUK", "#e65100"
        elif hedef_marj > HEDEF_OVERNIGHT_MAX:
            return "OVERNIGHT YUKSEK", "#FFC107"
        return "OVERNIGHT GECERSIZ", "#b71c1c"


def kalite_uygunluk_belirle(ro, ker, chop, nk_skor, hibrit, gnn):
    puan = 0
    if ro >= 1.5:
        puan += 2
    elif ro >= 1.3:
        puan += 1
    if ker >= KER_ESIK:
        puan += 1
    if chop <= 45:
        puan += 1
    if nk_skor >= 60:
        puan += 1
    if hibrit >= 55:
        puan += 1
    if gnn <= 50:
        puan += 1
    if puan >= 6:
        return "KALITE YUKSEK", "#1b5e20"
    elif puan >= 4:
        return "KALITE IYI", "#2e7d32"
    elif puan >= 2:
        return "KALITE ORTA", "#e65100"
    else:
        return "KALITE ZAYIF", "#b71c1c"


def hedef_kontrol(kar_yuzde, tip="gun_ici"):
    if tip == "gun_ici":
        if kar_yuzde >= HEDEF_GUN_ICI_MAX:
            return "HEDEF ASILDI", "#1b5e20"
        elif kar_yuzde >= HEDEF_GUN_ICI_MIN:
            return "HEDEF ARALIGINDA", "#2e7d32"
        elif kar_yuzde > 0:
            return "KUCUK KAR", "#66bb6a"
        elif kar_yuzde == 0:
            return "BASABAS", "#e65100"
        else:
            return "ZARARDA", "#b71c1c"
    else:
        if kar_yuzde >= HEDEF_OVERNIGHT_MAX:
            return "HEDEF ASILDI", "#1b5e20"
        elif kar_yuzde >= HEDEF_OVERNIGHT_MIN:
            return "HEDEF ARALIGINDA", "#2e7d32"
        elif kar_yuzde > 0:
            return "KUCUK KAR", "#66bb6a"
        elif kar_yuzde == 0:
            return "BASABAS", "#e65100"
        else:
            return "ZARARDA", "#b71c1c"


def sinyal_anlik_kaydet(kdf, tip="gun_ici"):
    kayit = []
    zaman = turkiye_saati().strftime("%Y-%m-%d %H:%M:%S")
    for _, r in kdf.iterrows():
        if r['KararSinyal'] in ["GUCLU AL", "AL"]:
            kayit.append({
                "zaman": zaman,
                "Hisse": r['Hisse'],
                "Sinyal": r['KararSinyal'],
                "GirisFiyat": r['FiyatRaw'],
                "Hedef": r['Hedef'],
                "SL": r['SL'],
                "HedefMarj": r.get('HedefYuzde', 0),
                "RO": r['RORaw'],
                "KararSkor": r['KararSkor'],
                "NK_Skor": r['NK_Skor'],
                "HibritSkor": r['HibritSkor'],
                "Tip": tip,
                "Durum": "ACIK",
                "CikisFiyat": 0.0,
                "KarYuzde": 0.0,
                "TutmaSaat": 0.0
            })
    return kayit


def performans_guncelle(gecmis_kayitlar, guncel_veriler):
    if not gecmis_kayitlar:
        return gecmis_kayitlar
    guncel_zaman = turkiye_saati()
    for k in gecmis_kayitlar:
        if k.get("Durum") == "ACIK":
            hisse = k["Hisse"]
            if hisse in guncel_veriler:
                try:
                    son_fiyat = float(guncel_veriler[hisse]['Close'].iloc[-1])
                    giris = float(k["GirisFiyat"])
                    if giris > 0:
                        kar_y = ((son_fiyat - giris) / giris) * 100
                        k["KarYuzde"] = round(kar_y, 2)
                        try:
                            sl_f = float(str(k["SL"]).replace(" TL", "").strip())
                            hd_f = float(str(k["Hedef"]).replace(" TL", "").strip())
                        except Exception:
                            sl_f = giris * 0.97
                            hd_f = giris * 1.03
                        if son_fiyat >= hd_f:
                            k["Durum"] = "HEDEF"
                            k["CikisFiyat"] = son_fiyat
                        elif son_fiyat <= sl_f:
                            k["Durum"] = "STOP"
                            k["CikisFiyat"] = son_fiyat
                        try:
                            zaman_giris = datetime.strptime(k["zaman"], "%Y-%m-%d %H:%M:%S")
                            zaman_giris = zaman_giris.replace(tzinfo=timezone(timedelta(hours=3)))
                            fark = (guncel_zaman - zaman_giris).total_seconds() / 3600
                            k["TutmaSaat"] = round(fark, 2)
                        except Exception:
                            k["TutmaSaat"] = 0
                except Exception:
                    continue
    return gecmis_kayitlar


def performans_hesapla(gecmis_kayitlar):
    if not gecmis_kayitlar:
        return {
            "toplam": 0, "kapali": 0, "acik": 0, "kazanan": 0, "kaybeden": 0,
            "basari_orani": 0.0, "ort_kar": 0.0, "ort_zarar": 0.0,
            "toplam_kar": 0.0, "beklenen_getiri": 0.0, "ort_tutma": 0.0,
            "hedef_asilan": 0, "stop_olan": 0, "en_iyi": 0.0, "en_kotu": 0.0
        }
    kapali = [k for k in gecmis_kayitlar if k.get("Durum") in ["HEDEF", "STOP"]]
    acik = [k for k in gecmis_kayitlar if k.get("Durum") == "ACIK"]
    kazanan = [k for k in kapali if k.get("KarYuzde", 0) > 0]
    kaybeden = [k for k in kapali if k.get("KarYuzde", 0) < 0]
    hedef_asilan = [k for k in kapali if k.get("Durum") == "HEDEF"]
    stop_olan = [k for k in kapali if k.get("Durum") == "STOP"]
    basari = (len(kazanan) / len(kapali) * 100) if kapali else 0.0
    kar_listesi = [k.get("KarYuzde", 0) for k in kapali if k.get("KarYuzde", 0) > 0]
    zarar_listesi = [k.get("KarYuzde", 0) for k in kapali if k.get("KarYuzde", 0) < 0]
    ort_kar = np.mean(kar_listesi) if kar_listesi else 0.0
    ort_zarar = np.mean(zarar_listesi) if zarar_listesi else 0.0
    toplam_kar = sum([k.get("KarYuzde", 0) for k in kapali])
    tutma_listesi = [k.get("TutmaSaat", 0) for k in kapali]
    ort_tutma = np.mean(tutma_listesi) if tutma_listesi else 0.0
    en_iyi = max([k.get("KarYuzde", 0) for k in kapali]) if kapali else 0.0
    en_kotu = min([k.get("KarYuzde", 0) for k in kapali]) if kapali else 0.0
    return {
        "toplam": len(gecmis_kayitlar),
        "kapali": len(kapali),
        "acik": len(acik),
        "kazanan": len(kazanan),
        "kaybeden": len(kaybeden),
        "basari_orani": round(basari, 1),
        "ort_kar": round(ort_kar, 2),
        "ort_zarar": round(ort_zarar, 2),
        "toplam_kar": round(toplam_kar, 2),
        "beklenen_getiri": round((basari / 100) * ort_kar + (1 - basari / 100) * ort_zarar, 2) if kapali else 0.0,
        "ort_tutma": round(ort_tutma, 2),
        "hedef_asilan": len(hedef_asilan),
        "stop_olan": len(stop_olan),
        "en_iyi": round(en_iyi, 2),
        "en_kotu": round(en_kotu, 2)
            } 

def hesapla(hs, v, kset, tum_veriler, haber_listesi):
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
        sn = "GUCLU AL"
        tp = "YUKSELIS BEKLENIYOR"
    elif sk >= 55:
        sn = "AL"
        tp = "YUKSELIS EGILIMI"
    elif sk < 35:
        sn = "SAT"
        tp = "DUSUS BEKLENIYOR"
    elif sk < 45:
        sn = "ZAYIF"
        tp = "ZAYIF"
    else:
        sn = "BEKLE"
        tp = "BEKLE"
    hz = hs + ".IS"
    y15, g15, b15 = tahmin_15(g)
    v5 = float((g['High'] - g['Low']).iloc[-5:].mean())
    v20 = float((g['High'] - g['Low']).iloc[-20:].mean())
    vrej = "YUKSEK" if v5 > v20 * 1.3 else ("DUSUK" if v5 < v20 * 0.7 else "NORMAL")
    obv_s = (np.sign(g['Close'].diff()) * g['Volume']).fillna(0).cumsum()
    ofi = float(obv_s.iloc[-1] - obv_s.iloc[-5]) / 1e6 if len(obv_s) >= 5 else 0
    gv_ = garch_vol(g['Close'])
    trend_str = "Yuk" if gd > 0 else "Dus"
    ker = kaufman_efficiency_ratio(g['Close'])
    chop = choppiness_index(g['High'], g['Low'], g['Close'])
    parkinson = parkinson_volatility(g['High'], g['Low'])
    gk = garman_klass_volatility(g['Open'], g['High'], g['Low'], g['Close'])
    kyle = kyle_lambda(g['Close'], g['Volume'])
    entropy = shannon_entropy(g['Close'])
    nk_skor = non_klise_skor(ker, chop, parkinson, gk, kyle, entropy)
    nk_kriterler, nk_gecen, nk_seviye = kriter_degerlendir(ker, chop, parkinson, gk, kyle, entropy)
    dt = derin_teknoloji_hesapla(hs, g, tum_veriler, haber_listesi)
    km_skor, km_sinyal, km_renk, km_neden = karar_motoru(sk, r, mh, hr, vrej, ofi, gv_, y15, g15, trend_str, ker, chop, kyle, entropy, nk_skor)
    ht_skor = dt["HibritSkor"]
    if ht_skor >= 72:
        dt_renk = "#1b5e20"
    elif ht_skor >= 58:
        dt_renk = "#2e7d32"
    elif ht_skor <= 28:
        dt_renk = "#b71c1c"
    elif ht_skor <= 42:
        dt_renk = "#c62828"
    else:
        dt_renk = "#e65100"
    s25 = g.iloc[-min(25, len(g)):]
    gh_s = float(s25['High'].max())
    gl_s = float(s25['Low'].min())
    kp = (sf - gl_s) / (gh_s - gl_s) if (gh_s - gl_s) > 0 else 0.5
    hedef_15dk = hedef_marj_15dk_hesapla(g, a, sk, r, mh, hr, vrej, ker, chop)
    overnight_15dk = overnight_marj_15dk_hesapla(g, a, sk, ker, chop, kp, hr)
    if a > 0:
        sl_atr = round(sf - a * 2, 2)
        hd_atr = round(sf + a * 3, 2)
        ro_atr = round((hd_atr - sf) / (sf - sl_atr), 2) if (sf - sl_atr) > 0 else 0
    else:
        sl_atr = 0
        hd_atr = 0
        ro_atr = 0
    hedef_fiyat = hedef_15dk["HedefFiyat"]
    sl_fiyat = hedef_15dk["SLFiyat"]
    hedef_marj = hedef_15dk["HedefMarj"]
    sl_marj = hedef_15dk["SLMarj"]
    ro_15dk = hedef_15dk["RO_15dk"]
    bar_zamani, gecikme_dk = son_bar_zamani_hesapla(g)
    tahmini_fiyat, tahmin_fark = tahmini_guncel_fiyat(g, sf)
    kalan_marj, kayip_marj = gecikme_kalan_marj(hedef_fiyat, sf, tahmini_fiyat)
    gecikme_uyari, gecikme_renk = gecikme_uyari_mesaji(kayip_marj, hedef_marj)
    zayiflik = sinyal_zayiflik_skoru(kayip_marj, hedef_marj, km_sinyal)
    marj_uygunluk, marj_renk = marj_uygunluk_belirle(hedef_marj, "gun_ici")
    marj_uygunluk_ov, marj_renk_ov = marj_uygunluk_belirle(overnight_15dk["OvernightHedefMarj"], "overnight")
    kalite_uygunluk, kalite_renk = kalite_uygunluk_belirle(ro_15dk, ker, chop, nk_skor, ht_skor, dt["GNN_Manip"])
    gun_ici_uygun = "EVET" if marj_uygunluk == "MARJ UYGUN" else "HAYIR"
    overnight_uygun = "EVET" if marj_uygunluk_ov == "OVERNIGHT UYGUN" else "HAYIR"
    ana = {
        "Hisse": hs,
        "Katilim": "EVET" if hz in kset else "HAYIR",
        "Guc": round(sk, 1),
        "Sinyal": sn,
        "Yorum": " | ".join(yr) if yr else "Notr",
        "RSI": f"{r:.1f}",
        "MACD": f"{mh:.3f}",
        "Trend": trend_str,
        "Getiri": f"%{gd:.2f}",
        "Hacim": f"{hr:.2f}x",
        "Fiyat": f"{sf:.2f} TL",
        "FiyatRaw": sf,
        "TahminiFiyat": tahmini_fiyat,
        "TahminFark": f"%{tahmin_fark}",
        "TahminFarkRaw": tahmin_fark,
        "SonBarZamani": bar_zamani,
        "GecikmeDk": gecikme_dk,
        "GecikmeUyari": gecikme_uyari,
        "GecikmeRenk": gecikme_renk,
        "KayipMarj": kayip_marj,
        "KalanMarj": kalan_marj,
        "SinyalZayiflik": zayiflik,
        "SL": f"{sl_fiyat} TL",
        "Hedef": f"{hedef_fiyat} TL",
        "SL_ATR": f"{sl_atr} TL",
        "Hedef_ATR": f"{hd_atr} TL",
        "HedefYuzde": hedef_marj,
        "SLYuzde": sl_marj,
        "RO": f"{ro_15dk:.2f}",
        "RO_ATR": f"{ro_atr:.2f}",
        "RORaw": ro_15dk,
        "MarjUygun": marj_uygunluk,
        "MarjRenk": marj_renk,
        "MarjUygunOvernight": marj_uygunluk_ov,
        "KaliteUygun": kalite_uygunluk,
        "KaliteRenk": kalite_renk,
        "GunIciUygun": gun_ici_uygun,
        "OvernightUygun": overnight_uygun,
        "OvernightHedefMarj": overnight_15dk["OvernightHedefMarj"],
        "OvernightSLMarj": overnight_15dk["OvernightSLMarj"],
        "OvernightHedefFiyat": overnight_15dk["OvernightHedefFiyat"],
        "OvernightSLFiyat": overnight_15dk["OvernightSLFiyat"],
        "OvernightRO": overnight_15dk["OvernightRO"],
        "BarAralik": hedef_15dk["BarAralik"],
        "ATRYuzde": hedef_15dk["ATRYuzde"],
        "Momentum5": hedef_15dk["Momentum5"],
        "Tahmin": tp,
        "Tahmin15": y15,
        "Guven15": f"%{g15}",
        "Beklenti15": f"%{b15}",
        "VolRejim": vrej,
        "OFI": round(ofi, 2),
        "GARCH": gv_,
        "KER": ker,
        "CHOP": chop,
        "Parkinson": parkinson,
        "GarmanKlass": gk,
        "Kyle": kyle,
        "Entropy": entropy,
        "NK_Skor": nk_skor,
        "NK_Gecen": nk_gecen,
        "NK_Seviye": nk_seviye,
        "KararSkor": km_skor,
        "KararSinyal": km_sinyal,
        "KararRenk": km_renk,
        "KararNeden": km_neden,
        "LSTM_Yon": dt["LSTM_Yon"],
        "LSTM_Guven": dt["LSTM_Guven"],
        "NLP_Skor": dt["NLP_Skor"],
        "NLP_Haber": dt["NLP_Haber"],
        "RL_Q": dt["RL_Q"],
        "RL_Sharpe": dt["RL_Sharpe"],
        "GNN_Manip": dt["GNN_Manip"],
        "GAN_VaR": dt["GAN_VaR"],
        "HibritSkor": ht_skor,
        "HibritSeviye": dt["HibritSeviye"],
        "HibritRenk": dt_renk
    }
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
    if ker >= KER_ESIK:
        gs += 5
    elif ker < (KER_ESIK * 0.6):
        gs -= 5
    if chop <= 45:
        gs += 4
    elif chop >= 62:
        gs -= 4
    if kyle <= 0.8:
        gs += 4
    elif kyle > 2.0:
        gs -= 4
    if entropy <= 2.0:
        gs += 3
    elif entropy > 2.7:
        gs -= 3
    gs = max(0, min(100, gs))
    if gs >= 75:
        os = "GECE TASI"
        bg = "YUKARI"
    elif gs >= 60:
        os = "GECE TASI"
        bg = "YUKARI"
    elif gs >= 50:
        os = "ZAYIF TASI"
        bg = "NOTR"
    elif gs < 35:
        os = "GECE TASIMA"
        bg = "ASAGI"
    else:
        os = "BEKLE"
        bg = "NOTR"
    if kp > 0.75:
        yorum_on = "Zirve"
    elif kp < 0.25:
        yorum_on = "Dip"
    else:
        yorum_on = "Notr"
    onc = {
        "Hisse": hs,
        "Kapanis": f"{sf:.2f} TL",
        "KapanisRaw": sf,
        "GapSkor": round(gs, 1),
        "Overnight": os,
        "GapYon": bg,
        "Gap%": f"%{overnight_15dk['OvernightHedefMarj']}",
        "GapPctRaw": overnight_15dk["OvernightHedefMarj"],
        "OvernightHedefMarj": overnight_15dk["OvernightHedefMarj"],
        "OvernightHedefFiyat": overnight_15dk["OvernightHedefFiyat"],
        "OvernightSLMarj": overnight_15dk["OvernightSLMarj"],
        "OvernightSLFiyat": overnight_15dk["OvernightSLFiyat"],
        "OvernightRO": overnight_15dk["OvernightRO"],
        "OvernightMarjUygun": marj_uygunluk_ov,
        "Yorum": yorum_on,
        "KER": ker,
        "CHOP": chop,
        "Kyle": kyle,
        "Entropy": entropy,
        "RSI": f"{r:.1f}",
        "Hacim": f"{hr:.2f}x",
        "VolRejim": vrej
    }
    return ana, onc


def en_iyi_firsat_bul(kdf):
    if kdf.empty:
        return None
    uygun = kdf[(kdf["KararSkor"] >= 60) & (kdf["RORaw"] >= 1.45)].copy()
    if uygun.empty:
        return None
    uygun = uygun.sort_values("KararSkor", ascending=False).reset_index(drop=True)
    en_iyi = uygun.iloc[0]
    puan = 0
    if en_iyi['KararSkor'] >= 75:
        puan += 4
    elif en_iyi['KararSkor'] >= 65:
        puan += 3
    else:
        puan += 2
    if en_iyi['KER'] >= KER_ESIK:
        puan += 2
    if en_iyi['CHOP'] <= 45:
        puan += 2
    if en_iyi['Kyle'] <= 1.5:
        puan += 1
    if en_iyi['Entropy'] <= 2.5:
        puan += 1
    if en_iyi['RORaw'] >= 1.5:
        puan += 2
    if en_iyi['GNN_Manip'] <= 50:
        puan += 1
    if en_iyi['NK_Skor'] >= 60:
        puan += 1
    if en_iyi['MarjUygun'] == "MARJ UYGUN":
        puan += 1
    if en_iyi['SinyalZayiflik'] >= 70:
        puan += 1
    karar = en_iyi["KararSinyal"]
    renk = en_iyi["KararRenk"]
    return {"hisse": en_iyi, "puan": puan, "karar": karar, "renk": renk}


def gecenin_en_iyisi_bul(odf):
    if odf.empty:
        return None
    uygun = odf[odf["Overnight"].isin(["GECE TASI", "ZAYIF TASI"])].copy()
    if uygun.empty:
        return None
    uygun = uygun.sort_values("GapSkor", ascending=False).reset_index(drop=True)
    en_iyi = uygun.iloc[0]
    if en_iyi['GapSkor'] >= 75:
        karar = "GECE TASI GUCLU"
        renk = "#1b5e20"
        aciklama = "Kapanis zirvede, yarin acilis gap pozitif bekleniyor"
    elif en_iyi['GapSkor'] >= 65:
        karar = "GECE TASI"
        renk = "#2e7d32"
        aciklama = "Guclu kapanis, gap beklentisi orta-yuksek"
    elif en_iyi['GapSkor'] >= 55:
        karar = "GECE TASI"
        renk = "#2e7d32"
        aciklama = "Orta-guclu kapanis, gap beklentisi var"
    else:
        karar = "ZAYIF TASI"
        renk = "#e65100"
        aciklama = "Zayif kapanis, gap beklentisi belirsiz"
    return {"hisse": en_iyi, "karar": karar, "renk": renk, "aciklama": aciklama} 

for k, v in [('g', False), ('s', 0), ('l', '-'), ('m', False), ('haber', []), ('gecmis', {}), ('son_gonderim', '-'), ('performans', []), ('son_kayit_zaman', '')]:
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

pk = piyasa_acik_mi()
if pk:
    st_autorefresh(interval=60000, key="y")

st.title("BIST Pro Terminali - Gecikme Telafi Edition")
st.caption("Son: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 dk Gecikmeli | Gecikme Telafisi Aktif | Gun Ici %" + str(HEDEF_GUN_ICI_MIN) + "-" + str(HEDEF_GUN_ICI_MAX) + " | Overnight %" + str(HEDEF_OVERNIGHT_MIN) + "-" + str(HEDEF_OVERNIGHT_MAX))

if pk:
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

st.markdown(
    '<div style="background-color:#3a2800; padding:12px; border-radius:8px; border-left:4px solid #FFC107; color:#FFC107; margin-bottom:15px;">'
    '<b>⚠️ 15 DAKIKA GECIKMELI VERI</b> - Panel 15 dakika onceki verilerle calisiyor. '
    '"Tahmini Fiyat" sutunu son 3 barin momentumu ile su anki fiyati tahmin eder. '
    '"Kalan Marj" hedefe ne kadar kaldigini guncel tahminle gosterir.'
    '</div>', unsafe_allow_html=True)

with st.spinner("Veri ve derin teknoloji hesaplaniyor..."):
    hl = H.split(",")
    ks = set(x + ".IS" for x in K.split(","))
    hv = toplu_veri_cek(hl)
    if not st.session_state.haber:
        st.session_state.haber = haber_cek()
    hb = st.session_state.haber
    sat, onc = [], []
    for x in hl:
        kod = x + ".IS"
        if kod in hv:
            a, o = hesapla(x, hv[kod], ks, hv, hb)
            if a:
                sat.append(a)
            if o:
                onc.append(o)
    if not st.session_state.m:
        st.session_state.s += 1
        st.session_state.l = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.m = False
    st.session_state.performans = performans_guncelle(st.session_state.performans, hv)

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
    st.session_state.haber = []
    st.rerun()

perf = performans_hesapla(st.session_state.performans)
if perf["toplam"] > 0:
    st.markdown("---")
    st.markdown("### 📊 PERFORMANS TAKIP")
    p1, p2, p3, p4, p5, p6 = st.columns(6)
    p1.metric("Toplam Sinyal", str(perf["toplam"]))
    p2.metric("Kapali", str(perf["kapali"]))
    p3.metric("Acik", str(perf["acik"]))
    if perf["basari_orani"] >= 70:
        p4.metric("Basari Orani", f"%{perf['basari_orani']} 🎯")
    elif perf["basari_orani"] >= 60:
        p4.metric("Basari Orani", f"%{perf['basari_orani']} ✅")
    elif perf["basari_orani"] >= 50:
        p4.metric("Basari Orani", f"%{perf['basari_orani']} ⚠️")
    else:
        p4.metric("Basari Orani", f"%{perf['basari_orani']} ❌")
    p5.metric("Hedef Asilan", str(perf["hedef_asilan"]))
    p6.metric("Stop Olan", str(perf["stop_olan"]))
    q1, q2, q3, q4, q5, q6 = st.columns(6)
    q1.metric("Ort. Kar", f"%{perf['ort_kar']}")
    q2.metric("Ort. Zarar", f"%{perf['ort_zarar']}")
    q3.metric("Toplam Kar", f"%{perf['toplam_kar']}")
    q4.metric("Ort. Tutma", f"{perf['ort_tutma']} saat")
    q5.metric("En Iyi", f"%{perf['en_iyi']}")
    q6.metric("En Kotu", f"%{perf['en_kotu']}")
    if perf["kapali"] >= 10:
        if perf["basari_orani"] >= 70:
            st.success("🎯 Basari %70+ | Sistem kanitlanmis, sermaye artirilabilir")
        elif perf["basari_orani"] >= 50:
            st.warning("⚠️ Basari %50-70 | Sistem calisiyor, optimizasyon gerekli")
        else:
            st.error("❌ Basari %50 alti | Parametreleri degistirmelisiniz")
    elif perf["kapali"] >= 5:
        st.info("ℹ️ Ilk degerlendirme icin 5+ kapali islem var. 10'a tamamlayin.")
    else:
        st.info("ℹ️ Degerlendirme icin en az 5 kapali islem gerekli. Su an: " + str(perf["kapali"]))


# ==================== GUNUN EN IYI FIRSATI ====================
if sat:
    kdf_ust = pd.DataFrame(sat)
    if sd:
        kdf_ust = kdf_ust[kdf_ust["Katilim"] == "EVET"]
    en_iyi_sonuc = en_iyi_firsat_bul(kdf_ust)
    if en_iyi_sonuc is not None:
        eh = en_iyi_sonuc["hisse"]
        st.markdown("---")
        st.markdown("## 🎯 GUNUN EN IYI FIRSATI")
        kutu_renk = en_iyi_sonuc["renk"]
        karar_txt = en_iyi_sonuc["karar"]
        puan = en_iyi_sonuc["puan"]
        st.markdown(
            '<div style="background-color:' + kutu_renk + '; padding:25px; border-radius:15px; color:white; margin-bottom:20px;">'
            '<h1 style="margin:0; color:white; font-size:42px;">' + str(eh["Hisse"]) + ' &nbsp;&nbsp; <span style="background:rgba(255,255,255,0.2); padding:8px 20px; border-radius:8px;">' + karar_txt + '</span></h1>'
            '<p style="font-size:22px; margin:15px 0 5px 0;"><b>Karar Skoru:</b> ' + str(eh["KararSkor"]) + '/100 &nbsp; | &nbsp; <b>Son Bar Fiyat:</b> ' + str(eh["Fiyat"]) + ' &nbsp; | &nbsp; <b>Son Bar:</b> ' + str(eh["SonBarZamani"]) + '</p>'
            '<p style="font-size:22px; margin:5px 0;"><b>Tahmini Su An Fiyat:</b> ' + str(eh["TahminiFiyat"]) + ' TL &nbsp; <span style="background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:5px;">' + str(eh["TahminFark"]) + '</span> &nbsp; | &nbsp; <b>Gecikme:</b> ' + str(eh["GecikmeDk"]) + ' dk</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Giris:</b> ' + str(eh["TahminiFiyat"]) + ' TL &nbsp; <b>Stop-Loss:</b> ' + str(eh["SL"]) + ' &nbsp; <b>Hedef:</b> ' + str(eh["Hedef"]) + '</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Hedef Marj:</b> %' + str(eh["HedefYuzde"]) + ' &nbsp; | &nbsp; <b>Kalan Marj:</b> %' + str(eh["KalanMarj"]) + ' &nbsp; | &nbsp; <b>R/O:</b> ' + str(eh["RO"]) + '</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Marj Uygunluk:</b> <span style="background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:5px;">' + str(eh["MarjUygun"]) + '</span> &nbsp; | &nbsp; <b>Kalite:</b> <span style="background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:5px;">' + str(eh["KaliteUygun"]) + '</span> &nbsp; | &nbsp; <b>Gecikme Durumu:</b> <span style="background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:5px;">' + str(eh["GecikmeUyari"]) + '</span></p>'
            '<p style="font-size:18px; margin:10px 0 0 0;">Kriter Skoru: ' + str(puan) + '/15 &nbsp; | &nbsp; Gun Ici Uygun: ' + str(eh["GunIciUygun"]) + ' &nbsp; | &nbsp; Overnight Uygun: ' + str(eh["OvernightUygun"]) + '</p>'
            '<p style="font-size:16px; margin:5px 0 0 0; font-style:italic;">' + str(eh["KararNeden"]) + '</p>'
            '</div>', unsafe_allow_html=True)
        st.markdown("### Gecikme Telafi Detayi")
        gc1, gc2, gc3, gc4 = st.columns(4)
        with gc1:
            st.metric("Son Bar Fiyat", str(eh["Fiyat"]))
        with gc2:
            st.metric("Tahmini Guncel Fiyat", str(eh["TahminiFiyat"]) + " TL", eh["TahminFark"])
        with gc3:
            st.metric("Hedef Marj", f"%{eh['HedefYuzde']}")
        with gc4:
            st.metric("Kalan Marj", f"%{eh['KalanMarj']}")
        st.markdown("### 6 Non-Klise Metrik Kontrolu")
        nk1, nk2, nk3, nk4, nk5, nk6 = st.columns(6)
        with nk1:
            if eh["KER"] >= KER_ESIK:
                st.success("KER: " + str(eh["KER"]) + " OK")
            else:
                st.warning("KER: " + str(eh["KER"]) + " X")
            st.caption("Trend kalitesi")
        with nk2:
            if eh["CHOP"] <= 45:
                st.success("CHOP: " + str(eh["CHOP"]) + " OK")
            else:
                st.warning("CHOP: " + str(eh["CHOP"]) + " X")
            st.caption("Yataylik")
        with nk3:
            if 0.1 <= eh["Parkinson"] <= 3.0:
                st.success("Park: " + str(eh["Parkinson"]) + " OK")
            else:
                st.warning("Park: " + str(eh["Parkinson"]) + " X")
            st.caption("High/Low vol")
        with nk4:
            if 0.1 <= eh["GarmanKlass"] <= 3.5:
                st.success("G-K: " + str(eh["GarmanKlass"]) + " OK")
            else:
                st.warning("G-K: " + str(eh["GarmanKlass"]) + " X")
            st.caption("OHLC vol")
        with nk5:
            if eh["Kyle"] <= 1.5:
                st.success("Kyle: " + str(eh["Kyle"]) + " OK")
            else:
                st.warning("Kyle: " + str(eh["Kyle"]) + " X")
            st.caption("Likidite")
        with nk6:
            if eh["Entropy"] <= 2.5:
                st.success("Ent: " + str(eh["Entropy"]) + " OK")
            else:
                st.warning("Ent: " + str(eh["Entropy"]) + " X")
            st.caption("Ongorulebilirlik")
        st.markdown("**Non-Klise Skor:** " + str(eh["NK_Skor"]) + "/100 | **Gecen:** " + str(eh["NK_Gecen"]) + "/6 | **Seviye:** " + str(eh["NK_Seviye"]) + " | **Deep Tech:** " + str(eh["HibritSeviye"]) + " (" + str(eh["HibritSkor"]) + ") | **Kalite:** " + str(eh["KaliteUygun"]) + " | **Marj:** " + str(eh["MarjUygun"]) + " | **Sinyal Zayiflik:** " + str(eh["SinyalZayiflik"]) + "/100")
        st.markdown("### 15dk Bar Bazli Detay")
        hb1, hb2, hb3, hb4 = st.columns(4)
        with hb1:
            st.metric("Son Bar Aralik", f"%{eh['BarAralik']}")
        with hb2:
            st.metric("ATR Yuzde", f"%{eh['ATRYuzde']}")
        with hb3:
            st.metric("Momentum 5 Bar", f"%{eh['Momentum5']}")
        with hb4:
            st.metric("Gecikme Kaybi", f"%{eh['KayipMarj']}")


# ==================== GECENIN EN IYI FIRSATI ====================
if onc:
    odf_ust = pd.DataFrame(onc)
    if sd:
        odf_ust = odf_ust[odf_ust["Hisse"].apply(lambda x: (x + ".IS") in ks)]
    gece_sonuc = gecenin_en_iyisi_bul(odf_ust)
    if gece_sonuc is not None:
        gh = gece_sonuc["hisse"]
        st.markdown("---")
        st.markdown("## 🌙 GECENIN EN IYI FIRSATI")
        kutu_renk_g = gece_sonuc["renk"]
        karar_g = gece_sonuc["karar"]
        st.markdown(
            '<div style="background-color:' + kutu_renk_g + '; padding:25px; border-radius:15px; color:white; margin-bottom:20px;">'
            '<h1 style="margin:0; color:white; font-size:42px;">' + str(gh["Hisse"]) + ' &nbsp;&nbsp; <span style="background:rgba(255,255,255,0.2); padding:8px 20px; border-radius:8px;">' + karar_g + '</span></h1>'
            '<p style="font-size:22px; margin:15px 0 5px 0;"><b>Gap Skoru:</b> ' + str(gh["GapSkor"]) + '/100 &nbsp; | &nbsp; <b>Kapanis:</b> ' + str(gh["Kapanis"]) + '</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Beklenen Gap:</b> ' + str(gh["GapYon"]) + ' &nbsp; <b>Overnight Hedef Marj:</b> %' + str(gh["OvernightHedefMarj"]) + ' &nbsp; <b>Kapanis Pozisyonu:</b> ' + str(gh["Yorum"]) + '</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Overnight Hedef Fiyat:</b> ' + str(gh["OvernightHedefFiyat"]) + ' TL &nbsp; | &nbsp; <b>Overnight SL:</b> ' + str(gh["OvernightSLFiyat"]) + ' TL &nbsp; | &nbsp; <b>R/O:</b> ' + str(gh["OvernightRO"]) + '</p>'
            '<p style="font-size:20px; margin:5px 0;"><b>Marj Uygunluk:</b> <span style="background:rgba(255,255,255,0.25); padding:2px 10px; border-radius:5px;">' + str(gh["OvernightMarjUygun"]) + '</span></p>'
            '<p style="font-size:18px; margin:10px 0 0 0;"><b>Overnight Hedef Aralik:</b> %' + str(HEDEF_OVERNIGHT_MIN) + '-%' + str(HEDEF_OVERNIGHT_MAX) + '</p>'
            '<p style="font-size:16px; margin:5px 0 0 0; font-style:italic;">' + str(gece_sonuc["aciklama"]) + '</p>'
            '</div>', unsafe_allow_html=True)
        gcol1, gcol2, gcol3, gcol4, gcol5 = st.columns(5)
        with gcol1:
            st.metric("RSI", str(gh["RSI"]))
        with gcol2:
            st.metric("Hacim", str(gh["Hacim"]))
        with gcol3:
            st.metric("Vol Rejim", str(gh["VolRejim"]))
        with gcol4:
            st.metric("KER", str(gh["KER"]))
        with gcol5:
            st.metric("CHOP", str(gh["CHOP"]))
        st.caption("Strateji: Kapanisa yakin al, ertesi gun acilista gap gerceklesince sat. Overnight hedef marj 15dk bar bazli hesaplanir.") 

st.markdown("---")

t1, t2, t3, t4, t5, t6, t7 = st.tabs(["Karar", "Trend", "Mum", "Risk", "Overnight", "Haber & Pairs", "Derin Teknoloji"])

with t1:
    st.subheader("Karar Motoru - Tum Metrikler Birlesik Sinyal")
    st.caption("9 klasik + 6 non-klise + Derin Teknoloji + 15dk Bar Bazli Hedef Marj + Gecikme Telafi")
    if not sat:
        st.warning("Veri yok.")
    else:
        kdf = pd.DataFrame(sat)
        if sd:
            kdf = kdf[kdf["Katilim"] == "EVET"]
        kdf = kdf.sort_values("KararSkor", ascending=False).reset_index(drop=True)
        st.markdown("### A) Secili Hisse Karari")
        col_sec1, col_sec2 = st.columns([1, 2])
        with col_sec1:
            secili_hisse = st.selectbox("Hisse Sec", kdf["Hisse"].tolist(), key="karar_sec")
        with col_sec2:
            secili = kdf[kdf["Hisse"] == secili_hisse].iloc[0]
            sr = secili["KararRenk"]
            st.markdown(
                '<div style="background-color:' + sr + '; padding:20px; border-radius:10px; text-align:center;">'
                '<h2 style="color:white; margin:0;">' + str(secili_hisse) + ' -> ' + str(secili["KararSinyal"]) + '</h2>'
                '<p style="color:white; margin:5px 0; font-size:18px;">Skor: ' + str(secili["KararSkor"]) + '/100 | Son Bar: ' + str(secili["Fiyat"]) + ' (' + str(secili["SonBarZamani"]) + ')</p>'
                '<p style="color:white; margin:5px 0; font-size:18px;">Tahmini Su An: ' + str(secili["TahminiFiyat"]) + ' TL (' + str(secili["TahminFark"]) + ')</p>'
                '<p style="color:white; margin:5px 0;">SL: ' + str(secili["SL"]) + ' (%' + str(secili["SLYuzde"]) + ') | Hedef: ' + str(secili["Hedef"]) + ' (%' + str(secili["HedefYuzde"]) + ') | R/O: ' + str(secili["RO"]) + '</p>'
                '<p style="color:white; margin:5px 0;">Kalan Marj: %' + str(secili["KalanMarj"]) + ' | Kayip Marj: %' + str(secili["KayipMarj"]) + ' | Gecikme: ' + str(secili["GecikmeDk"]) + ' dk</p>'
                '<p style="color:white; margin:5px 0;">Marj Uygunluk: ' + str(secili["MarjUygun"]) + ' | Kalite: ' + str(secili["KaliteUygun"]) + ' | Gecikme Durumu: ' + str(secili["GecikmeUyari"]) + '</p>'
                '<p style="color:white; margin:5px 0;">Gun Ici: ' + str(secili["GunIciUygun"]) + ' | Overnight: ' + str(secili["OvernightUygun"]) + ' (%' + str(secili["OvernightHedefMarj"]) + ')</p>'
                '<p style="color:white; margin:5px 0;">Non-Klise: ' + str(secili["NK_Seviye"]) + ' (' + str(secili["NK_Skor"]) + ') | Deep: ' + str(secili["HibritSeviye"]) + ' (' + str(secili["HibritSkor"]) + ') | Sinyal Zayiflik: ' + str(secili["SinyalZayiflik"]) + '</p>'
                '<p style="color:white; margin:5px 0; font-style:italic;">' + str(secili["KararNeden"]) + '</p>'
                '</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("B) Bugunun En Iyi 5 Firsati")
        firsatlar = kdf[(kdf["KararSkor"] >= 60) & (kdf["RORaw"] >= 1.45)].head(5).copy()
        if not firsatlar.empty:
            kart_cols = st.columns(min(5, len(firsatlar)))
            for i in range(len(firsatlar)):
                r = firsatlar.iloc[i]
                with kart_cols[i]:
                    rk = r['KararRenk']
                    st.markdown(
                        '<div style="background-color:' + rk + '; padding:12px; border-radius:8px; color:white;">'
                        '<h4 style="margin:0;">' + str(r["Hisse"]) + '</h4>'
                        '<p style="margin:3px 0; font-size:20px; font-weight:bold;">' + str(r["KararSinyal"]) + '</p>'
                        '<p style="margin:3px 0;">Skor: ' + str(r["KararSkor"]) + '</p>'
                        '<p style="margin:3px 0; font-size:11px;">Son Bar: ' + str(r["Fiyat"]) + '</p>'
                        '<p style="margin:3px 0; font-size:11px;">Tahmini: ' + str(r["TahminiFiyat"]) + ' TL</p>'
                        '<p style="margin:3px 0; font-size:12px;">Hedef: ' + str(r["Hedef"]) + ' (%' + str(r["HedefYuzde"]) + ')</p>'
                        '<p style="margin:3px 0; font-size:12px;">Kalan: %' + str(r["KalanMarj"]) + ' | R/O: ' + str(r["RO"]) + '</p>'
                        '<p style="margin:3px 0; font-size:11px;">Marj: ' + str(r["MarjUygun"]) + '</p>'
                        '<p style="margin:3px 0; font-size:11px;">Gecikme: ' + str(r["GecikmeUyari"]) + '</p>'
                        '</div>', unsafe_allow_html=True)
        else:
            st.info("Bugun icin kriterlere uyan firsat yok.")
        st.markdown("---")
        st.subheader("C) Telegram Bildirim")
        tgl1, tgl2 = st.columns(2)
        with tgl1:
            if st.button("Bugunun En Iyi 5 Firsatini Gonder"):
                if telegram_toplu_gonder(firsatlar, "BIST Bugunun Firsatlari"):
                    st.success("Gonderildi!")
                else:
                    st.warning("Telegram token ayarlanmamis.")
        with tgl2:
            if st.button("Tum GUCLU AL Sinyallerini Gonder"):
                guclu_al = kdf[kdf["KararSinyal"] == "GUCLU AL"].copy()
                if telegram_toplu_gonder(guclu_al, "BIST Guclu AL Sinyalleri"):
                    st.success("Gonderildi!")
                else:
                    st.warning("Telegram token ayarlanmamis.")
        st.markdown("---")
        st.subheader("D) Yeni Sinyal Degisimleri")
        gecmis_dict = st.session_state.get('gecmis', {})
        degisimler = sinyal_degisim_tespit(kdf, gecmis_dict)
        if degisimler:
            for d in degisimler[:10]:
                if "AL" in d['Yeni']:
                    ok_renk = "#1b5e20"
                elif "SAT" in d['Yeni']:
                    ok_renk = "#b71c1c"
                else:
                    ok_renk = "#e65100"
                st.markdown(
                    '<div style="background-color:' + ok_renk + '; padding:8px; border-radius:6px; margin:4px 0; color:white;">'
                    '<b>' + str(d["Hisse"]) + '</b>: ' + str(d["Eski"]) + ' -> <b>' + str(d["Yeni"]) + '</b> | Skor: ' + str(d["Skor"]) + ' | ' + str(d["Fiyat"]) +
                    '</div>', unsafe_allow_html=True)
        else:
            st.info("Onceki taramaya gore degisim yok. Ilk tarama ise bu normal.")
        st.session_state['gecmis'] = sinyal_dict_olustur(kdf)
        st.markdown("---")
        st.subheader("Karar Dagilimi")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("GUCLU AL", len(kdf[kdf["KararSinyal"] == "GUCLU AL"]))
        k2.metric("AL", len(kdf[kdf["KararSinyal"] == "AL"]))
        k3.metric("BEKLE", len(kdf[kdf["KararSinyal"] == "BEKLE"]))
        k4.metric("SAT", len(kdf[kdf["KararSinyal"] == "SAT"]))
        k5.metric("GUCLU SAT", len(kdf[kdf["KararSinyal"] == "GUCLU SAT"]))
        st.markdown("---")
        st.subheader("E) Tum Karar Skorlari")
        def rk_sinyal(v):
            if "GUCLU AL" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AL" in str(v):
                return 'background-color:#2e7d32;color:white;font-weight:bold;'
            if "GUCLU SAT" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "SAT" in str(v):
                return 'background-color:#c62828;color:white;'
            return 'background-color:#e65100;color:white;'
        def r_marj(v):
            if "MARJ UYGUN" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "MARJ DUSUK" in str(v):
                return 'background-color:#e65100;color:white;'
            if "MARJ YUKSEK" in str(v):
                return 'background-color:#FFC107;color:black;'
            return 'background-color:#b71c1c;color:white;'
        def r_gecikme(v):
            if "MINIMAL" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AZ GECIKME" in str(v):
                return 'background-color:#66bb6a;color:white;'
            if "ORTA GECIKME" in str(v):
                return 'background-color:#FFC107;color:black;'
            if "YUKSEK GECIKME" in str(v):
                return 'background-color:#e65100;color:white;'
            return 'background-color:#b71c1c;color:white;font-weight:bold;'
        kdf_goster = kdf[["Hisse", "Fiyat", "TahminiFiyat", "KararSkor", "KararSinyal", "HedefYuzde", "KalanMarj", "RO", "MarjUygun", "GecikmeUyari", "KaliteUygun", "NK_Skor", "HibritSkor"]].copy()
        st.dataframe(kdf_goster.style.map(rk_sinyal, subset=["KararSinyal"]).map(r_marj, subset=["MarjUygun"]).map(r_gecikme, subset=["GecikmeUyari"]), use_container_width=True, height=450)
        st.markdown("---")
        st.subheader("En Yuksek Karar Skoru 10")
        top10_df = kdf.head(10)[["Hisse", "Fiyat", "TahminiFiyat", "KararSkor", "KararSinyal", "SL", "Hedef", "HedefYuzde", "KalanMarj", "RO", "MarjUygun", "KaliteUygun", "NK_Skor", "HibritSkor"]].copy()
        st.dataframe(top10_df, use_container_width=True)
        st.markdown("---")
        st.subheader("En Dusuk Karar Skoru 10 (Riskli)")
        bot10_df = kdf.tail(10)[["Hisse", "Fiyat", "KararSkor", "KararSinyal", "KER", "CHOP", "GNN_Manip", "NK_Seviye"]].copy()
        st.dataframe(bot10_df, use_container_width=True)
        st.markdown("---")
        st.subheader("Marj Uygunluk Tablosu (15dk Bar Bazli)")
        marj_df = kdf[["Hisse", "Fiyat", "TahminiFiyat", "HedefYuzde", "KalanMarj", "SLYuzde", "MarjUygun", "KaliteUygun", "GecikmeUyari", "GunIciUygun", "OvernightUygun", "OvernightHedefMarj", "RO", "KararSinyal"]].copy()
        marj_df = marj_df.sort_values("HedefYuzde", ascending=False).reset_index(drop=True)
        st.dataframe(marj_df.style.map(r_marj, subset=["MarjUygun"]).map(r_gecikme, subset=["GecikmeUyari"]), use_container_width=True, height=400)
        st.markdown("---")
        st.subheader("Sadece Marj Uygun Hisseler (%2-3.5)")
        marj_uygun_df = kdf[kdf["MarjUygun"] == "MARJ UYGUN"].copy()
        if not marj_uygun_df.empty:
            st.success(str(len(marj_uygun_df)) + " hisse marj uygun")
            marj_uygun_goster = marj_uygun_df[["Hisse", "Fiyat", "TahminiFiyat", "Hedef", "HedefYuzde", "KalanMarj", "SL", "SLYuzde", "RO", "KararSkor", "KararSinyal", "KaliteUygun", "GecikmeUyari"]].copy()
            marj_uygun_goster = marj_uygun_goster.sort_values("KararSkor", ascending=False).reset_index(drop=True)
            st.dataframe(marj_uygun_goster.style.map(r_gecikme, subset=["GecikmeUyari"]), use_container_width=True, height=350)
        else:
            st.info("Marj uygun hisse yok.")
        st.markdown("---")
        st.subheader("Gecikme Durumu Dagilimi")
        g1, g2, g3, g4, g5 = st.columns(5)
        g1.metric("Minimal", len(kdf[kdf["GecikmeUyari"] == "MINIMAL GECIKME"]))
        g2.metric("Az Gecikme", len(kdf[kdf["GecikmeUyari"] == "AZ GECIKME"]))
        g3.metric("Orta Gecikme", len(kdf[kdf["GecikmeUyari"] == "ORTA GECIKME"]))
        g4.metric("Yuksek", len(kdf[kdf["GecikmeUyari"] == "YUKSEK GECIKME"]))
        g5.metric("Kritik", len(kdf[kdf["GecikmeUyari"] == "KRITIK GECIKME"]))
        st.markdown("---")
        st.subheader("6 Non-Klise Metrik Tablosu")
        nk_goster = kdf[["Hisse", "KER", "CHOP", "Parkinson", "GarmanKlass", "Kyle", "Entropy", "NK_Skor", "NK_Seviye", "KararSinyal"]].copy()
        nk_goster = nk_goster.sort_values("NK_Skor", ascending=False).reset_index(drop=True)
        st.dataframe(nk_goster, use_container_width=True, height=400)
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("En Yuksek OFI 5 (Alici Baskisi)")
            ofi_top = kdf.sort_values("OFI", ascending=False)[["Hisse", "OFI", "KararSkor", "KararSinyal", "MarjUygun"]].head(5).copy()
            st.dataframe(ofi_top, use_container_width=True)
        with colB:
            st.subheader("En Dusuk OFI 5 (Satici Baskisi)")
            ofi_bot = kdf.sort_values("OFI", ascending=True)[["Hisse", "OFI", "KararSkor", "KararSinyal", "MarjUygun"]].head(5).copy()
            st.dataframe(ofi_bot, use_container_width=True)
        if st.session_state.performans:
            st.markdown("---")
            st.subheader("F) Performans Gecmisi (Kapali Pozisyonlar)")
            kapali_kayitlar = [k for k in st.session_state.performans if k.get("Durum") in ["HEDEF", "STOP"]]
            if kapali_kayitlar:
                perf_df = pd.DataFrame(kapali_kayitlar)
                def r_durum(v):
                    if v == "HEDEF":
                        return 'background-color:#1b5e20;color:white;font-weight:bold;'
                    if v == "STOP":
                        return 'background-color:#b71c1c;color:white;font-weight:bold;'
                    return 'background-color:#e65100;color:white;'
                goster_cols = [c for c in ["zaman", "Hisse", "Sinyal", "GirisFiyat", "CikisFiyat", "KarYuzde", "HedefMarj", "TutmaSaat", "Durum", "Tip"] if c in perf_df.columns]
                st.dataframe(perf_df[goster_cols].style.map(r_durum, subset=["Durum"]), use_container_width=True, height=350)
            else:
                st.info("Henuz kapali pozisyon yok. Test islemlerinden sonra gorunecek.")
        st.markdown("---")
        if st.button("📝 ACIL Sinyalleri Performans Defterine Kaydet"):
            yeni_kayit = sinyal_anlik_kaydet(kdf, tip="gun_ici")
            if yeni_kayit:
                st.session_state.performans.extend(yeni_kayit)
                st.success(str(len(yeni_kayit)) + " sinyal kaydedildi!")
            else:
                st.warning("Kaydedilecek GUCLU AL veya AL sinyali yok.")

with t2:
    st.subheader("Trend Matrisi")
    if not sat:
        st.warning("Veri yok.")
    else:
        df = pd.DataFrame(sat)
        df['O'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
        df = df.sort_values(by=['O', 'Guc'], ascending=[True, False]).drop(columns=['O'])
        if sd:
            df = df[df["Katilim"] == "EVET"]
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
        def rk(v):
            if v == "EVET":
                return 'color:#4CAF50;font-weight:bold;'
            return 'color:#F44336;'
        def r15(v):
            if "YUKARI" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ASAGI" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            return 'background-color:#e65100;color:white;font-weight:bold;'
        st.dataframe(df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk, subset=["Katilim"]).map(r15, subset=["Tahmin15"]), use_container_width=True, height=600)
        st.markdown("---")
        st.subheader("15-25 Dakika Sonrasi Yon Dagilimi")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("YUKARI", len(df[df["Tahmin15"] == "YUKARI"]))
        m2.metric("ASAGI", len(df[df["Tahmin15"] == "ASAGI"]))
        m3.metric("YATAY", len(df[df["Tahmin15"] == "YATAY"]))
        gvv = pd.to_numeric(df['Guven15'].str.replace('%', ''), errors='coerce').mean()
        m4.metric("Ort Guven", "%" + str(round(gvv, 1) if not pd.isna(gvv) else 0))
        st.markdown("---")
        st.subheader("Gecikme Telafi Ozeti")
        gt1, gt2, gt3, gt4 = st.columns(4)
        gt1.metric("Ort Gecikme", str(round(df["GecikmeDk"].mean(), 1)) + " dk")
        gt2.metric("Ort Tahmin Fark", "%" + str(round(df["TahminFarkRaw"].mean(), 2)))
        gt3.metric("Ort Kalan Marj", "%" + str(round(df["KalanMarj"].mean(), 2)))
        gt4.metric("Ort Sinyal Zayiflik", str(round(df["SinyalZayiflik"].mean(), 1)) + "/100") 

with t3:
    st.subheader("Mum Grafigi")
    try:
        hs = st.selectbox("Hisse", hl[:80], key="mum_sec")
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
            f.add_trace(go.Scatter(x=h.index, y=h['BBA'], name='BBA', line=dict(color='#9c27b0', width=1, dash='dot')))
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

with t4:
    st.subheader("ATR Bazli Risk + Hedef Marj")
    if sat:
        dfr = pd.DataFrame(sat)
        if sd:
            dfr = dfr[dfr["Katilim"] == "EVET"]
        dfr = dfr.copy()
        def r_marj2(v):
            if "MARJ UYGUN" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "MARJ DUSUK" in str(v):
                return 'background-color:#e65100;color:white;'
            if "MARJ YUKSEK" in str(v):
                return 'background-color:#FFC107;color:black;'
            return 'background-color:#b71c1c;color:white;'
        def r_kalite2(v):
            if "KALITE YUKSEK" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "KALITE IYI" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "KALITE ORTA" in str(v):
                return 'background-color:#e65100;color:white;'
            return 'background-color:#b71c1c;color:white;'
        def r_gecikme2(v):
            if "MINIMAL" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AZ GECIKME" in str(v):
                return 'background-color:#66bb6a;color:white;'
            if "ORTA GECIKME" in str(v):
                return 'background-color:#FFC107;color:black;'
            if "YUKSEK GECIKME" in str(v):
                return 'background-color:#e65100;color:white;'
            return 'background-color:#b71c1c;color:white;font-weight:bold;'
        st.markdown("### A) Marj Uygun Hisseler (15dk bar bazli %" + str(HEDEF_GUN_ICI_MIN) + "-" + str(HEDEF_GUN_ICI_MAX) + ")")
        marj_ok = dfr[dfr["MarjUygun"] == "MARJ UYGUN"].copy()
        if not marj_ok.empty:
            st.success(str(len(marj_ok)) + " hisse marj uygun")
            marj_ok_goster = marj_ok[["Hisse", "Fiyat", "TahminiFiyat", "Hedef", "HedefYuzde", "KalanMarj", "RO", "KararSinyal", "KaliteUygun", "GecikmeUyari", "NK_Skor"]].copy()
            marj_ok_goster = marj_ok_goster.sort_values("HedefYuzde", ascending=False).reset_index(drop=True)
            st.dataframe(marj_ok_goster.style.map(r_gecikme2, subset=["GecikmeUyari"]), use_container_width=True, height=350)
        else:
            st.info("Marj uygun hisse yok.")
        st.markdown("---")
        st.markdown("### B) Marj Uygun + Kalite Yuksek")
        kalite_marj = dfr[(dfr["MarjUygun"] == "MARJ UYGUN") & (dfr["KaliteUygun"] == "KALITE YUKSEK")].copy()
        if not kalite_marj.empty:
            st.success(str(len(kalite_marj)) + " hisse marj uygun + kalite yuksek")
            km_goster = kalite_marj[["Hisse", "Fiyat", "TahminiFiyat", "Hedef", "HedefYuzde", "KalanMarj", "RO", "KararSinyal", "NK_Skor", "HibritSkor", "GecikmeUyari"]].copy()
            st.dataframe(km_goster.style.map(r_gecikme2, subset=["GecikmeUyari"]), use_container_width=True, height=350)
        else:
            st.info("Bu kombinasyonda hisse yok.")
        st.markdown("---")
        st.markdown("### C) R/O > 1.5 Olan Hisseler")
        def rok(x):
            try:
                return float(x) > 1.5
            except Exception:
                return False
        rdf = dfr[dfr["RO"].apply(rok)].copy()
        if not rdf.empty:
            rdf_goster = rdf[["Hisse", "Fiyat", "TahminiFiyat", "SL", "Hedef", "HedefYuzde", "KalanMarj", "RO", "Sinyal", "KararSinyal", "MarjUygun", "KaliteUygun", "GecikmeUyari", "NK_Skor", "HibritSkor"]].copy()
            st.dataframe(rdf_goster.style.map(r_marj2, subset=["MarjUygun"]).map(r_kalite2, subset=["KaliteUygun"]).map(r_gecikme2, subset=["GecikmeUyari"]), use_container_width=True, height=450)
        else:
            st.info("R/O > 1.5 olan hisse yok.")
        st.markdown("---")
        st.markdown("### D) Gecikme Durumu Risk Dagilimi")
        gr1, gr2, gr3, gr4, gr5 = st.columns(5)
        gr1.metric("Minimal", len(dfr[dfr["GecikmeUyari"] == "MINIMAL GECIKME"]))
        gr2.metric("Az", len(dfr[dfr["GecikmeUyari"] == "AZ GECIKME"]))
        gr3.metric("Orta", len(dfr[dfr["GecikmeUyari"] == "ORTA GECIKME"]))
        gr4.metric("Yuksek", len(dfr[dfr["GecikmeUyari"] == "YUKSEK GECIKME"]))
        gr5.metric("Kritik", len(dfr[dfr["GecikmeUyari"] == "KRITIK GECIKME"]))
        st.markdown("---")
        st.markdown("### E) Gecikme Etkisi Tablosu")
        gecikme_df = dfr[["Hisse", "Fiyat", "TahminiFiyat", "TahminFark", "GecikmeDk", "HedefYuzde", "KalanMarj", "KayipMarj", "SinyalZayiflik", "GecikmeUyari", "KararSinyal"]].copy()
        gecikme_df = gecikme_df.sort_values("KayipMarj", ascending=False).reset_index(drop=True)
        st.dataframe(gecikme_df.style.map(r_gecikme2, subset=["GecikmeUyari"]), use_container_width=True, height=400)
    else:
        st.warning("Veri yok.")

with t5:
    st.subheader("Overnight Gap Stratejisi")
    st.info("Kapanista al, acilista sat | 15dk bar bazli hedef marj %" + str(HEDEF_OVERNIGHT_MIN) + "-%" + str(HEDEF_OVERNIGHT_MAX))
    if onc:
        odf = pd.DataFrame(onc)
        if sd:
            odf = odf[odf["Hisse"].apply(lambda x: (x + ".IS") in ks)]
        odf = odf.copy()
        odf = odf.sort_values(by="GapSkor", ascending=False).reset_index(drop=True)
        def ron(v):
            if "GECE TASI GUCLU" in str(v):
                return 'background-color:#0d3d12;color:white;font-weight:bold;'
            if "GECE TASI" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ZAYIF TASI" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "GECE TASIMA" in str(v):
                return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'
        def rg(v):
            if "YUKARI" in str(v):
                return 'color:#4CAF50;font-weight:bold;'
            if "ASAGI" in str(v):
                return 'color:#F44336;font-weight:bold;'
            return 'color:#FFC107;'
        def r_ov_marj(v):
            if "OVERNIGHT UYGUN" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "OVERNIGHT DUSUK" in str(v):
                return 'background-color:#e65100;color:white;'
            if "OVERNIGHT YUKSEK" in str(v):
                return 'background-color:#FFC107;color:black;'
            return 'background-color:#b71c1c;color:white;'
        st.markdown("### Tum Overnight Sinyaller")
        st.dataframe(odf.style.map(ron, subset=["Overnight"]).map(rg, subset=["GapYon"]).map(r_ov_marj, subset=["OvernightMarjUygun"]), use_container_width=True, height=450)
        st.markdown("---")
        st.subheader("Gecenin En Guclu 10")
        top10_onc = odf.head(10)[["Hisse", "Kapanis", "GapSkor", "Overnight", "GapYon", "OvernightHedefMarj", "OvernightHedefFiyat", "OvernightSLFiyat", "OvernightRO", "OvernightMarjUygun", "KER", "CHOP"]].copy()
        st.dataframe(top10_onc, use_container_width=True)
        st.markdown("---")
        st.subheader("Overnight Marj Uygun (15dk bar bazli %3-5)")
        ov_uygun = odf[odf["OvernightMarjUygun"] == "OVERNIGHT UYGUN"].copy()
        if not ov_uygun.empty:
            st.success(str(len(ov_uygun)) + " hisse overnight marj uygun")
            ov_uygun_goster = ov_uygun[["Hisse", "Kapanis", "GapSkor", "Overnight", "OvernightHedefMarj", "OvernightHedefFiyat", "OvernightSLFiyat", "OvernightRO", "KER", "CHOP"]].copy()
            st.dataframe(ov_uygun_goster, use_container_width=True, height=350)
        else:
            st.info("Overnight hedef marji uygun hisse yok.")
        st.markdown("---")
        st.subheader("Overnight Hedef Marj Dagilimi")
        ov1, ov2, ov3, ov4 = st.columns(4)
        ov1.metric("Toplam Sinyal", len(odf))
        ov2.metric("GECE TASI", len(odf[odf["Overnight"] == "GECE TASI"]))
        ov3.metric("ZAYIF TASI", len(odf[odf["Overnight"] == "ZAYIF TASI"]))
        ov4.metric("Marj Uygun", len(ov_uygun))
        st.markdown("---")
        st.subheader("Overnight + Marj Uygun En Iyi 5 Kombine")
        ov_marj_top = odf[odf["OvernightMarjUygun"] == "OVERNIGHT UYGUN"].sort_values("GapSkor", ascending=False).head(5).copy()
        if not ov_marj_top.empty:
            ov_kombine = ov_marj_top[["Hisse", "Kapanis", "GapSkor", "OvernightHedefMarj", "OvernightHedefFiyat", "OvernightSLFiyat", "OvernightRO", "KER", "CHOP", "GapYon"]].copy()
            st.dataframe(ov_kombine, use_container_width=True)
        else:
            st.info("Kombine uygun sinyal yok.")
        st.markdown("---")
        if st.button("GECE TASI Sinyallerini Telegram'a Gonder"):
            mesaj = "<b>BIST Gece Tasi Sinyalleri</b>\n\n"
            for i in range(min(5, len(odf))):
                r = odf.iloc[i]
                mesaj += "- " + str(r['Hisse']) + " | Gap: " + str(r['GapSkor']) + " | Hedef Marj: %" + str(r['OvernightHedefMarj']) + "\n"
            if telegram_gonder(mesaj):
                st.success("Gonderildi!")
            else:
                st.warning("Telegram token ayarlanmamis.")
        st.markdown("---")
        if st.button("📝 GECE TASI Sinyallerini Performans Defterine Kaydet"):
            gece_kayit = []
            for _, r in odf.head(10).iterrows():
                if r['Overnight'] in ["GECE TASI", "ZAYIF TASI"]:
                    try:
                        giris = float(r['KapanisRaw'])
                        gece_kayit.append({
                            "zaman": turkiye_saati().strftime("%Y-%m-%d %H:%M:%S"),
                            "Hisse": r['Hisse'],
                            "Sinyal": r['Overnight'],
                            "GirisFiyat": giris,
                            "Hedef": str(r['OvernightHedefFiyat']) + " TL",
                            "SL": str(r['OvernightSLFiyat']) + " TL",
                            "HedefMarj": r['OvernightHedefMarj'],
                            "RO": r['OvernightRO'],
                            "KararSkor": float(r['GapSkor']),
                            "NK_Skor": 50,
                            "HibritSkor": 50,
                            "Tip": "overnight",
                            "Durum": "ACIK",
                            "CikisFiyat": 0.0,
                            "KarYuzde": 0.0,
                            "TutmaSaat": 0.0
                        })
                    except Exception:
                        continue
            if gece_kayit:
                st.session_state.performans.extend(gece_kayit)
                st.success(str(len(gece_kayit)) + " gece tasi sinyali kaydedildi!")
            else:
                st.warning("Kaydedilecek sinyal yok.")
    else:
        st.warning("Veri yok.") 

with t6:
    st.subheader("Finansal Haberler (Paratic RSS)")
    if st.session_state.haber:
        for i, h in enumerate(st.session_state.haber[:15]):
            st.markdown("**" + h['baslik'] + "**")
            st.caption(h['tarih'] + " | " + h['link'])
    else:
        st.info("Haber verisi yuklenemedi.")
    st.markdown("---")
    st.subheader("Kointegrasyon - Pairs Trading")
    st.caption("Kointegre hisse ciftleri. |Z| > 2 = islem sinyali.")
    if sat:
        top10 = [r["Hisse"] for r in sat[:10]]
        if st.button("Top 10 Icin Pairs Analizi"):
            with st.spinner("Test ediliyor..."):
                pairs = pairs_tara(hv, top10)
            if pairs:
                st.dataframe(pd.DataFrame(pairs), use_container_width=True)
                st.info("Z>2: 1.SAT 2.AL | Z<-2: 1.AL 2.SAT")
            else:
                st.warning("Kointegre cift bulunamadi.")

with t7:
    st.subheader("Derin Teknoloji Analizi")
    st.caption("LSTM, NLP, Pekistirmeli Ogrenme, GNN ve GAN modulleri birlesik skoru.")
    if not sat:
        st.warning("Veri yok.")
    else:
        ddf = pd.DataFrame(sat)
        if sd:
            ddf = ddf[ddf["Katilim"] == "EVET"]
        ddf = ddf.sort_values("HibritSkor", ascending=False).reset_index(drop=True)
        st.markdown("### Hibrit Deep Tech Skoru Dagilimi")
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("YUKSEK POZITIF", len(ddf[ddf["HibritSeviye"] == "YUKSEK POZITIF"]))
        d2.metric("POZITIF", len(ddf[ddf["HibritSeviye"] == "POZITIF"]))
        d3.metric("NOTR", len(ddf[ddf["HibritSeviye"] == "NOTR"]))
        d4.metric("NEGATIF", len(ddf[ddf["HibritSeviye"] == "NEGATIF"]))
        d5.metric("YUKSEK NEGATIF", len(ddf[ddf["HibritSeviye"] == "YUKSEK NEGATIF"]))
        st.markdown("---")
        st.subheader("Tum Derin Teknoloji Metrikleri")
        def rh(v):
            if "YUKSEK POZITIF" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "POZITIF" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "YUKSEK NEGATIF" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "NEGATIF" in str(v):
                return 'background-color:#c62828;color:white;'
            return 'background-color:#e65100;color:white;'
        goster = ddf[["Hisse", "Fiyat", "TahminiFiyat", "HibritSkor", "HibritSeviye", "LSTM_Yon", "LSTM_Guven", "NLP_Skor", "NLP_Haber", "RL_Q", "RL_Sharpe", "GNN_Manip", "GAN_VaR", "KararSinyal"]].copy()
        st.dataframe(goster.style.map(rh, subset=["HibritSeviye"]), use_container_width=True, height=500)
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("LSTM En Yuksek Tahmin 5")
            lstm_top = ddf.sort_values("LSTM_Yon", ascending=False)[["Hisse", "LSTM_Yon", "LSTM_Guven", "HibritSkor", "Fiyat", "TahminiFiyat"]].head(5).copy()
            st.dataframe(lstm_top, use_container_width=True)
            st.subheader("NLP Haber Skoru En Yuksek 5")
            nlp_df = ddf[ddf["NLP_Haber"] > 0].copy()
            nlp_top = nlp_df.sort_values("NLP_Skor", ascending=False)[["Hisse", "NLP_Skor", "NLP_Haber", "HibritSkor"]].head(5).copy()
            st.dataframe(nlp_top, use_container_width=True)
            st.subheader("Pekistirmeli Ogrenme En Yuksek 5")
            rl_top = ddf.sort_values("RL_Q", ascending=False)[["Hisse", "RL_Q", "RL_Sharpe", "HibritSkor"]].head(5).copy()
            st.dataframe(rl_top, use_container_width=True)
        with colB:
            st.subheader("Manipulasyon Riski Yuksek 5")
            gnn_top = ddf.sort_values("GNN_Manip", ascending=False)[["Hisse", "GNN_Manip", "HibritSkor", "Fiyat"]].head(5).copy()
            st.dataframe(gnn_top, use_container_width=True)
            st.subheader("GAN Risk En Dusuk 5 (Guvenli)")
            gan_top = ddf.sort_values("GAN_VaR", ascending=True)[["Hisse", "GAN_VaR", "HibritSkor", "Fiyat"]].head(5).copy()
            st.dataframe(gan_top, use_container_width=True)
            st.subheader("En Yuksek Hibrit Skor 10")
            hibrit_top = ddf.head(10)[["Hisse", "Fiyat", "TahminiFiyat", "HibritSkor", "HibritSeviye", "KararSinyal"]].copy()
            st.dataframe(hibrit_top, use_container_width=True)
        st.markdown("---")
        st.markdown("### Derin Teknoloji Ne Anlatiyor?")
        st.markdown("""
- **LSTM_Yon**: Agirlikli bellek modeli ile 5 adim sonrasi yon tahmini (%)
- **LSTM_Guven**: Tahmin guven yuzdesi
- **NLP_Skor**: Turkce finansal haber duygu analizi (-5 ile +5 arasi)
- **NLP_Haber**: Hisse ile ilgili bulunan haber sayisi
- **RL_Q**: Pekistirmeli ogrenme Q-degeri (getiri bazli odul)
- **RL_Sharpe**: Sharpe orani (risk ayarli getiri)
- **GNN_Manip**: Manipulasyon riski (0-100, yuksek = riskli)
- **GAN_VaR**: Sentetik senaryolarda %95 VaR (kayip tahmini)
- **HibritSkor**: Tum modellerin birlesik skoru (0-100)
- **HibritSeviye**: YUKSEK POZITIF / POZITIF / NOTR / NEGATIF / YUKSEK NEGATIF
        """) 

st.markdown("---")
st.markdown("## 📈 PERFORMANS DETAY RAPORU")
perf2 = performans_hesapla(st.session_state.performans)
if perf2["toplam"] == 0:
    st.info("Henuz kayitli sinyal yok. Karar sekmesinde 'ACIL Sinyalleri Performans Defterine Kaydet' butonuna basarak baslayin.")
else:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("### Genel Durum")
        st.write("- **Toplam Sinyal:** " + str(perf2["toplam"]))
        st.write("- **Kapali Pozisyon:** " + str(perf2["kapali"]))
        st.write("- **Acik Pozisyon:** " + str(perf2["acik"]))
        st.write("- **Hedef Asilan:** " + str(perf2["hedef_asilan"]))
        st.write("- **Stop Olan:** " + str(perf2["stop_olan"]))
    with col_b:
        st.markdown("### Basari Metrikleri")
        st.write("- **Basari Orani:** %" + str(perf2["basari_orani"]))
        st.write("- **Ort. Kar:** %" + str(perf2["ort_kar"]))
        st.write("- **Ort. Zarar:** %" + str(perf2["ort_zarar"]))
        st.write("- **Beklenen Getiri:** %" + str(perf2["beklenen_getiri"]))
        st.write("- **Ort. Tutma:** " + str(perf2["ort_tutma"]) + " saat")
    with col_c:
        st.markdown("### En Iyi / En Kotu")
        st.write("- **En Iyi Islem:** %" + str(perf2["en_iyi"]))
        st.write("- **En Kotu Islem:** %" + str(perf2["en_kotu"]))
        st.write("- **Toplam Kar:** %" + str(perf2["toplam_kar"]))
        st.write("- **Kazanan:** " + str(perf2["kazanan"]))
        st.write("- **Kaybeden:** " + str(perf2["kaybeden"]))
    st.markdown("---")
    if perf2["kapali"] >= 10:
        if perf2["basari_orani"] >= 70:
            st.success("🎯 Basari %70+ | Sistem kanitlanmis, sermaye artirilabilir")
        elif perf2["basari_orani"] >= 50:
            st.warning("⚠️ Basari %50-70 | Sistem calisiyor, optimizasyon gerekli")
        else:
            st.error("❌ Basari %50 alti | Parametreleri degistirmelisiniz")
    elif perf2["kapali"] >= 5:
        st.info("ℹ️ Ilk degerlendirme icin 5+ kapali islem var. 10'a tamamlayin.")
    else:
        st.info("ℹ️ Degerlendirme icin en az 5 kapali islem gerekli. Su an: " + str(perf2["kapali"]))
    st.markdown("---")
    st.subheader("Tum Kayitlar")
    try:
        tum_df = pd.DataFrame(st.session_state.performans)
        if not tum_df.empty:
            def r_durum2(v):
                if v == "HEDEF":
                    return 'background-color:#1b5e20;color:white;font-weight:bold;'
                if v == "STOP":
                    return 'background-color:#b71c1c;color:white;font-weight:bold;'
                if v == "ACIK":
                    return 'background-color:#e65100;color:white;'
                return ''
            st.dataframe(tum_df.style.map(r_durum2, subset=["Durum"]), use_container_width=True, height=400)
    except Exception:
        pass
    if st.button("🗑️ Performans Gecmisini Temizle"):
        st.session_state.performans = []
        st.success("Performans gecmisi temizlendi!")
        st.rerun()

st.markdown("---")
st.markdown("## ⏱️ GECIKME TELAFI SISTEMI")
st.markdown("""
### Nasil Calisir?

**Problem:** Panel 15 dakika gecikmeli veri kullaniyor. Bu, "son bar" fiyatinin **15 dakika onceki** fiyat oldugu anlamina gelir. Bu sirada gercek fiyat hareket etmis olabilir.

**Cozum 3 Katmanli:**

1. **Son Bar Zamani Gosterimi:** Her hisse kartinda "Son Bar: HH:MM" yazar. Boylece hangi veriyi gordugunuzu bilirsiniz.

2. **Tahmini Guncel Fiyat:** Son 3 barin ortalama degisimi (momentum) kullanilarak **"su anki tahmini fiyat"** hesaplanir:
   - `Tahmini Fiyat = Son Bar + (Son 3 barin ortalama degisimi)`
   - Bu size gercek fiyata **en yakin tahmini** verir.

3. **Kalan Marj:** Hedefe ne kadar marj kaldigini **tahmini guncel fiyata gore** hesaplar:
   - `Kalan Marj = (Hedef - Tahmini Fiyat) / Tahmini Fiyat`
   - Bu, size **gercekci kâr potansiyelini** gosterir.

4. **Gecikme Uyari Sistemi:** Kayip marj oranina gore 5 seviyede uyari:
   - **MINIMAL GECIKME:** Kayip %5 alti (yesil)
   - **AZ GECIKME:** Kayip %5-15 (acik yesil)
   - **ORTA GECIKME:** Kayip %15-30 (sari)
   - **YUKSEK GECIKME:** Kayip %30-50 (turuncu)
   - **KRITIK GECIKME:** Kayip %50+ (kirmizi)

5. **Sinyal Zayiflik Skoru:** Sinyalin gecikme nedeniyle ne kadar zayifladigini gosterir (0-100).
   - **70+:** Sinyal hala gecerli
   - **50-70:** Dikkatli ol
   - **50 alti:** Sinyal muhtemelen kacmis

### Nasil Kullanilir?

**Ornek:** CVKMD — Son Bar 13.83 TL (14:40), Tahmini Su An 13.88 TL
- Son bar: 14:40 (15 dakika once)
- Tahmini su an: 13.88 TL (+%0.36)
- Hedef: 14.12 TL → Kalan marj: %1.73
- Gecikme: AZ GECIKME

**Yani:** Panel size "13.88 TL'den al, %1.73 hedefe kadar kalan marj var" diyor. Son bar 13.83'e gore hesaplanmis %2.07'den daha **gercekci**.

### Sinirlar

- Tahmini fiyat **gecmis momentum bazli** — piyasa donusu olursa yaniltici olabilir
- Gercek fiyat **farkli olabilir** — Ziraat Mobil'den teyit edin
- Gecikme **kacinilmaz** — panel karar destek, kesin bilgi degil

### Sonuc

Bu 5 katmanli sistem ile panel **gercege en yakin** karar destek araci haline geldi.
""")

st.markdown("---")
st.markdown("### Hedef Marj Sistemi (15dk Bar Bazli)")
st.markdown("- **Gun Ici Hedef:** %" + str(HEDEF_GUN_ICI_MIN) + " - %" + str(HEDEF_GUN_ICI_MAX))
st.markdown("- **Overnight Hedef:** %" + str(HEDEF_OVERNIGHT_MIN) + " - %" + str(HEDEF_OVERNIGHT_MAX))
st.markdown("- **KER Esigi:** " + str(KER_ESIK) + " (dusuruldu 0.55 -> 0.40)")
st.markdown("- **Marj Hesabi:** 15dk bar ATR x " + str(BAR_15DK_HEDEF_KATSAYI) + " + kalite bonus + momentum bonus")
st.markdown("- **Gecikme Telafi:** Son 3 bar momentum + kalan marj hesabi + uyari sistemi")
st.markdown("- **Basari Degerlendirme:** %70+ = Mukemmel | %50-70 = Iyi | %50- = Gelistirme gerekli")
st.caption("15 dk gecikmeli. Yatirim tavsiyesi degildir.") 
