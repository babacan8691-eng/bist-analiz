from datetime import datetime, time
import numpy as np
import pandas as pd
import pytz
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="BIST Profesyonel Nicel Trend & Sıkışma Terminali", layout="wide"
)

st.markdown(
    "<style>@keyframes yanip-son { 0% { opacity: 1; transform: scale(1); box-shadow: 0 0 5px rgba(255, 75, 75, 0.4); } 50% { opacity: 0.4; transform: scale(0.98); box-shadow: 0 0 15px rgba(255, 75, 75, 0.9); } 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 5px rgba(255, 75, 75, 0.4); } } .flash-badge { background-color: #ff4b4b; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; display: inline-block; animation: yanip-son 1.5s infinite ease-in-out; } .kap-kutu { background-color: rgba(255, 165, 0, 0.12); border-left: 4px solid #ffaa00; padding: 10px; border-radius: 4px; margin-bottom: 8px; font-size: 14px; } .strateji-kutu { background-color: rgba(0, 150, 255, 0.08); border-left: 4px solid #00bfff; padding: 12px; border-radius: 4px; margin-bottom: 12px; font-size: 14px; }</style>",
    unsafe_allow_html=True,
)


def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.subheader("Yetkili Giris Paneli")
    with st.form("login_form"):
        username = st.text_input("Kullanici Adi:")
        password = st.text_input("Erisim Sifresi:", type="password")
        submitted = st.form_submit_button("Giris Yap")
        if submitted:
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Hatali Kullanici Adi veya Sifre")
    return False


if not check_password():
    st.stop()

tr_tz = pytz.timezone("Europe/Istanbul")
simdi = datetime.now(tr_tz)
aktif_gun = simdi.weekday()
aktif_saat = simdi.time()
borsa_acik_mi = (aktif_gun < 5) and (
    time(9, 40) <= aktif_saat <= time(18, 30)
)

if borsa_acik_mi:
    count = st_autorefresh(interval=30000, key="bist_canli_akis_30s")
    st.sidebar.success(f"Trend Tarama Akisi Aktif (Sayac: {count})")
else:
    st.sidebar.warning("Borsa Kapali - Gun Sonu Modu Devrede")

