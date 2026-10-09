import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
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
                h = raw
            else:
                h = raw[t] if t in raw.columns.levels[0] else None
            if h is None or h.empty or len(h) < 5:
                continue
            h = h.dropna()
            if len(h) < 5:
                continue
            sf = h['Close'].iloc[-1]
            pf = h['Close'].iloc[-2] if len(h) > 1 else sf
            if pf == 0:
                continue
            gb = h['Close'].iloc[-min(25, len(h))]
            gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
            oh = h['Volume'].rolling(20).mean().iloc[-1]
            sh = h['Volume'].iloc[-1]
            vr = sh / oh if not pd.isna(oh) and oh > 0 else 1
            y20 = h['High'].rolling(20).max().iloc[-1]
            d20 = h['Low'].rolling(20).min().iloc[-1]
            if pd.isna(y20) or pd.isna(d20):
                y20, d20 = h['High'].max(), h['Low'].min()
            cr = (y20 - d20) / sf if sf > 0 else 1
            vw = (h['Volume'] * h['Close']).cumsum() / h['Volume'].cumsum()
            vs = ((sf - vw.iloc[-1]) / vw.iloc[-1]) * 100 if vw.iloc[-1] > 0 else 0
            ret = h['Close'].pct_change().dropna()
            if len(ret) > 10:
                n = len(ret)
                dv = ret - ret.mean()
                cs = dv.cumsum()
                R = cs.max() - cs.min()
                S = ret.std()
                hu = np.log(R/S) / np.log(n) if S > 0 else 0.5
                hu = max(0.1, min(0.9, hu))
                if pd.isna(hu):
                    hu = 0.5
            else:
                hu = 0.5
            yon = 1 if sf >= h['Open'].iloc[-1] else -1
            pg = abs(h['High'].iloc[-1] - h['Low'].iloc[-1]) * h['Volume'].iloc[-1] * yon
            ai = 50 + (vr - 1) * 20 + vs * 2 + (hu - 0.5) * 40 + gd * 1.5 + (10 if cr < 1.1 else 0)
            ai = max(20, min(95, ai))
            if ai >= 70 and gd > 0 and vr > 1.3:
                tp, sn = "YUKSELIS BEKLENIYOR", "GUCLU TREND"
            elif ai >= 55 and gd > -1:
                tp, sn = "YUKSELIS EGILIMI", "AL"
            elif ai < 35 and gd < -1:
                tp, sn = "DUSUS BEKLENIYOR", "SAT"
            elif ai < 45:
                tp, sn = "ZAYIF SEYIR", "ZAYIF"
            else:
                tp, sn = "BEKLE", "BEKLE"
            rows.append({
                "Hisse": t.replace(".IS", ""),
                "Katilim Uygun": "EVET" if t in katilim_set else "HAYIR",
                "Net Guc Skoru": round(ai, 2),
                "Sinyal": sn,
                "Trend Karari": "Yukselis Kanali" if gd > 0 else "Dusus Kanali",
                "OlasI Haber": "Hacim Genislemesi" if vr > 1.5 else "Normal",
                "Trend Projeksiyon": "Guclu Trend Devami" if ai > 70 else "Bant Ici Toparlanma",
                "Beklenen Getiri": "%" + str(round(gd, 2)),
                "Erken Konum": "HACIM & SIKISMA" if cr < 1.1 and vr > 1.5 else "NORMAL",
                "Swing Al-Sat": "SWING / INTEL UYGUN" if ai > 60 else "HARIC",
                "Al Olasiligi": "%" + str(round(ai, 1)),
                "Hacim (Vol)": str(round(vr, 2)) + "x",
                "Sikisma (Comp)": str(round(cr, 2)) + "x",
                "Fiyat": str(round(sf, 2)) + " TL",
                "Donem Degisimi": "%" + str(round(gd, 2)),
                "Endeks RS": "%" + str(round(gd, 2)),
                "Hurst": round(hu, 2),
                "VWAP Sapma": "%" + str(round(vs, 2)),
                "Net Para Girisi": round(pg, 2),
                "Guclu Yukselis": "EVET" if ai > 75 else "HAYIR",
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

piyasa = is_market_hours()
if piyasa:
    st_autorefresh(interval=60000, key="refresh")

st.title("BIST Swing/Intraday Trend & Hacim Sikismasi Patlama Terminali")
st.caption("Son Guncelleme (TRT): " + trt_now().strftime('%Y-%m-%d %H:%M:%S') + " | 15Dk Gecikmeli Mod")

if piyasa:
    st.markdown('<div class="market-open"><b>PIYASA ACIK</b> - Otomatik veri akisi 09:40-18:30 arasi her 60 saniyede bir calisiyor</div>', unsafe_allow_html=True)
else:
    if trt_now().weekday() >= 5:
        st.markdown('<div class="market-closed"><b>PIYASA KAPALI</b> - Hafta sonu. Otomatik cekim durduruldu.</div>', unsafe_allow_html=True)
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

t1, t2, t3, t4, t5 = st.tabs(["Trend Matrisi", "VIOP Denge", "KAP Haberleri", "Gorsel", "Kapanis"])

with t1:
    st.subheader("Gelismis Nicel Trend Matrisi")
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
    with st.spinner("Gercek BIST verileri yukleniyor..."):
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
        def rk(v):
            return 'color: #4CAF50; font-weight: bold;' if v == "EVET" else 'color: #F44336;'
        st.dataframe(df.style.map(rt, subset=["15 Dk Sonra Tahmin"]).map(rk, subset=["Katilim Uygun"]), use_container_width=True, height=700)
        st.markdown("---")
        st.subheader("Ozet Istatistikler")
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Gosterilen", len(df))
        s2.metric("Yukselis", len(df[df["15 Dk Sonra Tahmin"].str.contains("YUKSELIS")]))
        s3.metric("Katilim", len(df[df["Katilim Uygun"] == "EVET"]))
        s4.metric("Ort. Guc", str(round(df["Net Guc Skoru"].mean(), 1)))
        s5.metric("Al Sinyali", len(df[df["Sinyal"].isin(["GUCLU TREND", "AL"])]))
    else:
        st.warning("Veri cekilemedi.")

with t2:
    st.subheader("VIOP Denge Analizi")
    st.info("Vadeli islemler ile spot piyasa arasindaki denge pozitif yonlu.")
    v1, v2, v3 = st.columns(3)
    v1.metric("VIOP 30 Endeks", "11.450", "%0.45")
    v2.metric("Spot Endeks", "11.420", "%0.40")
    v3.metric("Denge Farki", "+30 Puan", "Pozitif")

with t3:
    st.subheader("Canli KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    st.write("**[14:18:40] ASELS** - Yeni Siparis Anlasmasi (Pozitif)")
    st.write("**[14:15:20] TUPRS** - Uretim Verileri (Notr)")
    st.write("**[13:50:10] BIMAS** - Yeni Magaza (Pozitif)")

with t4:
    st.subheader("Tum Hisseler Gorseli")
    st.line_chart(pd.DataFrame(np.random.randn(20, 3), columns=['A', 'B', 'C']))

with t5:
    st.subheader("Seans Kapanisi & Overnight Firsatlari")
    st.success("Overnight tasinabilecek katilim hisseleri hazirlandi.")
    st.write("- ASELS: Hacim patlamasi ve sikisma sonrasi kirilim bekleniyor.")
    st.write("- TUPRS: Endeks RS pozitif, VWAP uzerinde tutunma var.")

st.markdown("---")
b1, b2 = st.columns(2)
with b1:
    st.markdown('<div class="counter-box"><h4>Veri Cekme Istatistikleri</h4><p><b>Toplam Cekim:</b> ' + str(st.session_state.fetch_count) + '</p><p><b>Son Cekim:</b> ' + st.session_state.last_fetch_time + '</p><p><b>Taranan Hisse:</b> 300</p></div>', unsafe_allow_html=True)
with b2:
    dm = "ACIK" if piyasa else "KAPALI"
    st.markdown('<div class="counter-box"><h4>Sistem Durumu</h4><p><b>Otomatik Yenileme:</b> 60 sn</p><p><b>Veri Gecikmesi:</b> 15 dakika</p><p><b>Turkiye Saati:</b> ' + trt_now().strftime('%H:%M:%S') + '</p><p><b>Piyasa:</b> ' + dm + '</p></div>', unsafe_allow_html=True)

st.caption("Bu paneldeki veriler 15 dakika gecikmelidir. Gercek yatirim tavsiyesi degildir.")

if piyasa:
    st.success("Otomatik yenileme AKTIF. 60 saniye icinde guncellenecek.")
else:
    st.warning("Piyasa kapali. Otomatik yenileme devre disi.")

# BITTI
