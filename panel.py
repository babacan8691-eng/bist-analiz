import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone, time
from streamlit_autorefresh import st_autorefresh

from data.fetcher import toplu_veri_cek, piyasa_acik_mi, turkiye_saati

st.set_page_config(page_title="BIST Pro Terminali", layout="wide")

HISSELER = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

KATILIM = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"


def rsi_hesapla(seri, periyot=14):
    fark = seri.diff()
    kazanc = fark.where(fark > 0, 0).rolling(periyot).mean()
    kayip = -fark.where(fark < 0, 0).rolling(periyot).mean()
    return 100 - (100 / (1 + kazanc / kayip))


def hisse_analiz(hisse_kodu, veri, katilim_kumesi):
    if veri.empty or len(veri) < 30:
        return None

    gecmis = veri.dropna()
    if len(gecmis) < 30:
        return None

    son_fiyat = gecmis['Close'].iloc[-1]
    baslangic_fiyat = gecmis['Close'].iloc[-min(25, len(gecmis))]
    gunluk_degisim = ((son_fiyat - baslangic_fiyat) / baslangic_fiyat) * 100 if baslangic_fiyat > 0 else 0

    sma20 = gecmis['Close'].rolling(20).mean().iloc[-1]
    rsi_serisi = rsi_hesapla(gecmis['Close'])
    rsi = rsi_serisi.iloc[-1] if not pd.isna(rsi_serisi.iloc[-1]) else 50

    hacim_ort = gecmis['Volume'].rolling(20).mean().iloc[-1]
    hacim_orani = gecmis['Volume'].iloc[-1] / hacim_ort if hacim_ort > 0 else 1

    atr = (gecmis['High'] - gecmis['Low']).rolling(14).mean().iloc[-1]

    skor = 50
    if son_fiyat > sma20:
        skor += 15
    if gunluk_degisim > 0:
        skor += 10
    if rsi < 40:
        skor += 10
    elif rsi > 70:
        skor -= 15
    if hacim_orani > 1.3:
        skor += 10
    skor = max(20, min(95, skor))

    if skor >= 70 and gunluk_degisim > 0 and hacim_orani > 1.2:
        sinyal = "GUCLU AL"
        tahmin = "YUKSELIS BEKLENIYOR"
    elif skor >= 55 and gunluk_degisim > -1:
        sinyal = "AL"
        tahmin = "YUKSELIS EGILIMI"
    elif skor < 35 and gunluk_degisim < -1:
        sinyal = "SAT"
        tahmin = "DUSUS BEKLENIYOR"
    elif skor < 45:
        sinyal = "ZAYIF"
        tahmin = "ZAYIF SEYIR"
    else:
        sinyal = "BEKLE"
        tahmin = "BEKLE"

    if not pd.isna(atr) and atr > 0:
        stop_loss = round(son_fiyat - atr * 2, 2)
        hedef = round(son_fiyat + atr * 3, 2)
        risk_odul = round((hedef - son_fiyat) / (son_fiyat - stop_loss), 2) if (son_fiyat - stop_loss) > 0 else 0
    else:
        stop_loss = 0
        hedef = 0
        risk_odul = 0

    katilim = "EVET" if (hisse_kodu + ".IS") in katilim_kumesi else "HAYIR"

    return {
        "Hisse": hisse_kodu,
        "Katilim": katilim,
        "Guc": round(skor, 2),
        "Sinyal": sinyal,
        "RSI": round(rsi, 1),
        "Trend": "Yukselis" if gunluk_degisim > 0 else "Dusus",
        "Getiri": "%" + str(round(gunluk_degisim, 2)),
        "Hacim": str(round(hacim_orani, 2)) + "x",
        "Fiyat": str(round(son_fiyat, 2)) + " TL",
        "StopLoss": str(stop_loss) + " TL",
        "Hedef": str(hedef) + " TL",
        "RiskOdul": risk_odul,
        "Tahmin": tahmin
    }


# Oturum değişkenleri
varsayilanlar = {
    'giris_yapildi': False,
    'sayac': 0,
    'son_cekim': '-',
    'manuel': False
}
for anahtar, deger in varsayilanlar.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

# Giriş ekranı
if not st.session_state.giris_yapildi:
    st.title("BIST Pro Terminali Giris")
    with st.form("giris_formu"):
        sutun1, sutun2 = st.columns(2)
        kullanici = sutun1.text_input("Kullanici Adi")
        sifre = sutun2.text_input("Sifre", type="password")
        if st.form_submit_button("Giris Yap"):
            if kullanici.strip() == "Cuma Babacan" and sifre.strip() == "784512":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Hatali kullanici adi veya sifre!")
    st.stop()

