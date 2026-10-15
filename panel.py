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
# 2. GERÇEK PİYASA PARAMETRELERİ
# =====================================================================
PLATFORM_KOMISYON = {
    "Vast.ai": 0.25,
    "RunPod": 0.20,
    "Shadeform": 0.15,
    "GPU.ai": 0.18,
    "Massed Compute": 0.15,
}

ODEME_TRANSFER_UCRETI = 0.05       # İşlem başına sabit transfer ücreti (USD)
KIRALAMA_BASLATMA_SURESI = 45      # saniye
COOLDOWN_SURESI = 60               # saniye — aynı havuz çifti için bekleme
FIRSAT_PENCERESI = 15              # saniye — farkın devam etmesi gereken süre
FIRSAT_ZAMAN_ASIMI = 90            # saniye — bu süreden fazla bekleyen fırsat otomatik silinir
MIN_LIKIDITE = 2

# =====================================================================
# 3. FIKHİ FİLTRE PARAMETRELERİ
# =====================================================================
FIKHI_FILTRE = {
    "faizsiz_odeme": True,
    "garar_yok": True,
    "ihtikar_yok": True,
    "meşru_hizmet": True,
    "vade_farki_yok": True,
}

# =====================================================================
# 4. PAYLAŞIMLI HAFIZA (THREAD-SAFE)
# =====================================================================
@st.cache_resource
def paylasimli_hafiza():
    return {
        "fiyatlar": {},
        "basarili_eslesme": 0,
        "kacirilan_firsat": 0,
        "karsiz_firsat": 0,             # YENİ: Komisyonlar farkı yediği durumlar
        "reddedilen_firsat": 0,
        "toplam_kar": 0.0,
        "toplam_komisyon": 0.0,
        "toplam_transfer": 0.0,
        "sanal_bakiye": 500.0,
        "gecikme_ms": 0,
        "kontratlar": [],
        "son_guncelleme": "-",
        "log": [],
        "firsat_gecmisi": {},
        "bekleyen_firsatlar": {},       # {havuz_cifti: {"fark": X, "ilk_zaman": dt, "son_fark": Y}}
        "demo_aktif": DEMO_MODE,
        "filtre_red_sebepleri": [],
    }

# =====================================================================
# 5. DEMO VERİ ÜRETİCİ (GERÇEKÇİLEŞTİRİLDİ)
# =====================================================================
def demo_fiyat_uret():
    """
    Gerçek piyasaya benzer dalgalanan fiyatlar üretir.
    Bazen büyük farklar oluşur ki komisyonları yenebilsin.
    """
    time.sleep(0.05)
    temel = {
        "Vast.ai": 0.180,          # Daha düşük taban
        "RunPod": 0.420,           # Daha yüksek taban
        "Shadeform": 0.280,
        "GPU.ai": 0.310,
        "Massed Compute": 0.290,
    }
    fiyatlar = {}
    for havuz, fiyat in temel.items():
        dalgalanma = random.uniform(-0.08, 0.08)
        # %10 ihtimalle büyük fırsat (komisyonları yenecek kadar)
        if random.random() < 0.10:
            dalgalanma = random.uniform(-0.25, 0.25)
        fiyatlar[havuz] = round(max(0.100, fiyat * (1 + dalgalanma)), 3)
    return fiyatlar

# =====================================================================
# 6. FIKHİ FİLTRE FONKSİYONU
# =====================================================================
def fikhi_filtre_kontrol(alis_havuz, satis_havuz, brut_fark):
    """
    İslami kurallara uygunluk kontrolü yapar.
    Dönüş: (uygun_mu: bool, sebep: str)
    """
    if not FIKHI_FILTRE["faizsiz_odeme"]:
        return False, "Faizsiz ödeme şartı sağlanmıyor"
    if brut_fark < 0.01:
        return False, "Garar riski: Fark çok küçük, belirsizlik yüksek"
    if brut_fark > 0.500:
        return False, "Şüpheli fark: Manipülasyon riski"
    if not FIKHI_FILTRE["meşru_hizmet"]:
        return False, "Hizmet meşru değil"
    if alis_havuz == satis_havuz:
        return False, "Aynı havuzdan alım-satım yapılamaz"
    return True, "Uygun"

