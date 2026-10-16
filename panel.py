# =====================================================================
# 4. VERİ TOPLAYICI — GOOGLE TRENDS (Gerçek Mod - Geliştirilmiş)
# =====================================================================
async def google_trends_ara(session, sektor_adi):
    """
    Google Trends — gerçek arama hacmi.
    pytrends kütüphanesi doğrudan çalışır, async wrapper ile.
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Google Trends",
            "talep_puani": random.randint(30, 95),
            "trend": random.choice(["yükseliyor", "sabit", "düşüyor"]),
            "arama_hacmi": random.randint(1000, 50000),
        }
    
    def _sync_cagri():
        try:
            from pytrends.request import TrendReq
            import time as _time
            pytrends = TrendReq(hl='tr-TR', tz=180, timeout=(10, 25))
            # Anahtar kelimeyi sadeleştir
            kelime = sektor_adi.replace("leri", "").replace("lar", "").strip()
            pytrends.build_payload([kelime], cat=0, timeframe='today 12-m', geo='TR')
            df = pytrends.interest_over_time()
            if not df.empty and kelime in df.columns:
                ortalama = int(df[kelime].mean())
                son_ay = int(df[kelime].tail(30).mean()) if len(df) >= 30 else ortalama
                ilk_ay = int(df[kelime].head(30).mean()) if len(df) >= 30 else ortalama
                if son_ay > ilk_ay * 1.15:
                    trend = "yükseliyor"
                elif son_ay < ilk_ay * 0.85:
                    trend = "düşüyor"
                else:
                    trend = "sabit"
                return {
                    "kaynak": "Google Trends",
                    "talep_puani": ortalama,
                    "trend": trend,
                    "arama_hacmi": ortalama * 100,
                }
        except Exception as e:
            return {"kaynak": "Google Trends", "hata": str(e)[:80], "talep_puani": 0}
        return {"kaynak": "Google Trends", "talep_puani": 0}
    
    # Async içinde sync çağrı (executor ile)
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_cagri)

# =====================================================================
# 5. VERİ TOPLAYICI — ŞİKAYETVAR (Gerçek Mod - Geliştirilmiş)
# =====================================================================
async def sikayetvar_ara(session, sektor_adi):
    """
    Şikayetvar.com — gerçek şikayet sayısı.
    Birden fazla HTML pattern'i dener.
    """
    if DEMO_MODE:
        import random
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
        # Arama kelimesini sadeleştir
        kelime = sektor_adi.lower().replace("leri", "").replace("lar", "").strip()
        url = f"https://www.sikayetvar.com/arama?q={kelime}"
        
        async with session.get(url, headers=headers, timeout=20, allow_redirects=True) as resp:
            if resp.status == 200:
                html = await resp.text()
                
                # Şikayet sayısını bulmak için birden fazla pattern dene
                sayi = 0
                
                # Pattern 1: "X şikayet" veya "X sonuç"
                match = re.search(r'(\d[\d.,]*)\s*(?:şikayet|sonuç|kayıt)', html, re.IGNORECASE)
                if match:
                    sayi = int(match.group(1).replace(".", "").replace(",", ""))
                
                # Pattern 2: JSON içinde
                if sayi == 0:
                    match = re.search(r'"totalCount"\s*:\s*(\d+)', html)
                    if match:
                        sayi = int(match.group(1))
                
                # Pattern 3: Şikayet kartı sayısı
                if sayi == 0:
                    soup = BeautifulSoup(html, "lxml")
                    kartlar = soup.find_all("article", class_=re.compile(r"card|complaint", re.I))
                    sayi = len(kartlar)
                
                return {
                    "kaynak": "Şikayetvar",
                    "sikayet_sayisi": sayi,
                    "aciliyet_puani": min(100, sayi // 10),
                }
            else:
                return {"kaynak": "Şikayetvar", "hata": f"HTTP {resp.status}", "aciliyet_puani": 0}
    except Exception as e:
        return {"kaynak": "Şikayetvar", "hata": str(e)[:80], "aciliyet_puani": 0}

# =====================================================================
# 6. VERİ TOPLAYICI — EKŞİ SÖZLÜK (Gerçek Mod - Geliştirilmiş)
# =====================================================================
async def eksisozluk_ara(session, sektor_adi):
    """
    Ekşi Sözlük — başlık sayısı.
    Ekşi Sözlük bot koruması vardır, düşük başarı oranı.
    """
    if DEMO_MODE:
        import random
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
        url = f"https://eksisozluk.com/basliklar/ara?SearchForm.Keywords={kelime}&SearchForm.NiceOnlyPattern=false"
        
        async with session.get(url, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                html = await resp.text()
                soup = BeautifulSoup(html, "lxml")
                # Başlık listesi
                basliklar = soup.find_all("a", class_="content-title")
                if not basliklar:
                    # Alternatif selector
                    basliklar = soup.find_all("li", class_="content") 
                sayi = len(basliklar)
                return {
                    "kaynak": "Ekşi Sözlük",
                    "baslik_sayisi": sayi,
                    "tartisma_puani": min(100, sayi * 2),
                }
            else:
                return {"kaynak": "Ekşi Sözlük", "hata": f"HTTP {resp.status}", "tartisma_puani": 0}
    except Exception as e:
        return {"kaynak": "Ekşi Sözlük", "hata": str(e)[:80], "tartisma_puani": 0}

# =====================================================================
# 7. VERİ TOPLAYICI — DONANIM HABER (Gerçek Mod - Geliştirilmiş)
# =====================================================================
async def donanimhaber_ara(session, sektor_adi):
    """
    Donanım Haber forumu — konu sayısı.
    """
    if DEMO_MODE:
        import random
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
                # Toplam sonuç sayısı
                match = re.search(r'(\d[\d.,]*)\s*(?:sonuç|konu|bulundu)', html, re.IGNORECASE)
                sayi = 0
                if match:
                    sayi = int(match.group(1).replace(".", "").replace(",", ""))
                if sayi == 0:
                    soup = BeautifulSoup(html, "lxml")
                    konular = soup.find_all("a", class_=re.compile(r"topic|thread", re.I))
                    sayi = len(konular)
                return {
                    "kaynak": "Donanım Haber",
                    "konu_sayisi": sayi,
                    "teknik_soru_puani": min(100, sayi),
                }
            else:
                return {"kaynak": "Donanım Haber", "hata": f"HTTP {resp.status}", "teknik_soru_puani": 0}
    except Exception as e:
        return {"kaynak": "Donanım Haber", "hata": str(e)[:80], "teknik_soru_puani": 0}

# =====================================================================
# 8. VERİ TOPLAYICI — SAHİBİNDEN (Engellenir, Manuel Giriş)
# =====================================================================
async def sahibinden_ara(session, sektor_adi):
    """
    Sahibinden.com scraping'e izin vermez.
    Bu kaynak için manuel veri girişi kullanılır.
    """
    if DEMO_MODE:
        import random
        return {
            "kaynak": "Sahibinden",
            "ilan_sayisi": random.randint(100, 10000),
            "pazar_canliligi": random.randint(30, 95),
        }
    # Gerçek modda manuel veri kullanılır (0 döner, kullanıcı elle girer)
    return {
        "kaynak": "Sahibinden",
        "ilan_sayisi": 0,
        "pazar_canliligi": 0,
        "not": "Manuel giriş gerekli (Sahibinden scraping yasak)",
  } # =====================================================================
# 9. RATE LIMITING (Kaynakları Yormamak İçin)
# =====================================================================
import asyncio

# Her kaynak için bekleme süreleri (saniye)
RATE_LIMITS = {
    "google_trends": 3.0,     # Google Trends dakikada max 20 istek
    "sikayetvar": 2.0,        # Siteyi yormamak için
    "eksisozluk": 4.0,        # Bot koruması var, yavaş git
    "donanimhaber": 2.0,
    "sahibinden": 0.0,        # Zaten scraping yok
}

# Kaynak bazlı son kullanım zamanı
_kaynak_son_kullanim = {}

async def rate_limit_bekle(kaynak_adi):
    """Bir kaynağa istek atmadan önce bekleme süresi kontrolü."""
    simdi = time.time()
    son = _kaynak_son_kullanim.get(kaynak_adi, 0)
    bekleme = RATE_LIMITS.get(kaynak_adi, 1.0)
    gecen = simdi - son
    if gecen < bekleme:
        await asyncio.sleep(bekleme - gecen)
    _kaynak_son_kullanim[kaynak_adi] = time.time()

# =====================================================================
# 10. TEK SEKTÖRÜ TARA (Hata Toleranslı)
# =====================================================================
async def sektor_tara(session, sektor):
    """
    Bir sektörü 5 kaynaktan paralel tarar.
    Bir kaynak çökerse diğerleri devam eder.
    """
    sektor_adi = sektor["isim"]
    sonuclar = {}
    
    # Her kaynak için bağımsız görev
    async def guvenli_cagri(kaynak_adi, fonksiyon):
        try:
            await rate_limit_bekle(kaynak_adi)
            return await fonksiyon(session, sektor_adi)
        except Exception as e:
            return {"kaynak": kaynak_adi, "hata": str(e)[:80], "puan": 0}
    
    # 5 kaynağı paralel çağır
    gorevler = [
        guvenli_cagri("google_trends", google_trends_ara),
        guvenli_cagri("sikayetvar", sikayetvar_ara),
        guvenli_cagri("eksisozluk", eksisozluk_ara),
        guvenli_cagri("donanimhaber", donanimhaber_ara),
        guvenli_cagri("sahibinden", sahibinden_ara),
    ]
    
    sonuclar_liste = await asyncio.gather(*gorevler, return_exceptions=True)
    
    # Sonuçları sözlüğe çevir
    kaynak_isimleri = ["google_trends", "sikayetvar", "eksisozluk", "donanimhaber", "sahibinden"]
    for i, isim in enumerate(kaynak_isimleri):
        sonuc = sonuclar_liste[i]
        if isinstance(sonuc, Exception):
            sonuclar[isim] = {"hata": str(sonuc)[:80]}
        else:
            sonuclar[isim] = sonuc
    
    # Başarılı kaynak sayısı
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
# 11. TÜM SEKTÖRLERİ TARA (Sıralı, Kaydederek)
# =====================================================================
async def tum_sektorleri_tara(hafiza):
    """
    30 sektörü sırayla tarar.
    Her sektörden sonra hafızaya kaydeder (çökme olsa bile veri kurtulur).
    """
    hafiza["log"].append(f"🔍 GERÇEK MOD tarama başladı: {len(SEKTORLER)} sektör")
    hafiza["log"].append(f"⏱️ Tahmini süre: {len(SEKTORLER) * 15 // 60} dakika")
    
    basarili = 0
    basarisiz = 0
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        connector=aiohttp.TCPConnector(limit=5)
    ) as session:
        for i, sektor in enumerate(SEKTORLER):
            try:
                hafiza["log"].append(f"⏳ [{i+1}/{len(SEKTORLER)}] {sektor['isim']} taranıyor...")
                sonuc = await sektor_tara(session, sektor)
                hafiza["sektor_verileri"][sektor["id"]] = sonuc
                basarili += 1
                
                # Her 5 sektörden sonra kaydet (veri kaybını önle)
                if (i + 1) % 5 == 0:
                    verileri_kaydet(hafiza)
                    hafiza["log"].append(f"💾 Ara kayıt: {i+1} sektör tamamlandı")
                
                # Sektörler arası bekleme (siteyi yormamak için)
                await asyncio.sleep(1.5)
                
            except Exception as e:
                basarisiz += 1
                hafiza["log"].append(f"❌ {sektor['isim']}: {str(e)[:80]}")
    
    hafiza["son_guncelleme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    verileri_kaydet(hafiza)
    
    hafiza["log"].append(f"✅ Tarama tamamlandı.")
    hafiza["log"].append(f"   Başarılı: {basarili} | Başarısız: {basarisiz}")
    
    if len(hafiza["log"]) > 200:
        hafiza["log"] = hafiza["log"][-200:]

# =====================================================================
# 12. ARKA PLAN BOT BAŞLATICI
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
        hafiza["calisiyor"] = False

# =====================================================================
# 13. MANUEL VERİ GİRİŞİ (Sahibinden ve başarısız kaynaklar için)
# =====================================================================
MANUEL_VERI_DOSYASI = "manuel_veri.json"

def manuel_veri_yukle():
    """Manuel girilen verileri yükler."""
    if os.path.exists(MANUEL_VERI_DOSYASI):
        try:
            with open(MANUEL_VERI_DOSYASI, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def manuel_veri_kaydet(veri):
    """Manuel girilen verileri kaydeder."""
    with open(MANUEL_VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)

def manuel_veri_uygula(hafiza):
    """Manuel verileri hafızaya uygular (scraping başarısız olduğunda)."""
    manuel = manuel_veri_yukle()
    for sektor_id, veriler in manuel.items():
        sid = int(sektor_id)
        if sid in hafiza["sektor_verileri"]:
            # Kaynak bazlı uygula
            for kaynak, puan in veriler.items():
                if kaynak in hafiza["sektor_verileri"][sid]["kaynaklar"]:
                    hafiza["sektor_verileri"][sid]["kaynaklar"][kaynak] = puan

# =====================================================================
# 14. DEMO vs GERÇEK KARŞILAŞTIRMA
# =====================================================================
def demo_gercek_karsilastir(hafiza):
    """
    Demo modu ile gerçek mod sonuçlarını karşılaştırır.
    (Sadece bilgi amaçlı)
    """
    return {
        "demo_modu": DEMO_MODE,
        "toplanan_sektor": len(hafiza.get("sektor_verileri", {})),
        "hedef_sektor": len(SEKTORLER),
        "son_guncelleme": hafiza.get("son_guncelleme"),
  } # =====================================================================
# 15. STREAMLIT ARAYÜZÜ (GERÇEK MOD UYUMLU)
# =====================================================================
st.set_page_config(
    page_title="Fırsat Madenciliği - 30 Sektör",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        st.sidebar.caption("Gerçek veri için DEMO_MODE = False yapın")
    else:
        st.sidebar.warning("🔴 GERÇEK MOD (Canlı Scraping)")
        st.sidebar.caption("Tarama 7-10 dakika sürer")

    st.sidebar.markdown("### 📊 Sistem Bilgisi")
    st.sidebar.caption(f"Sektör: {len(SEKTORLER)}")
    st.sidebar.caption(f"Kaynak: 5")
    st.sidebar.caption(f"Son güncelleme: {hafiza.get('son_guncelleme', '-')}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Kontroller")

    if st.sidebar.button("🔄 Verileri Yenile", help="Cache'i siler, yeniden tarar"):
        hafiza["sektor_verileri"] = {}
        hafiza["log"] = []
        hafiza["calisiyor"] = False
        if os.path.exists(VERI_DOSYASI):
            os.remove(VERI_DOSYASI)
        st.rerun()

    if st.sidebar.button("📂 Cache'i Temizle", help="Dosyayı siler, tarama başlatmaz"):
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
    if not hafiza["sektor_verileri"]:
        verileri_yukle(hafiza)
    
    # Manuel verileri uygula (varsa)
    manuel_veri_uygula(hafiza)
    
    # Cache geçerli değilse ve tarama çalışmıyorsa başlat
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
        st.info(f"⏳ Tarama devam ediyor... {tamamlanan}/{toplam} sektör tamamlandı. "
                f"Tahmini kalan süre: {(toplam - tamamlanan) * 15 // 60} dk.")
        st.progress(oran)
        # Otomatik yenile (tarama sürerken)
        time.sleep(5)
        st.rerun()

    # =================================================================
    # VERİ YOKSA UYARI
    # =================================================================
    if not hafiza["sektor_verileri"]:
        st.warning("Henüz veri yok. Tarama başlatılıyor... Sayfayı yenileyin.")
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
    # KAYNAK DURUMU TABLOSU (Gerçek modda önemli)
    # =================================================================
    with st.expander("📡 Veri Kaynağı Durumu (Hangi Kaynak Çalışıyor?)", expanded=False):
        kaynak_isimleri = ["google_trends", "sikayetvar", "eksisozluk", "donanimhaber", "sahibinden"]
        kaynak_etiketler = {
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
            toplam = 0
            for s in hafiza["sektor_verileri"].values():
                toplam += 1
                k_veri = s.get("kaynaklar", {}).get(kaynak, {})
                if "hata" in k_veri or k_veri.get("puan", 0) == 0:
                    if k_veri.get("not") == "Manuel giriş gerekli":
                        pass  # manuel sayılmaz
                    elif "hata" in k_veri:
                        hatali += 1
                    else:
                        basarili += 1
                else:
                    basarili += 1
            
            basari_orani = (basarili / toplam * 100) if toplam > 0 else 0
            durum = "✅ Çalışıyor" if basari_orani > 70 else \
                    "⚠️ Kısmen" if basari_orani > 30 else \
                    "❌ Çalışmıyor"
            
            durum_listesi.append({
                "Kaynak": kaynak_etiketler.get(kaynak, kaynak),
                "Başarılı": basarili,
                "Hatalı": hatali,
                "Başarı %": f"{basari_orani:.0f}%",
                "Durum": durum,
            })
        
        df_durum = pd.DataFrame(durum_listesi)
        st.dataframe(df_durum, use_container_width=True, hide_index=True)
        st.caption("💡 Çalışmayan kaynaklar için manuel veri girebilirsiniz (aşağıdaki bölümde).")

    st.markdown("---")

    # =================================================================
    # ÖDEMEYE HAZIR SEKTÖRLER
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
    # MANUEL VERİ GİRİŞİ (Başarısız Kaynaklar İçin)
    # =================================================================
    with st.expander("✍️ Manuel Veri Girişi (Scraping Başarısız Olduğunda)"):
        st.caption("Şikayetvar veya Ekşi gibi kaynaklar çalışmadıysa, buradan manuel puan girebilirsiniz.")
        
        manuel = manuel_veri_yukle()
        
        # Hangi sektörlerde hangi kaynak başarısız?
        basarisiz_kayitlar = []
        for sid, s in hafiza["sektor_verileri"].items():
            for kaynak in ["sikayetvar", "eksisozluk", "donanimhaber"]:
                k_veri = s.get("kaynaklar", {}).get(kaynak, {})
                if "hata" in k_veri or (k_veri.get("puan", 0) == 0 and not k_veri.get("sikayet_sayisi")):
                    basarisiz_kayitlar.append({
                        "Sektör": s["isim"],
                        "Kaynak": kaynak,
                        "Hata": k_veri.get("hata", "Veri yok")[:50],
                    })
        
        if basarisiz_kayitlar:
            st.warning(f"⚠️ {len(basarisiz_kayitlar)} kayıtta sorun var")
            df_basarisiz = pd.DataFrame(basarisiz_kayitlar[:20])
            st.dataframe(df_basarisiz, use_container_width=True, hide_index=True)
        else:
            st.success("✅ Tüm kaynaklar sorunsuz çalıştı")
        
        st.markdown("---")
        st.markdown("**Manuel Puan Girişi:**")
        
        sektor_secenekleri = {s["id"]: s["isim"] for s in SEKTORLER}
        secili_sektor = st.selectbox(
            "Sektör seçin",
            options=list(sektor_secenekleri.keys()),
            format_func=lambda x: sektor_secenekleri[x]
        )
        
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            sv_puan = st.number_input("Şikayetvar aciliyet puanı", 0, 100, 50)
        with col_m2:
            eks_puan = st.number_input("Ekşi tartışma puanı", 0, 100, 50)
        with col_m3:
            dh_puan = st.number_input("Donanım Haber puanı", 0, 100, 50)
        
        if st.button("💾 Manuel Veriyi Kaydet ve Uygula"):
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
            manuel_veri_uygula(hafiza)
            st.success("✅ Manuel veri kaydedildi ve uygulandı. Sayfayı yenileyin.")
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
            "30 sektörü 5 kaynaktan tarar ve her sektöre **fırsat puanı** verir.\n\n"
            "**5 Kaynak:**\n"
            "- Google Trends → Ne aranıyor?\n"
            "- Şikayetvar → Neyden şikayet ediliyor?\n"
            "- Ekşi Sözlük → Ne tartışılıyor?\n"
            "- Donanım Haber → Hangi teknik sorunlar var?\n"
            "- Sahibinden → Pazar canlı mı? (Manuel)\n\n"
            "**4 Kriter:**\n"
            "- Talep (%35), Ödeme (%30), Aciliyet (%20), Rekabet (%15)\n\n"
            f"**Mevcut Mod:** {'🧪 DEMO' if DEMO_MODE else '🔴 GERÇEK'}\n\n"
            "**Gerçek moda geçmek için:** Kodun başındaki `DEMO_MODE = False` yapın."
        )

    # =================================================================
    # SAYFAYI PERİYODİK YENİLE
    # =================================================================
    if hafiza["calisiyor"]:
        time.sleep(5)
        st.rerun()