# Piyasa kontrolü
piyasa_acik = piyasa_acik_mi()
if piyasa_acik:
    st_autorefresh(interval=60000, key="yenileme")

# Başlık
st.title("BIST Pro Terminali")
st.caption("Son Guncelleme: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 Dakika Gecikmeli")

if piyasa_acik:
    st.success("PIYASA ACIK - Otomatik yenileme her 60 saniyede")
else:
    st.warning("PIYASA KAPALI - Seans saatleri disinda")

# Üst metrikler
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.metric("BIST 100", "-", "0")
with s2:
    st.metric("VIOP Denge", "Denge", "0")
with s3:
    st.metric("Taranan Hisse", str(len(HISSELER.split(","))), "0")
with s4:
    st.metric("Veri Cekme", str(st.session_state.sayac), "Son: " + st.session_state.son_cekim)

# Filtre ve buton
sadece_katilim = st.checkbox("Sadece Islam'a Uygun Hisseleri Goster", value=True)
manuel_buton = st.button("Manuel Veri Cek", type="primary")

if manuel_buton:
    st.cache_data.clear()
    st.session_state.manuel = True
    st.session_state.sayac += 1
    st.session_state.son_cekim = turkiye_saati().strftime("%H:%M:%S")
    st.rerun()

# Veri çekme ve analiz
with st.spinner("Veriler yukleniyor..."):
    hisse_listesi = HISSELER.split(",")
    katilim_kumesi = set(k + ".IS" for k in KATILIM.split(","))
    ham_veriler = toplu_veri_cek(hisse_listesi)

    tablo_satirlari = []
    for hisse in hisse_listesi:
        hisse_kodu = hisse + ".IS"
        if hisse_kodu in ham_veriler:
            analiz = hisse_analiz(hisse, ham_veriler[hisse_kodu], katilim_kumesi)
            if analiz:
                tablo_satirlari.append(analiz)

    if not st.session_state.manuel:
        st.session_state.sayac += 1
        st.session_state.son_cekim = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.manuel = False

# Tabloyu oluştur
if tablo_satirlari:
    tablo = pd.DataFrame(tablo_satirlari)

    # Sıralama: Yükseliş > Bekle > Diğer
    tablo['Oncelik'] = tablo['Tahmin'].apply(
        lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3)
    )
    tablo = tablo.sort_values(by=['Oncelik', 'Guc'], ascending=[True, False])
    tablo = tablo.drop(columns=['Oncelik'])

    # İslami filtre
    if sadece_katilim:
        tablo = tablo[tablo["Katilim"] == "EVET"]

    # Renklendirme fonksiyonları
    def tahmin_rengi(deger):
        if "YUKSELIS" in str(deger):
            return 'background-color:#1b5e20;color:white;font-weight:bold;'
        if "DUSUS" in str(deger) or "ZAYIF" in str(deger):
            return 'background-color:#b71c1c;color:white;font-weight:bold;'
        if "BEKLE" in str(deger):
            return 'background-color:#e65100;color:white;font-weight:bold;'
        return ''

    def sinyal_rengi(deger):
        if "GUCLU AL" in str(deger):
            return 'background-color:#1b5e20;color:white;font-weight:bold;'
        if "AL" in str(deger):
            return 'background-color:#2e7d32;color:white;'
        if "SAT" in str(deger) or "ZAYIF" in str(deger):
            return 'background-color:#b71c1c;color:white;'
        return 'background-color:#e65100;color:white;'

    def katilim_rengi(deger):
        if deger == "EVET":
            return 'color:#4CAF50;font-weight:bold;'
        return 'color:#F44336;'

    stilli_tablo = tablo.style.map(tahmin_rengi, subset=["Tahmin"]).map(sinyal_rengi, subset=["Sinyal"]).map(katilim_rengi, subset=["Katilim"])

    st.dataframe(stilli_tablo, use_container_width=True, height=700)

    # Özet
    st.markdown("---")
    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Gosterilen", len(tablo))
    o2.metric("Yukselis", len(tablo[tablo["Tahmin"].str.contains("YUKSELIS")]))
    o3.metric("Guclu AL", len(tablo[tablo["Sinyal"] == "GUCLU AL"]))
    o4.metric("Ortalama Guc", str(round(tablo["Guc"].mean(), 1)))
else:
    st.warning("Veri cekilemedi. Lutfen 'Manuel Veri Cek' butonuna basin.")

st.caption("Bu paneldeki veriler 15 dakika gecikmelidir. Yatirim tavsiyesi degildir.")