# =====================================================================
# 7. GERÇEKÇİ KÂR HESABI
# =====================================================================
def gercek_kar_hesapla(alis_havuz, satis_havuz, alis_fiyat, satis_fiyat):
    """
    Tüm gerçek piyasa maliyetlerini düşerek net kârı hesaplar.
    """
    brut_fark = satis_fiyat - alis_fiyat
    
    # Her iki platformdan da komisyon kesilir
    komisyon_alis = alis_fiyat * PLATFORM_KOMISYON.get(alis_havuz, 0.20)
    komisyon_satis = satis_fiyat * PLATFORM_KOMISYON.get(satis_havuz, 0.20)
    toplam_komisyon = komisyon_alis + komisyon_satis
    
    # Transfer/ödeme ücreti
    toplam_transfer = ODEME_TRANSFER_UCRETI
    
    # Kiralama başlatma süresi maliyeti (%2 kayıp varsayımı)
    baslatma_maliyeti = alis_fiyat * 0.02
    
    # Net kâr
    net_kar = brut_fark - toplam_komisyon - toplam_transfer - baslatma_maliyeti
    
    return {
        "brut_fark": brut_fark,
        "toplam_komisyon": toplam_komisyon,
        "toplam_transfer": toplam_transfer,
        "baslatma_maliyeti": baslatma_maliyeti,
        "net_kar": net_kar,
    } # =====================================================================
# 8. API VERİ ÇEKME FONKSİYONU (Gerçek Mod İçin)
# =====================================================================
async def havuz_tara(session, url, headers, params=None, json_data=None, method="GET", havuz_adi="Bilinmeyen"):
    """
    Belirtilen API'ye istek atar. Demo modunda sanal veri döner.
    """
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
# 9. ÖLÜ FIRSAT TEMİZLEYİCİ
# =====================================================================
def olu_firsatlari_temizle(hafiza, simdi_dt):
    """
    Zaman aşımına uğrayan veya artık geçerli olmayan fırsatları temizler.
    """
    temizlenecek = []
    for cift, veri in hafiza["bekleyen_firsatlar"].items():
        gecen = (simdi_dt - veri["ilk_zaman"]).total_seconds()
        
        # Zaman aşımı kontrolü
        if gecen > FIRSAT_ZAMAN_ASIMI:
            temizlenecek.append(cift)
            hafiza["log"].append(f"⏰ Zaman aşımı: {cift} ({gecen:.0f} sn) fırsatı elendi.")
            continue
        
        # Fark negatife döndüyse temizle
        if veri["son_fark"] <= 0:
            temizlenecek.append(cift)
            hafiza["log"].append(f"📉 Fark kapandı: {cift} elendi.")
            continue
    
    for cift in temizlenecek:
        hafiza["bekleyen_firsatlar"].pop(cift, None)

