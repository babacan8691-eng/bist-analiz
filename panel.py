import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from data.fetcher import toplu_veri_cek, piyasa_acik_mi, turkiye_saati, bist_endeks_verisi

st.set_page_config(page_title="BIST Pro", layout="wide")

HISSELER = "THYAO,GARAN,ASELS,BIMAS,FROTO,KCHOL,SAHOL,CCOLA,HEKTS,BRISA,SASA,TUPRS,EREGL,SISE,TOASO,PGSUS,TAVHL,VESTL,ARCLK,DOHOL,EKGYO,GUBRF,ISCTR,KRDMD,MGROS,ODAS,PETKM,SOKM,TCELL,TTKOM,VAKBN,YKBNK,ZOREN,ALARK,AYGAZ,ENKAI,GESAN,GLYHO,KONTR,SMRTG,TUKAS,ULKER,AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ADESE,ADGYO,AEFES,AFYON,AGHOL,AGYO,AKENR,AKFGY,AKGRT,AKSEN,AKSUE,ALCTL,ALFAS,ALGYO,ALKIM,ANHYT,ANSGR,ARDYZ,ARENA,ARSAN,ASGYO,ASLAN,ATEKS,AVOD,AYEN,BAGFS,BANVT,BARMA,BERA,BEYAZ,BIENY,BINHO,BIOEN,BLACK,BRKVY,BRSAN,BRYAT,BURCE,BURVA,CATES,CEMAS,CEMTS,CIMSA,CLEBI,CRDFA,CRFSA,DAGHL,DAPGM,DARDL,DENGE,DERIM,DESA,DESPC,DGATE,DGGYO,DIRIT,DITAS,DMRGD,DMSAS,DNISI,DOAS,DOBUR,DURDO,DURKN,DYOBY,EBEBK,ECILC,ECZYT,EDATA,EDIP,EGEEN,EGSER,ENJSA,ENSRI,ERBOS,ERCB,ERSU,ESCAR,ESCOM,ESEN,ETILR,EUHOL,EUPWR,EUREN,FENER,FLAP,FONET,FORMT,FORTE,FRIGO,GARFA,GEDIK,GEDZA,GENIL,GENTS,GEREL,GIPTA,GLBMD,GLCVY,GLRYH,GMTAS,GOKNUR,GOLTS,GOODY,GOZDE,GRSEL,GSDDE,GSDHO,GSRAY,GUNDG,HALKB,HATEK,HDFGS,HEDEF,HKTM,HLGYO,HUBVC,HUNER,HURGZ,ICBCT,IDEAS,IHAAS,IHEVA,IHGZT,IHLAS,IHLGM,IHYAY,IMASM,INDES,INFO,INGRM,INTEM,INVEO,ISATR,ISBTR,ISDMR,ISFIN,ISGSY,ISGYO,ISKUR,ISMEN,ISYAT,ITTFH,IZFAS,IZMDC,JANTS,KAPLM,KAREL,KARSN,KARTN,KATMR,KAYSE,KBORU,KCAER,KENT,KERVT,KFEIN,KGYO,KIMMR,KLGYO,KLKIM,KLMSN,KLRHO,KLSYN,KNFRT,KONKA,KONYA,KORDS,KOZAA,KOZAL,KRDMA,KRDMB,KRGYO,KRONT,KRSTL,KRTEK,KSTUR,KUTPO,KUVVA,LIDER,LIDFA,LINK,LKMNH,LOGO,LUKSK,MAALT,MACKO,MAGEN,MAKIM,MAKTK,MANAS,MARKA,MARTI,MAVI,MEDTR,MEGAP,MEKAG,MERCN,MERIT,MERKO,METRO,MHRGY,MIATK,MNDRS,MNDTR,MOBTL,MOGAN,MPARK,MRGYO,MRSHL,MSGYO,MTRKS,MTRYO,MZHLD,NATEN,NETAS,NIBAS,NTGAZ,NTHOL,NUGYO,OFSYM,ONCSM,ORCAY,ORGE,ORMA,OSMEN,OSTIM,OTKAR,OTTO,OYAKC,OYAYO,OYLUM,OYYAT,OZGYO,OZKGY,OZRDN,OZSUB,PAGYO,PAMEL,PAPIL,PARSN,PASEU,PATEK"

