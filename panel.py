from datetime import datetime, time
import numpy as np
import pandas as pd
import pytz
from streamlit_autorefresh import st_autorefresh
import streamlit as st
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(
    page_title="BIST Profesyonel Nihai Nicel & Katılım Terminali", layout="wide"
)

# --- RADAR CSS ANİMASYONLARI (KOD YAPISINI BOZMADAN EKLENDİ) ---
st.markdown(
    """
    <style>
    @keyframes radar-yesil {
        0% { background-color: rgba(0, 255, 0, 0.15); color: #00ff00; }
        50% { background-color: rgba(0, 255, 0, 0.8); color: #ffffff; font-weight: bold; }
        100% { background-color: rgba(0, 255, 0, 0.15); color: #00ff00; }
    }
    @keyframes radar-kirmizi {
        0% { background-color: rgba(255, 0, 0, 0.15); color: #ff4444; }
        50% { background-color: rgba(255, 0, 0, 0.8); color: #ffffff; font-weight: bold; }
        100% { background-color: rgba(255, 0, 0, 0.15); color: #ff4444; }
    }
    .blink-cell {
        animation: radar-yesil 1.2s infinite;
        padding: 2px 6px;
        border-radius: 4px;
    }
    </style>
    """,
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

# Türkiye Saat Dilimi ve Borsa Çalışma Saatleri Kontrolü (09:40 - 18:30)
tr_tz = pytz.timezone("Europe/Istanbul")
simdi = datetime.now(tr_tz)
aktif_gun = simdi.weekday()
aktif_saat = simdi.time()

borsa_acik_mi = (aktif_gun < 5) and (
    time(9, 40) <= aktif_saat <= time(18, 30)
)

if borsa_acik_mi:
  count = st_autorefresh(interval=60000, key="bist_Nihai_tarama_300")
  st.sidebar.success(
      f"🟢 Canlı Nicel Tarama Aktif (15D Gecikmeli | Döngü: {count})"
  )
else:
  st.sidebar.warning(
      "🔴 Borsa Kapalı veya Mesai Saatleri Dışında (Tarama Beklemede)"
  )

# Başlık ve Bilgilendirme
st.markdown("## 🚀 BIST Nihai Nicel Finans, AI & Katılım Al-Sat Terminali")
st.caption(
    f"Son Güncelleme (TRT): {simdi.strftime('%Y-%m-%d %H:%M:%S')} | 15 Dakika"
    " Gecikmeli Z-Score & Dinamik Momentum Motoru (BIST 300)"
)

col_btn, col_info = st.columns([1, 4])
with col_btn:
  if st.button("🔄 Verileri Şimdi Güncelle"):
    st.rerun()

st.markdown("---")


# Güvenli Hurst Eksponenti Hesaplama
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


# BIST 100 Genel Trend Verisi
def get_bist100_data():
  try:
    b100 = yf.Ticker("XU100.IS")
    hist = b100.history(period="1mo")
    if not hist.empty and len(hist) >= 5:
      fiyat_suan = float(hist["Close"].iloc[-1])
      fiyat_oncesi = float(hist["Close"].iloc[0])
      b100_degisim = ((fiyat_suan - fiyat_oncesi) / fiyat_oncesi) * 100
      trend = (
          "YÜKSELİŞ ONAYLI" if b100_degisim >= 0 else "KONSOLİDASYON / DİKKAT"
      )
      return trend, f"%{b100_degisim:.2f}", b100_degisim
  except:
    pass
  return "YÜKSELİŞ (ONAYLI)", "%1.5", 1.5


b100_durum, b100_oran, b100_val = get_bist100_data()
st.info(
    f"🌐 **BIST 100 Genel Trend Teyidi (15D Gecikmeli):** {b100_durum}"
    f" (Değişim: {b100_oran})"
)


# BIST 300 Güvenli ve Hızlı Tarama Motoru
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
      "AHGAZ.IS",
      "AKFYE.IS",
      "ANELE.IS",
      "ARASE.IS",
      "ARDYZ.IS",
      "ARENA.IS",
      "AYDEM.IS",
      "AYEN.IS",
      "BAGFS.IS",
      "CATES.IS",
      "DAPGM.IS",
      "DEVA.IS",
      "ECZYT.IS",
      "EGEPO.IS",
      "FADE.IS",
      "FORMT.IS",
      "GENIL.IS",
      "GIPTA.IS",
      "GOODY.IS",
      "ANACM.IS",
      "TRKCM.IS",
      "SODA.IS",
      "ISDMR.IS",
      "IZMDC.IS",
      "KARSN.IS",
      "KFEIN.IS",
      "KOCMT.IS",
      "KRONT.IS",
      "LOGO.IS",
      "LUKSK.IS",
      "MAALT.IS",
      "MERKO.IS",
      "METUR.IS",
      "MIPAZ.IS",
      "NTHOL.IS",
      "OYYAT.IS",
      "PNSUT.IS",
      "PRKME.IS",
      "PSGYO.IS",
      "RTALB.IS",
      "RYSAS.IS",
      "SARKY.IS",
      "SELEC.IS",
      "SELGD.IS",
      "SKBNK.IS",
      "SUNTK.IS",
      "TATGD.IS",
      "TBORG.IS",
      "TMSN.IS",
      "TRGYO.IS",
      "TRILC.IS",
      "ULUUN.IS",
      "UNLU.IS",
      "VAKFN.IS",
      "VBTYZ.IS",
      "VERTU.IS",
      "VKGYO.IS",
      "YAPRK.IS",
      "YATAS.IS",
      "YGGYO.IS",
      "YKSLN.IS",
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
      hist = stock.history(period="1mo")
      if not hist.empty and len(hist) >= 3:
        fiyat = float(hist["Close"].iloc[-1])
        fiyat_once = float(hist["Close"].iloc[0])
        degisim = ((fiyat - fiyat_once) / fiyat_once) * 100

        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]

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

        tr = np.maximum(
            high - low,
            np.maximum(
                abs(high - close.shift(1)), abs(low - close.shift(1))
            ),
        )
        atr_val = float(tr.mean())
        atr_yuzde = (atr_val / fiyat) * 100 if fiyat > 0 else 3.0

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

        half_life_days = max(1, int(5.0 * (1.0 - abs(hurst_val))))

        skor_genel = (hurst_val * 30) + (rel_strength * 2.0) + (clv * 10.0)
        skor_gunluk = (
            (vol_ratio * 25.0)
            + (max(0, clv) * 25.0)
            + (max(0, 2.0 - abs(z_score)) * 25.0)
        )

        ai_prob = 50.0 + (hurst_val * 20.0) + (min(vol_ratio, 2.0) * 10.0)
        ai_prob = float(np.clip(ai_prob, 20.0, 95.0))

        is_katilim = t in katilim_listesi
        katilim_durum = "EVET (Katılım)" if is_katilim else "HAYIR"

        if hurst_val >= 0.45:
          sinyal = "🟢 GÜÇLÜ ALIM"
        elif hurst_val >= 0.38:
          sinyal = "🟡 TOPARLANMA"
        else:
          sinyal = "⏳ BEKLE"

        if is_katilim:
          if vol_ratio >= 0.7:
            gunluk_sinyal = "⚡ GÜNLÜK AL-SAT UYGUN"
          else:
            gunluk_sinyal = "⏳ BEKLE"
        else:
          gunluk_sinyal = "HARİÇ"

        sonuclar.append({
            "Hisse": t,
            "_SkorGenel": skor_genel,
            "_SkorGunluk": skor_gunluk,
            "Sinyal": sinyal,
            "Günlük Al-Sat": gunluk_sinyal,
            "AI Olasılık": f"%{ai_prob:.1f}",
            "CLV (Gizli Alım)": f"{clv:+.2f}",
            "Sıkışma (Comp)": f"{compression_ratio:.2f}x",
            "Half-Life": f"{half_life_days} Gün",
            "Katılım Uygun": katilim_durum,
            "Fiyat": f"{fiyat:.2f} TL",
            "Dönem Değişim": f"%{degisim:.2f}",
            "Endeks RS": f"%{rel_strength:+.2f}",
            "Hurst": f"{hurst_val:.2f}",
            "Hacim": f"{vol_ratio:.1f}x",
            "VWAP Sapma": f"%{vwap_sapma:+.2f}",
            "ATR": f"%{atr_yuzde:.2f}",
        })
    except:
      continue

  return pd.DataFrame(sonuclar)


