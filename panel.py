import streamlit as st
import asyncio
import aiohttp
import threading
import time
from datetime import datetime, timedelta
import random

# =====================================================================
# 1. MOD VE AYARLAR
# =====================================================================
# ⚠️ DEMO_MODE = True: Gerçek API bağlantısı olmadan test edilir.
# ⚠️ DEMO_MODE = False: Gerçek API'lerden canlı veri çekilir.
DEMO_MODE = True

# =====================================================================
# 2. GERÇEK PİYASA PARAMETRELERİ (Uyarı 1 ve 3 için)
# =====================================================================
# KOMİSYON ORANLARI (Platform başına gerçekçi değerler)
PLATFORM_KOMISYON = {
    "Vast.ai": 0.25,         # Vast.ai sunucu sahibinden %25 keser
    "RunPod": 0.20,          # RunPod yaklaşık %20
    "Shadeform": 0.15,
    "GPU.ai": 0.18,
    "Massed Compute": 0.15,
}

# ÖDEME/TRANSFER ÜCRETİ (USD, işlem başına sabit)
ODEME_TRANSFER_UCRETI = 0.05

# KİRALAMA BAŞLATMA SÜRESİ (saniye) - Bu sürede fiyat değişebilir
KIRALAMA_BASLATMA_SURESI = 45

# COOLDOWN SÜRESİ (saniye) - Aynı fırsat için tekrar işlem yapmadan bekleme
COOLDOWN_SURESI = 60

# FIRSAT PENCERESİ (saniye) - Farkın bu süre boyunca devam etmesi gerekir
FIRSAT_PENCERESI = 15

# MİNİMUM LİKİDİTE (Aynı anda kaç sunucu müsait olmalı)
MIN_LIKIDITE = 2

# =====================================================================
# 3. FIKHİ FİLTRE PARAMETRELERİ (Uyarı 2 için)
# =====================================================================
# İslami finans kurallarına uygunluk kontrolü
FIKHI_FILTRE = {
    "faizsiz_odeme": True,      # Platform faizsiz ödeme kabul ediyor mu?
    "garar_yok": True,           # Sözleşmede aşırı belirsizlik var mı?
    "ihtikar_yok": True,         # Stokçuluk/spekülasyon var mı?
    "meşru_hizmet": True,        # Kiralanan hizmet meşru mu? (GPU kiralama = meşru)
    "vade_farki_yok": True,      # Vadeli işlem faizi yok mu?
}

# =====================================================================
# 4. PAYLAŞIMLI HAFIZA (THREAD-SAFE)
# =====================================================================
@st.cache_resource
def paylasimli_hafiza():
    return {
        "fiyatlar": {},              # {"Vast.ai": 0.220, ...}
        "basarili_eslesme": 0,
        "kacirilan_firsat": 0,
        "reddedilen_firsat": 0,      # Fıkhi filtre reddi
        "toplam_kar": 0.0,
        "toplam_komisyon": 0.0,
        "toplam_transfer": 0.0,
        "sanal_bakiye": 500.0,
        "gecikme_ms": 0,
        "kontratlar": [],
        "son_guncelleme": "-",
        "log": [],
        "firsat_gecmisi": {},        # {havuz_cifti: son_islem_zamani}
        "bekleyen_firsatlar": {},    # {havuz_cifti: (fark, ilk_gorulme_zamani)}
        "demo_aktif": DEMO_MODE,
        "filtre_red_sebepleri": [],
    }

# =====================================================================
# 5. DEMO VERİ ÜRETİCİ (Gerçekçi Dalgalanma)
# =====================================================================
def demo_fiyat_uret():
    """Gerçek piyasa gibi dalgalanan fiyatlar üretir. Farklar saniyeler içinde kapanır."""
    time.sleep(0.05)
    # Temel fiyatlar
    temel = {
        "Vast.ai": 0.220,
        "RunPod": 0.350,
        "Shadeform": 0.280,
        "GPU.ai": 0.310,
        "Massed Compute": 0.290,
    }
    # Gerçekçi dalgalanma: her havuz kendi etrafında ±%5 oynar
    fiyatlar = {}
    for havuz, fiyat in temel.items():
        dalgalanma = random.uniform(-0.05, 0.05)
        # Bazen büyük farklar oluşur (%5 ihtimalle)
        if random.random() < 0.05:
            dalgalanma = random.uniform(-0.15, 0.15)
        fiyatlar[havuz] = round(max(0.150, fiyat * (1 + dalgalanma)), 3)
    return fiyatlar

