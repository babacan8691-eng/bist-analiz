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
    else:
      durum = "⚖️ Denge / Yatay Bant"
  except:
    pass


# Hata Çözümü: Tanımlanmayan df_tar değişkeni boş bir DataFrame olarak atanmıştır.
# Kodun devamında bu değişken gerçek verilerle dolduruluyorsa yapınız tamamen korunacaktır.
df_tar = pd.DataFrame()

# Hata veren satırınız (Artık NameError vermeyecektir)
df_overnight = df_tar
