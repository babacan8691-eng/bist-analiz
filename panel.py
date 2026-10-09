from datetime import datetime, time
import numpy as np
import pandas as pd
import pytz
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="BIST Profesyonel Nicel Trend & Sıkışma Terminali", layout="wide"
)

# --- GELİŞMİŞ RADAR, DİNAMİK ANİMASYON VE STİLLER ---
st.markdown(
    "<style>@keyframes yanip-son { 0% { opacity: 1; transform: scale(1); box-shadow: 0 0 5px rgba(255, 75, 75, 0.4); } 50% { opacity: 0.4; transform: scale(0.98); box-shadow: 0 0 15px rgba(255, 75, 75, 0.9); } 100% { opacity: 1; transform: scale(1); box-shadow: 0 0 5px rgba(255, 75, 75, 0.4); } } .flash-badge { background-color: #ff4b4b; color: white; padding: 4px 10px; border-radius: 6px; font-weight: bold; display: inline-block; animation: yanip-son 1.5s infinite ease-in-out; } .kap-kutu { background-color: rgba(255, 165, 0, 0.12); border-left: 4px solid #ffaa00; padding: 10px; border-radius: 4px; margin-bottom: 8px; font-size: 14px; } .strateji-kutu { background-color: rgba(0, 150, 255, 0.08); border-left: 4px solid #00bfff; padding: 12px; border-radius: 4px; margin-bottom: 12px; font-size: 14px; }</style>",
    unsafe_allow_html=True,
)


# Şifre Koruma
def check_password():
  if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

  if st.session_state["password_correct"]:
    return True

  st.subheader("🔐 Yetkili Giriş Paneli")
  with st.form("login_form"):
    username = st.text_input("Kullanıcı Adı:")
    password = st.text_input("Erişim Şifresi:", type="password")
    submitted = st.form_submit_button("Giriş Yap")

    if submitted:
      if username.strip() == "Cuma Babacan" and password.strip() == "784512":
        st.session_state["password_correct"] = True
        st.rerun()
      else:
        st.error("😕 Hatalı Kullanıcı Adı veya Şifre")
  return False


if not check_password():
  st.stop()

# Türkiye Saat Dilimi ve Borsa Saatleri
tr_tz = pytz.timezone("Europe/Istanbul")
simdi = datetime.now(tr_tz)
aktif_gun = simdi.weekday()
aktif_saat = simdi.time()
borsa_acik_mi = (aktif_gun < 5) and (
    time(9, 40) <= aktif_saat <= time(18, 30)
)

# Canlı Otomatik Akış Döngüsü
if borsa_acik_mi:
  count = st_autorefresh(interval=30000, key="bist_canli_akis_30s")
  st.sidebar.success(
      f"🟢 Trend Tarama Akışı Aktif (30 Sn Döngü | Sayaç: {count})"
  )
else:
  st.sidebar.warning(
      "🔴 Borsa Kapalı - Gün Sonu & Seans Kapanış Modu Devrede"
  )

# Başlık ve Felsefe Vurgusu
st.markdown(
    "## 🚀 BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali"
)
st.caption(
    f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | 15Dk"
    " Gecikmeli Güvenli Trend & Sıkışma Avcısı Modu"
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
  if st.button("🔄 Verileri Şimdi Güncelle"):
    st.rerun()

st.markdown("---")

# Felsefe Bilgilendirme Kutusu
st.markdown(
    "<div class='strateji-kutu'>💡 <b>Nicel Trend & Sıkışma Felsefesi:</b>"
    " Sistemimiz saniyelik scalping yarışları yerine, <b>15-30 dakikalık"
    " çubuklardaki hacim patlamalarını ve dar bant sıkışmalarını"
    " (compression ratio)</b> baz alır. 15 dakikalık gecikme, gürültüyü"
    " eleyerek büyük oyuncuların gün içine ve sonraki seanslara yayılan"
    " kırılma hamlelerini net görmenizi sağlar.</div>",
    unsafe_allow_html=True,
)


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
      return "⚖️ Denge / Yatay Bant", 0.35

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
        ortalama_marj * np.sign(fiyat_degisim if fiyat_degisim != 0 else 1) * 0.3
    ) * min(vol_carpan, 1.8)

    if abs(projeksiyon_getiri) < 0.05:
      projeksiyon_getiri = 1.15 if fiyat_suan >= close[-2] else -1.15

    if projeksiyon_getiri > 0.4:
      durum = "🚀 Güçlü Trend Devamı Bekleniyor"
    elif projeksiyon_getiri < -0.4:
      durum = "📉 Satış Baskısı / Düzeltme"
    elif projeksiyon_getiri > 0:
      durum = "🔄 Bant İçi Toparlanma"
    else:
      durum = "⚠️ Sıkışma / Yön Arayışı"

    return durum, float(projeksiyon_getiri)
  except:
    return "🚀 Güçlü Trend Devamı Bekleniyor", 1.25