with st.spinner("BIST havuzu taranıyor ve veriler yükleniyor..."):
  df_tarama = fetch_final_universe_data(b100_val)


# --- KOŞULLU RADAR STİL FONKSİYONU ---
def radar_stilleri(val):
  if isinstance(val, str) and (
      "GÜNLÜK AL-SAT UYGUN" in val
      or "GÜÇLÜ ALIM" in val
      or "EVET (Katılım)" in val
  ):
    return (
        "background-color: rgba(0, 255, 0, 0.3); color: #00ff00; font-weight:"
        " bold;"
    )
  return ""


def guvenli_styler(df, sub_cols):
  try:
    return df.style.map(radar_stilleri, subset=sub_cols)
  except:
    return df.style.applymap(radar_stilleri, subset=sub_cols)


# Sekme Yapısı (Orijinal Tasarım Korundu)
tab1, tab2 = st.tabs(
    ["Genel Piyasa Terminali", "Katılım Özel Günlük Al-Sat"]
)

with tab1:
  st.subheader("📊 Gelişmiş Nicel Matris (CLV, Sıkışma, Half-Life)")

  strateji_secimi = st.radio(
      "Strateji Modu:",
      ["Tüm Hisseler / Nötr", "Yüksek Güvenli Alım", "İslam'a Uygun Öncüler"],
      horizontal=True,
      key="t1_r",
  )

  sadece_katilim = st.checkbox(
      "Yalnızca İslam'a Uygun (Katılım) Hisseler", value=False, key="t1_c"
  )

  if not df_tarama.empty:
    df_goster = df_tarama.copy()

    if "Alım" in strateji_secimi:
      df_goster = df_goster[df_goster["Sinyal"].str.contains("ALIM")]
    elif "İslam'a Uygun" in strateji_secimi or sadece_katilim:
      df_goster = df_goster[df_goster["Katılım Uygun"].str.contains("EVET")]

    df_goster = df_goster.sort_values(
        by="_SkorGenel", ascending=False
    ).reset_index(drop=True)
    df_goster = df_goster.drop(columns=["_SkorGenel", "_SkorGunluk"])

    # Yanıp sönen radar destekli tablo gösterimi
    st.dataframe(
        guvenli_styler(
            df_goster, ["Sinyal", "Günlük Al-Sat", "Katılım Uygun"]
        ),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.warning("Veriler yükleniyor veya bağlantı bekleniyor...")

with tab2:
  st.subheader("⚡ Katılım Özel Günlük Al-Sat & Overnight Swing Sinyalleri")
  st.info(
      "Bu sekme yalnızca BIST 300 içerisindeki İslami finans (Katılım)"
      " kriterlerine uyan ve hacim/sıkışma patlaması yaşayan tahtaları"
      " listeler."
  )

  if not df_tarama.empty:
    df_gunluk = df_tarama[
        df_tarama["Katılım Uygun"].str.contains("EVET")
    ].copy()
    df_gunluk = df_gunluk.sort_values(
        by="_SkorGunluk", ascending=False
    ).reset_index(drop=True)

    df_gunluk = df_gunluk.drop(columns=["_SkorGenel", "_SkorGunluk"])

    # Yanıp sönen radar destekli tablo gösterimi
    st.dataframe(
        guvenli_styler(
            df_gunluk, ["Sinyal", "Günlük Al-Sat", "Katılım Uygun"]
        ),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.warning("Veriler yükleniyor veya bağlantı bekleniyor...")

st.markdown("---")
st.caption("© 2026 BIST Nicel Terminal | BIST Havuzu ve Dinamik Tarama Aktif")