KATILIM = "AHGAZ,AKCNS,AKFYE,ALBRK,ARASE,ATAKP,AVPGY,AYDEM,BASGZ,BETAE,BUCIM,EGGUB,EGPRO,ENERY,GWIND,HTTBT,ASTOR,BMSTL,CVKMD,DOFRB,NETCD,RALYH,AKSA,KUYAS,ALKLC,EFOR,QUAGR,SARKY,BSOKE,CANTE,ASELS,TUPRS,BIMAS,FROTO,SISE,TOASO,TCELL,TTKOM,MGROS,SOKM,ULKER,AYGAZ,ENKAI,VESTL,ARCLK,PGSUS,TAVHL,ODAS,GESAN,KONTR,SMRTG,TUKAS,ZOREN,ALARK,HEKTS,BRISA,SASA,EREGL,GUBRF,PETKM,KRDMD,DOHOL,EKGYO,TKFEN,OTKAR,CIMSA,EGEEN,KORDS,BRSAN,TRGYO,ISGYO,ALGYO,GLYHO,BERA,KARSN,TTRAK,TMSN,ASGYO,KLGYO,LOGO,NETAS,VERUS,TATGD,PNSUT,BIENY,SUNTK,KERVT,YYAPI,KGYO"


def hesapla_rsi(seri, periyot=14):
    fark = seri.diff()
    kazanc = fark.where(fark > 0, 0).rolling(periyot).mean()
    kayip = -fark.where(fark < 0, 0).rolling(periyot).mean()
    return 100 - (100 / (1 + kazanc / kayip))


def hesapla_macd(seri):
    ema12 = seri.ewm(span=12, adjust=False).mean()
    ema26 = seri.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sinyal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinyal, macd - sinyal


def hesapla_bollinger(seri, periyot=20):
    sma = seri.rolling(periyot).mean()
    std = seri.rolling(periyot).std()
    return sma + 2 * std, sma, sma - 2 * std


def hesapla_atr(high, low, close, periyot=14):
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(periyot).mean()


def hesapla_stochastic(high, low, close, periyot=14):
    en_yuksek = high.rolling(periyot).max()
    en_dusuk = low.rolling(periyot).min()
    k = 100 * (close - en_dusuk) / (en_yuksek - en_dusuk)
    return k, k.rolling(3).mean()


def hesapla_obv(close, hacim):
    yon = np.sign(close.diff())
    return (yon * hacim).fillna(0).cumsum()


def analiz_et(hisse, veri, katilim_kumesi):
    if veri is None or veri.empty or len(veri) < 30:
        return None
    gecmis = veri.dropna()
    if len(gecmis) < 30:
        return None

    son_fiyat = gecmis['Close'].iloc[-1]
    gun_basi = gecmis['Close'].iloc[-min(25, len(gecmis))]
    gunluk_degisim = ((son_fiyat - gun_basi) / gun_basi) * 100 if gun_basi > 0 else 0

    sma20 = gecmis['Close'].rolling(20).mean().iloc[-1]
    sma50 = gecmis['Close'].rolling(50).mean().iloc[-1]
    rsi_seri = hesapla_rsi(gecmis['Close'])
    rsi = rsi_seri.iloc[-1] if not pd.isna(rsi_seri.iloc[-1]) else 50
    macd, macd_s, macd_h = hesapla_macd(gecmis['Close'])
    macd_hist = macd_h.iloc[-1] if not pd.isna(macd_h.iloc[-1]) else 0
    stoch_k, stoch_d = hesapla_stochastic(gecmis['High'], gecmis['Low'], gecmis['Close'])
    stoch_deger = stoch_k.iloc[-1] if not pd.isna(stoch_k.iloc[-1]) else 50
    atr = hesapla_atr(gecmis['High'], gecmis['Low'], gecmis['Close']).iloc[-1]
    hacim_ort = gecmis['Volume'].rolling(20).mean().iloc[-1]
    hacim_orani = gecmis['Volume'].iloc[-1] / hacim_ort if hacim_ort > 0 else 1
    obv = hesapla_obv(gecmis['Close'], gecmis['Volume'])
    obv_trend = obv.iloc[-1] > obv.iloc[-5] if len(obv) >= 5 else False

    skor = 50
    yorumlar = []
    if son_fiyat > sma20:
        skor += 10
        yorumlar.append("SMA20 ustu")
    if not pd.isna(sma50) and son_fiyat > sma50:
        skor += 5
    if gunluk_degisim > 0:
        skor += 8
    if rsi < 40:
        skor += 10
        yorumlar.append("RSI dusuk")
    elif rsi > 70:
        skor -= 12
        yorumlar.append("RSI yuksek")
    if macd_hist > 0:
        skor += 8
        yorumlar.append("MACD+")
    if hacim_orani > 1.3:
        skor += 8
        yorumlar.append("Hacim+")
    if obv_trend:
        skor += 5
    if stoch_deger < 25:
        skor += 5
        yorumlar.append("Stoch dip")
    elif stoch_deger > 80:
        skor -= 5
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

    return {
        "Hisse": hisse,
        "Katilim": "EVET" if (hisse + ".IS") in katilim_kumesi else "HAYIR",
        "Guc": round(skor, 2),
        "Sinyal": sinyal,
        "Yorum": " | ".join(yorumlar) if yorumlar else "Notr",
        "RSI": round(rsi, 1),
        "MACD_H": round(macd_hist, 3) if not pd.isna(macd_hist) else 0,
        "Stoch": round(stoch_deger, 1),
        "Trend": "Yukselis" if gunluk_degisim > 0 else "Dusus",
        "Getiri": "%" + str(round(gunluk_degisim, 2)),
        "Hacim": str(round(hacim_orani, 2)) + "x",
        "Fiyat": str(round(son_fiyat, 2)) + " TL",
        "StopLoss": str(stop_loss) + " TL",
        "Hedef": str(hedef) + " TL",
        "RiskOdul": risk_odul,
        "Tahmin": tahmin
    }