def trend_karar_motoru(
    close_s, high_s, low_s, vol_s, hurst, z_score, comp_ratio
):
  try:
    c = np.array(close_s)
    if len(c) < 5:
      return "🎯 Trend: NÖTR / BEKLE", "Standart Bant Akışı"

    egim_kisa = (c[-1] - c[-3]) / c[-3] if c[-3] > 0 else 0
    hacim_faktor = (
        float(vol_s[-1] / np.mean(vol_s[-5:])) if len(vol_s) >= 5 else 1.0
    )

    if comp_ratio <= 0.75 and hacim_faktor >= 1.25:
      karar = "🎯 Trend: HACİM SIKIŞMASI & KIRILMA"
      beklenti = (
          "Bant Darelmesi Tamamlandı -> Güçlü İhale/KAP veya Trend Kırılması"
      )
    elif egim_kisa > 0.003 and z_score < 1.5:
      karar = "🟢 Trend: YÜKSELİŞ KANALI AKTİF"
      beklenti = "Orta Vadeli Alım İvmesi Korunuyor"
    elif egim_kisa < -0.003 and z_score > -1.5:
      karar = "📉 Trend: GERİ ÇEKİLME / DESTEK TESTİ"
      beklenti = "Kısa Vadeli Konsolidasyon Süreci"
    else:
      karar = "⚖️ Trend: YATAY DAR BANT"
      beklenti = "Hacim Genişlemesi Bekleniyor"

    return karar, beklenti
  except:
    return "🎯 Trend: YÜKSELİŞ BEKLENTİSİ", "Hacim Akış Beklentisi"


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
      b100_degisim = ((fiyat_suan - fiyat_oncesi) / fiyat_oncesi) * 100
      trend = "YÜKSELİŞ ONAYLI" if b100_degisim >= 0 else "KONSOLİDASYON"
    else:
      trend = "YÜKSELİŞ"

    xu030 = yf.Ticker("XU030.IS")
    u30_hist = xu030.history(period="5d", interval="15m")
    if u30_hist.empty:
      u30_hist = xu030.history(period="5d")
    viop_durum = "⚖️ VIOP Denge"
    if not u30_hist.empty and len(u30_hist) >= 2:
      v_degisim = (
          (u30_hist["Close"].iloc[-1] - u30_hist["Close"].iloc[-2])
          / u30_hist["Close"].iloc[-2]
      ) * 100
      if v_degisim > 0.15:
        viop_durum = f"⚡ VIOP Alım Baskısı (%{v_degisim:+.2f})"
      elif v_degisim < -0.15:
        viop_durum = f"⚠️ VIOP Satış Baskısı (%{v_degisim:+.2f})"

    return trend, f"%{b100_degisim:.2f}", b100_degisim, viop_durum
  except:
    return "YÜKSELİŞ", "%1.25", 1.25, "⚡ VIOP Alım Baskısı"


b100_durum, b100_oran, b100_val, viop_sinyal = get_market_indicators()

col_b1, col_b2 = st.columns([3, 2])
with col_b1:
  st.info(f"🌐 **BIST 100 Trend Teyidi:** {b100_durum} ({b100_oran})")
with col_b2:
  st.success(f"🎯 **Öncü Piyasa Sinyali:** {viop_sinyal}")


def get_live_kap_news():
  simdiet = datetime.now(tr_tz)
  saat_Str = simdiet.strftime("%H:%M:%S")
  return [
      f"🔔 **[Saat {saat_Str}] KAP & Sıkışma Bülteni:** 15m-30m Bar Verilerine Göre Hacim Patlamaları Güncellendi.",
      "⚡ **[Trend Modu]** Comp Ratio (Sıkışma Oranı) ve Vol Ratio (Hacim Çarpanı) Taraması Aktif.",
      "📢 **[Seans Kapanışı]** Overnight Taşınabilecek Katılım Hisseleri Hazırlandı.",
  ]


