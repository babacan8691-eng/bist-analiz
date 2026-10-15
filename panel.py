import streamlit as st
import pandas as pd
import sqlite3

# 1. Panel Genel Tasarım Ayarları
st.set_page_config(page_title="Otonom GPU Arbitraj Paneli", layout="wide")

# 2. Güvenli Giriş (Authentication) Mekanizması
def giris_ekrani():
    st.markdown("<h2 style='text-align: center;'>🔒 GPU Arbitraj Kontrol Paneli Girişi</h2>", unsafe_allow_html=True)
    
    # Giriş formu tasarımı
    with st.form("login_form"):
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        giris_butonu = st.form_submit_button("Sisteme Giriş Yap")
        
        if giris_butonu:
            # .strip() sayesinde kullanıcı adının veya şifrenin sonundaki gizli boşluklar otomatik silinir
            temiz_kullanici = kullanici_adi.strip()
            temiz_sifre = sifre.strip()
            
            # Tam ve kesin bilgilerle doğrulama
            if temiz_kullanici == "Cuma Babacan" and temiz_sifre == "784512":
                st.session_state["oturum_acik"] = True
                st.success("Giriş başarılı! Panel yükleniyor...")
                st.rerun()
            else:
                st.error("Hatalı Kullanıcı Adı veya Şifre! Erişim reddedildi.")

# Oturum durum kontrolü
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    giris_ekrani()
else:
    # 3. BAŞARILI GİRİŞ SONRASI AÇILACAK ANA PANEL
    st.sidebar.markdown(f"👤 **Kullanıcı:** Cuma Babacan")
    if st.sidebar.button("Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()

    st.title("🤖 Otonom Bilişim Altyapısı & GPU Arbitraj Kontrol Merkezi")
    st.caption("İslami Finans İlkelerine Uygun - Tam Otonom Alt Kiralama Döngüsü")
    st.markdown("---")

    # Üst Metrik Kartları
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Toplam Sermaye", value="$500.00")
    with col2:
        st.metric(label="Aktif Kiralanan Emtia (GPU)", value="3 Adet")
    with col3:
        st.metric(label="Ortalama Saatlik Kâr Marjı", value="%38.5")
    with col4:
        st.metric(label="Bugünkü Net Kâr", value="$14.20", delta="+12%")

    st.markdown("---")

    # Gerçek Veritabanından (arbitraj.db) Aktif Kontratları Çekme Bölümü
    st.subheader("⚡ Aktif Alt Kiralama (Re-Lease) Sözleşmeleri")
    
    try:
        conn = sqlite3.connect("arbitraj.db")
        df = pd.read_sql_query("SELECT id as 'Sunucu ID', donanim as 'Donanım', alis_fiyati as 'Alış Fiyatı (Saat)', satis_fiyati as 'Satış Fiyatı (Saat)', durum as 'Anlık Durum' FROM kontratlar", conn)
        conn.close()
        
        if df.empty:
            st.info("Şu an havuzda aktif bir kiralama sözleşmesi bulunmuyor. Bot arka planda ucuz GPU aramaya devam ediyor.")
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.warning("Veritabanı bağlantısı bekleniyor... Bot ilk alımı yaptığında veriler burada listelenecektir.")
        