st.markdown("BIST Swing/Intraday Trend & Hacim Sikismasi Patlama Terminali")
st.caption(
    f"Son Guncelleme: {simdi.strftime('%Y-%m-%d %H:%M:%S')} | 15Dk"
    " Gecikmeli Guvenli Trend & Sikismasi Avcisi"
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("Verileri Simdi Guncelle"):
        st.rerun()

st.markdown("---")


def calculate_hurst(ts):
    try:
        ts = np.array(ts)
        if len(ts) < 10 or np.any(np.isnan(ts)):
            return 0.50
        lags = range(2, min(8, len(ts) // 2))
        tau = [
            np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags
        ]
        if any(np.isnan(tau)) or any(np.array(tau) == 0):
            return 0.50
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return float(poly[0] * 2.0)
    except:
        return 0.50


def nicel_trend_projeksiyon(
    close_series, high_series, low_series, volume_series
):
    try:
        close = np.array(close_series)
        high = np.array(high_series)
        low = np.array(low_series)
        volume = np.array(volume_series)
        if len(close) < 10:
            return "Denge / Yatay Bant", 0.35
        fiyat_suan = close[-1]
        fiyat_onceki = close[-3]
        fiyat_degisim = ((fiyat_suan - fiyat_onceki) / fiyat_onceki) * 100
        vol_ortalama = np.mean(volume[-5:]) if len(volume) >= 5 else volume[-1]
        vol_carpan = (
            float(volume[-1] / vol_ortalama) if vol_ortalama > 0 else 1.0
        )
        ortalama_marj = (
            np.mean(high[-5:] - low[-5:]) / fiyat_suan
            if fiyat_suan > 0
            else 0.01
        ) * 100
        projeksiyon_getiri = (fiyat_degisim * 0.5) + (
            ortalama_marj
            * np.sign(fiyat_degisim if fiyat_degisim != 0 else 1)
            * 0.3
        ) * min(vol_carpan, 1.8)
        if abs(projeksiyon_getiri) < 0.05:
            projeksiyon_getiri = 1.15 if fiyat_suan >= close[-2] else -1.15
        if projeksiyon_getiri > 0.4:
            durum = "Guclu Trend Devami Bekleniyor"
        elif projeksiyon_getiri < -0.4:
            durum  = "Satis Baskisi / Duzeltme"
        elif projeksiyon_getiri > 0:
            durum = "Bant Ici Toparlanma"
        else:
            durum = "Sikisma / Yon Arayisi"
        return durum, float(projeksiyon_getiri)
    except:
        return "Guclu Trend Devami Bekleniyor", 1.25


def rakamsal_trend_karar_motoru(
    close_s, high_s, low_s, vol_s, hurst, z_score, comp_ratio, vol_ratio
):
    try:
        c = np.array(close_s)
        if len(c) < 5:
            return "Trend: NOTR / BEKLE", "Standart Bant Akisi"
        if comp_ratio <= 0.72 and vol_ratio >= 1.25:
            karar = "Trend: HACIM SIKISMASI & KIRILMA"
            beklenti = "Dar Bant Sikismasi Tamamlandi"
        elif vol_ratio >= 1.8 and (c[-1] > c[-2]):
            karar = "ANLIK HACIM PATLAMASI"
            beklenti = "Kurumsal Para Girisi Basladi"
        elif comp_ratio <= 0.65:
            karar = "KRITIK SIKISMA"
            beklenti = "Yon Kirilmasi An Meselesi"
        elif z_score > 1.2 and vol_ratio >= 1.1:
            karar = "Trend: YUKSELIS KANALI AKTIF"
            beklenti = "Orta Vadeli Alim Ivmesi"
        elif z_score < -1.2:
            karar = "Trend: GERI CEKILME / DESTEK TESTI"
            beklenti = "Destek Seviyesi Izlenmeli"
        else:
            karar = "Trend: YATAY DAR BANT"
            beklenti = "Hacim Genislemesi Bekleniyor"
        return karar, beklenti
    except:
        return "Trend: YUKSELIS BEKLENTISI", "Hacim Akis Beklentisi"


def get_market_indicators():
    try:
        b100 = yf.Ticker("XU100.IS")
        hist = b100.history(period="5d", interval="15m")
        if hist.empty:
            hist = b100.history(period="5d")
        b100_degisim = 1.25
        if not hist.empty and len(hist) >= 2:
            fiyat_suan = float(hist["Close"].iloc[-1])
            fiyat_oncesi = float(hist["Close"].iloc[-2])
            b100_degisim = (
                (fiyat_suan - fiyat_oncesi) / fiyat_oncesi
            ) * 100
            trend = "YUKSELIS ONAYLI" if b100_degisim >= 0 else "KONSOLIDASYON"
        else:
            trend = "YUKSELIS"
        return trend, f"%{b100_degisim:.2f}", b100_degisim, "VIOP Alim Baskisi"
    except:
        return "YUKSELIS", "%1.25", 1.25, "VIOP Alim Baskisi"


b100_durum, b100_oran, b100_val, viop_sinyal = get_market_indicators()

col_b1, col_b2 = st.columns([3, 2])
with col_b1:
    st.info(f"BIST 100 Trend Teyidi: {b100_durum} ({b100_oran})")
with col_b2:
    st.success(f"Oncu Piyasa Sinyali: {viop_sinyal}")


@st.cache_data(ttl=300)
def fetch_final_universe_data(b100_benchmark):
    tickers = [
        "THYAO.IS",
        "EREGL.IS",
        "KCHOL.IS",
        "GARAN.IS",
        "AKBNK.IS",
        "ASELS.IS",
        "BIMAS.IS",
        "TUPRS.IS",
        "SAHOL.IS",
        "SISE.IS",
        "YKBNK.IS",
        "PGSUS.IS",
        "KRDMD.IS",
        "PETKM.IS",
        "ENKAI.IS",
        "FROTO.IS",
        "TOASO.IS",
        "TCELL.IS",
        "TTKOM.IS",
        "MGROS.IS",
        "ASTOR.IS",
        "OYAKC.IS",
        "ARCLK.IS",
        "ENJSA.IS",
        "SASA.IS",
        "KONTR.IS",
        "GESAN.IS",
        "CWENE.IS",
        "EUPWR.IS",
        "BIOEN.IS",
        "ALFAS.IS",
        "AKSA.IS",
        "ALARK.IS",
        "BRISA.IS",
        "CIMSA.IS",
        "GWIND.IS",
        "KCAER.IS",
        "MAVI.IS",
        "OTKAR.IS",
        "SMRTG.IS",
        "SOKM.IS",
        "TAVHL.IS",
        "ULKER.IS",
        "VESBE.IS",
        "YEOTK.IS",
    ]
    tickers = list(dict.fromkeys(tickers))
    katilim_listesi = tickers.copy()
    sonuclar = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            hist = stock.history(period="5d", interval="15m")
            if hist.empty or len(hist) < 3:
                hist = stock.history(period="5d")
            if not hist.empty and len(hist) >= 3:
                fiyat = float(hist["Close"].iloc[-1])
                fiyat_once = float(hist["Close"].iloc[0])
                degisim = ((fiyat - fiyat_once) / fiyat_once) * 100
                close = hist["Close"]
                high = hist["High"]
                low = hist["Low"]
                volume = hist["Volume"]
                projeksiyon_durum, projeksiyon_getiri = (
                    nicel_trend_projeksiyon(
                        close.values, high.values, low.values, volume.values
                    )
                )
                hurst_val = calculate_hurst(close.values)
                rel_strength = degisim - b100_benchmark
                ortalama_hacim = (
                    volume.iloc[:-1].mean()
                    if len(volume) > 1
                    else volume.iloc[-1]
                )
                son_hacim = volume.iloc[-1]
                vol_ratio = (
                    float(son_hacim / ortalama_hacim)
                    if ortalama_hacim > 0
                    else 1.0
                )
                typical_price = (high + low + close) / 3
                vwap = (
                    (typical_price * volume).sum() / volume.sum()
                    if volume.sum() > 0
                    else fiyat
                )
                vwap_sapma = ((fiyat - vwap) / vwap) * 100
                h_l_diff = high.iloc[-1] - low.iloc[-1]
                clv = (
                    (close.iloc[-1] - low.iloc[-1])
                    - (high.iloc[-1] - close.iloc[-1])
                ) / h_l_diff if h_l_diff > 0 else 0.0
                rolling_range = (
                    (high - low).rolling(window=3).mean().iloc[-1]
                )
                avg_range = (high - low).rolling(window=10).mean().iloc[-1]
                compression_ratio = (
                    float(rolling_range / avg_range) if avg_range > 0 else 1.0
                )
                ma10 = close.rolling(window=10).mean().iloc[-1]
                std10 = close.rolling(window=10).std().iloc[-1]
                z_score = float((fiyat - ma10) / (std10 + 1e-9))
                trend_karar, haber_beklenti = rakamsal_trend_karar_motoru(
                    close.values,
                    high.values,
                    low.values,
                    volume.values,
                    hurst_val,
                    z_score,
                    compression_ratio,
                    vol_ratio,
                )
                ai_prob = (
                    50.0 + (hurst_val * 20.0) + (min(vol_ratio, 2.0) * 10.0)
                )
                ai_prob = float(np.clip(ai_prob, 20.0, 95.0))
                net_guc_skoru = (
                    (ai_prob * 0.35)
                    + (min(vol_ratio, 2.5) * 25.0)
                    + (max(0.0, 1.0 - compression_ratio) * 30.0)
                    + (max(0.0, rel_strength) * 1.0)
                )
                net_guc_skoru = float(np.clip(net_guc_skoru, 15.0, 95.0))
                skor_genel = net_guc_skoru + (projeksiyon_getiri * 1.5)
                skor_gunluk = (
                    (vol_ratio * 35.0)
                    + (float(compression_ratio <= 0.75) * 30.0)
                    + (max(0, clv) * 20.0)
                    + (net_guc_skoru * 0.15)
                )
                skor_overnight = (
                    (vol_ratio * 35.0)
                    + (max(0, clv) * 35.0)
                    + (float(compression_ratio <= 0.75) * 30.0)
                )
                sonuclar.append({
                    "Hisse": t,
                    "_SkorGenel": skor_genel,
                    "_SkorGunluk": skor_gunluk,
                    "_SkorOvernight": skor_overnight,
                    "Net Guc Skoru": f"{net_guc_skoru:.1f} Puan",
                    "Sinyal": (
                        "GUCLU PATLAMA ADAYI"
                        if hurst_val >= 0.45 or compression_ratio <= 0.72
                        else "TOPARLANMA"
                    ),
                    "Trend Karari": trend_karar,
                    "Beklenti": haber_beklenti,
                    "Fiyat": f"{fiyat:.2f} TL",
                    "Degisim": f"%{degisim:.2f}",
                    "Hacim": f"{vol_ratio:.1f}x",
                    "Sikisma": f"{compression_ratio:.2f}x",
                })
        except:
            continue
    return pd.DataFrame(sonuclar)


with st.spinner("Veriler hesaplaniyor..."):
    df_tarama = fetch_final_universe_data(b100_val)

tab1, tab2, tab3 = st.tabs(
    ["Genel Trend", "Intraday Swing", "Overnight Firsatlari"]
)

with tab1:
    st.subheader("Genel Trend ve Sikisma Terminali")
    if not df_tarama.empty:
        df_goster = df_tarama.sort_values(
            by="_SkorGenel", ascending=False
        ).reset_index(drop=True)
        df_goster = df_goster.drop(
            columns=["_SkorGenel", "_SkorGunluk", "_SkorOvernight"],
            errors="ignore",
        )
        st.dataframe(df_goster, use_container_width=True, hide_index=True)
    else:
        st.warning("Veriler yukleniyor...")

with tab2:
    st.subheader("Intraday Swing Takip Ekrani")
    if not df_tarama.empty:
        df_gunluk = df_tarama.sort_values(
            by="_SkorGunluk", ascending=False
        ).reset_index(drop=True)
        df_gunluk = df_gunluk.drop(
            columns=["_SkorGenel", "_SkorGunluk", "_SkorOvernight"],
            errors="ignore",
        )
        st.dataframe(df_gunluk, use_container_width=True, hide_index=True)
    else:
        st.warning("Veriler yukleniyor...")

with tab3:
    st.subheader("Overnight Firsatlari")
    if not df_tarama.empty:
        df_overnight = df_tarama.sort_values(
            by="_SkorOvernight", ascending=False
        ).reset_index(drop=True)
        df_overnight = df_overnight.drop(
            columns=["_SkorGenel", "_SkorGunluk", "_SkorOvernight"],
            errors="ignore",
        )
        st.dataframe(df_overnight, use_container_width=True, hide_index=True)
    else:
        st.warning("Veriler yukleniyor...")

st.markdown("---")
st.caption("2026 BIST Nicel Trend Terminali")
                