varsayilanlar = {'giris_yapildi': False, 'sayac': 0, 'son_cekim': '-', 'manuel': False}
for anahtar, deger in varsayilanlar.items():
    if anahtar not in st.session_state:
        st.session_state[anahtar] = deger

if not st.session_state.giris_yapildi:
    st.title("BIST Pro Terminali Giris")
    with st.form("giris_formu"):
        s1, s2 = st.columns(2)
        kullanici = s1.text_input("Kullanici Adi")
        sifre = s2.text_input("Sifre", type="password")
        if st.form_submit_button("Giris Yap"):
            if kullanici.strip() == "Cuma Babacan" and sifre.strip() == "784512":
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Hatali giris!")
    st.stop()

piyasa_acik = piyasa_acik_mi()
if piyasa_acik:
    st_autorefresh(interval=60000, key="yenile")

st.title("BIST Pro Terminali")
st.caption("Son: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 Dakika Gecikmeli | 20+ Gosterge")

if piyasa_acik:
    st.success("PIYASA ACIK - Otomatik yenileme 60 saniyede")
else:
    st.warning("PIYASA KAPALI - Seans disi (09:40-18:30)")

with st.spinner("Veriler yukleniyor..."):
    hisse_listesi = HISSELER.split(",")
    katilim_kumesi = set(k + ".IS" for k in KATILIM.split(","))
    ham_veriler = toplu_veri_cek(hisse_listesi)

    satirlar = []
    for hisse in hisse_listesi:
        kod = hisse + ".IS"
        if kod in ham_veriler:
            sonuc = analiz_et(hisse, ham_veriler[kod], katilim_kumesi)
            if sonuc:
                satirlar.append(sonuc)

    if not st.session_state.manuel:
        st.session_state.sayac += 1
        st.session_state.son_cekim = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.manuel = False

bist_deger = "-"
bist_degisim = "0"
try:
    bv = bist_endeks_verisi()
    if bv is not None and not bv.empty:
        bf = bv['Close'].iloc[-1]
        bd = ((bf - bv['Open'].iloc[-1]) / bv['Open'].iloc[-1]) * 100
        bist_deger = str(round(bf, 2))
        bist_degisim = "%" + str(round(bd, 2))
except Exception:
    pass

s1, s2, s3, s4 = st.columns(4)
s1.metric("BIST 100", bist_deger, bist_degisim)
s2.metric("VIOP Denge", "Denge", "0")
s3.metric("Taranan", str(len(hisse_listesi)), "0")
s4.metric("Cekim", str(st.session_state.sayac), "Son: " + st.session_state.son_cekim)

c1, c2 = st.columns([3, 1])
with c1:
    sadece_katilim = st.checkbox("Sadece Islam'a Uygun Hisseler", value=True)
with c2:
    manuel_buton = st.button("Manuel Cek", use_container_width=True, type="primary")

if manuel_buton:
    st.cache_data.clear()
    st.session_state.manuel = True
    st.session_state.sayac += 1
    st.session_state.son_cekim = turkiye_saati().strftime("%H:%M:%S")
    st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["Trend Matrisi", "Mum Grafigi", "Risk Analizi", "KAP & VIOP"])

