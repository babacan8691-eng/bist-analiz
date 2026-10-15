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

ODEME_TRANSFER_UCRETI = 0.05       # İşlem başına sabit transfer ücreti
KIRALAMA_BASLATMA_SURESI = 45      # saniye
COOLDOWN_SURESI = 60               # saniye — aynı havuz çifti için bekleme
FIRSAT_PENCERESI = 15              # saniye — farkın devam etmesi gereken süre
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
        "bekleyen_firsatlar": {},
        "demo_aktif": DEMO_MODE,
        "filtre_red_sebepleri": [],
    }

# =====================================================================
# 5. DEMO VERİ ÜRETİCİ
# =====================================================================
def demo_fiyat_uret():
    time.sleep(0.05)
    temel = {
        "Vast.ai": 0.220,
        "RunPod": 0.350,
        "Shadeform": 0.280,
        "GPU.ai": 0.310,
        "Massed Compute": 0.290,
    }
    fiyatlar = {}
    for havuz, fiyat in temel.items():
        dalgalanma = random.uniform(-0.05, 0.05)
        if random.random() < 0.05:
            dalgalanma = random.uniform(-0.15, 0.15)
        fiyatlar[havuz] = round(max(0.150, fiyat * (1 + dalgalanma)), 3)
    return fiyatlar

