import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="BIST Profesyonel Takip Paneli", layout="wide")

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
            # .strip() komutu ile olası yanlışlıkla eklenen boşluklar temizlenir
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("😕 Hatalı Kullanıcı Adı veya Şifre")
    return False

if not check_password():
    st.stop()

st.title("📈 BIST 70 Profesyonel Takip Paneli")
st.write("Hoş geldiniz, Cuma Babacan. Sistem başarıyla aktif edildi, canlı veriler yükleniyor...")

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
    