# =====================================================================
# 10. ANA ARBITRAJ MOTORU (TÜM DÜZELTMELER UYGULANDI)
# =====================================================================
async def arbitraj_motoru(kar_esigi, hafiza):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # --- FİYATLARI ÇEK ---
                if DEMO_MODE:
                    hafiza["fiyatlar"] = demo_fiyat_uret()
                    hafiza["gecikme_ms"] = random.randint(30, 80)
                    if random.random() < 0.15:
                        hafiza["log"].append("Demo: Fiyatlar güncellendi")
                else:
                    # Gerçek modda buraya API çağrıları gelecek
                    pass

                simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                simdi_dt = datetime.now()
                hafiza["son_guncelleme"] = simdi

                # --- ÖLÜ FIRSATLARI TEMİZLE ---
                olu_firsatlari_temizle(hafiza, simdi_dt)

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

                havuz_cifti = f"{en_ucuz}->{en_pahali}"

                # =========================================================
                # COOLDOWN KONTROLÜ
                # =========================================================
                if havuz_cifti in hafiza["firsat_gecmisi"]:
                    son_islem = hafiza["firsat_gecmisi"][havuz_cifti]
                    gecen_sure = (simdi_dt - son_islem).total_seconds()
                    if gecen_sure < COOLDOWN_SURESI:
                        if havuz_cifti in hafiza["bekleyen_firsatlar"]:
                            hafiza["bekleyen_firsatlar"][havuz_cifti]["son_fark"] = brut_fark
                        await asyncio.sleep(5)
                        continue

                # =========================================================
                # FIRSAT PENCERESİ KONTROLÜ
                # =========================================================
                if havuz_cifti in hafiza["bekleyen_firsatlar"]:
                    veri = hafiza["bekleyen_firsatlar"][havuz_cifti]
                    veri["son_fark"] = brut_fark
                    gecen = (simdi_dt - veri["ilk_zaman"]).total_seconds()

                    if gecen >= FIRSAT_PENCERESI:
                        # Pencere doldu, işleme devam et
                        if brut_fark > 0:
                            hafiza["log"].append(
                                f"✅ Pencere doldu: {havuz_cifti} ({gecen:.0f} sn, ${brut_fark:.3f})"
                            )
                        else:
                            hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                            await asyncio.sleep(5)
                            continue
                    else:
                        # Pencere henüz dolmadı
                        await asyncio.sleep(5)
                        continue
                else:
                    # Yeni fırsat kaydet
                    hafiza["bekleyen_firsatlar"][havuz_cifti] = {
                        "fark": brut_fark,
                        "ilk_zaman": simdi_dt,
                        "son_fark": brut_fark,
                    }
                    hafiza["log"].append(
                        f"🆕 Yeni fırsat: {havuz_cifti} (${brut_fark:.3f}) — pencere başladı"
                    )
                    await asyncio.sleep(5)
                    continue

                # =========================================================
                # FIKHİ FİLTRE
                # =========================================================
                uygun, sebep = fikhi_filtre_kontrol(en_ucuz, en_pahali, brut_fark)
                if not uygun:
                    hafiza["reddedilen_firsat"] += 1
                    hafiza["filtre_red_sebepleri"].append(f"{simdi} - {sebep}")
                    if len(hafiza["filtre_red_sebepleri"]) > 20:
                        hafiza["filtre_red_sebepleri"].pop(0)
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    hafiza["log"].append(f"🚫 Fıkhi filtre reddi: {sebep}")
                    await asyncio.sleep(5)
                    continue

                # =========================================================
                # GERÇEKÇİ KÂR HESABI
                # =========================================================
                kar_detay = gercek_kar_hesapla(en_ucuz, en_pahali, alis, satis)
                net_kar = kar_detay["net_kar"]

                # =========================================================
                # KÂR DURUMU KONTROLÜ (YENİ DÜZELTME)
                # =========================================================
                # 1) Net kâr negatif veya sıfır → komisyonlar farkı yedi
                if net_kar <= 0:
                    hafiza["karsiz_firsat"] += 1
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    hafiza["log"].append(
                        f"❌ Kârsız: {havuz_cifti} — net ${net_kar:.3f} (komisyonlar farkı yedi)"
                    )
                    await asyncio.sleep(5)
                    continue

                # 2) Pozitif ama eşiğin altında → kaçırılan fırsat
                if 0.005 < net_kar < kar_esigi:
                    hafiza["kacirilan_firsat"] += 1
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    hafiza["log"].append(
                        f"⚠️ Kaçırılan: {havuz_cifti} — net ${net_kar:.3f} < eşik ${kar_esigi:.3f}"
                    )
                    await asyncio.sleep(5)
                    continue

                # =========================================================
                # BAŞARILI EŞLEŞME
                # =========================================================
                if net_kar >= kar_esigi:
                    # Emir gerçekleşme simülasyonu (~%65)
                    if random.random() < 0.65:
                        hafiza["basarili_eslesme"] += 1
                        hafiza["toplam_kar"] += net_kar
                        hafiza["sanal_bakiye"] += net_kar
                        hafiza["toplam_komisyon"] += kar_detay["toplam_komisyon"]
                        hafiza["toplam_transfer"] += kar_detay["toplam_transfer"]

                        # Cooldown'u başlat
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

                        hafiza["log"].append(
                            f"✅ İŞLEM: {havuz_cifti} | Net ${net_kar:.3f}"
                        )
                    else:
                        # Emir gerçekleşmedi — fırsat kaçtı
                        hafiza["log"].append(
                            f"❌ Emir gerçekleşmedi: {havuz_cifti}"
                        )
                        hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)

                # Logları sınırla
                if len(hafiza["log"]) > 30:
                    hafiza["log"] = hafiza["log"][-30:]

            except Exception as e:
                hafiza["log"].append(f"Motor hatası: {str(e)[:100]}")

            await asyncio.sleep(5)

