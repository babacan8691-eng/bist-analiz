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

# =====================================================================
# 1. AYARLAR
# =====================================================================
DEMO_MODE = True  # True: gerçek scraping yapılmaz, simüle veri üretir
                  # False: gerçek veri çekilir (yavaş ama gerçek)

VERI_DOSYASI = "firsat_verileri.json"
CACHE_SURESI = 24 * 60 * 60  # 24 saat — veriyi bu süre boyunca tekrar çekmez

# =====================================================================
# 2. 30 SEKTÖR TANIMI
# =====================================================================
SEKTORLER = [
    # === SAĞLIK ===
    {"id": 1,  "isim": "Veteriner Klinikleri",     "kategori": "Sağlık",     "isletme_sayisi": 12000, "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 2,  "isim": "Diş Hekimleri",            "kategori": "Sağlık",     "isletme_sayisi": 25000, "aylik_butce": 2000, "yazilim_sayisi": 8},
    {"id": 3,  "isim": "Psikologlar",              "kategori": "Sağlık",     "isletme_sayisi": 15000, "aylik_butce": 800,  "yazilim_sayisi": 4},
    {"id": 4,  "isim": "Fizyoterapistler",         "kategori": "Sağlık",     "isletme_sayisi": 8000,  "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 5,  "isim": "Eczaneler",                "kategori": "Sağlık",     "isletme_sayisi": 28000, "aylik_butce": 1200, "yazilim_sayisi": 6},
    {"id": 6,  "isim": "Optikçiler",               "kategori": "Sağlık",     "isletme_sayisi": 6000,  "aylik_butce": 1000, "yazilim_sayisi": 3},
    
    # === HUKUK / MUHASEBE ===
    {"id": 7,  "isim": "Avukatlar",                "kategori": "Hukuk",      "isletme_sayisi": 50000, "aylik_butce": 1500, "yazilim_sayisi": 5},
    {"id": 8,  "isim": "Muhasebeciler",            "kategori": "Muhasebe",   "isletme_sayisi": 40000, "aylik_butce": 1200, "yazilim_sayisi": 7},
    {"id": 9,  "isim": "Mali Müşavirler",          "kategori": "Muhasebe",   "isletme_sayisi": 30000, "aylik_butce": 1500, "yazilim_sayisi": 6},
    
    # === TİCARET ===
    {"id": 10, "isim": "Kuyumcular",               "kategori": "Perakende",  "isletme_sayisi": 35000, "aylik_butce": 2500, "yazilim_sayisi": 4},
    {"id": 11, "isim": "Emlakçılar",               "kategori": "Perakende",  "isletme_sayisi": 60000, "aylik_butce": 800,  "yazilim_sayisi": 12},
    {"id": 12, "isim": "Oto Galeriler",            "kategori": "Perakende",  "isletme_sayisi": 25000, "aylik_butce": 1800, "yazilim_sayisi": 8},
    {"id": 13, "isim": "Oto Servisleri",           "kategori": "Hizmet",     "isletme_sayisi": 60000, "aylik_butce": 1000, "yazilim_sayisi": 6},
    {"id": 14, "isim": "Tornacılar",               "kategori": "Sanayi",     "isletme_sayisi": 15000, "aylik_butce": 900,  "yazilim_sayisi": 2},
    {"id": 15, "isim": "Marangozlar",              "kategori": "Sanayi",     "isletme_sayisi": 20000, "aylik_butce": 800,  "yazilim_sayisi": 2},
    
    # === GIDA / SERVİS ===
    {"id": 16, "isim": "Restoranlar",              "kategori": "Gıda",       "isletme_sayisi": 200000,"aylik_butce": 1500, "yazilim_sayisi": 25},
    {"id": 17, "isim": "Kafeler",                  "kategori": "Gıda",       "isletme_sayisi": 80000, "aylik_butce": 800,  "yazilim_sayisi": 20},
    {"id": 18, "isim": "Pastaneler",               "kategori": "Gıda",       "isletme_sayisi": 30000, "aylik_butce": 1000, "yazilim_sayisi": 5},
    {"id": 19, "isim": "Kasaplar",                 "kategori": "Gıda",       "isletme_sayisi": 40000, "aylik_butce": 700,  "yazilim_sayisi": 3},
    {"id": 20, "isim": "Manavlar",                 "kategori": "Gıda",       "isletme_sayisi": 50000, "aylik_butce": 500,  "yazilim_sayisi": 2},
    
    # === GÜZELLİK / KUAFÖR ===
    {"id": 21, "isim": "Berberler",                "kategori": "Güzellik",   "isletme_sayisi": 80000, "aylik_butce": 500,  "yazilim_sayisi": 8},
    {"id": 22, "isim": "Kuaförler",                "kategori": "Güzellik",   "isletme_sayisi": 70000, "aylik_butce": 700,  "yazilim_sayisi": 8},
    {"id": 23, "isim": "Güzellik Salonları",       "kategori": "Güzellik",   "isletme_sayisi": 40000, "aylik_butce": 1500, "yazilim_sayisi": 10},
    {"id": 24, "isim": "Spor Salonları",           "kategori": "Spor",       "isletme_sayisi": 10000, "aylik_butce": 2000, "yazilim_sayisi": 7},
    
    # === ETKİNLİK ===
    {"id": 25, "isim": "Düğün Salonları",          "kategori": "Etkinlik",   "isletme_sayisi": 8000,  "aylik_butce": 1800, "yazilim_sayisi": 4},
    {"id": 26, "isim": "Fotoğrafçılar",            "kategori": "Etkinlik",   "isletme_sayisi": 20000, "aylik_butce": 900,  "yazilim_sayisi": 6},
    {"id": 27, "isim": "Organizasyon Şirketleri",  "kategori": "Etkinlik",   "isletme_sayisi": 5000,  "aylik_butce": 2500, "yazilim_sayisi": 3},
    
    # === DİĞER ===
    {"id": 28, "isim": "Matbaalar",                "kategori": "Sanayi",     "isletme_sayisi": 12000, "aylik_butce": 1500, "yazilim_sayisi": 3},
    {"id": 29, "isim": "Çiçekçiler",               "kategori": "Perakende",  "isletme_sayisi": 25000, "aylik_butce": 600,  "yazilim_sayisi": 3},
    {"id": 30, "isim": "Terziler",                 "kategori": "Hizmet",     "isletme_sayisi": 30000, "aylik_butce": 500,  "yazilim_sayisi": 1},
]

# =====================================================================
# 3. HAFIZA
# =====================================================================
@st.cache_resource
def get_hafiza():
    return {
        "sektor_verileri": {},     # Her sektör için toplanan veriler
        "son_guncelleme": None,
        "log": [],
        "calisiyor": False,
    }

# =====================================================================
# 4. VERİ TOPLAYICI — GOOGLE TRENDS
# =====================================================================
async def google_trends_ara(session, sektor_adi):
    """
    Google Trends üzerinden arama hacmini ölçer.
    Demo modda simüle veri üretir.
    """
    if DEMO_MODE:
        # Demo: sektöre göre rastgele bir talep puanı üret
        import random
        return {
            "kaynak": "Google Trends",
            "talep_puani": random.randint(30, 95),
            "trend": random.choice(["yükseliyor", "sabit", "düşüyor"]),
            "arama_hacmi": random.randint(1000, 50000),
        }
    
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl='tr-TR', tz=180)
        pytrends.build_payload([sektor_adi], cat=0, timeframe='today 12-m', geo='TR')
        df = pytrends.interest_over_time()
        if not df.empty:
            ortalama = int(df[sektor_adi].mean())
            son_ay = int(df[sektor_adi].tail(30).mean())
            ilk_ay = int(df[sektor_adi].head(30).mean())
            trend = "yükseliyor" if son_ay > ilk_ay * 1.1 else "düşüyor" if son_ay < ilk_ay * 0.9 else "sabit"
            return {
                "kaynak": "Google Trends",
                "talep_puani": ortalama,
                "trend": trend,
                "arama_hacmi": ortalama * 100,
            }
    except Exception as e:
        return {"kaynak": "Google Trends", "hata": str(e)[:80]}
    return {"kaynak": "Google Trends", "talep_puani": 0}

# =====================================================================
# 5. VERİ TOPLAYICI — ŞİKAYETVAR
# =====================================================================
async def sikayetvar_ara(session, sektor_adi):
    """
    Şikayetvar.com'da o sektörle ilgili şikayet sayısını ölçer.
    Yüksek şikayet = çözülmemiş sorun = fırsat
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Şikayetvar",
            "sikayet_sayisi": random.randint(50, 3000),
            "aciliyet_puani": random.randint(30, 95),
        }
    
    try:
        url = f"https://www.sikayetvar.com/arama?q={sektor_adi.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                # Şikayet sayısını bul
                sayi_metni = soup.find(string=re.compile(r'\d+\s*şikayet', re.IGNORECASE))
                sayi = 0
                if sayi_metni:
                    match = re.search(r'(\d+)', sayi_metni)
                    if match:
                        sayi = int(match.group(1))
                return {
                    "kaynak": "Şikayetvar",
                    "sikayet_sayisi": sayi,
                    "aciliyet_puani": min(100, sayi // 10),
                }
    except Exception as e:
        return {"kaynak": "Şikayetvar", "hata": str(e)[:80]}
    return {"kaynak": "Şikayetvar", "sikayet_sayisi": 0, "aciliyet_puani": 0}

# =====================================================================
# 6. VERİ TOPLAYICI — EKŞİ SÖZLÜK
# =====================================================================
async def eksisozluk_ara(session, sektor_adi):
    """
    Ekşi Sözlük'te o sektörle ilgili başlıkları ve tartışmaları ölçer.
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Ekşi Sözlük",
            "baslik_sayisi": random.randint(10, 500),
            "tartisma_puani": random.randint(20, 90),
        }
    
    try:
        url = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={sektor_adi.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                basliklar = soup.find_all("a", class_="content-title")
                return {
                    "kaynak": "Ekşi Sözlük",
                    "baslik_sayisi": len(basliklar),
                    "tartisma_puani": min(100, len(basliklar) * 2),
                }
    except Exception as e:
        return {"kaynak": "Ekşi Sözlük", "hata": str(e)[:80]}
    return {"kaynak": "Ekşi Sözlük", "baslik_sayisi": 0, "tartisma_puani": 0}

# =====================================================================
# 7. VERİ TOPLAYICI — DONANIM HABER
# =====================================================================
async def donanimhaber_ara(session, sektor_adi):
    """
    Donanım Haber forumunda o sektörle ilgili konu sayısını ölçer.
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Donanım Haber",
            "konu_sayisi": random.randint(20, 800),
            "teknik_soru_puani": random.randint(30, 90),
        }
    
    try:
        url = f"https://forum.donanimhaber.com/search?q={sektor_adi.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with session.get(url, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                konular = soup.find_all("a", class_="topic-title")
                return {
                    "kaynak": "Donanım Haber",
                    "konu_sayisi": len(konular),
                    "teknik_soru_puani": min(100, len(konular)),
                }
    except Exception as e:
        return {"kaynak": "Donanım Haber", "hata": str(e)[:80]}
    return {"kaynak": "Donanım Haber", "konu_sayisi": 0, "teknik_soru_puani": 0}

# =====================================================================
# 8. VERİ TOPLAYICI — SAHİBİNDEN
# =====================================================================
async def sahibinden_ara(session, sektor_adi):
    """
    Sahibinden.com'da o sektörle ilgili ilan sayısını ölçer.
    Yüksek ilan = canlı pazar
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Sahibinden",
            "ilan_sayisi": random.randint(100, 10000),
            "pazar_canliligi": random.randint(30, 95),
        }
    # Gerçek scraping Sahibinden tarafından engellenir, demo modda kalacak
    return {"kaynak": "Sahibinden", "ilan_sayisi": 0, "pazar_canliligi": 0}