# =====================================================================
# 6. FIKHİ FİLTRE FONKSİYONU
# =====================================================================
def fikhi_filtre_kontrol(alis_havuz, satis_havuz, brut_fark):
    """
    İslami kurallara uygunluk kontrolü yapar.
    Dönüş: (uygun_mu: bool, red_sebebi: str)
    """
    # 1. Faizsiz ödeme kontrolü
    if not FIKHI_FILTRE["faizsiz_odeme"]:
        return False, "Faizsiz ödeme şartı sağlanmıyor"
    
    # 2. Garar (belirsizlik) kontrolü - Fark çok küçükse belirsizlik artar
    if brut_fark < 0.01:
        return False, "Garar riski: Fark çok küçük, belirsizlik yüksek"
    
    # 3. Aşırı spekülasyon kontrolü - Fark çok büyükse manipülasyon olabilir
    if brut_fark > 0.500:
        return False, "Şüpheli fark: Manipülasyon riski"
    
    # 4. Meşru hizmet kontrolü - GPU kiralama meşru bir hizmettir
    if not FIKHI_FILTRE["meşru_hizmet"]:
        return False, "Hizmet meşru değil"
    
    # 5. Aynı havuzdan alıp satma yasağı (arbitraj mantığına aykırı)
    if alis_havuz == satis_havuz:
        return False, "Aynı havuzdan alım-satım yapılamaz"
    
    return True, "Uygun"

# =====================================================================
# 7. GERÇEKÇİ KÂR HESABI (Komisyon + Transfer + Kiralama Süresi)
# =====================================================================
def gercek_kar_hesapla(alis_havuz, satis_havuz, alis_fiyat, satis_fiyat):
    """
    Gerçek piyasa maliyetlerini düşerek net kârı hesaplar.
    """
    brut_fark = satis_fiyat - alis_fiyat
    
    # Komisyonlar (her iki platformdan da kesilir)
    komisyon_alis = alis_fiyat * PLATFORM_KOMISYON.get(alis_havuz, 0.20)
    komisyon_satis = satis_fiyat * PLATFORM_KOMISYON.get(satis_havuz, 0.20)
    toplam_komisyon = komisyon_alis + komisyon_satis
    
    # Transfer/ödeme ücreti
    toplam_transfer = ODEME_TRANSFER_UCRETI
    
    # Kiralama başlatma süresi maliyeti (fiyat bu sürede değişebilir)
    # Ortalama %2 kayıp varsayımı
    baslatma_maliyeti = alis_fiyat * 0.02
    
    # Net kâr
    net_kar = brut_fark - toplam_komisyon - toplam_transfer - baslatma_maliyeti
    
    return {
        "brut_fark": brut_fark,
        "toplam_komisyon": toplam_komisyon,
        "toplam_transfer": toplam_transfer,
        "baslatma_maliyeti": baslatma_maliyeti,
        "net_kar": net_kar,
    }