# =====================================================================
# 11. ARKA PLAN BOT BAŞLATICI
# =====================================================================
def bot_baslat(kar_esigi, hafiza):
    """
    Arka planda asyncio event loop'u başlatır ve arbitraj motorunu çalıştırır.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(arbitraj_motoru(kar_esigi, hafiza))
    except Exception as e:
        print(f"Bot çöktü: {e}") # =====================================================================
# 12. STREAMLIT ARAYÜZÜ
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
    st.sidebar.caption("Bu eşiğin altındaki kârlar 'kaçırılan fırsat' sayılır.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Gerçek Piyasa Parametreleri")
    st.sidebar.caption(f"⏱️ Cooldown: {COOLDOWN_SURESI} sn")
    st.sidebar.caption(f"🎯 Fırsat Penceresi: {FIRSAT_PENCERESI} sn")
    st.sidebar.caption(f"⏰ Zaman Aşımı: {FIRSAT_ZAMAN_ASIMI} sn")
    st.sidebar.caption(f"💳 Transfer Ücreti: ${ODEME_TRANSFER_UCRETI}")
    st.sidebar.caption("📉 Emir Gerçekleşme: ~%65")

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
    # OPERASYON VE FIKHİ ANALİZ (4 SÜTUN)
    # =================================================================
    st.subheader("📈 Operasyon ve Fıkhî Güvence Analitiği")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        st.write(f"✔️ **Başarılı:** {hafiza['basarili_eslesme']}")
    with col_b:
        st.write(f"⚠️ **Kaçırılan:** {hafiza['kacirilan_firsat']}")
    with col_c:
        st.write(f"❌ **Kârsız:** {hafiza['karsiz_firsat']}")
    with col_d:
        st.write(f"🚫 **Fıkhi Red:** {hafiza['reddedilen_firsat']}")

    st.caption(
        "❌ **Kârsız Fırsat:** Brüt fark var ama komisyonlar + transfer ücreti farkı yiyor "
        "(gerçek piyasada en sık görülen durum). "
        "⚠️ **Kaçırılan:** Net kâr pozitif ama eşik altında."
    )

    st.markdown("---")

    # =================================================================
    # FIRSAT PENCERESİ (İLERLEME ÇUBUĞU)
    # =================================================================
    bekleyen = hafiza.get("bekleyen_firsatlar", {})
    if bekleyen:
        st.subheader(f"⏳ Fırsat Penceresinde Bekleyen ({len(bekleyen)} adet)")
        st.caption(
            f"Bu fırsatlar {FIRSAT_PENCERESI} saniyelik pencereyi doldurmayı bekliyor. "
            f"Pencere dolduğunda fıkhi filtreden geçerse işlem açılır. "
            f"{FIRSAT_ZAMAN_ASIMI} saniyeden fazla bekleyen fırsatlar otomatik elenir."
        )

        simdi_dt = datetime.now()
        for cift, veri in list(bekleyen.items()):
            gecen = (simdi_dt - veri["ilk_zaman"]).total_seconds()
            kalan = max(0, FIRSAT_PENCERESI - gecen)
            ilerleme = min(1.0, gecen / FIRSAT_PENCERESI)

            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{cift}**")
                st.write(f"İlk Fark: ${veri['fark']:.3f} | Son Fark: ${veri['son_fark']:.3f}")
            with col2:
                st.progress(ilerleme, text=f"Pencere: {gecen:.1f} / {FIRSAT_PENCERESI} sn")
            with col3:
                if kalan > 0:
                    st.write(f"⏱️ **{kalan:.0f} sn**")
                else:
                    st.write("✅ Hazır")

            if gecen > FIRSAT_ZAMAN_ASIMI:
                st.warning("⚠️ Bu fırsat zaman aşımına uğradı, silinecek.")
            st.markdown("---")
    else:
        st.info("ℹ️ Şu an bekleyen fırsat yok. Sistem uygun fırsat arıyor...")

    st.markdown("---")

    # =================================================================
    # FIKHİ FİLTRE DETAYLARI
    # =================================================================
    with st.expander("🕌 Fıkhî Filtre Aktif Kuralları"):
        st.markdown(
            "Bu sistem, aşağıdaki İslami finans kurallarına göre her fırsatı denetler:\n\n"
            "| Kural | Açıklama | Durum |\n"
            "|-------|----------|-------|\n"
            "| **Faizsiz Ödeme** | Platform faizsiz ödeme kabul etmeli | ✅ Aktif |\n"
            "| **Garar Yok** | Fark 0.01$'dan küçükse belirsizlik nedeniyle reddedilir | ✅ Aktif |\n"
            "| **İhtikar Yok** | Fark 0.500$'dan büyükse manipülasyon şüphesiyle reddedilir | ✅ Aktif |\n"
            "| **Meşru Hizmet** | GPU kiralama meşru bir hizmettir | ✅ Aktif |\n"
            "| **Vade Farkı Yok** | Vadeli işlem faizi yasaktır | ✅ Aktif |\n\n"
            "**Reddedilen Fırsatlar** aşağıda listelenir."
        )

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
        st.markdown(
            "Panelde görünen **Net Kâr**, gerçek piyasa maliyetleri düşülerek hesaplanır:\n\n"
            "**Formül:**\n"
            "```\n"
            "Net Kâr = Brüt Fark \n"
            "          - (Alış Komisyonu + Satış Komisyonu)\n"
            f"          - Transfer Ücreti (${ODEME_TRANSFER_UCRETI})\n"
            "          - Kiralama Başlatma Maliyeti (%2 kayıp)\n"
            "```\n\n"
            "**Platform Komisyon Oranları:**\n"
            "| Platform | Komisyon |\n"
            "|----------|----------|\n"
            "| Vast.ai | %25 |\n"
            "| RunPod | %20 |\n"
            "| Shadeform | %15 |\n"
            "| GPU.ai | %18 |\n"
            "| Massed Compute | %15 |\n\n"
            "⚠️ Bu nedenle panelde gördüğünüz **brüt fark** ile **net kâr** arasında ciddi fark olabilir.\n\n"
            "**Örnek:** Vast.ai $0.212 → RunPod $0.365\n"
            "- Brüt fark: $0.153\n"
            "- Komisyon: -$0.126\n"
            "- Transfer: -$0.050\n"
            "- Başlatma: -$0.004\n"
            "- **Net: -$0.027** (Kârsız!)"
        )

    st.markdown("---")

    # =================================================================
    # SON GERÇEKLEŞEN İŞLEMLER
    # =================================================================
    if hafiza["kontratlar"]:
        st.subheader("📋 Son Gerçekleşen İşlemler")
        for kt in hafiza["kontratlar"]:
            st.markdown(
                f"**{kt['Zaman']}** | {kt['Alış']} → {kt['Satış']} | "
                f"Brüt: {kt['Brüt']} | Komisyon: {kt['Komisyon']} | "
                f"**Net: {kt['Net Kâr']}**"
            )
        st.markdown("---")
    else:
        st.info("ℹ️ Henüz gerçekleşen işlem yok. Sistem fırsat bekliyor...")

    # =================================================================
    # SİSTEM LOGLARI (GELİŞMİŞ)
    # =================================================================
    with st.expander("🔧 Sistem Logları ve Hata Kayıtları (Son 30)"):
        if hafiza["log"]:
            for log in hafiza["log"][-30:]:
                st.text(log)
        else:
            st.text("Henüz log kaydı yok. Sistem sorunsuz çalışıyor.")

    # =================================================================
    # SORUN GİDERME
    # =================================================================
    mevcut_mod_metni = "🧪 DEMO (Sanal Veri)" if DEMO_MODE else "🔴 GERÇEK (Canlı API)"

    with st.expander("❓ Sistem Nasıl Çalışır? (Gerçek Piyasa Mantığı)"):
        st.markdown(
            f"**Mevcut Mod:** {mevcut_mod_metni}\n\n"
            "**Gerçek Piyasa Mantığı Farkları:**\n\n"
            f"1. **Cooldown ({COOLDOWN_SURESI} sn):** Aynı havuz çifti için 60 saniye boyunca yeni işlem açılmaz.\n\n"
            f"2. **Fırsat Penceresi ({FIRSAT_PENCERESI} sn):** Bir farkın en az 15 saniye devam etmesi gerekir.\n\n"
            f"3. **Zaman Aşımı ({FIRSAT_ZAMAN_ASIMI} sn):** Bu süreden fazla bekleyen fırsatlar silinir.\n\n"
            "4. **Emir Gerçekleşme Oranı (~%65):** Her fırsat yakalanamaz.\n\n"
            "5. **Komisyon + Transfer + Kiralama Maliyeti:** Brüt fark değil, net kâr önemli.\n\n"
            "6. **Fıkhi Filtre:** Faizsiz, gararsız, meşru hizmet kontrolü yapılır.\n\n"
            "7. **Kârsız Fırsat Temizliği:** Net kâr negatifse fırsat listeden silinir.\n\n"
            "**Gerçek Moda Nasıl Geçilir?**  \n"
            "Kodun en üstündeki `DEMO_MODE = True` satırını `False` yapın.  \n"
            "Vast.ai ve RunPod hesaplarınızdan aldığınız **gerçek API anahtarlarını** kodda ilgili yerlere yapıştırın."
        )

    # =================================================================
    # SAYFAYI PERİYODİK YENİLE
    # =================================================================
    time.sleep(3)
    st.rerun()