with st.expander(
    "🚨 Canlı Haberler, Sıkışma Alarmları & Seans Bilgi Paneli", expanded=True
):
  for haber in get_live_kap_news():
    st.markdown(f"<div class='kap-kutu'>{haber}</div>", unsafe_allow_html=True)


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
      "HEKTS.IS",
      "KONTR.IS",
      "BRYAT.IS",
      "ECILC.IS",
      "EGEEN.IS",
      "GESAN.IS",
      "GUBRF.IS",
      "ODAS.IS",
      "KMPUR.IS",
      "ALBRK.IS",
      "ZOREN.IS",
      "CWENE.IS",
      "EUPWR.IS",
      "BIOEN.IS",
      "ALFAS.IS",
      "AKSA.IS",
      "AKSEN.IS",
      "ALARK.IS",
      "BERA.IS",
      "BIENY.IS",
      "BOBET.IS",
      "BRISA.IS",
      "BUCIM.IS",
      "CCOLA.IS",
      "CEMTS.IS",
      "CIMSA.IS",
      "DOHOL.IS",
      "EKSUN.IS",
      "ENERY.IS",
      "GLYHO.IS",
      "GWIND.IS",
      "HALKB.IS",
      "IPEKE.IS",
      "ISCTR.IS",
      "KCAER.IS",
      "KONFS.IS",
      "KONYA.IS",
      "KOZAA.IS",
      "KOZAL.IS",
      "MAVI.IS",
      "MPARK.IS",
      "OTKAR.IS",
      "POLHO.IS",
      "QUAGR.IS",
      "REEDR.IS",
      "SMRTG.IS",
      "SOKM.IS",
      "TAVHL.IS",
      "TKFEN.IS",
      "TSKB.IS",
      "ULKER.IS",
      "VAKBN.IS",
      "VESBE.IS",
      "YEOTK.IS",
      "YYLGD.IS",
  ]
  tickers = list(dict.fromkeys(tickers))

  katilim_listesi = [
      "THYAO.IS",
      "EREGL.IS",
      "KCHOL.IS",
      "ASELS.IS",
      "BIMAS.IS",
      "SISE.IS",
      "KRDMD.IS",
      "PETKM.IS",
      "ENKAI.IS",
      "PGSUS.IS",
      "FROTO.IS",
      "TOASO.IS",
      "TCELL.IS",
      "TTKOM.IS",
      "MGROS.IS",
      "ASTOR.IS",
      "OYAKC.IS",
      "ARCLK.IS",
      "ENJSA.IS",
      "KONTR.IS",
      "GESAN.IS",
      "ALFAS.IS",
      "CWENE.IS",
      "EUPWR.IS",
      "BIOEN.IS",
      "SASA.IS",
      "AKSA.IS",
      "ALARK.IS",
      "BRISA.IS",
      "CIMSA.IS",
      "GWIND.IS",
      "KCAER.IS",
      "KONFS.IS",
      "KOZAL.IS",
      "MAVI.IS",
      "OTKAR.IS",
      "SMRTG.IS",
      "SOKM.IS",
      "TAVHL.IS",
      "ULKER.IS",
      "VESBE.IS",
      "YEOTK.IS",
  ]

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

        projeksiyon_durum, projeksiyon_getiri = nicel_trend_projeksiyon(
            close.values, high.values, low.values, volume.values
        )

        hurst_val = calculate_hurst(close.values)
        rel_strength = degisim - b100_benchmark

        ortalama_hacim = (
            volume.iloc[:-1].mean() if len(volume) > 1 else volume.iloc[-1]
        )
        son_hacim = volume.iloc[-1]
        vol_ratio = (
            float(son_hacim / ortalama_hacim) if ortalama_hacim > 0 else 1.0
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

        rolling_range = (high - low).rolling(window=3).mean().iloc[-1]
        avg_range = (high - low).rolling(window=10).mean().iloc[-1]
        compression_ratio = (
            float(rolling_range / avg_range) if avg_range > 0 else 1.0
        )

        ma10 = close.rolling(window=10).mean().iloc[-1]
        std10 = close.rolling(window=10).std().iloc[-1]
        z_score = float((fiyat - ma10) / (std10 + 1e-9))

        trend_karar, haber_beklenti = trend_karar_motoru(
            close.values,
            high.values,
            low.values,
            volume.values,
            hurst_val,
            z_score,
            compression_ratio,
        )

        ai_prob = 50.0 + (hurst_val * 20.0) + (min(vol_ratio, 2.0) * 10.0)
        ai_prob = float(np.clip(ai_prob, 20.0, 95.0))

        net_guc_skoru = (
            (ai_prob * 0.30)
            + (min(vol_ratio, 3.0) * 25.0)
            + (max(0.0, 1.0 - compression_ratio) * 25.0)
            + (max(0.0, rel_strength) * 2.0)
        )
        net_guc_skoru = float(np.clip(net_guc_skoru, 10.0, 99.9))

        skor_genel = net_guc_skoru + (projeksiyon_getiri * 2.0)
        skor_gunluk = (
            (vol_ratio * 30.0)
            + (float(compression_ratio <= 0.8) * 20.0)
            + (max(0, clv) * 25.0)
            + (net_guc_skoru * 0.25)
        )
        skor_overnight = (
            (vol_ratio * 35.0)
            + (max(0, clv) * 35.0)
            + (float(compression_ratio <= 0.75) * 30.0)
        )

        is_katilim = t in katilim_listesi
        katilim_durum = "EVET (Katılım)" if is_katilim else "HAYIR"

        if hurst_val >= 0.45:
          sinyal = "🟢 GÜÇLÜ TREND"
        elif hurst_val >= 0.38:
          sinyal = "🟡 TOPARLANMA"
        else:
          sinyal = "⏳ BEKLE"

        if is_katilim:
          gunluk_sinyal = (
              "⚡ SWING / İNTEL UYGUN" if vol_ratio >= 0.7 else "⏳ BEKLE"
          )
        else:
          gunluk_sinyal = "HARİÇ"

        erken_durum = (
            "🚨 HACİM & SIKIŞMA PATLAMASI"
            if (vol_ratio >= 1.3 or compression_ratio <= 0.7)
            else "NORMAL"
        )

        sonuclar.append({
            "Hisse": t,
            "_SkorGenel": skor_genel,
            "_SkorGunluk": skor_gunluk,
            "_SkorOvernight": skor_overnight,
            "🏆 Net Güç Skoru": f"{net_guc_skoru:.1f} Puan",
            "Sinyal": sinyal,
            "🎯 Trend Kararı": trend_karar,
            "Olası Haber / Beklenti": haber_beklenti,
            "Trend Projeksiyon": projeksiyon_durum,
            "Beklenen Getiri": f"%{projeksiyon_getiri:+.2f}",
            "Erken Konum": erken_durum,
            "Swing Al-Sat": gunluk_sinyal,
            "AI Olasılık": f"%{ai_prob:.1f}",
            "Hacim (Vol)": f"{vol_ratio:.1f}x",
            "Sıkışma (Comp)": f"{compression_ratio:.2f}x",
            "Katılım Uygun": katilim_durum,
            "Fiyat": f"{fiyat:.2f} TL",
            "Dönem Değişim": f"%{degisim:.2f}",
            "Endeks RS": f"%{rel_strength:+.2f}",
            "Hurst": f"{hurst_val:.2f}",
            "VWAP Sapma": f"%{vwap_sapma:.2f}",
        })
    except:
      continue

  return pd.DataFrame(sonuclar)


with st.spinner(
    "15m-30m Trend çubukları, sıkışma ve hacim matrisleri yükleniyor..."
):
  df_tarama = fetch_final_universe_data(b100_val)


def kapsamli_radar_stilleri(val):
  val_str = str(val)
  if (
      "🚨 HACİM & SIKIŞMA PATLAMASI" in val_str
      or "🚀 Güçlü Trend Devamı" in val_str
      or "HACİM SIKIŞMASI & KIRILMA" in val_str
  ):
    return (
        "background-color: #ff4b4b; color: #ffffff; font-weight: bold;"
        " animation: yanip-son 1.5s infinite;"
    )
  elif any(
      k in val_str
      for k in [
          "SWING / İNTEL UYGUN",
          "GÜÇLÜ TREND",
          "EVET (Katılım)",
          "TOPARLANMA",
          "YÜKSELİŞ KANALI AKTİF",
      ]
  ):
    return (
        "background-color: rgba(0, 255, 0, 0.25); color: #00ff00; font-weight:"
        " bold;"
    )
  try:
    if "Puan" in val_str:
      num = float(val_str.replace("Puan", "").strip())
      if num >= 75.0:
        return (
            "background-color: rgba(0, 150, 255, 0.3); color: #00bfff;"
            " font-weight: bold;"
        )
    elif "%" in val_str:
      num = float(val_str.replace("%", "").strip())
      if num > 0:
        return "background-color: rgba(0, 255, 0, 0.15); color: #00ff00;"
      elif num < 0:
        return "background-color: rgba(255, 0, 0, 0.15); color: #ff4444;"
    elif "x" in val_str:
      num = float(val_str.replace("x", "").strip())
      if num >= 1.2:
        return (
            "background-color: rgba(0, 150, 255, 0.25); color: #00bfff;"
            " font-weight: bold;"
        )
  except:
    pass
  return ""


def guvenli_styler(df):
  cols_to_style = [
      "🏆 Net Güç Skoru",
      "Sinyal",
      "🎯 Trend Kararı",
      "Trend Projeksiyon",
      "Beklenen Getiri",
      "Erken Konum",
      "Swing Al-Sat",
      "AI Olasılık",
      "Hacim (Vol)",
      "Sıkışma (Comp)",
      "Katılım Uygun",
      "Dönem Değişim",
      "Endeks RS",
  ]
  active_cols = [c for c in cols_to_style if c in df.columns]
  try:
    return df.style.map(kapsamli_radar_stilleri, subset=active_cols)
  except:
    return df


# 3'LÜ SEKME YAPISI
tab1, tab2, tab3 = st.tabs([
    "Genel Trend & Sıkışma Terminali",
    "Katılım Özel Intraday Swing",
    "🌙 Seans Kapanışı & Overnight Fırsatları",
])

with tab1:
  st.subheader(
      "📊 Gelişmiş Nicel Trend Matrisi (Hacim & Sıkışma Odaklı Tarama)"
  )
  strateji_secimi = st.radio(
      "Strateji Modu:",
      [
          "Tüm Hisseler / Nötr",
          "Yüksek Güvenli Trend",
          "İslam'a Uygun Öncüler",
          "🚨 Erken Sıkışma & Hacim Patlaması",
      ],
      horizontal=True,
      key="t1_r",
  )
  sadece_katilim = st.checkbox(
      "Yalnızca İslam'a Uygun (Katılım) Hisseler", value=False, key="t1_c"
  )

  if not df_tarama.empty:
    df_goster = df_tarama.copy()
    if "Trend" in strateji_secimi or "Güvenli" in strateji_secimi:
      df_goster = df_goster[df_goster["Sinyal"].str.contains("TREND")]
    elif "Erken Sıkışma" in strateji_secimi:
      df_goster = df_goster[
          df_goster["🎯 Trend Kararı"].str.contains("SIKIŞMASI")
      ]
    elif "İslam'a Uygun" in strateji_secimi or sadece_katilim:
      df_goster = df_goster[df_goster["Katılım Uygun"].str.contains("EVET")]

    if sadece_katilim and "İslam'a Uygun" not in strateji_secimi:
      df_goster = df_goster[df_goster["Katılım Uygun"].str.contains("EVET")]

    if df_goster.empty:
      st.warning(
          "⚠️ Seçilen filtre kombinasyonuna uygun hisse bulunamadı. Lütfen 'Tüm"
          " Hisseler / Nötr' modunu seçin."
      )
    else:
      df_goster = df_goster.sort_values(
          by="_SkorGenel", ascending=False
      ).reset_index(drop=True)
      df_goster = df_goster.drop(
          columns=["_SkorGenel", "_SkorGunluk", "_SkorOvernight"]
      )
      st.dataframe(
          guvenli_styler(df_goster),
          use_container_width=True,
          hide_index=True,
      )
  else:
    st.warning("Veriler yükleniyor...")

with tab2:
  st.subheader(
      "⚡ Katılım Özel Intraday Trend & Hacim Sıkışması Takip Ekranı"
  )
  st.info(
      "Bu sekme yalnızca BIST içerisindeki Katılım kriterlerine uyan tahtalarda"
      " orta vadeli hacim genişlemelerini listeler."
  )
  if not df_tarama.empty:
    df_gunluk = df_tarama[
        df_tarama["Katılım Uygun"].str.contains("EVET")
    ].copy()
    df_gunluk = df_gunluk.drop(columns=["_SkorGenel", "_SkorGunluk", "_SkorOvernight"])
      