# =====================================================================
# 9. TEK SEKTÖRÜ TARA (5 kaynağı paralel)
# =====================================================================
async def sektor_tara(session, sektor):
    """
    Bir sektörü 5 farklı kaynaktan paralel tarar.
    """
    sektor_adi = sektor["isim"]
    
    gorevler = [
        google_trends_ara(session, sektor_adi),
        sikayetvar_ara(session, sektor_adi),
        eksisozluk_ara(session, sektor_adi),
        donanimhaber_ara(session, sektor_adi),
        sahibinden_ara(session, sektor_adi),
    ]
    
    sonuclar = await asyncio.gather(*gorevler, return_exceptions=True)
    
    return {
        "sektor_id": sektor["id"],
        "isim": sektor_adi,
        "kategori": sektor["kategori"],
        "isletme_sayisi": sektor["isletme_sayisi"],
        "aylik_butce": sektor["aylik_butce"],
        "yazilim_sayisi": sektor["yazilim_sayisi"],
        "kaynaklar": {
            "google_trends": sonuclar[0] if not isinstance(sonuclar[0], Exception) else {"hata": "exception"},
            "sikayetvar": sonuclar[1] if not isinstance(sonuclar[1], Exception) else {"hata": "exception"},
            "eksisozluk": sonuclar[2] if not isinstance(sonuclar[2], Exception) else {"hata": "exception"},
            "donanimhaber": sonuclar[3] if not isinstance(sonuclar[3], Exception) else {"hata": "exception"},
            "sahibinden": sonuclar[4] if not isinstance(sonuclar[4], Exception) else {"hata": "exception"},
        },
        "tarama_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# =====================================================================
# 10. TÜM SEKTÖRLERİ TARA (30 sektör)
# =====================================================================
async def tum_sektorleri_tara(hafiza):
    """
    30 sektörü sırayla tarar (aynı anda değil, rate limit için).
    """
    hafiza["log"].append(f"🔍 Tarama başladı: {len(SEKTORLER)} sektör")
    
    async with aiohttp.ClientSession() as session:
        for i, sektor in enumerate(SEKTORLER):
            try:
                hafiza["log"].append(f"⏳ [{i+1}/{len(SEKTORLER)}] {sektor['isim']} taranıyor...")
                sonuc = await sektor_tara(session, sektor)
                hafiza["sektor_verileri"][sektor["id"]] = sonuc
                await asyncio.sleep(0.5)  # Rate limit için bekle
            except Exception as e:
                hafiza["log"].append(f"❌ {sektor['isim']}: {str(e)[:80]}")
    
    hafiza["son_guncelleme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hafiza["log"].append(f"✅ Tarama tamamlandı.")
    
    # Log'u 100 ile sınırla
    if len(hafiza["log"]) > 100:
        hafiza["log"] = hafiza["log"][-100:]

# =====================================================================
# 11. ARKA PLAN BOT BAŞLATICI
# =====================================================================
def bot_baslat(hafiza):
    if hafiza["calisiyor"]:
        return
    hafiza["calisiyor"] = True
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(tum_sektorleri_tara(hafiza))
    except Exception as e:
        hafiza["log"].append(f"Bot çöktü: {str(e)[:100]}")
    finally:
        hafiza["calisiyor"] = False # =====================================================================
# 12. PUANLAMA MOTORU
# =====================================================================
def sektor_puanla(veri):
    """
    Bir sektörün verilerini alır, 4 kriterde puanlar ve toplam fırsat puanı üretir.
    
    Puanlama:
    - Talep (0-100)      → Google Trends + Ekşi Sözlük + Donanım Haber
    - Ödeme Gücü (0-100) → İşletme sayısı + aylık bütçe
    - Aciliyet (0-100)   → Şikayetvar şikayetleri
    - Rekabet (0-100)    → Yazılım sayısı (düşük = iyi)
    
    Toplam = (Talep×0.35) + (Ödeme×0.30) + (Aciliyet×0.20) + (Rekabet×0.15)
    """
    kaynaklar = veri.get("kaynaklar", {})
    
    # --- TALEP PUANI ---
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
    
    # --- ÖDEME GÜCÜ PUANI ---
    isletme = veri.get("isletme_sayisi", 0)
    butce = veri.get("aylik_butce", 0)
    # İşletme sayısı: 5.000 → 50 puan, 100.000+ → 100 puan
    isletme_puan = min(100, (isletme / 100000) * 100)
    # Bütçe: 500 TL → 30 puan, 3.000 TL+ → 100 puan
    butce_puan = min(100, (butce / 3000) * 100)
    odeme_puani = (isletme_puan * 0.4) + (butce_puan * 0.6)
    
    # --- ACİLİYET PUANI ---
    sv = kaynaklar.get("sikayetvar", {})
    aciliyet_puani = sv.get("aciliyet_puani", 0)
    
    # --- REKABET PUANI (düşük yazılım = yüksek puan) ---
    yazilim = veri.get("yazilim_sayisi", 0)
    # 0 yazılım → 100 puan, 25+ yazılım → 0 puan
    rekabet_puani = max(0, 100 - (yazilim * 4))
    
    # --- TOPLAM FIRSAT PUANI ---
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

# =====================================================================
# 13. ÖDEMEYE HAZIR FİLTRESİ
# =====================================================================
def odemeye_hazir_mi(sektor_veri, puanlar):
    """
    Bir sektörün 'ödemeye hazır' olup olmadığını kontrol eder.
    
    Şartlar:
    - Toplam puan ≥ 60
    - Ödeme gücü ≥ 50
    - Aciliyet ≥ 40
    - Rekabet puanı ≥ 40 (yani yazılım sayısı az)
    """
    return (
        puanlar["toplam_puan"] >= 60 and
        puanlar["odeme_puani"] >= 50 and
        puanlar["aciliyet_puani"] >= 40 and
        puanlar["rekabet_puani"] >= 40
    )

# =====================================================================
# 14. TÜM SEKTÖRLERİ PUANLA VE SIRALA
# =====================================================================
def tum_sektorleri_puanla(hafiza):
    """
    Hafızadaki tüm sektör verilerini puanlar, sıralar ve rapor üretir.
    """
    sonuclar = []
    
    for sektor_id, veri in hafiza.get("sektor_verileri", {}).items():
        try:
            puanlar = sektor_puanla(veri)
            sektor = veri.copy()
            sektor.update(puanlar)
            sektor["odemeye_hazir"] = odemeye_hazir_mi(veri, puanlar)
            sonuclar.append(sektor)
        except Exception as e:
            hafiza["log"].append(f"Puanlama hatası (ID {sektor_id}): {str(e)[:80]}")
    
    # Toplam puana göre sırala (yüksekten düşüğe)
    sonuclar.sort(key=lambda x: x["toplam_puan"], reverse=True)
    
    return sonuclar

# =====================================================================
# 15. KATEGORİ BAZINDA ÖZET
# =====================================================================
def kategori_ozeti(sonuclar):
    """
    Kategorilere göre ortalama puanları hesaplar.
    """
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
# 16. VERİ KAYDETME / YÜKLEME
# =====================================================================
def verileri_kaydet(hafiza):
    """Hafızadaki verileri JSON dosyasına kaydeder."""
    try:
        veri = {
            "sektor_verileri": hafiza.get("sektor_verileri", {}),
            "son_guncelleme": hafiza.get("son_guncelleme"),
            "kayit_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
        hafiza["log"].append("💾 Veriler dosyaya kaydedildi.")
    except Exception as e:
        hafiza["log"].append(f"Kayıt hatası: {str(e)[:80]}")

def verileri_yukle(hafiza):
    """JSON dosyasından verileri hafızaya yükler."""
    try:
        if os.path.exists(VERI_DOSYASI):
            with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
                veri = json.load(f)
            # JSON anahtarları string olur, int'e çevir
            hafiza["sektor_verileri"] = {int(k): v for k, v in veri.get("sektor_verileri", {}).items()}
            hafiza["son_guncelleme"] = veri.get("son_guncelleme")
            hafiza["log"].append(f"📂 Veriler yüklendi (son güncelleme: {hafiza['son_guncelleme']})")
            return True
    except Exception as e:
        hafiza["log"].append(f"Yükleme hatası: {str(e)[:80]}")
    return False

# =====================================================================
# 17. CACHE KONTROLÜ
# =====================================================================
def cache_gecerli_mi(hafiza):
    """Son güncellemenin 24 saatten yeni olup olmadığını kontrol eder."""
    son = hafiza.get("son_guncelleme")
    if not son:
        return False
    try:
        son_dt = datetime.strptime(son, "%Y-%m-%d %H:%M:%S")
        return (datetime.now() - son_dt).total_seconds() < CACHE_SURESI
    except:
        return False

# =====================================================================
# 18. RAPOR OLUŞTURMA
# =====================================================================
def rapor_olustur(sonuclar):
    """
    En iyi 5 sektör için detaylı rapor üretir.
    """
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
    return rapor # =====================================================================
# 19. STREAMLIT ARAYÜZÜ
# =====================================================================
st.set_page_config(
    page_title="Fırsat Madenciliği - 30 Sektör Analizi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- OTURUM AÇMA ---
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 Fırsat Madenciliği Paneli Girişi</h2>", unsafe_allow_html=True)
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
    else:
        st.sidebar.warning("🔴 GERÇEK MOD (Canlı Scraping)")

    st.sidebar.markdown("### 📊 Sistem Bilgisi")
    st.sidebar.caption(f"Sektör sayısı: {len(SEKTORLER)}")
    st.sidebar.caption(f"Kaynak sayısı: 5")
    st.sidebar.caption(f"Son güncelleme: {hafiza.get('son_guncelleme', '-')}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Kontroller")

    if st.sidebar.button("🔄 Verileri Yenile"):
        hafiza["sektor_verileri"] = {}
        hafiza["log"] = []
        hafiza["calisiyor"] = False
        verileri_kaydet(hafiza)
        st.rerun()

    if st.sidebar.button("📂 Cache'i Temizle"):
        if os.path.exists(VERI_DOSYASI):
            os.remove(VERI_DOSYASI)
        hafiza["sektor_verileri"] = {}
        hafiza["son_guncelleme"] = None
        hafiza["log"] = []
        st.rerun()

    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚖️ Puanlama Ağırlıkları")
    st.sidebar.caption("Talep: %35")
    st.sidebar.caption("Ödeme: %30")
    st.sidebar.caption("Aciliyet: %20")
    st.sidebar.caption("Rekabet: %15")

    # =================================================================
    # VERİ DURUMU KONTROLÜ
    # =================================================================
    # Cache varsa yükle
    if not hafiza["sektor_verileri"]:
        verileri_yukle(hafiza)

    # Cache geçerli değilse veya boşsa taramayı başlat
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
        st.info(f"⏳ Tarama devam ediyor... {len(hafiza['sektor_verileri'])}/{len(SEKTORLER)} sektör tamamlandı.")
        st.progress(min(1.0, len(hafiza["sektor_verileri"]) / len(SEKTORLER)))

    # =================================================================
    # SONUÇLARI HESAPLA
    # =================================================================
    if not hafiza["sektor_verileri"]:
        st.warning("Henüz veri yok. Sol menüden '🔄 Verileri Yenile' butonuna basın.")
        st.stop()

    sonuclar = tum_sektorleri_puanla(hafiza)
    
    if not sonuclar:
        st.warning("Puanlanacak veri bulunamadı.")
        st.stop()

    # =================================================================
    # ÜST ÖZET METRİKLERİ
    # =================================================================
    toplam_sektor = len(sonuclar)
    odemeye_hazir_sayisi = sum(1 for s in sonuclar if s["odemeye_hazir"])
    en_yuksek_puan = max(s["toplam_puan"] for s in sonuclar)
    ortalama_puan = sum(s["toplam_puan"] for s in sonuclar) / toplam_sektor

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Analiz Edilen", f"{toplam_sektor} Sektör")
    with col2:
        st.metric("✅ Ödemeye Hazır", f"{odemeye_hazir_sayisi} Sektör")
    with col3:
        st.metric("🏆 En Yüksek Puan", f"{en_yuksek_puan:.1f}")
    with col4:
        st.metric("📈 Ortalama Puan", f"{ortalama_puan:.1f}")

    st.markdown("---")

    # =================================================================
    # ÖDEMEYE HAZIR SEKTÖRLER (EN ÖNEMLİ BÖLÜM)
    # =================================================================
    st.subheader("💰 Ödemeye Hazır Sektörler (Öncelikli)")
    
    hazir_sektorler = [s for s in sonuclar if s["odemeye_hazir"]]
    
    if hazir_sektorler:
        st.caption(f"Bu sektörler 4 kriteri de geçti: yüksek talep, ödeme gücü, aciliyet ve düşük rekabet.")
        
        for s in hazir_sektorler[:10]:
            with st.container():
                col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
                with col_a:
                    st.markdown(f"### 🎯 {s['isim']}")
                    st.caption(f"Kategori: {s['kategori']} | Trend: {s.get('trend', '-')}")
                with col_b:
                    st.metric("Fırsat Puanı", f"{s['toplam_puan']:.1f}")
                with col_c:
                    st.metric("İşletme Sayısı", f"{s['isletme_sayisi']:,}")
                with col_d:
                    st.metric("Aylık Bütçe", f"{s['aylik_butce']} TL")
                
                # Alt detaylar
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
    # TÜM SEKTÖRLER SIRALAMASI (TABLO)
    # =================================================================
    st.subheader("📋 Tüm Sektörler Sıralaması")
    
    df_veri = []
    for s in sonuclar:
        df_veri.append({
            "Sıra": len(df_veri) + 1,
            "Sektör": s["isim"],
            "Kategori": s["kategori"],
            "Fırsat Puanı": s["toplam_puan"],
            "Talep": s["talep_puani"],
            "Ödeme": s["odeme_puani"],
            "Aciliyet": s["aciliyet_puani"],
            "Rekabet": s["rekabet_puani"],
            "Trend": s.get("trend", "-"),
            "İşletme": s["isletme_sayisi"],
            "Bütçe (TL)": s["aylik_butce"],
            "Yazılım": s["yazilim_sayisi"],
            "Durum": "✅ Hazır" if s["odemeye_hazir"] else "—",
        })
    
    df = pd.DataFrame(df_veri)
    
    # Filtreleme
    filtre_col1, filtre_col2 = st.columns(2)
    with filtre_col1:
        sadece_hazir = st.checkbox("Sadece ödemeye hazır olanları göster")
    with filtre_col2:
        min_puan = st.slider("Minimum puan", 0, 100, 0, 5)
    
    if sadece_hazir:
        df_goster = df[df["Durum"] == "✅ Hazır"]
    else:
        df_goster = df[df["Fırsat Puanı"] >= min_puan]
    
    st.dataframe(df_goster, use_container_width=True, hide_index=True)
    st.caption(f"Toplam {len(df_goster)} sektör gösteriliyor.")

    st.markdown("---")

    # =================================================================
    # KATEGORİ ÖZETİ
    # =================================================================
    st.subheader("📂 Kategori Bazında Özet")
    
    kat_ozet = kategori_ozeti(sonuclar)
    df_kat = pd.DataFrame(kat_ozet)
    df_kat.columns = ["Kategori", "Ortalama Puan", "Sektör Sayısı", "Toplam İşletme"]
    st.dataframe(df_kat, use_container_width=True, hide_index=True)

    st.markdown("---")

    # =================================================================
    # EN İYİ 5 SEKTÖR DETAY RAPORU
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
                st.markdown(f"**Talep Puanı:** {r['talep']:.0f}/100")
                st.markdown(f"**Ödeme Puanı:** {r['odeme']:.0f}/100")
                st.markdown(f"**Aciliyet Puanı:** {r['aciliyet']:.0f}/100")
                st.markdown(f"**Rekabet Puanı:** {r['rekabet']:.0f}/100")
            
            st.markdown("---")
            st.markdown(f"**Potansiyel Aylık Gelir (tahmini):** {r['potansiyel_aylik_gelir']:,.0f} TL")
            st.markdown(f"**Mevcut Yazılım Sayısı:** {r['yazilim_sayisi']}")
            if r["odemeye_hazir"]:
                st.success("✅ Bu sektör ödemeye hazır — 4 kriteri de geçti")
            else:
                st.warning("⚠️ Bazı kriterler yetersiz — dikkatli değerlendirilmeli")

    st.markdown("---")

    # =================================================================
    # SİSTEM LOGLARI
    # =================================================================
    with st.expander("🔧 Sistem Logları (Son 30 Kayıt)"):
        loglar = hafiza.get("log", [])
        if loglar:
            for log in loglar[-30:]:
                st.text(log)
        else:
            st.text("Henüz log kaydı yok.")

    # =================================================================
    # BİLGİLENDİRME
    # =================================================================
    with st.expander("❓ Sistem Nasıl Çalışır?"):
        st.markdown(
            "**Bu sistem ne yapar?**\n\n"
            "30 farklı sektörü 5 farklı kaynaktan tarar ve her sektöre **fırsat puanı** verir.\n\n"
            "**5 Kaynak:**\n"
            "- Google Trends → İnsanlar ne arıyor?\n"
            "- Şikayetvar → İnsanlar neyden şikayet ediyor?\n"
            "- Ekşi Sözlük → Ne tartışılıyor?\n"
            "- Donanım Haber → Hangi teknik sorunlar var?\n"
            "- Sahibinden → Hangi pazar canlı?\n\n"
            "**4 Kriter (Puanlama):**\n"
            "- **Talep (%35):** Bu sektör ne kadar aranıyor?\n"
            "- **Ödeme (%30):** Bu sektör ne kadar ödeyebilir?\n"
            "- **Aciliyet (%20):** Ne kadar şikayet var?\n"
            "- **Rekabet (%15):** Kaç yazılım var? (Az = iyi)\n\n"
            "**Ödemeye Hazır Şartları:**\n"
            "- Toplam puan ≥ 60\n"
            "- Ödeme gücü ≥ 50\n"
            "- Aciliyet ≥ 40\n"
            "- Rekabet puanı ≥ 40 (yani yazılım sayısı az)\n\n"
            "**Nasıl Kullanılır?**\n"
            "1. 'Ödemeye Hazır Sektörler' bölümüne bak\n"
            "2. En yüksek puanlı 3 sektörü not al\n"
            "3. O sektörlerdeki işletmelerle konuş\n"
            "4. Ürünü onlara göre tasarla\n\n"
            f"**Şu anki mod:** {'🧪 DEMO (sanal veri)' if DEMO_MODE else '🔴 GERÇEK (canlı veri)'}\n\n"
            "Gerçek moda geçmek için kodun başındaki `DEMO_MODE = True` satırını `False` yapın."
        )

    # =================================================================
    # SAYFAYI PERİYODİK YENİLE (Tarama devam ediyorsa)
    # =================================================================
    if hafiza["calisiyor"]:
        time.sleep(3)
        st.rerun()