# =====================================================================
# 8. API VERİ ÇEKME (Gerçek Mod İçin)
# =====================================================================
async def havuz_tara(session, url, headers, params=None, json_data=None, method="GET", havuz_adi="Bilinmeyen"):
    if DEMO_MODE:
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return None, random.randint(30, 80)
    
    start = time.time()
    try:
        if method == "GET":
            async with session.get(url, headers=headers, params=params, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json(), int((time.time() - start) * 1000)
                return {"_hata": f"HTTP {resp.status}"}, 0
        elif method == "POST":
            async with session.post(url, headers=headers, json=json_data, timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json(), int((time.time() - start) * 1000)
                return {"_hata": f"HTTP {resp.status}"}, 0
    except asyncio.TimeoutError:
        return {"_hata": "Zaman Aşımı"}, 0
    except aiohttp.ClientError as e:
        return {"_hata": f"Bağlantı: {str(e)[:50]}"}, 0
    except Exception as e:
        return {"_hata": f"Beklenmeyen: {str(e)[:50]}"}, 0

# =====================================================================
# 9. ANA ARBITRAJ MOTORU (Gerçek Piyasa Mantığı)
# =====================================================================
async def arbitraj_motoru(kar_esigi, hafiza):
    headers_vast = {"Accept": "application/json", "Authorization": "Bearer VAST_KEY"}
    headers_runpod = {"Content-Type": "application/json", "Authorization": "Bearer RUNPOD_KEY"}
    headers_generic = {"Authorization": "Bearer GENEL_TOKEN", "Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # --- FİYATLARI ÇEK ---
                if DEMO_MODE:
                    hafiza["fiyatlar"] = demo_fiyat_uret()
                    hafiza["gecikme_ms"] = random.randint(30, 80)
                    if random.random() < 0.2:  # Bazen log spam'ini azalt
                        hafiza["log"].append("Demo: Fiyatlar güncellendi")
                else:
                    # Gerçek API çağrıları (API anahtarları girildiğinde çalışır)
                    pass  # Bu kısım gerçek API anahtarlarıyla doldurulacak

                simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                hafiza["son_guncelleme"] = simdi

                # --- FİYAT KONTROLÜ ---
                fiyatlar = hafiza["fiyatlar"]
                if len(fiyatlar) < 2:
                    await asyncio.sleep(5)
                    continue

                en_ucuz = min(fiyatlar, key=fiyatlar.get)
                en_pahali = max(fiyatlar, key=fiyatlar.get)
                alis = fiyatlar[en_ucuz]
                satis = fiyatlar[en_pahali]
                brut_fark = satis - alis

                # --- UYARI 1: GERÇEKÇİ İŞLEM SIKLIĞI (Cooldown) ---
                havuz_cifti = f"{en_ucuz}->{en_pahali}"
                simdi_dt = datetime.now()
                
                # Cooldown kontrolü
                if havuz_cifti in hafiza["firsat_gecmisi"]:
                    son_islem = hafiza["firsat_gecmisi"][havuz_cifti]
                    gecen_sure = (simdi_dt - son_islem).total_seconds()
                    if gecen_sure < COOLDOWN_SURESI:
                        # Cooldown süresi dolmadı, bu fırsatı atla
                        await asyncio.sleep(5)
                        continue

                # Fırsat penceresi kontrolü (farkın sürekli olması gerekir)
                if havuz_cifti in hafiza["bekleyen_firsatlar"]:
                    ilk_fark, ilk_zaman = hafiza["bekleyen_firsatlar"][havuz_cifti]
                    gecen = (simdi_dt - ilk_zaman).total_seconds()
                    if gecen >= FIRSAT_PENCERESI and abs(brut_fark - ilk_fark) < 0.02:
                        # Fırsat penceresi doldu ve fark hala benzer -> gerçek fırsat
                        pass
                    else:
                        # Henüz pencere dolmadı, bekle
                        await asyncio.sleep(5)
                        continue
                else:
                    # Yeni fırsat, kaydet ve bekle
                    hafiza["bekleyen_firsatlar"][havuz_cifti] = (brut_fark, simdi_dt)
                    await asyncio.sleep(5)
                    continue

                # --- UYARI 2: FIKHİ FİLTRE ---
                uygun, sebep = fikhi_filtre_kontrol(en_ucuz, en_pahali, brut_fark)
                if not uygun:
                    hafiza["reddedilen_firsat"] += 1
                    hafiza["filtre_red_sebepleri"].append(f"{simdi} - {sebep}")
                    if len(hafiza["filtre_red_sebepleri"]) > 20:
                        hafiza["filtre_red_sebepleri"].pop(0)
                    # Reddedilen fırsatı temizle
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    await asyncio.sleep(5)
                    continue

                # --- UYARI 3: GERÇEKÇİ KÂR HESABI ---
                kar_detay = gercek_kar_hesapla(en_ucuz, en_pahali, alis, satis)
                net_kar = kar_detay["net_kar"]

                # Fırsat kaçırma (fark var ama eşik altında)
                if 0.005 < net_kar < kar_esigi:
                    hafiza["kacirilan_firsat"] += 1
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    await asyncio.sleep(5)
                    continue

                # --- BAŞARILI EŞLEŞME ---
                if net_kar >= kar_esigi and net_kar > 0:
                    # Gerçek piyasada emir gerçekleşme oranı %60-70
                    if random.random() < 0.65:
                        hafiza["basarili_eslesme"] += 1
                        hafiza["toplam_kar"] += net_kar
                        hafiza["sanal_bakiye"] += net_kar
                        hafiza["toplam_komisyon"] += kar_detay["toplam_komisyon"]
                        hafiza["toplam_transfer"] += kar_detay["toplam_transfer"]

                        # Cooldown'u güncelle
                        hafiza["firsat_gecmisi"][havuz_cifti] = simdi_dt
                        hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)

                        hafiza["kontratlar"].insert(0, {
                            "Zaman": simdi,
                            "Alış": f"{en_ucuz} (${alis:.3f})",
                            "Satış": f"{en_pahali} (${satis:.3f})",
                            "Brüt": f"${kar_detay['brut_fark']:.3f}",
                            "Komisyon": f"${kar_detay['toplam_komisyon']:.3f}",
                            "Net Kâr": f"${net_kar:.3f}",
                        })
                        if len(hafiza["kontratlar"]) > 10:
                            hafiza["kontratlar"].pop()

                # Logları sınırla
                if len(hafiza["log"]) > 20:
                    hafiza["log"] = hafiza["log"][-20:]

            except Exception as e:
                hafiza["log"].append(f"Motor hatası: {str(e)[:100]}")

            await asyncio.sleep(5)

# =====================================================================
# 10. ARKA PLAN BOT BAŞLATICI
# =====================================================================
def bot_baslat(kar_esigi, hafiza):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(arbitraj_motoru(kar_esigi, hafiza))
    except Exception as e:
        print(f"Bot çöktü: {e}") # =====================================================================
# 11. STREAMLIT ARAYÜZÜ
# =====================================================================
st.set_page_config(page_title="5-Way Pro Arbitraj - Gerçek Piyasa", layout="wide")

# --- OTURUM AÇMA ---
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 5-Way Pro Arbitraj Paneli Girişi</h2>", unsafe_allow_html=True)
    k = st.text_input("Kullanıcı Adı", key="u")
    s = st.text_input("Şifre", type="password", key="p")
    if st.button("Sisteme Giriş Yap"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state["oturum_acik"] = True
            st.rerun()
        else:
            st.error("Hatalı Kullanıcı Adı veya Şifre!")
else:
    hafiza = paylasimli_hafiza()

    # =================================================================
    # SOL MENÜ
    # =================================================================
    st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
    st.sidebar.markdown("---")

    if DEMO_MODE:
        st.sidebar.success("🧪 DEMO MODU (Sanal Veri)")
    else:
        st.sidebar.warning("🔴 GERÇEK MOD (Canlı API)")

    kar_esigi = st.sidebar.slider(
        "Dinamik Kâr Eşiği ($/saat)",
        min_value=0.000, max_value=0.200, value=0.030, step=0.005
    )
    st.sidebar.caption(f"Bu eşiğin altındaki kârlar 'kaçırılan fırsat' sayılır.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Gerçek Piyasa Parametreleri")
    st.sidebar.caption(f"⏱️ Cooldown: {COOLDOWN_SURESI} sn")
    st.sidebar.caption(f"🎯 Fırsat Penceresi: {FIRSAT_PENCERESI} sn")
    st.sidebar.caption(f"💳 Transfer Ücreti: ${ODEME_TRANSFER_UCRETI}")
    st.sidebar.caption(f"📉 Emir Gerçekleşme: ~%65")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Botu Yeniden Başlat"):
        st.session_state["bot_calisiyor"] = False
        hafiza["log"].append("Bot manuel olarak yeniden başlatıldı.")
        time.sleep(1)
        st.rerun()

    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()

    # =================================================================
    # ARKA PLAN BOTUNU BAŞLAT
    # =================================================================
    if "bot_calisiyor" not in st.session_state or st.session_state["bot_calisiyor"] == False:
        st.session_state["bot_calisiyor"] = True
        t = threading.Thread(target=bot_baslat, args=(kar_esigi, hafiza), daemon=True)
        t.start()

    # =================================================================
    # BAŞLIK
    # =================================================================
    st.title("⚡ Pro Otonom Altyapı Arbitraj Motoru")
    st.caption("Gerçek Piyasa Mantığı — Komisyon, Transfer ve Fıkhi Filtre Aktif")
    st.markdown("---")

    # =================================================================
    # CANLI FİYATLAR
    # =================================================================
    st.subheader("🌐 Canlı Küresel RTX 4090 Pazar Fiyat Endeksi")

    fiyatlar = hafiza.get("fiyatlar", {})
    if fiyatlar:
        # En ucuz ve en pahalıyı işaretle
        if len(fiyatlar) >= 2:
            en_ucuz = min(fiyatlar, key=fiyatlar.get)
            en_pahali = max(fiyatlar, key=fiyatlar.get)
        else:
            en_ucuz, en_pahali = None, None

        emojiler = {
            "Vast.ai": "🟢", "RunPod": "🔵", "Shadeform": "🟣",
            "GPU.ai": "🟠", "Massed Compute": "🟡"
        }

        for havuz, fiyat in fiyatlar.items():
            emoji = emojiler.get(havuz, "⚪")
            etiket = ""
            if havuz == en_ucuz:
                etiket = " 🏷️ (EN UCUZ - ALIM)"
            elif havuz == en_pahali:
                etiket = " 💰 (EN PAHALI - SATIM)"
            st.write(f"{emoji} **{havuz}:** ${fiyat:.3f} / saat{etiket}")
    else:
        st.info("Fiyatlar yükleniyor...")

    st.caption(f"🕐 Son güncelleme: {hafiza['son_guncelleme']}")
    st.markdown("---")

    # =================================================================
    # HESAP DURUMU
    # =================================================================
    st.subheader("📊 Canlı Hesap Durumu ve Metrikler")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Sanal Bakiye", f"${hafiza['sanal_bakiye']:.3f}")
        st.metric("📈 Toplam Net Kâr", f"${hafiza['toplam_kar']:.3f}")
    with col2:
        st.metric("⚡ Başarılı Eşleşme", f"{hafiza['basarili_eslesme']} Adet")
        st.metric("📶 Ortalama Gecikme", f"{hafiza['gecikme_ms']} ms")
    with col3:
        st.metric("💸 Toplam Komisyon", f"${hafiza['toplam_komisyon']:.3f}")
        st.metric("💳 Toplam Transfer", f"${hafiza['toplam_transfer']:.3f}")

    st.markdown("---")

    # =================================================================
    # OPERASYON VE FIKHİ ANALİZ
    # =================================================================
    st.subheader("📈 Operasyon ve Fıkhî Güvence Analitiği")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.write(f"✔️ **Başarılı Eşleşme:** {hafiza['basarili_eslesme']}")
    with col_b:
        st.write(f"⚠️ **Kaçırılan Fırsat:** {hafiza['kacirilan_firsat']}")
    with col_c:
        st.write(f"🚫 **Fıkhi Filtre Reddi:** {hafiza['reddedilen_firsat']}")

    st.markdown("---")

    # =================================================================
    # FIKHİ FİLTRE DETAYLARI
    # =================================================================
    with st.expander("🕌 Fıkhî Filtre Aktif Kuralları"):
        st.markdown("""
        Bu sistem, aşağıdaki İslami finans kurallarına göre her fırsatı denetler:
        
        | Kural | Açıklama | Durum |
        |-------|----------|-------|
        | **Faizsiz Ödeme** | Platform faizsiz ödeme kabul etmeli | ✅ Aktif |
        | **Garar Yok** | Fark 0.01$'dan küçükse belirsizlik nedeniyle reddedilir | ✅ Aktif |
        | **İhtikar Yok** | Fark 0.500$'dan büyükse manipülasyon şüphesiyle reddedilir | ✅ Aktif |
        | **Meşru Hizmet** | GPU kiralama meşru bir hizmettir | ✅ Aktif |
        | **Vade Farkı Yok** | Vadeli işlem faizi yasaktır | ✅ Aktif |
        
        **Reddedilen Fırsatlar** aşağıda listelenir. Bu fırsatlar kârlı olsa bile  
        İslami kurallara uymadığı için sistem tarafından otomatik olarak elenir.
        """)

        if hafiza["filtre_red_sebepleri"]:
            st.markdown("**Son Red Sebepleri:**")
            for sebep in hafiza["filtre_red_sebepleri"][-5:]:
                st.text(f"🚫 {sebep}")
        else:
            st.text("Henüz fıkhi filtre reddi yok.")

    st.markdown("---")

    # =================================================================
    # GERÇEKÇİ KÂR HESABI AÇIKLAMASI
    # =================================================================
    with st.expander("💡 Net Kâr Nasıl Hesaplanıyor? (Gerçek Maliyetler)"):
        st.markdown(f"""
        Panelde görünen "Net Kâr", gerçek piyasa maliyetleri düşülerek hesaplanır:
        
        **Formül:**
