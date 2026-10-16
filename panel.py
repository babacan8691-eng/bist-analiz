# =====================================================================
# FIRSAT MADENCİLİĞİ — 20 SEKTÖR (BASİT ve STABİL)
# =====================================================================

import streamlit as st

st.set_page_config(
    page_title="Fırsat Madenciliği",
    layout="wide",
    initial_sidebar_state="expanded"
)

import json
import os
import re
import random
import time
from datetime import datetime
import pandas as pd

# =====================================================================
# 1. AYARLAR
# =====================================================================
DEMO_MODE = True
VERI_DOSYASI = "firsat_verileri.json"
CACHE_SURESI = 24 * 60 * 60

# =====================================================================
# 2. 20 SEKTÖR
# =====================================================================
SEKTORLER = [
    {"id": 1,  "isim": "Veteriner Klinikleri",    "kategori": "Sağlık",    "isletme_sayisi": 12000,  "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 2,  "isim": "Diş Hekimleri",           "kategori": "Sağlık",    "isletme_sayisi": 25000,  "aylik_butce": 2000, "yazilim_sayisi": 8},
    {"id": 3,  "isim": "Psikologlar",             "kategori": "Sağlık",    "isletme_sayisi": 15000,  "aylik_butce": 800,  "yazilim_sayisi": 4},
    {"id": 4,  "isim": "Eczaneler",               "kategori": "Sağlık",    "isletme_sayisi": 28000,  "aylik_butce": 1200, "yazilim_sayisi": 6},
    {"id": 5,  "isim": "Avukatlar",               "kategori": "Hukuk",     "isletme_sayisi": 50000,  "aylik_butce": 1500, "yazilim_sayisi": 5},
    {"id": 6,  "isim": "Muhasebeciler",           "kategori": "Muhasebe",  "isletme_sayisi": 40000,  "aylik_butce": 1200, "yazilim_sayisi": 7},
    {"id": 7,  "isim": "Kuyumcular",              "kategori": "Perakende", "isletme_sayisi": 35000,  "aylik_butce": 2500, "yazilim_sayisi": 4},
    {"id": 8,  "isim": "Emlakçılar",              "kategori": "Perakende", "isletme_sayisi": 60000,  "aylik_butce": 800,  "yazilim_sayisi": 12},
    {"id": 9,  "isim": "Oto Galeriler",           "kategori": "Perakende", "isletme_sayisi": 25000,  "aylik_butce": 1800, "yazilim_sayisi": 8},
    {"id": 10, "isim": "Oto Servisleri",          "kategori": "Hizmet",    "isletme_sayisi": 60000,  "aylik_butce": 1000, "yazilim_sayisi": 6},
    {"id": 11, "isim": "Marangozlar",             "kategori": "Sanayi",    "isletme_sayisi": 20000,  "aylik_butce": 800,  "yazilim_sayisi": 2},
    {"id": 12, "isim": "Restoranlar",             "kategori": "Gıda",      "isletme_sayisi": 200000, "aylik_butce": 1500, "yazilim_sayisi": 25},
    {"id": 13, "isim": "Kafeler",                 "kategori": "Gıda",      "isletme_sayisi": 80000,  "aylik_butce": 800,  "yazilim_sayisi": 20},
    {"id": 14, "isim": "Pastaneler",              "kategori": "Gıda",      "isletme_sayisi": 30000,  "aylik_butce": 1000, "yazilim_sayisi": 5},
    {"id": 15, "isim": "Kasaplar",                "kategori": "Gıda",      "isletme_sayisi": 40000,  "aylik_butce": 700,  "yazilim_sayisi": 3},
    {"id": 16, "isim": "Berberler",               "kategori": "Güzellik",  "isletme_sayisi": 80000,  "aylik_butce": 500,  "yazilim_sayisi": 8},
    {"id": 17, "isim": "Kuaförler",               "kategori": "Güzellik",  "isletme_sayisi": 70000,  "aylik_butce": 700,  "yazilim_sayisi": 8},
    {"id": 18, "isim": "Spor Salonları",          "kategori": "Spor",      "isletme_sayisi": 10000,  "aylik_butce": 2000, "yazilim_sayisi": 7},
    {"id": 19, "isim": "Düğün Salonları",         "kategori": "Etkinlik",  "isletme_sayisi": 8000,   "aylik_butce": 1800, "yazilim_sayisi": 4},
    {"id": 20, "isim": "Matbaalar",               "kategori": "Sanayi",    "isletme_sayisi": 12000,  "aylik_butce": 1500, "yazilim_sayisi": 3},
]

# =====================================================================
# 3. HAFIZA
# =====================================================================
@st.cache_resource
def get_hafiza():
    return {"sektor_verileri": {}, "son_guncelleme": None} # =====================================================================
# 4. TARAYICI
# =====================================================================
def sektor_tara(sektor):
    google = {
        "talep_puani": random.randint(30, 95),
        "trend": random.choice(["yükseliyor", "sabit", "düşüyor"]),
    }
    sv_sayi = random.randint(50, 3000)
    sikayetvar = {
        "sikayet_sayisi": sv_sayi,
        "aciliyet_puani": min(100, sv_sayi // 10),
    }
    eks_sayi = random.randint(10, 500)
    eksisozluk = {
        "baslik_sayisi": eks_sayi,
        "tartisma_puani": min(100, eks_sayi * 2),
    }
    dh_sayi = random.randint(20, 800)
    donanimhaber = {
        "konu_sayisi": dh_sayi,
        "teknik_soru_puani": min(100, dh_sayi),
    }
    sahibinden = {
        "ilan_sayisi": random.randint(100, 10000),
        "pazar_canliligi": random.randint(30, 95),
    }
    
    return {
        "sektor_id": sektor["id"],
        "isim": sektor["isim"],
        "kategori": sektor["kategori"],
        "isletme_sayisi": sektor["isletme_sayisi"],
        "aylik_butce": sektor["aylik_butce"],
        "yazilim_sayisi": sektor["yazilim_sayisi"],
        "kaynaklar": {
            "google_trends": google,
            "sikayetvar": sikayetvar,
            "eksisozluk": eksisozluk,
            "donanimhaber": donanimhaber,
            "sahibinden": sahibinden,
        },
        "tarama_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def tum_sektorleri_tara(hafiza):
    hafiza["sektor_verileri"] = {}
    for i, sektor in enumerate(SEKTORLER):
        try:
            sonuc = sektor_tara(sektor)
            hafiza["sektor_verileri"][sektor["id"]] = sonuc
        except Exception as e:
            pass
    
    hafiza["son_guncelleme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verileri_kaydet(hafiza)

# =====================================================================
# 5. PUANLAMA
# =====================================================================
def sektor_puanla(veri):
    kaynaklar = veri.get("kaynaklar", {})
    
    talep_puani = 0
    gt = kaynaklar.get("google_trends", {})
    if "talep_puani" in gt:
        talep_puani += gt["talep_puani"] * 0.5
    eks = kaynaklar.get("eksisozluk", {})
    if "tartisma_puani" in eks:
        talep_puani += eks["tartisma_puani"] * 0.3
    dh = kaynaklar.get("donanimhaber", {})
    if "teknik_soru_puani" in dh:
        talep_puani += dh["teknik_soru_puani"] * 0.2
    talep_puani = min(100, talep_puani)
    
    isletme = veri.get("isletme_sayisi", 0)
    butce = veri.get("aylik_butce", 0)
    isletme_puan = min(100, (isletme / 100000) * 100)
    butce_puan = min(100, (butce / 3000) * 100)
    odeme_puani = (isletme_puan * 0.4) + (butce_puan * 0.6)
    
    sv = kaynaklar.get("sikayetvar", {})
    aciliyet_puani = sv.get("aciliyet_puani", 0)
    
    yazilim = veri.get("yazilim_sayisi", 0)
    rekabet_puani = max(0, 100 - (yazilim * 4))
    
    toplam = (
        talep_puani * 0.35 +
        odeme_puani * 0.30 +
        aciliyet_puani * 0.20 +
        rekabet_puani * 0.15
    )
    
    return {
        "talep_puani": round(talep_puani, 1),
        "odeme_puani": round(odeme_puani, 1),
        "aciliyet_puani": round(aciliyet_puani, 1),
        "rekabet_puani": round(rekabet_puani, 1),
        "toplam_puan": round(toplam, 1),
        "trend": gt.get("trend", "bilinmiyor"),
    }

def odemeye_hazir_mi(puanlar):
    return (
        puanlar["toplam_puan"] >= 60 and
        puanlar["odeme_puani"] >= 50 and
        puanlar["aciliyet_puani"] >= 40 and
        puanlar["rekabet_puani"] >= 40
    )

def tum_sektorleri_puanla(hafiza):
    sonuclar = []
    for sektor_id, veri in hafiza.get("sektor_verileri", {}).items():
        try:
            puanlar = sektor_puanla(veri)
            sektor = veri.copy()
            sektor.update(puanlar)
            sektor["odemeye_hazir"] = odemeye_hazir_mi(puanlar)
            sonuclar.append(sektor)
        except:
            continue
    sonuclar.sort(key=lambda x: x["toplam_puan"], reverse=True)
    return sonuclar

def kategori_ozeti(sonuclar):
    kategoriler = {}
    for s in sonuclar:
        kat = s["kategori"]
        if kat not in kategoriler:
            kategoriler[kat] = {"toplam": 0, "sayi": 0, "isletme_toplami": 0}
        kategoriler[kat]["toplam"] += s["toplam_puan"]
        kategoriler[kat]["sayi"] += 1
        kategoriler[kat]["isletme_toplami"] += s["isletme_sayisi"]
    
    ozet = []
    for kat, veri in kategoriler.items():
        ozet.append({
            "kategori": kat,
            "ortalama_puan": round(veri["toplam"] / veri["sayi"], 1),
            "sektor_sayisi": veri["sayi"],
            "toplam_isletme": veri["isletme_toplami"],
        })
    ozet.sort(key=lambda x: x["ortalama_puan"], reverse=True)
    return ozet

# =====================================================================
# 6. CACHE
# =====================================================================
def verileri_kaydet(hafiza):
    try:
        veri = {
            "sektor_verileri": hafiza.get("sektor_verileri", {}),
            "son_guncelleme": hafiza.get("son_guncelleme"),
        }
        with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, default=str)
    except:
        pass

def verileri_yukle(hafiza):
    try:
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
            hafiza["sektor_verileri"] = {int(k): v for k, v in veri.get("sektor_verileri", {}).items()}
            hafiza["son_guncelleme"] = veri.get("son_guncelleme")
            return True
    except:
        pass
    return False # =====================================================================
# 7. ARAYÜZ
# =====================================================================
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 Fırsat Madenciliği Paneli</h2>", unsafe_allow_html=True)
    st.caption("20 sektör analizi — hangi sektör ödemeye hazır?")

    k = st.text_input("Kullanıcı Adı", key="giris_u")
    s = st.text_input("Şifre", type="password", key="giris_p")

    if st.button("Sisteme Giriş Yap"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state["oturum_acik"] = True
            st.rerun()
        else:
            st.error("Hatalı Kullanıcı Adı veya Şifre!")

    st.stop()

hafiza = get_hafiza()

# SOL MENÜ
st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
st.sidebar.markdown("---")
st.sidebar.success("🧪 DEMO MODU")
st.sidebar.caption(f"Sektör: {len(SEKTORLER)}")
st.sidebar.caption(f"Son: {hafiza.get('son_guncelleme', 'Tarama yok')}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Kontroller")

if st.sidebar.button("▶️ Taramayı Başlat", type="primary"):
    with st.spinner("20 sektör taranıyor... (5-10 saniye)"):
        tum_sektorleri_tara(hafiza)
    st.sidebar.success("✅ Tarama tamamlandı! Sayfayı F5 ile yenileyin.")
    st.rerun()

if st.sidebar.button("🗑️ Cache Temizle"):
    hafiza["sektor_verileri"] = {}
    hafiza["son_guncelleme"] = None
    try:
        if os.path.exists(VERI_DOSYASI):
            os.remove(VERI_DOSYASI)
    except:
        pass
    st.sidebar.success("Cache temizlendi. F5 yapın.")
    st.rerun()

if st.sidebar.button("🚪 Oturumu Kapat"):
    st.session_state["oturum_acik"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚖️ Puanlama")
st.sidebar.caption("Talep: %35 | Ödeme: %30")
st.sidebar.caption("Aciliyet: %20 | Rekabet: %15")

# VERİ YÜKLE
if not hafiza["sektor_verileri"]:
    verileri_yukle(hafiza)

# BAŞLIK
st.title("🎯 Fırsat Madenciliği — 20 Sektör")
st.caption("Hangi sektör çözüm bekliyor? Hangi sektör ödemeye hazır?")
st.markdown("---")

if not hafiza["sektor_verileri"]:
    st.info("👈 Sol menüden **▶️ Taramayı Başlat** butonuna tıklayın.")
    st.caption("20 sektör 5-10 saniyede taranır.")
    st.stop()

sonuclar = tum_sektorleri_puanla(hafiza)

if not sonuclar:
    st.warning("Puanlanacak veri yok.")
    st.stop()

# METRİKLER
toplam = len(sonuclar)
hazir_sayisi = sum(1 for s in sonuclar if s["odemeye_hazir"])
en_yuksek = max(s["toplam_puan"] for s in sonuclar)
ortalama = sum(s["toplam_puan"] for s in sonuclar) / toplam

col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 Analiz", f"{toplam} Sektör")
col2.metric("✅ Hazır", f"{hazir_sayisi} Sektör")
col3.metric("🏆 En Yüksek", f"{en_yuksek:.1f}")
col4.metric("📈 Ortalama", f"{ortalama:.1f}")

st.caption(f"🕐 Son tarama: {hafiza.get('son_guncelleme', '-')}")
st.markdown("---")

# ÖDEMEYE HAZIR
st.subheader("💰 Ödemeye Hazır Sektörler")
hazir_sektorler = [s for s in sonuclar if s["odemeye_hazir"]]

if hazir_sektorler:
    for s in hazir_sektorler:
        with st.container(border=True):
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            with col_a:
                st.markdown(f"### 🎯 {s['isim']}")
                st.caption(f"{s['kategori']} | Trend: {s.get('trend', '-')}")
            with col_b:
                st.metric("Puan", f"{s['toplam_puan']:.1f}")
            with col_c:
                st.metric("İşletme", f"{s['isletme_sayisi']:,}")
            with col_d:
                st.metric("Bütçe", f"{s['aylik_butce']} TL")
            st.caption(
                f"📈 Talep: {s['talep_puani']:.0f}  |  "
                f"💵 Ödeme: {s['odeme_puani']:.0f}  |  "
                f"⚠️ Aciliyet: {s['aciliyet_puani']:.0f}  |  "
                f"🥊 Rekabet: {s['rekabet_puani']:.0f}"
            )
else:
    st.info("Şu an 4 kriteri de geçen sektör yok.")

st.markdown("---")

# TABLO
st.subheader("📋 Tüm Sektörler")
df_veri = []
for i, s in enumerate(sonuclar, 1):
    df_veri.append({
        "Sıra": i,
        "Sektör": s["isim"],
        "Kategori": s["kategori"],
        "Fırsat": s["toplam_puan"],
        "Talep": s["talep_puani"],
        "Ödeme": s["odeme_puani"],
        "Aciliyet": s["aciliyet_puani"],
        "Rekabet": s["rekabet_puani"],
        "Trend": s.get("trend", "-"),
        "İşletme": s["isletme_sayisi"],
        "Bütçe": s["aylik_butce"],
        "Yazılım": s["yazilim_sayisi"],
        "Durum": "✅" if s["odemeye_hazir"] else "—",
    })

df = pd.DataFrame(df_veri)

col_f1, col_f2 = st.columns(2)
with col_f1:
    sadece_hazir = st.checkbox("Sadece ödemeye hazır")
with col_f2:
    min_puan = st.slider("Minimum puan", 0, 100, 0, 5)

if sadece_hazir:
    df_goster = df[df["Durum"] == "✅"]
else:
    df_goster = df[df["Fırsat"] >= min_puan]

st.dataframe(df_goster, use_container_width=True, hide_index=True)
st.markdown("---")

# KATEGORİ
st.subheader("📂 Kategori Özeti")
kat_ozet = kategori_ozeti(sonuclar)
if kat_ozet:
    df_kat = pd.DataFrame(kat_ozet)
    df_kat.columns = ["Kategori", "Ortalama Puan", "Sektör Sayısı", "Toplam İşletme"]
    st.dataframe(df_kat, use_container_width=True, hide_index=True)

st.markdown("---")

# EN İYİ 5
st.subheader("🏆 En İyi 5 Sektör")
for i, s in enumerate(sonuclar[:5], 1):
    with st.expander(f"#{i} {s['isim']} — Puan: {s['toplam_puan']:.1f}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Kategori:** {s['kategori']}")
            st.markdown(f"**Trend:** {s.get('trend', '-')}")
            st.markdown(f"**İşletme:** {s['isletme_sayisi']:,}")
            st.markdown(f"**Aylık Bütçe:** {s['aylik_butce']} TL")
        with col2:
            st.markdown(f"**Talep:** {s['talep_puani']:.0f}/100")
            st.markdown(f"**Ödeme:** {s['odeme_puani']:.0f}/100")
            st.markdown(f"**Aciliyet:** {s['aciliyet_puani']:.0f}/100")
            st.markdown(f"**Rekabet:** {s['rekabet_puani']:.0f}/100")
        
        tahmini = s["isletme_sayisi"] * s["aylik_butce"] * 0.001
        st.markdown(f"**Potansiyel Aylık Gelir:** {tahmini:,.0f} TL")
        st.markdown(f"**Mevcut Yazılım Sayısı:** {s['yazilim_sayisi']}")
        
        if s["odemeye_hazir"]:
            st.success("✅ Bu sektör ödemeye hazır")
        else:
            st.warning("⚠️ Bazı kriterler yetersiz")

st.markdown("---")

with st.expander("❓ Sistem Nasıl Çalışır?"):
    st.markdown(
        "**Bu sistem 20 sektörü 4 kriterde puanlar:**\n\n"
        "- **Talep (%35):** Google Trends, Ekşi, Donanım Haber\n"
        "- **Ödeme (%30):** İşletme sayısı × Aylık bütçe\n"
        "- **Aciliyet (%20):** Şikayetvar şikayetleri\n"
        "- **Rekabet (%15):** Mevcut yazılım sayısı (az = iyi)\n\n"
        "**Ödemeye Hazır Şartları:**\n"
        "- Toplam ≥ 60, Ödeme ≥ 50, Aciliyet ≥ 40, Rekabet ≥ 40"
) 
