import streamlit as st
import asyncio
import aiohttp
import threading
import time
import json
import os
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import random

# =====================================================================
# 1. AYARLAR
# =====================================================================
DEMO_MODE = True
VERI_DOSYASI = "firsat_verileri.json"
MANUEL_VERI_DOSYASI = "manuel_veri.json"
CACHE_SURESI = 24 * 60 * 60

# Rate limits (saniye)
RATE_LIMITS = {
    "google_trends": 3.0,
    "sikayetvar": 2.0,
    "eksisozluk": 4.0,
    "donanimhaber": 2.0,
    "sahibinden": 0.0,
}
_kaynak_son_kullanim = {}

# =====================================================================
# 2. 30 SEKTÖR TANIMI
# =====================================================================
SEKTORLER = [
    {"id": 1,  "isim": "Veteriner Klinikleri",    "kategori": "Sağlık",     "isletme_sayisi": 12000, "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 2,  "isim": "Diş Hekimleri",           "kategori": "Sağlık",     "isletme_sayisi": 25000, "aylik_butce": 2000, "yazilim_sayisi": 8},
    {"id": 3,  "isim": "Psikologlar",             "kategori": "Sağlık",     "isletme_sayisi": 15000, "aylik_butce": 800,  "yazilim_sayisi": 4},
    {"id": 4,  "isim": "Fizyoterapistler",        "kategori": "Sağlık",     "isletme_sayisi": 8000,  "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 5,  "isim": "Eczaneler",               "kategori": "Sağlık",     "isletme_sayisi": 28000, "aylik_butce": 1200, "yazilim_sayisi": 6},
    {"id": 6,  "isim": "Optikçiler",              "kategori": "Sağlık",     "isletme_sayisi": 6000,  "aylik_butce": 1000, "yazilim_sayisi": 3},
    {"id": 7,  "isim": "Avukatlar",               "kategori": "Hukuk",      "isletme_sayisi": 50000, "aylik_butce": 1500, "yazilim_sayisi": 5},
    {"id": 8,  "isim": "Muhasebeciler",           "kategori": "Muhasebe",   "isletme_sayisi": 40000, "aylik_butce": 1200, "yazilim_sayisi": 7},
    {"id": 9,  "isim": "Mali Müşavirler",         "kategori": "Muhasebe",   "isletme_sayisi": 30000, "aylik_butce": 1500, "yazilim_sayisi": 6},
    {"id": 10, "isim": "Kuyumcular",              "kategori": "Perakende",  "isletme_sayisi": 35000, "aylik_butce": 2500, "yazilim_sayisi": 4},
    {"id": 11, "isim": "Emlakçılar",              "kategori": "Perakende",  "isletme_sayisi": 60000, "aylik_butce": 800,  "yazilim_sayisi": 12},
    {"id": 12, "isim": "Oto Galeriler",           "kategori": "Perakende",  "isletme_sayisi": 25000, "aylik_butce": 1800, "yazilim_sayisi": 8},
    {"id": 13, "isim": "Oto Servisleri",          "kategori": "Hizmet",     "isletme_sayisi": 60000, "aylik_butce": 1000, "yazilim_sayisi": 6},
    {"id": 14, "isim": "Tornacılar",              "kategori": "Sanayi",     "isletme_sayisi": 15000, "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 15, "isim": "Marangozlar",             "kategori": "Sanayi",     "isletme_sayisi": 20000, "aylik_butce": 800,  "yazilim_sayisi": 2},
    {"id": 16, "isim": "Restoranlar",             "kategori": "Gıda",       "isletme_sayisi": 200000,"aylik_butce": 1500, "yazilim_sayisi": 25},
    {"id": 17, "isim": "Kafeler",                 "kategori": "Gıda",       "isletme_sayisi": 80000, "aylik_butce": 800,  "yazilim_sayisi": 20},
    {"id": 18, "isim": "Pastaneler",              "kategori": "Gıda",       "isletme_sayisi": 30000, "aylik_butce": 1000, "yazilim_sayisi": 5},
    {"id": 19, "isim": "Kasaplar",                "kategori": "Gıda",       "isletme_sayisi": 40000, "aylik_butce": 700,  "yazilim_sayisi": 3},
    {"id": 20, "isim": "Manavlar",                "kategori": "Gıda",       "isletme_sayisi": 50000, "aylik_butce": 500,  "yazilim_sayisi": 2},
    {"id": 21, "isim": "Berberler",               "kategori": "Güzellik",   "isletme_sayisi": 80000, "aylik_butce": 500,  "yazilim_sayisi": 8},
    {"id": 22, "isim": "Kuaförler",               "kategori": "Güzellik",   "isletme_sayisi": 70000, "aylik_butce": 700,  "yazilim_sayisi": 8},
    {"id": 23, "isim": "Güzellik Salonları",      "kategori": "Güzellik",   "isletme_sayisi": 40000, "aylik_butce": 1500, "yazilim_sayisi": 10},
    {"id": 24, "isim": "Spor Salonları",          "kategori": "Spor",       "isletme_sayisi": 10000, "aylik_butce": 2000, "yazilim_sayisi": 7},
    {"id": 25, "isim": "Düğün Salonları",         "kategori": "Etkinlik",   "isletme_sayisi": 8000,  "aylik_butce": 1800, "yazilim_sayisi": 4},
    {"id": 26, "isim": "Fotoğrafçılar",           "kategori": "Etkinlik",   "isletme_sayisi": 20000, "aylik_butce": 900,  "yazilim_sayisi": 6},
    {"id": 27, "isim": "Organizasyon Şirketleri", "kategori": "Etkinlik",   "isletme_sayisi": 5000,  "aylik_butce": 2500, "yazilim_sayisi": 3},
    {"id": 28, "isim": "Matbaalar",               "kategori": "Sanayi",     "isletme_sayisi": 12000, "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 29, "isim": "Çiçekçiler",              "kategori": "Perakende",  "isletme_sayisi": 25000, "aylik_butce": 600,  "yazilim_sayisi": 3},
    {"id": 30, "isim": "Terziler",                "kategori": "Hizmet",     "isletme_sayisi": 30000, "aylik_butce": 500,  "yazilim_sayisi": 1},
]

# =====================================================================
# 3. HAFIZA
# =====================================================================
@st.cache_resource
def get_hafiza():
    return {
        "sektor_verileri": {},
        "son_guncelleme": None,
        "log": [],
        "calisiyor": False,
    }

# =====================================================================
# 4. DEMO VERİ ÜRETİCİ
# =====================================================================
def demo_fiyat_uret():
    time.sleep(0.05)
    temel = {
        "Vast.ai": 0.180,
        "RunPod": 0.420,
        "Shadeform": 0.280,
        "GPU.ai": 0.310,
        "Massed Compute": 0.290,
    }
    fiyatlar = {}
    for havuz, fiyat in temel.items():
        dalgalanma = random.uniform(-0.08, 0.08)
        if random.random() < 0.10:
            dalgalanma = random.uniform(-0.25, 0.25)
        fiyatlar[havuz] = round(max(0.100, fiyat * (1 + dalgalanma)), 3)
    return fiyatlar

# =====================================================================
# 5. PUANLAMA MOTORU
# =====================================================================
def sektor_puanla(veri):
    kaynaklar = veri.get("kaynaklar", {})
    
    # TALEP
    talep = 0
    gt = kaynaklar.get("google_trends", {})
    if "talep_puani" in gt: talep += gt["talep_puani"] * 0.5
    eks = kaynaklar.get("eksisozluk", {})
    if "tartisma_puani" in eks: talep += eks["tartisma_puani"] * 0.3
    dh = kaynaklar.get("donanimhaber", {})
    if "teknik_soru_puani" in dh: talep += dh["teknik_soru_puani"] * 0.2
    talep = min(100, talep)
    
    # ÖDEME
    isletme = veri.get("isletme_sayisi", 0)
    butce = veri.get("aylik_butce", 0)
    isletme_puan = min(100, (isletme / 100000) * 100)
    butce_puan = min(100, (butce / 3000) * 100)
    odeme = (isletme_puan * 0.4) + (butce_puan * 0.6)
    
    # ACİLİYET
    sv = kaynaklar.get("sikayetvar", {})
    aciliyet = sv.get("aciliyet_puani", 0)
    
    # REKABET
    yazilim = veri.get("yazilim_sayisi", 0)
    rekabet = max(0, 100 - (yazilim * 4))
    
    # TOPLAM
    toplam = talep * 0.35 + odeme * 0.30 + aciliyet * 0.20 + rekabet * 0.15
    
    return {
        "talep_puani": round(talep, 1),
        "odeme_puani": round(odeme, 1),
        "aciliyet_puani": round(aciliyet, 1),
        "rekabet_puani": round(rekabet, 1),
        "toplam_puan": round(toplam, 1),
        "trend": gt.get("trend", "bilinmiyor"),
    }

def odemeye_hazir_mi(veri, puanlar):
    return (puanlar["toplam_puan"] >= 60 and
            puanlar["odeme_puani"] >= 50 and
            puanlar["aciliyet_puani"] >= 40 and
            puanlar["rekabet_puani"] >= 40)

def tum_sektorleri_puanla(hafiza):
    sonuclar = []
    for sid, veri in hafiza.get("sektor_verileri", {}).items():
        try:
            puanlar = sektor_puanla(veri)
            s = veri.copy()
            s.update(puanlar)
            s["odemeye_hazir"] = odemeye_hazir_mi(veri, puanlar)
            sonuclar.append(s)
        except Exception as e:
            hafiza["log"].append(f"Puanlama hatası: {str(e)[:80]}")
    sonuclar.sort(key=lambda x: x["toplam_puan"], reverse=True)
    return sonuclar

def kategori_ozeti(sonuclar):
    kat = {}
    for s in sonuclar:
        k = s["kategori"]
        if k not in kat:
            kat[k] = {"toplam": 0, "sayi": 0, "isletme": 0}
        kat[k]["toplam"] += s["toplam_puan"]
        kat[k]["sayi"] += 1
        kat[k]["isletme"] += s["isletme_sayisi"]
    ozet = []
    for k, v in kat.items():
        ozet.append({
            "kategori": k,
            "ortalama_puan": round(v["toplam"] / v["sayi"], 1),
            "sektor_sayisi": v["sayi"],
            "toplam_isletme": v["isletme"],
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
# 6. CACHE
# =====================================================================
def cache_gecerli_mi(hafiza):
    son = hafiza.get("son_guncelleme")
    if not son: return False
    try:
        son_dt = datetime.strptime(son, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - son_dt).total_seconds() < CACHE_SURESI
    except: return False

def verileri_kaydet(hafiza):
    try:
        veri = {
            "sektor_verileri": hafiza.get("sektor_verileri", {}),
            "son_guncelleme": hafiza.get("son_guncelleme"),
            "kayit_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    except Exception as e:
        hafiza["log"].append(f"Kayıt hatası: {str(e)[:80]}")

def verileri_yukle(hafiza):
    try:
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
            hafiza["sektor_verileri"] = {int(k): v for k, v in veri.get("sektor_verileri", {}).items()}
            hafiza["son_guncelleme"] = veri.get("son_guncelleme")
            return True
    except: pass
    return False

def manuel_veri_yukle():
    if os.path.exists(MANUEL_VERI_DOSYASI):
        try:
            with open(MANUEL_VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def manuel_veri_kaydet(veri):
    with open(MANUEL_VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

def manuel_veri_uygula(hafiza):
    manuel = manuel_veri_yukle()
    for sid, veriler in manuel.items():
        sid_int = int(sid)
        if sid_int in hafiza["sektor_verileri"]:
            for kaynak, veri in veriler.items():
                if kaynak in hafiza["sektor_verileri"][sid_int]["kaynaklar"]:
                    hafiza["sektor_verileri"][sid_int]["kaynaklar"][kaynak] = veri # =====================================================================
# 7. SCRAPER — GOOGLE TRENDS
# =====================================================================
async def google_trends_ara(session, sektor_adi):
    if DEMO_MODE:
        return {"kaynak": "Google Trends", "talep_puani": random.randint(30, 95),
                "trend": random.choice(["yükseliyor", "sabit", "düşüyor"]),
                "arama_hacmi": random.randint(1000, 50000)}
    def _sync():
        try:
            from pytrends.request import TrendReq
            pt = TrendReq(hl='tr-TR', tz=180, timeout=(10, 25))
            kelime = sektor_adi.replace("leri", "").replace("lar", "").strip()
            pt.build_payload([kelime], cat=0, timeframe='today 12-m', geo='TR')
            df = pt.interest_over_time()
            if not df.empty and kelime in df.columns:
                ort = int(df[kelime].mean())
                son = int(df[kelime].tail(30).mean()) if len(df) >= 30 else ort
                ilk = int(df[kelime].head(30).mean()) if len(df) >= 30 else ort
                trend = "yükseliyor" if son > ilk * 1.15 else "düşüyor" if son < ilk * 0.85 else "sabit"
                return {"kaynak": "Google Trends", "talep_puani": ort, "trend": trend,
                        "arama_hacmi": ort * 100}
        except Exception as e:
            return {"kaynak": "Google Trends", "hata": str(e)[:80], "talep_puani": 0}
        return {"kaynak": "Google Trends", "talep_puani": 0}
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync)

# =====================================================================
# 8. SCRAPER — ŞİKAYETVAR
# =====================================================================
async def sikayetvar_ara(session, sektor_adi):
    if DEMO_MODE:
        return {"kaynak": "Şikayetvar", "sikayet_sayisi": random.randint(50, 3000),
                "aciliyet_puani": random.randint(30, 95)}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
               "Accept-Language": "tr-TR,tr;q=0.9"}
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://www.sikayetvar.com/arama?q={kelime}"
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                sayi = 0
                m = re.search(r'(\d[\d.,]*)\s*(?:şikayet|sonuç|kayıt)', html, re.IGNORECASE)
                if m: sayi = int(m.group(1).replace(".", "").replace(",", ""))
                if sayi == 0:
                    m = re.search(r'"totalCount"\s*:\s*(\d+)', html)
                    if m: sayi = int(m.group(1))
                return {"kaynak": "Şikayetvar", "sikayet_sayisi": sayi,
                        "aciliyet_puani": min(100, sayi // 10)}
            return {"kaynak": "Şikayetvar", "hata": f"HTTP {resp.status}", "aciliyet_puani": 0}
    except Exception as e:
        return {"kaynak": "Şikayetvar", "hata": str(e)[:80], "aciliyet_puani": 0}

# =====================================================================
# 9. SCRAPER — EKŞİ SÖZLÜK
# =====================================================================
async def eksisozluk_ara(session, sektor_adi):
    if DEMO_MODE:
        return {"kaynak": "Ekşi Sözlük", "baslik_sayisi": random.randint(10, 500),
                "tartisma_puani": random.randint(20, 90)}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
               "Accept-Language": "tr-TR,tr;q=0.9"}
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={kelime}"
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                basliklar = soup.find_all("a", class_="content-title")
                sayi = len(basliklar)
                return {"kaynak": "Ekşi Sözlük", "baslik_sayisi": sayi,
                        "tartisma_puani": min(100, sayi * 2)}
            return {"kaynak": "Ekşi Sözlük", "hata": f"HTTP {resp.status}", "tartisma_puani": 0}
    except Exception as e:
        return {"kaynak": "Ekşi Sözlük", "hata": str(e)[:80], "tartisma_puani": 0}

# =====================================================================
# 10. SCRAPER — DONANIM HABER
# =====================================================================
async def donanimhaber_ara(session, sektor_adi):
    if DEMO_MODE:
        return {"kaynak": "Donanım Haber", "konu_sayisi": random.randint(20, 800),
                "teknik_soru_puani": random.randint(30, 90)}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
               "Accept-Language": "tr-TR,tr;q=0.9"}
    try:
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://forum.donanimhaber.com/arama?q={kelime}"
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                sayi = 0
                m = re.search(r'(\d[\d.,]*)\s*(?:sonuç|konu|bulundu)', html, re.IGNORECASE)
                if m: sayi = int(m.group(1).replace(".", "").replace(",", ""))
                return {"kaynak": "Donanım Haber", "konu_sayisi": sayi,
                        "teknik_soru_puani": min(100, sayi)}
            return {"kaynak": "Donanım Haber", "hata": f"HTTP {resp.status}", "teknik_soru_puani": 0}
    except Exception as e:
        return {"kaynak": "Donanım Haber", "hata": str(e)[:80], "teknik_soru_puani": 0}

# =====================================================================
# 11. SCRAPER — SAHİBİNDEN (Manuel)
# =====================================================================
async def sahibinden_ara(session, sektor_adi):
    if DEMO_MODE:
        return {"kaynak": "Sahibinden", "ilan_sayisi": random.randint(100, 10000),
                "pazar_canliligi": random.randint(30, 95)}
    return {"kaynak": "Sahibinden", "ilan_sayisi": 0, "pazar_canliligi": 0,
            "not": "Manuel giriş gerekli"}

# =====================================================================
# 12. RATE LIMIT
# =====================================================================
async def rate_limit_bekle(kaynak_adi):
    simdi = time.time()
    son = _kaynak_son_kullanim.get(kaynak_adi, 0)
    bekleme = RATE_LIMITS.get(kaynak_adi, 1.0)
    gecen = simdi - son
    if gecen < bekleme:
        await asyncio.sleep(bekleme - gecen)
    _kaynak_son_kullanim[kaynak_adi] = time.time() # =====================================================================
# 13. TEK SEKTÖR TARAMA
# =====================================================================
async def sektor_tara(session, sektor):
    sektor_adi = sektor["isim"]
    
    async def guvenli(kaynak_adi, fonk):
        try:
            await rate_limit_bekle(kaynak_adi)
            return await fonk(session, sektor_adi)
        except Exception as e:
            return {"kaynak": kaynak_adi, "hata": str(e)[:80]}
    
    gorevler = [
        guvenli("google_trends", google_trends_ara),
        guvenli("sikayetvar", sikayetvar_ara),
        guvenli("eksisozluk", eksisozluk_ara),
        guvenli("donanimhaber", donanimhaber_ara),
        guvenli("sahibinden", sahibinden_ara),
    ]
    sonuclar_liste = await asyncio.gather(*gorevler, return_exceptions=True)
    isimler = ["google_trends", "sikayetvar", "eksisozluk", "donanimhaber", "sahibinden"]
    kaynaklar = {}
    for i, isim in enumerate(isimler):
        s = sonuclar_liste[i]
        kaynaklar[isim] = s if not isinstance(s, Exception) else {"hata": str(s)[:80]}
    basarili = sum(1 for v in kaynaklar.values() if "hata" not in v)
    
    return {
        "sektor_id": sektor["id"],
        "isim": sektor_adi,
        "kategori": sektor["kategori"],
        "isletme_sayisi": sektor["isletme_sayisi"],
        "aylik_butce": sektor["aylik_butce"],
        "yazilim_sayisi": sektor["yazilim_sayisi"],
        "kaynaklar": kaynaklar,
        "basarili_kaynak": basarili,
        "tarama_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# =====================================================================
# 14. TÜM SEKTÖRLERİ TARA
# =====================================================================
async def tum_sektorleri_tara(hafiza):
    hafiza["log"].append(f"🔍 Tarama başladı: {len(SEKTORLER)} sektör")
    hafiza["log"].append(f"⏱️ Tahmini süre: ~{len(SEKTORLER) * 5 // 60} dakika")
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        connector=aiohttp.TCPConnector(limit=5)
    ) as session:
        for i, sektor in enumerate(SEKTORLER):
            try:
                hafiza["log"].append(f"⏳ [{i+1}/{len(SEKTORLER)}] {sektor['isim']}")
                sonuc = await sektor_tara(session, sektor)
                hafiza["sektor_verileri"][sektor["id"]] = sonuc
                if (i + 1) % 5 == 0:
                    verileri_kaydet(hafiza)
                await asyncio.sleep(0.8)
            except Exception as e:
                hafiza["log"].append(f"❌ {sektor['isim']}: {str(e)[:80]}")
    
    hafiza["son_guncelleme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verileri_kaydet(hafiza)
    hafiza["log"].append(f"✅ Tamamlandı.")
    if len(hafiza["log"]) > 200:
        hafiza["log"] = hafiza["log"][-200:]

# =====================================================================
# 15. BOT BAŞLATICI
# =====================================================================
def bot_baslat(hafiza):
    if hafiza["calisiyor"]: return
    hafiza["calisiyor"] = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(tum_sektorleri_tara(hafiza))
    except Exception as e:
        hafiza["log"].append(f"Bot çöktü: {str(e)[:100]}")
    finally:
        hafiza["calisiyor"] = False # =====================================================================
# 16. STREAMLIT ARAYÜZÜ
# =====================================================================
st.set_page_config(
    page_title="Fırsat Madenciliği",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OTURUM AÇMA
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 Fırsat Madenciliği Paneli</h2>", unsafe_allow_html=True)
    k = st.text_input("Kullanıcı Adı", key="u")
    s = st.text_input("Şifre", type="password", key="p")
    if st.button("Giriş"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state["oturum_acik"] = True
            st.rerun()
        else:
            st.error("Hatalı giriş!")
else:
    hafiza = get_hafiza()
    
    # SOL MENÜ
    st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
    st.sidebar.markdown("---")
    
    if DEMO_MODE:
        st.sidebar.success("🧪 DEMO MODU")
    else:
        st.sidebar.warning("🔴 GERÇEK MOD")
    
    st.sidebar.caption(f"Sektör: {len(SEKTORLER)}")
    st.sidebar.caption(f"Son güncelleme: {hafiza.get('son_guncelleme', '-')}")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🔄 Verileri Yenile"):
        hafiza["sektor_verileri"] = {}
        hafiza["log"] = []
        hafiza["calisiyor"] = False
        if os.path.exists(VERI_DOSYASI):
            try: os.remove(VERI_DOSYASI)
            except: pass
        st.rerun()
    
    if st.sidebar.button("📂 Cache Temizle"):
        if os.path.exists(VERI_DOSYASI):
            try: os.remove(VERI_DOSYASI)
            except: pass
        hafiza["sektor_verileri"] = {}
        hafiza["son_guncelleme"] = None
        hafiza["log"] = []
        st.rerun()
    
    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Puanlama:**")
    st.sidebar.caption("Talep %35 | Ödeme %30")
    st.sidebar.caption("Aciliyet %20 | Rekabet %15")
    
    # VERİ YÜKLEME
    if not hafiza["sektor_verileri"]:
        verileri_yukle(hafiza)
    manuel_veri_uygula(hafiza)
    
    # OTOMATİK BAŞLAT
    if not cache_gecerli_mi(hafiza) and not hafiza["calisiyor"]:
        t = threading.Thread(target=bot_baslat, args=(hafiza,), daemon=True)
        t.start()
        time.sleep(0.5)
    
    # BAŞLIK
    st.title("🎯 Fırsat Madenciliği — 30 Sektör")
    st.caption("Hangi sektör çözüm bekliyor? Hangisi ödemeye hazır?")
    st.markdown("---")
    
    # TARAMA DURUMU
    if hafiza["calisiyor"]:
        tamamlanan = len(hafiza["sektor_verileri"])
        toplam = len(SEKTORLER)
        st.info(f"⏳ Tarama sürüyor... {tamamlanan}/{toplam} sektör")
        st.progress(tamamlanan / toplam if toplam > 0 else 0)
        if st.button("🔄 Durumu Güncelle"):
            st.rerun()
        st.stop()
    
    if not hafiza["sektor_verileri"]:
        st.warning("Henüz veri yok. Tarama başlatılıyor...")
        if st.button("🔄 Yenile"):
            st.rerun()
        st.stop()
    
    # SONUÇLAR
    sonuclar = tum_sektorleri_puanla(hafiza)
    if not sonuclar:
        st.warning("Puanlanacak veri yok.")
        st.stop()
    
    # ÜST METRİKLER
    odemeye_hazir_sayisi = sum(1 for s in sonuclar if s["odemeye_hazir"])
    en_yuksek = max(s["toplam_puan"] for s in sonuclar)
    ort = sum(s["toplam_puan"] for s in sonuclar) / len(sonuclar)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("📊 Analiz", f"{len(sonuclar)} Sektör")
    with c2: st.metric("✅ Hazır", f"{odemeye_hazir_sayisi} Sektör")
    with c3: st.metric("🏆 En Yüksek", f"{en_yuksek:.1f}")
    with c4: st.metric("📈 Ortalama", f"{ort:.1f}")
    
    st.markdown("---")
    
    # KAYNAK DURUMU
    with st.expander("📡 Kaynak Durumu"):
        kaynak_etiket = {"google_trends": "Google Trends", "sikayetvar": "Şikayetvar",
                        "eksisozluk": "Ekşi Sözlük", "donanimhaber": "Donanım Haber",
                        "sahibinden": "Sahibinden"}
        durum = []
        for kaynak, etiket in kaynak_etiket.items():
            bas = 0; hat = 0
            for s in hafiza["sektor_verileri"].values():
                v = s.get("kaynaklar", {}).get(kaynak, {})
                if "hata" in v: hat += 1
                else: bas += 1
            tot = bas + hat
            orani = (bas / tot * 100) if tot > 0 else 0
            durum.append({
                "Kaynak": etiket,
                "Başarılı": bas,
                "Hatalı": hat,
                "Başarı %": f"{orani:.0f}%",
                "Durum": "✅" if orani > 70 else "⚠️" if orani > 30 else "❌"
            })
        st.dataframe(pd.DataFrame(durum), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # ÖDEMEYE HAZIR
    st.subheader("💰 Ödemeye Hazır Sektörler")
    hazir = [s for s in sonuclar if s["odemeye_hazir"]]
    
    if hazir:
        for s in hazir[:10]:
            col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
            with col_a:
                st.markdown(f"### 🎯 {s['isim']}")
                st.caption(f"{s['kategori']} | Trend: {s.get('trend','-')}")
            with col_b: st.metric("Fırsat", f"{s['toplam_puan']:.1f}")
            with col_c: st.metric("İşletme", f"{s['isletme_sayisi']:,}")
            with col_d: st.metric("Bütçe", f"{s['aylik_butce']} TL")
            cc1, cc2, cc3, cc4 = st.columns(4)
            with cc1: st.caption(f"📈 Talep: {s['talep_puani']:.0f}")
            with cc2: st.caption(f"💵 Ödeme: {s['odeme_puani']:.0f}")
            with cc3: st.caption(f"⚠️ Aciliyet: {s['aciliyet_puani']:.0f}")
            with cc4: st.caption(f"🥊 Rekabet: {s['rekabet_puani']:.0f}")
            st.markdown("---")
    else:
        st.info("Kriterleri geçen sektör yok.")
    
    # TÜM SEKTÖRLER TABLO
    st.subheader("📋 Tüm Sektörler")
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
            "Durum": "✅" if s["odemeye_hazir"] else "—",
        })
    df = pd.DataFrame(df_veri)
    sadece_hazir = st.checkbox("Sadece ödemeye hazır")
    df_goster = df[df["Durum"] == "✅"] if sadece_hazir else df
    st.dataframe(df_goster, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # KATEGORİ ÖZETİ
    st.subheader("📂 Kategori Özeti")
    kat = kategori_ozeti(sonuclar)
    st.dataframe(pd.DataFrame(kat), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # EN İYİ 5 RAPOR
    st.subheader("🏆 En İyi 5 Detay")
    for r in rapor_olustur(sonuclar):
        with st.expander(f"#{r['sira']} {r['sektor']} — {r['toplam_puan']:.1f}"):
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown(f"**Kategori:** {r['kategori']}")
                st.markdown(f"**Trend:** {r['trend']}")
                st.markdown(f"**İşletme:** {r['isletme_sayisi']:,}")
                st.markdown(f"**Bütçe:** {r['aylik_butce']} TL")
            with cc2:
                st.markdown(f"**Talep:** {r['talep']:.0f}")
                st.markdown(f"**Ödeme:** {r['odeme']:.0f}")
                st.markdown(f"**Aciliyet:** {r['aciliyet']:.0f}")
                st.markdown(f"**Rekabet:** {r['rekabet']:.0f}")
            st.markdown(f"**Potansiyel:** {r['potansiyel_aylik_gelir']:,.0f} TL/ay")
            if r["odemeye_hazir"]:
                st.success("✅ Ödemeye hazır")
    
    st.markdown("---")
    
    # MANUEL VERİ GİRİŞİ
    with st.expander("✍️ Manuel Veri Girişi"):
        manuel = manuel_veri_yukle()
        secenekler = {s["id"]: s["isim"] for s in SEKTORLER}
        secili = st.selectbox("Sektör", list(secenekler.keys()),
                             format_func=lambda x: secenekler[x])
        cc1, cc2, cc3 = st.columns(3)
        with cc1: sv = st.number_input("Şikayetvar", 0, 100, 50)
        with cc2: eks = st.number_input("Ekşi", 0, 100, 50)
        with cc3: dh = st.number_input("Donanım Haber", 0, 100, 50)
        if st.button("💾 Kaydet"):
            if str(secili) not in manuel: manuel[str(secili)] = {}
            manuel[str(secili)]["sikayetvar"] = {"kaynak": "Şikayetvar",
                "sikayet_sayisi": sv * 10, "aciliyet_puani": sv, "manuel": True}
            manuel[str(secili)]["eksisozluk"] = {"kaynak": "Ekşi Sözlük",
                "baslik_sayisi": eks, "tartisma_puani": eks, "manuel": True}
            manuel[str(secili)]["donanimhaber"] = {"kaynak": "Donanım Haber",
                "konu_sayisi": dh, "teknik_soru_puani": dh, "manuel": True}
            manuel_veri_kaydet(manuel)
            manuel_veri_uygula(hafiza)
            st.success("Kaydedildi. Sayfayı yenileyin.")
    
    st.markdown("---")
    
    # LOGLAR
    with st.expander("🔧 Sistem Logları"):
        for log in hafiza.get("log", [])[-50:]:
            st.text(log)
