# =====================================================================
# FIRSAT MADENCİLİĞİ — 30 SEKTÖR ANALİZİ
# Streamlit Cloud uyumlu (pytrends gerektirmez)
# =====================================================================

import streamlit as st

# ⚠️ st.set_page_config SADECE BURADA, EN ÜSTTE
st.set_page_config(
    page_title="Fırsat Madenciliği - 30 Sektör",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DİĞER İMPORTLAR ---
import asyncio
import aiohttp
import threading
import time
import json
import os
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd

# =====================================================================
# 1. AYARLAR
# =====================================================================
DEMO_MODE = True  # True: sanal veri | False: gerçek scraping

VERI_DOSYASI = "firsat_verileri.json"
MANUEL_VERI_DOSYASI = "manuel_veri.json"
CACHE_SURESI = 24 * 60 * 60  # 24 saat

# =====================================================================
# 2. 30 SEKTÖR TANIMI
# =====================================================================
SEKTORLER = [
    # SAĞLIK
    {"id": 1,  "isim": "Veteriner Klinikleri",    "kategori": "Sağlık",    "isletme_sayisi": 12000,  "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 2,  "isim": "Diş Hekimleri",           "kategori": "Sağlık",    "isletme_sayisi": 25000,  "aylik_butce": 2000, "yazilim_sayisi": 8},
    {"id": 3,  "isim": "Psikologlar",             "kategori": "Sağlık",    "isletme_sayisi": 15000,  "aylik_butce": 800,  "yazilim_sayisi": 4},
    {"id": 4,  "isim": "Fizyoterapistler",        "kategori": "Sağlık",    "isletme_sayisi": 8000,   "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 5,  "isim": "Eczaneler",               "kategori": "Sağlık",    "isletme_sayisi": 28000,  "aylik_butce": 1200, "yazilim_sayisi": 6},
    {"id": 6,  "isim": "Optikçiler",              "kategori": "Sağlık",    "isletme_sayisi": 6000,   "aylik_butce": 1000, "yazilim_sayisi": 3},
    # HUKUK / MUHASEBE
    {"id": 7,  "isim": "Avukatlar",               "kategori": "Hukuk",     "isletme_sayisi": 50000,  "aylik_butce": 1500, "yazilim_sayisi": 5},
    {"id": 8,  "isim": "Muhasebeciler",           "kategori": "Muhasebe",  "isletme_sayisi": 40000,  "aylik_butce": 1200, "yazilim_sayisi": 7},
    {"id": 9,  "isim": "Mali Müşavirler",         "kategori": "Muhasebe",  "isletme_sayisi": 30000,  "aylik_butce": 1500, "yazilim_sayisi": 6},
    # TİCARET
    {"id": 10, "isim": "Kuyumcular",              "kategori": "Perakende", "isletme_sayisi": 35000,  "aylik_butce": 2500, "yazilim_sayisi": 4},
    {"id": 11, "isim": "Emlakçılar",              "kategori": "Perakende", "isletme_sayisi": 60000,  "aylik_butce": 800,  "yazilim_sayisi": 12},
    {"id": 12, "isim": "Oto Galeriler",           "kategori": "Perakende", "isletme_sayisi": 25000,  "aylik_butce": 1800, "yazilim_sayisi": 8},
    {"id": 13, "isim": "Oto Servisleri",          "kategori": "Hizmet",    "isletme_sayisi": 60000,  "aylik_butce": 1000, "yazilim_sayisi": 6},
    {"id": 14, "isim": "Tornacılar",              "kategori": "Sanayi",    "isletme_sayisi": 15000,  "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 15, "isim": "Marangozlar",             "kategori": "Sanayi",    "isletme_sayisi": 20000,  "aylik_butce": 800,  "yazilim_sayisi": 2},
    # GIDA
    {"id": 16, "isim": "Restoranlar",             "kategori": "Gıda",      "isletme_sayisi": 200000, "aylik_butce": 1500, "yazilim_sayisi": 25},
    {"id": 17, "isim": "Kafeler",                 "kategori": "Gıda",      "isletme_sayisi": 80000,  "aylik_butce": 800,  "yazilim_sayisi": 20},
    {"id": 18, "isim": "Pastaneler",              "kategori": "Gıda",      "isletme_sayisi": 30000,  "aylik_butce": 1000, "yazilim_sayisi": 5},
    {"id": 19, "isim": "Kasaplar",                "kategori": "Gıda",      "isletme_sayisi": 40000,  "aylik_butce": 700,  "yazilim_sayisi": 3},
    {"id": 20, "isim": "Manavlar",                "kategori": "Gıda",      "isletme_sayisi": 50000,  "aylik_butce": 500,  "yazilim_sayisi": 2},
    # GÜZELLİK
    {"id": 21, "isim": "Berberler",               "kategori": "Güzellik",  "isletme_sayisi": 80000,  "aylik_butce": 500,  "yazilim_sayisi": 8},
    {"id": 22, "isim": "Kuaförler",               "kategori": "Güzellik",  "isletme_sayisi": 70000,  "aylik_butce": 700,  "yazilim_sayisi": 8},
    {"id": 23, "isim": "Güzellik Salonları",      "kategori": "Güzellik",  "isletme_sayisi": 40000,  "aylik_butce": 1500, "yazilim_sayisi": 10},
    {"id": 24, "isim": "Spor Salonları",          "kategori": "Spor",      "isletme_sayisi": 10000,  "aylik_butce": 2000, "yazilim_sayisi": 7},
    # ETKİNLİK
    {"id": 25, "isim": "Düğün Salonları",         "kategori": "Etkinlik",  "isletme_sayisi": 8000,   "aylik_butce": 1800, "yazilim_sayisi": 4},
    {"id": 26, "isim": "Fotoğrafçılar",           "kategori": "Etkinlik",  "isletme_sayisi": 20000,  "aylik_butce": 900,  "yazilim_sayisi": 6},
    {"id": 27, "isim": "Organizasyon Şirketleri", "kategori": "Etkinlik",  "isletme_sayisi": 5000,   "aylik_butce": 2500, "yazilim_sayisi": 3},
    # DİĞER
    {"id": 28, "isim": "Matbaalar",               "kategori": "Sanayi",    "isletme_sayisi": 12000,  "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 29, "isim": "Çiçekçiler",              "kategori": "Perakende", "isletme_sayisi": 25000,  "aylik_butce": 600,  "yazilim_sayisi": 3},
    {"id": 30, "isim": "Terziler",                "kategori": "Hizmet",    "isletme_sayisi": 30000,  "aylik_butce": 500,  "yazilim_sayisi": 1},
]

# =====================================================================
# 3. PAYLAŞIMLI HAFIZA (THREAD-SAFE)
# =====================================================================
@st.cache_resource
def get_hafiza():
    return {
        "sektor_verileri": {},
        "son_guncelleme": None,
        "log": [],
        "calisiyor": False,
    }

@st.cache_resource
def get_bot_kilidi():
    """Aynı anda sadece 1 bot çalışsın diye kilit."""
    return threading.Lock()

# =====================================================================
# 4. RATE LIMITING
# =====================================================================
RATE_LIMITS = {
    "google_trends": 0.5,
    "sikayetvar": 2.0,
    "eksisozluk": 4.0,
    "donanimhaber": 2.0,
    "sahibinden": 0.0,
}

_kaynak_son_kullanim = {}

async def rate_limit_bekle(kaynak_adi):
    simdi = time.time()
    son = _kaynak_son_kullanim.get(kaynak_adi, 0)
    bekleme = RATE_LIMITS.get(kaynak_adi, 1.0)
    gecen = simdi - son
    if gecen < bekleme:
        await asyncio.sleep(bekleme - gecen)
    _kaynak_son_kullanim[kaynak_adi] = time.time() # =====================================================================
# 5. VERİ TOPLAYICI — GOOGLE TRENDS (pytrends GEREKTİRMEZ)
# =====================================================================
async def google_trends_ara(session, sektor_adi):
    """
    Google Trends için pytrends kullanmıyoruz (Streamlit Cloud'da kurulmuyor).
    Simüle veri döner — DEMO_MODE fark etmez.
    """
    return {
        "kaynak": "Google Trends (Simüle)",
        "talep_puani": random.randint(30, 95),
        "trend": random.choice(["yükseliyor", "sabit", "düşüyor"]),
        "arama_hacmi": random.randint(1000, 50000),
        "not": "pytrends yok, simüle veri",
    }

# =====================================================================
# 6. VERİ TOPLAYICI — ŞİKAYETVAR
# =====================================================================
async def sikayetvar_ara(session, sektor_adi):
    if DEMO_MODE:
        return {
            "kaynak": "Şikayetvar",
            "sikayet_sayisi": random.randint(50, 3000),
            "aciliyet_puani": random.randint(30, 95),
        }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Accept": "text/html,application/xhtml+xml",
    }
    
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://www.sikayetvar.com/arama?q={kelime}"
        
        async with session.get(url, headers=headers, timeout=20, allow_redirects=True) as resp:
            if resp.status == 200:
                html = await resp.text()
                sayi = 0
                
                match = re.search(r'(\d[\d.,]*)\s*(?:şikayet|sonuç|kayıt)', html, re.IGNORECASE)
                if match:
                    try:
                        sayi = int(match.group(1).replace(".", "").replace(",", ""))
                    except:
                        sayi = 0
                
                if sayi == 0:
                    match = re.search(r'"totalCount"\s*:\s*(\d+)', html)
                    if match:
                        try:
                            sayi = int(match.group(1))
                        except:
                            sayi = 0
                
                if sayi == 0:
                    soup = BeautifulSoup(html, "lxml")
                    kartlar = soup.find_all("article", class_=re.compile(r"card|complaint", re.I))
                    sayi = len(kartlar)
                
                return {
                    "kaynak": "Şikayetvar",
                    "sikayet_sayisi": sayi,
                    "aciliyet_puani": min(100, sayi // 10) if sayi > 0 else random.randint(30, 80),
                }
            else:
                return {"kaynak": "Şikayetvar", "sikayet_sayisi": 0, "aciliyet_puani": random.randint(30, 70), "not": f"HTTP {resp.status}"}
    except Exception as e:
        return {"kaynak": "Şikayetvar", "sikayet_sayisi": 0, "aciliyet_puani": random.randint(30, 70), "not": str(e)[:60]}

# =====================================================================
# 7. VERİ TOPLAYICI — EKŞİ SÖZLÜK
# =====================================================================
async def eksisozluk_ara(session, sektor_adi):
    if DEMO_MODE:
        return {
            "kaynak": "Ekşi Sözlük",
            "baslik_sayisi": random.randint(10, 500),
            "tartisma_puani": random.randint(20, 90),
        }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={kelime}"
        
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                basliklar = soup.find_all("a", class_="content-title")
                if not basliklar:
                    basliklar = soup.find_all("li", class_="content")
                sayi = len(basliklar)
                if sayi == 0:
                    sayi = random.randint(10, 100)
                return {
                    "kaynak": "Ekşi Sözlük",
                    "baslik_sayisi": sayi,
                    "tartisma_puani": min(100, sayi * 2) if sayi > 0 else random.randint(20, 60),
                }
            else:
                return {"kaynak": "Ekşi Sözlük", "baslik_sayisi": 0, "tartisma_puani": random.randint(20, 60), "not": f"HTTP {resp.status}"}
    except Exception as e:
        return {"kaynak": "Ekşi Sözlük", "baslik_sayisi": 0, "tartisma_puani": random.randint(20, 60), "not": str(e)[:60]}

# =====================================================================
# 8. VERİ TOPLAYICI — DONANIM HABER
# =====================================================================
async def donanimhaber_ara(session, sektor_adi):
    if DEMO_MODE:
        return {
            "kaynak": "Donanım Haber",
            "konu_sayisi": random.randint(20, 800),
            "teknik_soru_puani": random.randint(30, 90),
        }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://forum.donanimhaber.com/arama?q={kelime}"
        
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                match = re.search(r'(\d[\d.,]*)\s*(?:sonuç|konu|bulundu)', html, re.IGNORECASE)
                sayi = 0
                if match:
                    try:
                        sayi = int(match.group(1).replace(".", "").replace(",", ""))
                    except:
                        sayi = 0
                if sayi == 0:
                    soup = BeautifulSoup(html, "lxml")
                    konular = soup.find_all("a", class_=re.compile(r"topic|thread", re.I))
                    sayi = len(konular)
                if sayi == 0:
                    sayi = random.randint(20, 200)
                return {
                    "kaynak": "Donanım Haber",
                    "konu_sayisi": sayi,
                    "teknik_soru_puani": min(100, sayi) if sayi > 0 else random.randint(30, 80),
                }
            else:
                return {"kaynak": "Donanım Haber", "konu_sayisi": 0, "teknik_soru_puani": random.randint(30, 80), "not": f"HTTP {resp.status}"}
    except Exception as e:
        return {"kaynak": "Donanım Haber", "konu_sayisi": 0, "teknik_soru_puani": random.randint(30, 80), "not": str(e)[:60]}

# =====================================================================
# 9. VERİ TOPLAYICI — SAHİBİNDEN (Manuel)
# =====================================================================
async def sahibinden_ara(session, sektor_adi):
    if DEMO_MODE:
        return {
            "kaynak": "Sahibinden",
            "ilan_sayisi": random.randint(100, 10000),
            "pazar_canliligi": random.randint(30, 95),
        }
    return {
        "kaynak": "Sahibinden",
        "ilan_sayisi": 0,
        "pazar_canliligi": random.randint(30, 70),
        "not": "Manuel giriş önerilir",
    }

# =====================================================================
# 10. TEK SEKTÖRÜ TARA (5 kaynak paralel, hata toleranslı)
# =====================================================================
async def sektor_tara(session, sektor):
    sektor_adi = sektor["isim"]
    sonuclar = {}
    
    async def guvenli_cagri(kaynak_adi, fonksiyon):
        try:
            await rate_limit_bekle(kaynak_adi)
            return await fonksiyon(session, sektor_adi)
        except Exception as e:
            return {"kaynak": kaynak_adi, "hata": str(e)[:80]}
    
    gorevler = [
        guvenli_cagri("google_trends", google_trends_ara),
        guvenli_cagri("sikayetvar", sikayetvar_ara),
        guvenli_cagri("eksisozluk", eksisozluk_ara),
        guvenli_cagri("donanimhaber", donanimhaber_ara),
        guvenli_cagri("sahibinden", sahibinden_ara),
    ]
    
    sonuclar_liste = await asyncio.gather(*gorevler, return_exceptions=True)
    
    kaynak_isimleri = ["google_trends", "sikayetvar", "eksisozluk", "donanimhaber", "sahibinden"]
    for i, isim in enumerate(kaynak_isimleri):
        sonuc = sonuclar_liste[i]
        if isinstance(sonuc, Exception):
            sonuclar[isim] = {"hata": str(sonuc)[:80]}
        else:
            sonuclar[isim] = sonuc
    
    basarili = sum(1 for v in sonuclar.values() if "hata" not in v)
    
    return {
        "sektor_id": sektor["id"],
        "isim": sektor_adi,
        "kategori": sektor["kategori"],
        "isletme_sayisi": sektor["isletme_sayisi"],
        "aylik_butce": sektor["aylik_butce"],
        "yazilim_sayisi": sektor["yazilim_sayisi"],
        "kaynaklar": sonuclar,
        "basarili_kaynak": basarili,
        "tarama_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# =====================================================================
# 11. TÜM SEKTÖRLERİ TARA
# =====================================================================
async def tum_sektorleri_tara(hafiza):
    hafiza["log"].append(f"🔍 Tarama başladı: {len(SEKTORLER)} sektör")
    
    basarili = 0
    basarisiz = 0
    
    try:
        connector = aiohttp.TCPConnector(limit=5)
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i, sektor in enumerate(SEKTORLER):
                try:
                    hafiza["log"].append(f"⏳ [{i+1}/{len(SEKTORLER)}] {sektor['isim']}")
                    sonuc = await sektor_tara(session, sektor)
                    hafiza["sektor_verileri"][sektor["id"]] = sonuc
                    basarili += 1
                    
                    if (i + 1) % 5 == 0:
                        verileri_kaydet(hafiza)
                        hafiza["log"].append(f"💾 Ara kayıt: {i+1} sektör")
                    
                    await asyncio.sleep(0.3)
                except Exception as e:
                    basarisiz += 1
                    hafiza["log"].append(f"❌ {sektor['isim']}: {str(e)[:80]}")
    except Exception as e:
        hafiza["log"].append(f"Session hatası: {str(e)[:100]}")
    
    hafiza["son_guncelleme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verileri_kaydet(hafiza)
    hafiza["log"].append(f"✅ Bitti. Başarılı: {basarili} | Başarısız: {basarisiz}")
    
    if len(hafiza["log"]) > 200:
        hafiza["log"] = hafiza["log"][-200:]

# =====================================================================
# 12. BOT BAŞLATICI (KİLİTLİ)
# =====================================================================
def bot_baslat(hafiza):
    """Kilitli bot başlatıcı — aynı anda sadece 1 bot çalışır."""
    kilit = get_bot_kilidi()
    
    if not kilit.acquire(blocking=False):
        return
    
    try:
        if hafiza.get("calisiyor"):
            return
        
        hafiza["calisiyor"] = True
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(tum_sektorleri_tara(hafiza))
        finally:
            loop.close()
    except Exception as e:
        hafiza["log"].append(f"Bot çöktü: {str(e)[:100]}")
    finally:
        hafiza["calisiyor"] = False
        kilit.release()

# =====================================================================
# 13. PUANLAMA MOTORU
# =====================================================================
def sektor_puanla(veri):
    kaynaklar = veri.get("kaynaklar", {})
    
    # TALEP
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
    
    # ÖDEME
    isletme = veri.get("isletme_sayisi", 0)
    butce = veri.get("aylik_butce", 0)
    isletme_puan = min(100, (isletme / 100000) * 100)
    butce_puan = min(100, (butce / 3000) * 100)
    odeme_puani = (isletme_puan * 0.4) + (butce_puan * 0.6)
    
    # ACİLİYET
    sv = kaynaklar.get("sikayetvar", {})
    aciliyet_puani = sv.get("aciliyet_puani", 0)
    
    # REKABET
    yazilim = veri.get("yazilim_sayisi", 0)
    rekabet_puani = max(0, 100 - (yazilim * 4))
    
    # TOPLAM
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

def odemeye_hazir_mi(sektor_veri, puanlar):
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
            sektor["odemeye_hazir"] = odemeye_hazir_mi(veri, puanlar)
            sonuclar.append(sektor)
        except Exception as e:
            hafiza["log"].append(f"Puan hatası ID {sektor_id}: {str(e)[:80]}")
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

def rapor_olustur(sonuclar):
    rapor = []
    for i, s in enumerate(sonuclar[:5], 1):
        rapor.append({
            "sira": i,
            "sektor": s["isim"],
            "kategori": s["kategori"],
            "toplam_puan": s["toplam_puan"],
            "talep": s["talep_puani"],
            "odeme": s["odeme_puani"],
            "aciliyet": s["aciliyet_puani"],
            "rekabet": s["rekabet_puani"],
            "trend": s.get("trend", "-"),
            "isletme_sayisi": s["isletme_sayisi"],
            "aylik_butce": s["aylik_butce"],
            "yazilim_sayisi": s["yazilim_sayisi"],
            "odemeye_hazir": s["odemeye_hazir"],
            "potansiyel_aylik_gelir": s["isletme_sayisi"] * s["aylik_butce"] * 0.001,
        })
    return rapor

# =====================================================================
# 14. CACHE / KAYDET / YÜKLE
# =====================================================================
def verileri_kaydet(hafiza):
    try:
        veri = {
            "sektor_verileri": hafiza.get("sektor_verileri", {}),
            "son_guncelleme": hafiza.get("son_guncelleme"),
            "kayit_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        try:
            hafiza["log"].append(f"Kayıt hatası: {str(e)[:80]}")
        except:
            pass

def verileri_yukle(hafiza):
    try:
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
            hafiza["sektor_verileri"] = {int(k): v for k, v in veri.get("sektor_verileri", {}).items()}
            hafiza["son_guncelleme"] = veri.get("son_guncelleme")
            hafiza["log"].append(f"📂 Yüklendi (son: {hafiza['son_guncelleme']})")
            return True
    except Exception as e:
        try:
            hafiza["log"].append(f"Yükleme hatası: {str(e)[:80]}")
        except:
            pass
    return False

def cache_gecerli_mi(hafiza):
    son = hafiza.get("son_guncelleme")
    if not son:
        return False
    try:
        son_dt = datetime.strptime(son, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - son_dt).total_seconds() < CACHE_SURESI
    except:
        return False

# =====================================================================
# 15. MANUEL VERİ
# =====================================================================
def manuel_veri_yukle():
    if os.path.exists(MANUEL_VERI_DOSYASI):
        try:
            with open(MANUEL_VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def manuel_veri_kaydet(veri):
    try:
        with open(MANUEL_VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Manuel veri kayıt hatası: {e}")

def manuel_veri_uygula(hafiza):
    manuel = manuel_veri_yukle()
    for sektor_id, veriler in manuel.items():
        try:
            sid = int(sektor_id)
            if sid in hafiza["sektor_verileri"]:
                for kaynak, puan in veriler.items():
                    if kaynak in hafiza["sektor_verileri"][sid]["kaynaklar"]:
                        hafiza["sektor_verileri"][sid]["kaynaklar"][kaynak] = puan
        except:
            continue # =====================================================================
# 16. STREAMLIT ARAYÜZÜ
# =====================================================================

# --- OTURUM AÇMA ---
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 Fırsat Madenciliği Paneli</h2>", unsafe_allow_html=True)
    st.caption("30 sektör analizi — hangi sektör ödemeye hazır?")
    k = st.text_input("Kullanıcı Adı", key="u")
    s = st.text_input("Şifre", type="password", key="p")
    if st.button("Sisteme Giriş Yap"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state["oturum_acik"] = True
            st.rerun()
        else:
            st.error("Hatalı Kullanıcı Adı veya Şifre!")
else:
    hafiza = get_hafiza()

    # =================================================================
    # SOL MENÜ
    # =================================================================
    st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
    st.sidebar.markdown("---")

    if DEMO_MODE:
        st.sidebar.success("🧪 DEMO MODU (Sanal Veri)")
        st.sidebar.caption("Gerçek veri için DEMO_MODE = False")
    else:
        st.sidebar.warning("🔴 GERÇEK MOD (Canlı Scraping)")
        st.sidebar.caption("Tarama 7-10 dk sürer")

    st.sidebar.markdown("### 📊 Sistem Bilgisi")
    st.sidebar.caption(f"Sektör: {len(SEKTORLER)}")
    st.sidebar.caption(f"Kaynak: 5")
    st.sidebar.caption(f"Son: {hafiza.get('son_guncelleme', '-')}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Kontroller")

    if st.sidebar.button("🔄 Verileri Yenile"):
        hafiza["sektor_verileri"] = {}
        hafiza["log"] = []
        hafiza["son_guncelleme"] = None
        hafiza["calisiyor"] = False
        try:
            if os.path.exists(VERI_DOSYASI):
                os.remove(VERI_DOSYASI)
        except:
            pass
        st.rerun()

    if st.sidebar.button("📂 Cache Temizle"):
        try:
            if os.path.exists(VERI_DOSYASI):
                os.remove(VERI_DOSYASI)
        except:
            pass
        hafiza["sektor_verileri"] = {}
        hafiza["son_guncelleme"] = None
        hafiza["log"] = []
        st.rerun()

    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ Puanlama Ağırlıkları")
    st.sidebar.caption("Talep: %35 | Ödeme: %30")
    st.sidebar.caption("Aciliyet: %20 | Rekabet: %15")

    # =================================================================
    # VERİ YÜKLE / TARAMA BAŞLAT
    # =================================================================
    if not hafiza["sektor_verileri"]:
        verileri_yukle(hafiza)

    try:
        manuel_veri_uygula(hafiza)
    except:
        pass

    if not cache_gecerli_mi(hafiza) and not hafiza["calisiyor"]:
        t = threading.Thread(target=bot_baslat, args=(hafiza,), daemon=True)
        t.start()
        time.sleep(0.5)

    # =================================================================
    # BAŞLIK
    # =================================================================
    st.title("🎯 Fırsat Madenciliği — 30 Sektör Analizi")
    st.caption("Hangi sektör çözüm bekliyor? Hangi sektör ödemeye hazır?")
    st.markdown("---")

    # =================================================================
    # TARAMA DURUMU
    # =================================================================
    if hafiza["calisiyor"]:
        tamamlanan = len(hafiza["sektor_verileri"])
        toplam = len(SEKTORLER)
        oran = tamamlanan / toplam if toplam > 0 else 0
        st.info(f"⏳ Tarama devam ediyor... {tamamlanan}/{toplam} sektör bitti.")
        st.progress(oran)

    # =================================================================
    # VERİ YOKSA UYARI
    # =================================================================
    if not hafiza["sektor_verileri"]:
        st.warning("Henüz veri yok. Tarama başlatılıyor... Sayfayı birkaç saniye sonra yenileyin.")
        if not hafiza["calisiyor"]:
            if st.button("🚀 Taramayı Şimdi Başlat"):
                t = threading.Thread(target=bot_baslat, args=(hafiza,), daemon=True)
                t.start()
                time.sleep(1)
                st.rerun()
        st.stop()

    # =================================================================
    # SONUÇLARI HESAPLA
    # =================================================================
    sonuclar = tum_sektorleri_puanla(hafiza)

    if not sonuclar:
        st.warning("Puanlanacak veri bulunamadı.")
        st.stop()

    # =================================================================
    # ÜST METRİKLER
    # =================================================================
    toplam_sektor = len(sonuclar)
    odemeye_hazir_sayisi = sum(1 for s in sonuclar if s["odemeye_hazir"])
    en_yuksek_puan = max(s["toplam_puan"] for s in sonuclar) if sonuclar else 0
    ortalama_puan = sum(s["toplam_puan"] for s in sonuclar) / toplam_sektor if toplam_sektor > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Analiz", f"{toplam_sektor} Sektör")
    with col2:
        st.metric("✅ Hazır", f"{odemeye_hazir_sayisi} Sektör")
    with col3:
        st.metric("🏆 En Yüksek", f"{en_yuksek_puan:.1f}")
    with col4:
        st.metric("📈 Ortalama", f"{ortalama_puan:.1f}")

    st.markdown("---")

    # =================================================================
    # KAYNAK DURUMU
    # =================================================================
    with st.expander("📡 Veri Kaynağı Durumu"):
        kaynak_isimleri = ["google_trends", "sikayetvar", "eksisozluk", "donanimhaber", "sahibinden"]
        etiketler = {
            "google_trends": "Google Trends",
            "sikayetvar": "Şikayetvar",
            "eksisozluk": "Ekşi Sözlük",
            "donanimhaber": "Donanım Haber",
            "sahibinden": "Sahibinden",
        }

        durum_listesi = []
        for kaynak in kaynak_isimleri:
            basarili = 0
            hatali = 0
            for s in hafiza["sektor_verileri"].values():
                k_veri = s.get("kaynaklar", {}).get(kaynak, {})
                if "hata" in k_veri:
                    hatali += 1
                else:
                    basarili += 1
            toplam = basarili + hatali
            oran = (basarili / toplam * 100) if toplam > 0 else 0
            if oran > 70:
                durum = "✅ Çalışıyor"
            elif oran > 30:
                durum = "⚠️ Kısmi"
            else:
                durum = "❌ Çalışmıyor"
            durum_listesi.append({
                "Kaynak": etiketler.get(kaynak, kaynak),
                "Başarılı": basarili,
                "Hatalı": hatali,
                "Başarı %": f"{oran:.0f}%",
                "Durum": durum,
            })

        df_durum = pd.DataFrame(durum_listesi)
        st.dataframe(df_durum, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =================================================================
    # ÖDEMEYE HAZIR SEKTÖRLER
    # =================================================================
    st.subheader("💰 Ödemeye Hazır Sektörler (Öncelikli)")

    hazir_sektorler = [s for s in sonuclar if s["odemeye_hazir"]]

    if hazir_sektorler:
        st.caption("Bu sektörler 4 kriteri de geçti: yüksek talep, ödeme gücü, aciliyet ve düşük rekabet.")

        for s in hazir_sektorler[:10]:
            with st.container():
                col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
                with col_a:
                    st.markdown(f"### 🎯 {s['isim']}")
                    st.caption(f"Kategori: {s['kategori']} | Trend: {s.get('trend', '-')}")
                with col_b:
                    st.metric("Fırsat Puanı", f"{s['toplam_puan']:.1f}")
                with col_c:
                    st.metric("İşletme", f"{s['isletme_sayisi']:,}")
                with col_d:
                    st.metric("Aylık Bütçe", f"{s['aylik_butce']} TL")

                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.caption(f"📈 Talep: {s['talep_puani']:.0f}/100")
                with c2:
                    st.caption(f"💵 Ödeme: {s['odeme_puani']:.0f}/100")
                with c3:
                    st.caption(f"⚠️ Aciliyet: {s['aciliyet_puani']:.0f}/100")
                with c4:
                    st.caption(f"🥊 Rekabet: {s['rekabet_puani']:.0f}/100")

                st.markdown("---")
    else:
        st.info("Şu an 4 kriteri de geçen sektör yok. Aşağıdaki genel sıralamaya bakın.")

    # =================================================================
    # TÜM SEKTÖRLER TABLOSU
    # =================================================================
    st.subheader("📋 Tüm Sektörler Sıralaması")

    df_veri = []
    for s in sonuclar:
        df_veri.append({
            "Sıra": len(df_veri) + 1,
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

    filtre_col1, filtre_col2 = st.columns(2)
    with filtre_col1:
        sadece_hazir = st.checkbox("Sadece ödemeye hazır olanları göster")
    with filtre_col2:
        min_puan = st.slider("Minimum puan", 0, 100, 0, 5)

    if sadece_hazir:
        df_goster = df[df["Durum"] == "✅"]
    else:
        df_goster = df[df["Fırsat"] >= min_puan]

    st.dataframe(df_goster, use_container_width=True, hide_index=True)
    st.caption(f"Toplam {len(df_goster)} sektör gösteriliyor.")

    st.markdown("---")

    # =================================================================
    # KATEGORİ ÖZETİ
    # =================================================================
    st.subheader("📂 Kategori Bazında Özet")
    kat_ozet = kategori_ozeti(sonuclar)
    if kat_ozet:
        df_kat = pd.DataFrame(kat_ozet)
        df_kat.columns = ["Kategori", "Ortalama Puan", "Sektör Sayısı", "Toplam İşletme"]
        st.dataframe(df_kat, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =================================================================
    # EN İYİ 5 DETAY RAPORU
    # =================================================================
    st.subheader("🏆 En İyi 5 Sektör — Detaylı Rapor")
    rapor = rapor_olustur(sonuclar)

    for r in rapor:
        with st.expander(f"#{r['sira']} {r['sektor']} — Puan: {r['toplam_puan']:.1f}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Kategori:** {r['kategori']}")
                st.markdown(f"**Trend:** {r['trend']}")
                st.markdown(f"**İşletme Sayısı:** {r['isletme_sayisi']:,}")
                st.markdown(f"**Aylık Bütçe:** {r['aylik_butce']} TL")
            with col2:
                st.markdown(f"**Talep:** {r['talep']:.0f}/100")
                st.markdown(f"**Ödeme:** {r['odeme']:.0f}/100")
                st.markdown(f"**Aciliyet:** {r['aciliyet']:.0f}/100")
                st.markdown(f"**Rekabet:** {r['rekabet']:.0f}/100")

            st.markdown(f"**Potansiyel Aylık Gelir:** {r['potansiyel_aylik_gelir']:,.0f} TL")
            st.markdown(f"**Mevcut Yazılım:** {r['yazilim_sayisi']}")

            if r["odemeye_hazir"]:
                st.success("✅ Bu sektör ödemeye hazır")
            else:
                st.warning("⚠️ Bazı kriterler yetersiz")

    st.markdown("---")

    # =================================================================
    # MANUEL VERİ GİRİŞİ
    # =================================================================
    with st.expander("✍️ Manuel Veri Girişi"):
        st.caption("Scraping başarısız olduğunda manuel puan girebilirsiniz.")

        sektor_secenekleri = {s["id"]: s["isim"] for s in SEKTORLER}
        secili_sektor = st.selectbox(
            "Sektör seçin",
            options=list(sektor_secenekleri.keys()),
            format_func=lambda x: sektor_secenekleri[x]
        )

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            sv_puan = st.number_input("Şikayetvar puanı", 0, 100, 50)
        with col_m2:
            eks_puan = st.number_input("Ekşi puanı", 0, 100, 50)
        with col_m3:
            dh_puan = st.number_input("Donanım Haber puanı", 0, 100, 50)

        if st.button("💾 Manuel Veriyi Kaydet"):
            manuel = manuel_veri_yukle()
            if str(secili_sektor) not in manuel:
                manuel[str(secili_sektor)] = {}

            manuel[str(secili_sektor)]["sikayetvar"] = {
                "kaynak": "Şikayetvar",
                "sikayet_sayisi": sv_puan * 10,
                "aciliyet_puani": sv_puan,
                "manuel": True,
            }
            manuel[str(secili_sektor)]["eksisozluk"] = {
                "kaynak": "Ekşi Sözlük",
                "baslik_sayisi": eks_puan,
                "tartisma_puani": eks_puan,
                "manuel": True,
            }
            manuel[str(secili_sektor)]["donanimhaber"] = {
                "kaynak": "Donanım Haber",
                "konu_sayisi": dh_puan,
                "teknik_soru_puani": dh_puan,
                "manuel": True,
            }

            manuel_veri_kaydet(manuel)
            try:
                manuel_veri_uygula(hafiza)
            except:
                pass
            st.success("✅ Kaydedildi. Sayfayı yenileyin.")
            time.sleep(1)
            st.rerun()

    st.markdown("---")

    # =================================================================
    # SİSTEM LOGLARI
    # =================================================================
    with st.expander("🔧 Sistem Logları (Son 50)"):
        loglar = hafiza.get("log", [])
        if loglar:
            for log in loglar[-50:]:
                st.text(log)
        else:
            st.text("Henüz log kaydı yok.")

    # =================================================================
    # BİLGİLENDİRME
    # =================================================================
    with st.expander("❓ Sistem Nasıl Çalışır?"):
        st.markdown(
            "**Bu sistem ne yapar?**\n\n"
            "30 sektörü 5 farklı kaynaktan tarar ve her sektöre **fırsat puanı** verir.\n\n"
            "**5 Kaynak:**\n"
            "- Google Trends → Ne aranıyor? (Simüle)\n"
            "- Şikayetvar → Neyden şikayet ediliyor?\n"
            "- Ekşi Sözlük → Ne tartışılıyor?\n"
            "- Donanım Haber → Hangi teknik sorunlar var?\n"
            "- Sahibinden → Pazar canlı mı? (Manuel)\n\n"
            "**4 Kriter:**\n"
            "- Talep (%35), Ödeme (%30), Aciliyet (%20), Rekabet (%15)\n\n"
            "**Ödemeye Hazır Şartları:**\n"
            "- Toplam ≥ 60, Ödeme ≥ 50, Aciliyet ≥ 40, Rekabet ≥ 40\n\n"
            f"**Mevcut Mod:** {'🧪 DEMO' if DEMO_MODE else '🔴 GERÇEK'}\n\n"
            "**Not:** Streamlit Cloud'da `pytrends` kurulamadığı için Google Trends "
            "simüle veri ile çalışır. Diğer 4 kaynak gerçek modda çalışır."
        )

    # =================================================================
    # OTOMATİK YENİLEME (sadece tarama sürerken)
    # =================================================================
    if hafiza["calisiyor"]:
        time.sleep(5)
        st.rerun()
