import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Sayfa Yapılandırması
st.set_page_config(page_title="BIST Profesyonel Takip Paneli", layout="wide")

# Şifre ve Kullanıcı Adı Koruma Mekanizması
def check_password():
    def credentials_entered():
        if st.session_state["username"] == "Cuma Babacan" and st.session_state["password"] == "784512":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.subheader("🔐 Yetkili Giriş Paneli")
        st.text_input("Kullanıcı Adı:", key="username")
        st.text_input("Erişim Şifresi:", type="password", key="password")
        st.button("Giriş Yap", on_click=credentials_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.subheader("🔐 Yetkili Giriş Paneli")
        st.text_input("Kullanıcı Adı:", key="username")
        st.text_input("Erişim Şifresi:", type="password", key="password")
        st.button("Giriş Yap", on_click=credentials_entered)
        st.error("😕 Hatalı Kullanıcı Adı veya Şifre")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Ana Panel İçeriği
st.title("📈 BIST 70 Profesyonel Takip Paneli")
st.write("Hoş geldiniz, Cuma Babacan. Sistem başarıyla aktif edildi, canlı veriler yükleniyor...")

# Örnek BIST Hisseleri
tickers = ["THYAO.IS", "GARAN.IS", "EREGL.IS", "AKBNK.IS", "KCHOL.IS"]

@st.cache_data(ttl=300)
def load_data(hisseler):
    veri_listesi = []
    for h in hisseler:
        try:
            t = yf.Ticker(h)
            hist = t.history(period="1d")
            if not hist.empty:
                fiyat = hist['Close'].iloc[-1]
                veri_listesi.append({"Hisse": h, "Fiyat": fiyat})
        except:
            pass
    return pd.DataFrame(veri_listesi)

df = load_data(tickers)

if not df.empty:
    df["Stop-Loss (-%5)"] = df["Fiyat"] * 0.95
    df["Take-Profit (+%15)"] = df["Fiyat"] * 1.15
    
    st.dataframe(df, use_container_width=True)
else:
    st.warning("Veriler yüklenirken geçici bir sorun oluştu.")
  