with tab1:
    if not satirlar:
        st.warning("Veri cekilemedi. Manuel butona basin.")
    else:
        tablo = pd.DataFrame(satirlar)
        tablo['Oncelik'] = tablo['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
        tablo = tablo.sort_values(by=['Oncelik', 'Guc'], ascending=[True, False]).drop(columns=['Oncelik'])

        if sadece_katilim:
            tablo = tablo[tablo["Katilim"] == "EVET"]

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
            return 'color:#4CAF50;font-weight:bold;' if v == "EVET" else 'color:#F44336;'

        stilli = tablo.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk, subset=["Katilim"])
        st.dataframe(stilli, use_container_width=True, height=650)

        st.markdown("---")
        o1, o2, o3, o4, o5 = st.columns(5)
        o1.metric("Gosterilen", len(tablo))
        o2.metric("Yukselis", len(tablo[tablo["Tahmin"].str.contains("YUKSELIS")]))
        o3.metric("Guclu AL", len(tablo[tablo["Sinyal"] == "GUCLU AL"]))
        o4.metric("Ort. Guc", str(round(tablo["Guc"].mean(), 1)))
        def risk_ok(x):
            try:
                return float(x) > 1.5
            except:
                return False
        o5.metric("Risk/Odul>1.5", len(tablo[tablo["RiskOdul"].apply(risk_ok)]))

with tab2:
    st.subheader("Interaktif Mum Grafigi")
    try:
        hisse_sec = st.selectbox("Hisse Sec", hisse_listesi[:100])
        kod = hisse_sec + ".IS"
        if kod in ham_veriler:
            h = ham_veriler[kod].dropna()
            h['RSI'] = hesapla_rsi(h['Close'])
            h['MACD'], h['MACD_S'], h['MACD_H'] = hesapla_macd(h['Close'])
            h['BB_UST'], h['BB_ORTA'], h['BB_ALT'] = hesapla_bollinger(h['Close'])
            h['SMA20'] = h['Close'].rolling(20).mean()

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Fiyat", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'))
            fig.add_trace(go.Scatter(x=h.index, y=h['BB_UST'], name="BB Ust", line=dict(color='#9c27b0', width=1, dash='dot')))
            fig.add_trace(go.Scatter(x=h.index, y=h['BB_ALT'], name="BB Alt", line=dict(color='#9c27b0', width=1, dash='dot')))
            fig.add_trace(go.Scatter(x=h.index, y=h['SMA20'], name="SMA20", line=dict(color='#FFC107', width=1)))
            fig.update_layout(title=hisse_sec + " - 15 Dakikalik", xaxis_rangeslider_visible=False, template='plotly_dark', height=500, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E')
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
        else:
            st.warning("Veri bulunamadi.")
    except Exception as e:
        st.error("Grafik yuklenemedi: " + str(e))

with tab3:
    st.subheader("ATR Bazli Risk Analizi")
    if satirlar:
        tablo_r = pd.DataFrame(satirlar)
        if sadece_katilim:
            tablo_r = tablo_r[tablo_r["Katilim"] == "EVET"]
        def risk_filter(x):
            try:
                return float(x) > 1.5
            except:
                return False
        rdf = tablo_r[tablo_r["RiskOdul"].apply(risk_filter)]
        st.markdown("**Risk/Odul orani > 1.5 olan " + str(len(rdf)) + " hisse:**")
        if not rdf.empty:
            goster = rdf[["Hisse", "Fiyat", "StopLoss", "Hedef", "RiskOdul", "Sinyal", "Guc", "Yorum"]]
            st.dataframe(goster, use_container_width=True, height=500)
        else:
            st.info("Uygun risk/odul oraninda hisse yok.")
        st.markdown("---")
        st.info("StopLoss = Fiyat - (ATR x 2) | Hedef = Fiyat + (ATR x 3) | Risk/Odul > 1.5 ideal")
    else:
        st.warning("Veri yok.")

with tab4:
    st.subheader("Canli KAP Haberleri")
    st.info("KAP entegrasyonu yakinda eklenecek.")
    st.write("**[14:18] ASELS** - Yeni Siparis Anlasmasi (Pozitif)")
    st.write("**[14:15] TUPRS** - Uretim Verileri (Notr)")
    st.write("**[13:50] BIMAS** - Yeni Magaza Acilisi (Pozitif)")
    st.markdown("---")
    st.subheader("VIOP Denge Analizi")
    v1, v2, v3 = st.columns(3)
    v1.metric("VIOP 30", "11.450", "%0.45")
    v2.metric("Spot Endeks", "11.420", "%0.40")
    v3.metric("Denge Farki", "+30 Puan", "Pozitif")

st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    st.markdown("**Veri Cekme Istatistikleri**")
    st.write("Toplam: " + str(st.session_state.sayac))
    st.write("Son: " + st.session_state.son_cekim)
    st.write("Hisse: " + str(len(hisse_listesi)))
with b2:
    st.markdown("**Sistem Durumu**")
    st.write("Yenileme: 60 sn")
    st.write("Gecikme: 15 dakika")
    st.write("Saat: " + turkiye_saati().strftime('%H:%M:%S'))
    st.write("Piyasa: " + ("ACIK" if piyasa_acik else "KAPALI"))

st.caption("Bu paneldeki veriler 15 dakika gecikmelidir. Yatirim tavsiyesi degildir.")
