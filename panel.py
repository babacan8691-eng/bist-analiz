import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime

# Sayfa Ayarları (Karanlık Tema ve Geniş Ekran)
st.set_page_config(page_title="BIST Pro Terminali", layout="wide", initial_sidebar_state="collapsed")

# Karanlık Tema CSS
st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .stDataFrame { background-color: #1E1E1E; }
    div[data-testid="stMetricValue"] { font-size: 20px; }
    .stMetric { background-color: #1E1E1E; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- OTOMATİK YENİLEME (Her 60 Saniye) ---
# Bu script sayesinde sayfa her 1 dakikada bir otomatik yenilenir ve veriler tazelenir.
st.markdown(
    """
    <script>
        setTimeout(function(){
           window.location.reload(1);
        }, 60000);
    </script>
    """, unsafe_allow_html=True)

# --- 1. OTURUM AÇMA (LOGIN) MODÜLÜ ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 BIST Pro Terminali Girişi")
    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Kullanıcı Adı")
        with col2:
            password = st.text_input("Şifre", type="password")
        
        submit_button = st.form_submit_button("Giriş Yap")

        if submit_button:
            if username.strip() == "Cuma Babacan" and password.strip() == "784512":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre! Lütfen büyük/küçük harf ve boşluklara dikkat edin.")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- 2. VERİ SİMÜLASYONU (300 HİSSE VE İSLAMİ FİLTRE) ---
@st.cache_data(ttl=60) # Verileri 60 saniye önbelleğe al
def get_mock_data():
    hisseler = [f"HISSE{i}.IS" for i in range(1, 301)]
    bilinen_hisseler = ["ASELS.IS", "TUPRS.IS", "BIMAS.IS", "FROTO.IS", "KCHOL.IS", "SAHOL.IS", "CCOLA.IS", "HEKTS.IS", "BRISA.IS", "SASA.IS"]
    hisseler = bilinen_hisseler + hisseler[:290]
    
    data = []
    for h in hisseler:
        net_guc = random.uniform(20, 95)
        vol = random.uniform(0.5, 3.5)
        comp = random.uniform(0.8, 1.8)
        fiyat = random.uniform(10, 150)
        
        # İslam'a Uygunluk Simülasyonu (%70 Evet, %30 Hayır)
        katilim_uygun = "EVET" if random.random() > 0.3 else "HAYIR"
        
        # 15 Dakika Sonrası Tahmin Mantığı
        if comp > 1.3 and vol > 2.0:
            tahmin = "🚀 YÜKSELİŞ BEKLENİYOR (%78)"
        elif comp < 0.9 and vol < 1.0:
            tahmin = "📉 DÜŞÜŞ BEKLENİYOR (%65)"
        else:
            tahmin = "⏳ BEKLE (%50)"
            
        data.append({
            "Hisse": h,
            "Katılım Uygun": katilim_uygun,
            "Net Güç Skoru": round(net_guc, 2),
            "Sinyal": "GÜÇLÜ TREND" if net_guc > 70 else "BEKLE",
            "Trend Kararı": "Yükseliş Kanalı" if net_guc > 60 else "Yatay Dar Bant",
            "Olası Haber/Beklenti": "Hacim Genişlemesi Bekleniyor" if vol > 1.5 else "Normal",
            "Trend Projeksiyon": "Güçlü Trend Devamı" if net_guc > 75 else "Bant İçi Toparlanma",
            "Beklenen Getiri": f"%{round(random.uniform(-2, 5), 2)}",
            "Erken Konum": "HACIM & SIKIŞMA" if comp > 1.2 else "NORMAL",
            "Swing Al-Sat": "SWING / İNTEL UYGUN" if net_guc > 60 else "HARİÇ",
            "Al Olasılığı (AI)": f"%{round(random.uniform(50, 90), 1)}",
            "Hacim (Vol)": f"{round(vol, 2)}x",
            "Sıkışma (Comp)": f"{round(comp, 2)}x",
            "Fiyat": f"{round(fiyat, 2)} TL",
            "Dönem Değişimi": f"%{round(random.uniform(-5, 10), 2)}",
            "Endeks RS": f"%{round(random.uniform(-3, 6), 2)}",
            "Hurst": round(random.uniform(0.3, 0.8), 2),
            "VWAP Sapma": f"%{round(random.uniform(-2, 3), 2)}",
            "Net Para Girişi": round(random.uniform(-1000000, 5000000), 2),
            "Güçlü Yükseliş": "EVET" if net_guc > 80 else "HAYIR",
            "15 Dk Sonra Tahmin": tahmin
        })
    
    df = pd.DataFrame(data)
    
    # --- SIRALAMA MANTIĞI (EN İYİ ADAY EN ÜSTTE) ---
    # 1. Öncelik: 15 Dk Sonra Tahmin (Yükseliş > Bekle > Düşüş)
    df['Tahmin_Agirlik'] = df['15 Dk Sonra Tahmin'].apply(lambda x: 1 if 'YÜKSELİŞ' in x else (2 if 'BEKLE' in x else 3))
    # 2. Öncelik: Net Güç Skoru (Büyükten küçüğe)
    df = df.sort_values(by=['Tahmin_Agirlik', 'Net Güç Skoru'], ascending=[True, False])
    
    # Geçici sütunu temizle
    df = df.drop(columns=['Tahmin_Agirlik'])
    return df

# --- 3. ANA PANEL ARAYÜZÜ ---
st.title("🚀 BIST Swing/Intraday Trend & Hacim Sıkışması Patlama Terminali")
st.caption(f"Son Güncelleme (TRT): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 15Dk Gecikmeli Güvenli Trend & Sıkışma Avcısı Modu")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="🌐 BIST 100 Trend Teyidi", value="YÜKSELİŞ ONAYLI", delta="%0.02")
with col2:
    st.metric(label="⚖️ Öncü Piyasa Sinyali (VIOP Denge)", value="Denge", delta="Nötr")
with col3:
    st.metric(label="🔄 Trend Tarama Akışı", value="Aktif (30 Sn Döngü)", delta="Sayfa: 34")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Genel Trend & Sıkışma Matrisi", "⚖️ VIOP Denge", "📰 Canlı KAP Haberleri", "📈 Tüm Hisseler Görseli", "🌙 Seans Kapanış Fırsatları"])

with tab1:
    st.subheader("Gelişmiş Nicel Trend Matrisi (Hacim & Sıkışma Odaklı Tarama)")
    
    # --- FİLTRELEME VE BUTONLAR ---
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sadece_katilim = st.checkbox("✅ Sadece İslam'a Uygun Hisseleri Göster", value=True)
    with col_f2:
        st.checkbox("🚀 Erken Sıkışma & Hacim Patlaması")
    with col_f3:
        st.checkbox("Yalnızca Yüksek Güvenli Trendler")

    df = get_mock_data()
    
    # Filtreleme Mantığı
    if sadece_katilim:
        df = df[df["Katılım Uygun"] == "EVET"]
    
    # Tabloyu Göster
    if not df.empty:
        def color_prediction(val):
            if "YÜKSELİŞ" in str(val):
                return 'background-color: #1b5e20; color: white; font-weight: bold;'
            elif "DÜŞÜŞ" in str(val):
                return 'background-color: #b71c1c; color: white; font-weight: bold;'
            elif "BEKLE" in str(val):
                return 'background-color: #e65100; color: white; font-weight: bold;'
            return ''

        def color_katilim(val):
            if val == "EVET":
                return 'color: #4CAF50; font-weight: bold;'
            return 'color: #F44336;'

        styled_df = df.style.map(color_prediction, subset=["15 Dk Sonra Tahmin"]).map(color_katilim, subset=["Katılım Uygun"])
        
        st.dataframe(styled_df, use_container_width=True, height=800)
    else:
        st.warning("Seçilen filtrelere uygun hisse bulunamadı.")

with tab2:
    st.subheader("VIOP Denge Analizi")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        st.metric(label="VIOP 30 Endeks", value="11.450", delta="%0.45")
    with col_v2:
        st.metric(label="Spot Endeks", value="11.420", delta="%0.40")
    with col_v3:
        st.metric(label="Denge Farkı", value="+30 Puan", delta="Pozitif", delta_color="normal")
    st.info("Vadeli işlemler ile spot piyasa arasındaki denge pozitif yönlü. Öncü sinyal AL konumunda.")

with tab3:
    st.subheader("Canlı KAP Haberleri")
    st.warning("Paneldeki hisselerle ilgili KAP bildirimleri burada listelenecek.")
    kap_haberleri = [
        {"Saat": "14:18:40", "Hisse": "ASELS.IS", "Başlık": "Yeni Sipariş Anlaşması İmzalandı", "Etki": "Pozitif"},
        {"Saat": "14:15:20", "Hisse": "TUPRS.IS", "Başlık": "Üretim Verileri Açıklandı", "Etki": "Nötr"},
        {"Saat": "13:50:10", "Hisse": "BIMAS.IS", "Başlık": "Yeni Mağaza Açılışı", "Etki": "Pozitif"},
        {"Saat": "13:20:00", "Hisse": "SASA.IS", "Başlık": "Kapasite Artırım Yatırımı", "Etki": "Pozitif"},
    ]
    for haber in kap_haberleri:
        st.write(f"**[{haber['Saat']}] {haber['Hisse']}** - {haber['Başlık']} (Etki: {haber['Etki']})")

with tab4:
    st.subheader("Tüm Hisseler Görseli")
    st.info("Tüm hisseleri gösteren grafiksel görünüm burada yer alacak.")
    chart_data = pd.DataFrame(
        np.random.randn(20, 3),
        columns=['Hisse A', 'Hisse B', 'Hisse C']
    )
    st.line_chart(chart_data)

with tab5:
    st.subheader("Seans Kapanışı & Overnight Fırsatları")
    st.success("Overnight Taşınabilecek Katılım Hisseleri Hazırlandı.")
    st.write("- ASELS.IS: Hacim patlaması ve sıkışma sonrası kırılım bekleniyor.")
    st.write("- TUPRS.IS: Endeks RS pozitif, VWAP üzerinde tutunma var.")

# Alt Bilgi
st.markdown("---")
st.caption("⚠️ Bu paneldeki veriler simülasyondur. Gerçek yatırım tavsiyesi değildir.")