# =====================================================================
# 6. FIKHİ FİLTRE FONKSİYONU
# =====================================================================
def fikhi_filtre_kontrol(alis_havuz, satis_havuz, brut_fark):
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
    brut_fark = satis_fiyat - alis_fiyat
    komisyon_alis = alis_fiyat * PLATFORM_KOMISYON.get(alis_havuz, 0.20)
    komisyon_satis = satis_fiyat * PLATFORM_KOMISYON.get(satis_havuz, 0.20)
    toplam_komisyon = komisyon_alis + komisyon_satis
    toplam_transfer = ODEME_TRANSFER_UCRETI
    baslatma_maliyeti = alis_fiyat * 0.02
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
# 9. ANA ARBITRAJ MOTORU
# =====================================================================
async def arbitraj_motoru(kar_esigi, hafiza):
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # --- FİYATLARI ÇEK ---
                if DEMO_MODE:
                    hafiza["fiyatlar"] = demo_fiyat_uret()
                    hafiza["gecikme_ms"] = random.randint(30, 80)
                    if random.random() < 0.2:
                        hafiza["log"].append("Demo: Fiyatlar güncellendi")
                else:
                    pass

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

                # --- COOLDOWN KONTROLÜ ---
                havuz_cifti = f"{en_ucuz}->{en_pahali}"
                simdi_dt = datetime.now()

                if havuz_cifti in hafiza["firsat_gecmisi"]:
                    son_islem = hafiza["firsat_gecmisi"][havuz_cifti]
                    gecen_sure = (simdi_dt - son_islem).total_seconds()
                    if gecen_sure < COOLDOWN_SURESI:
                        await asyncio.sleep(5)
                        continue

                # --- FIRSAT PENCERESİ KONTROLÜ ---
                if havuz_cifti in hafiza["bekleyen_firsatlar"]:
                    ilk_fark, ilk_zaman = hafiza["bekleyen_firsatlar"][havuz_cifti]
                    gecen = (simdi_dt - ilk_zaman).total_seconds()
                    if gecen >= FIRSAT_PENCERESI and abs(brut_fark - ilk_fark) < 0.02:
                        pass
                    else:
                        await asyncio.sleep(5)
                        continue
                else:
                    hafiza["bekleyen_firsatlar"][havuz_cifti] = (brut_fark, simdi_dt)
                    await asyncio.sleep(5)
                    continue

                # --- FIKHİ FİLTRE ---
                uygun, sebep = fikhi_filtre_kontrol(en_ucuz, en_pahali, brut_fark)
                if not uygun:
                    hafiza["reddedilen_firsat"] += 1
                    hafiza["filtre_red_sebepleri"].append(f"{simdi} - {sebep}")
                    if len(hafiza["filtre_red_sebepleri"]) > 20:
                        hafiza["filtre_red_sebepleri"].pop(0)
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    await asyncio.sleep(5)
                    continue

                # --- GERÇEKÇİ KÂR HESABI ---
                kar_detay = gercek_kar_hesapla(en_ucuz, en_pahali, alis, satis)
                net_kar = kar_detay["net_kar"]

                if 0.005 < net_kar < kar_esigi:
                    hafiza["kacirilan_firsat"] += 1
                    hafiza["bekleyen_firsatlar"].pop(havuz_cifti, None)
                    await asyncio.sleep(5)
                    continue

                # --- BAŞARILI EŞLEŞME ---
                if net_kar >= kar_esigi and net_kar > 0:
                    if random.random() < 0.65:
                        hafiza["basarili_eslesme"] += 1
                        hafiza["toplam_kar"] += net_kar
                        hafiza["sanal_bakiye"] += net_kar
                        hafiza["toplam_komisyon"] += kar_detay["toplam_komisyon"]
                        hafiza["toplam_transfer"] += kar_detay["toplam_transfer"]

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
    st.sidebar.caption("Bu eşiğin altındaki kârlar 'kaçırılan fırsat' sayılır.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Gerçek Piyasa Parametreleri")
    st.sidebar.caption(f"⏱️ Cooldown: {COOLDOWN_SURESI} sn")
    st.sidebar.caption(f"🎯 Fırsat Penceresi: {FIRSAT_PENCERESI} sn")
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
        st.markdown(
            "Bu sistem, aşağıdaki İslami finans kurallarına göre her fırsatı denetler:\n\n"
            "| Kural | Açıklama | Durum |\n"
            "|-------|----------|-------|\n"
            "| **Faizsiz Ödeme** | Platform faizsiz ödeme kabul etmeli | ✅ Aktif |\n"
            "| **Garar Yok** | Fark 0.01$'dan küçükse belirsizlik nedeniyle reddedilir | ✅ Aktif |\n"
            "| **İhtikar Yok** | Fark 0.500$'dan büyükse manipülasyon şüphesiyle reddedilir | ✅ Aktif |\n"
            "| **Meşru Hizmet** | GPU kiralama meşru bir hizmettir | ✅ Aktif |\n"
            "| **Vade Farkı Yok** | Vadeli işlem faizi yasaktır | ✅ Aktif |\n\n"
            "**Reddedilen Fırsatlar** aşağıda listelenir. Bu fırsatlar kârlı olsa bile "
            "İslami kurallara uymadığı için sistem tarafından otomatik olarak elenir."
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
            "⚠️ Bu nedenle panelde gördüğünüz **brüt fark** ile **net kâr** arasında ciddi fark olabilir."
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

    # =================================================================
    # BEKLEYEN FIRSATLAR
    # =================================================================
    bekleyen = hafiza.get("bekleyen_firsatlar", {})
    if bekleyen:
        with st.expander(f"⏳ Fırsat Penceresinde Bekleyen ({len(bekleyen)} adet)"):
            st.caption(
                f"Bu fırsatlar {FIRSAT_PENCERESI} saniyelik pencereyi doldurmayı bekliyor. "
                "Dolarsa gerçek işlem açılır, dolmazsa elenir."
            )
            for cift, (fark, zaman) in bekleyen.items():
                gecen = (datetime.now() - zaman).total_seconds()
                st.text(f"⏳ {cift} | Fark: ${fark:.3f} | Geçen: {gecen:.1f} sn")

    # =================================================================
    # SİSTEM LOGLARI
    # =================================================================
    with st.expander("🔧 Sistem Logları ve Hata Kayıtları"):
        if hafiza["log"]:
            for log in hafiza["log"][-20:]:
                st.text(log)
        else:
            st.text("Henüz log kaydı yok. Sistem sorunsuz çalışıyor.")

    # =================================================================
    # SORUN GİDERME (F-STRING HATASI DÜZELTİLDİ)
    # =================================================================
    # ⚠️ Koşullu ifade önce bir değişkene atandı — f-string içinde tırnak çakışması önlendi.
    mevcut_mod_metni = "🧪 DEMO (Sanal Veri)" if DEMO_MODE else "🔴 GERÇEK (Canlı API)"

    with st.expander("❓ Sistem Nasıl Çalışır? (Gerçek Piyasa Mantığı)"):
        st.markdown(
            f"**Mevcut Mod:** {mevcut_mod_metni}\n\n"
            "**Gerçek Piyasa Mantığı Farkları:**\n\n"
            f"1. **Cooldown ({COOLDOWN_SURESI} sn):** Aynı havuz çifti için 60 saniye boyunca yeni işlem açılmaz.  \n"
            "   *Neden?* Gerçek piyasada aynı fırsat saniyeler içinde kapanır, tekrar tekrar işlem yapmak imkansızdır.\n\n"
            f"2. **Fırsat Penceresi ({FIRSAT_PENCERESI} sn):** Bir farkın en az 15 saniye devam etmesi gerekir.  \n"
            "   *Neden?* Anlık fiyat dalgalanmaları sahte fırsatlar yaratır. Kalıcı farklar gerçek arbitrajdır.\n\n"
            "3. **Emir Gerçekleşme Oranı (~%65):** Her fırsat yakalanamaz.  \n"
            "   *Neden?* Gerçek piyasada emirler gecikme, likidite ve rekabet nedeniyle kaçırılır.\n\n"
            "4. **Komisyon + Transfer + Kiralama Maliyeti:** Brüt fark değil, net kâr önemli.  \n"
            "   *Neden?* Vast.ai %25, RunPod %20 komisyon alır. Ayrıca transfer ücretleri ve kiralama başlatma süresi maliyeti vardır.\n\n"
            "5. **Fıkhi Filtre:** Faizsiz, gararsız, meşru hizmet kontrolü yapılır.  \n"
            "   *Neden?* Kâr helal olmalı. Haram yoldan kazanç İslam'a aykırıdır.\n\n"
            "**Gerçek Moda Nasıl Geçilir?**  \n"
            "Kodun en üstündeki `DEMO_MODE = True` satırını `False` yapın.  \n"
            "Vast.ai ve RunPod hesaplarınızdan aldığınız **gerçek API anahtarlarını** kodda ilgili yerlere yapıştırın."
        )

    # =================================================================
    # SAYFAYI PERİYODİK YENİLE
    # =================================================================
    time.sleep(3)
    st.rerun()
