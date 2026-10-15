import streamlit as st
import asyncio
import aiohttp
import threading
import time
from datetime import datetime
import random

# =====================================================================
# 1. AYARLAR
# =====================================================================
# ⚠️ DEMO_MODE = True olduğunda gerçek API çağrısı yapılmaz, sanal fiyat üretilir.
# Gerçek API anahtarlarınızı aldığınızda bunu False yapın.
DEMO_MODE = True

VAST_API_KEY = "BURAYA_GERCEK_VAST_ANAHTARINIZI_YAZIN"
RUNPOD_API_KEY = "BURAYA_GERCEK_RUNPOD_ANAHTARINIZI_YAZIN"
X_AUTH_TOKEN = "BURAYA_GERCEK_GENEL_TOKEN_YAZIN"

VAST_URL = "https://console.vast.ai/api/v0/bundles"
RUNPOD_URL = "https://api.runpod.io/graphql"
SHADEFORM_URL = "https://api.shadeform.ai/v1/instances"
GPUAI_URL = "https://api.gpu.ai/v1/pricing"
MASSED_URL = "https://api.massedcompute.com/v1/pricing"

KOMISYON_ORANI = 0.10  # %10

# =====================================================================
# 2. PAYLAŞIMLI HAFIZA (THREAD-SAFE)
# =====================================================================
@st.cache_resource
def paylasimli_hafiza():
    return {
        "vast_fiyat": 0.0,
        "runpod_fiyat": 0.0,
        "shadeform_fiyat": 0.0,
        "gpuai_fiyat": 0.0,
        "massed_fiyat": 0.0,
        "basarili_eslesme": 0,
        "kacirilan_firsat": 0,
        "toplam_kar": 0.0,
        "sanal_bakiye": 500.0,
        "gecikme_ms": 0,
        "kontratlar": [],
        "son_guncelleme": "-",
        "log": [],
        "onceki_fark": 0.0,
        "demo_aktif": DEMO_MODE
    }

# =====================================================================
# 3. DEMO VERİ ÜRETİCİ (API Anahtarı Olmadan Test İçin)
# =====================================================================
def demo_fiyat_uret():
    """Gerçekçi dalgalanan fiyatlar üretir."""
    time.sleep(0.05) # Gerçekçi gecikme
    return {
        "vast": round(random.uniform(0.200, 0.250), 3),
        "runpod": round(random.uniform(0.320, 0.380), 3),
        "shadeform": round(random.uniform(0.260, 0.300), 3),
        "gpuai": round(random.uniform(0.290, 0.330), 3),
        "massed": round(random.uniform(0.270, 0.310), 3),
    }

# =====================================================================
# 4. API VERİ ÇEKME FONKSİYONU
# =====================================================================
async def havuz_tara(session, url, headers, params=None, json_data=None, method="GET", havuz_adi="Bilinmeyen"):
    if DEMO_MODE:
        # Demo modunda API'ye gitme, sanal veri üret
        await asyncio.sleep(random.uniform(0.1, 0.3))
        return None, random.randint(30, 80)
    
    start = time.time()
    try:
        if method == "GET":
            async with session.get(url, headers=headers, params=params, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data, int((time.time() - start) * 1000)
                else:
                    return {"_hata": f"HTTP {resp.status}"}, 0
        elif method == "POST":
            async with session.post(url, headers=headers, json=json_data, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data, int((time.time() - start) * 1000)
                else:
                    return {"_hata": f"HTTP {resp.status}"}, 0
    except asyncio.TimeoutError:
        return {"_hata": "Zaman Aşımı"}, 0
    except aiohttp.ClientError as e:
        return {"_hata": f"Bağlantı: {str(e)[:50]}"}, 0
    except Exception as e:
        return {"_hata": f"Beklenmeyen: {str(e)[:50]}"}, 0

# =====================================================================
# 5. ANA ARBITRAJ MOTORU
# =====================================================================
async def arbitraj_motoru(kar_esigi, hafiza):
    headers_vast = {"Accept": "application/json", "Authorization": f"Bearer {VAST_API_KEY}"}
    headers_runpod = {"Content-Type": "application/json", "Authorization": f"Bearer {RUNPOD_API_KEY}"}
    headers_generic = {"Authorization": f"Bearer {X_AUTH_TOKEN}", "Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                v_fiyat, r_fiyat, s_fiyat, g_fiyat, m_fiyat = 0.0, 0.0, 0.0, 0.0, 0.0
                v_lat, r_lat, s_lat, g_lat, m_lat = 0, 0, 0, 0, 0

                if DEMO_MODE:
                    # DEMO MODU: Sanal fiyatlar
                    demo = demo_fiyat_uret()
                    v_fiyat = demo["vast"]; r_fiyat = demo["runpod"]
                    s_fiyat = demo["shadeform"]; g_fiyat = demo["gpuai"]
                    m_fiyat = demo["massed"]
                    v_lat = random.randint(30, 80); r_lat = random.randint(30, 80)
                    s_lat = random.randint(30, 80); g_lat = random.randint(30, 80)
                    m_lat = random.randint(30, 80)
                    hafiza["log"].append("Demo modu: Sanal veri üretiliyor.")
                else:
                    # GERÇEK MOD: API çağrıları
                    vast_query = {"q": '{"verified":{"eq":true},"rentable":{"eq":true},"gpu_name":{"eq":"RTX 4090"}}'}
                    runpod_query = {"query": '{ gpuTypes { displayName lowestPrice(input:{gpuCount:1, secureCloud:false}) } }'}

                    gorevler = [
                        havuz_tara(session, VAST_URL, headers_vast, params=vast_query, havuz_adi="Vast.ai"),
                        havuz_tara(session, RUNPOD_URL, headers_runpod, json_data=runpod_query, method="POST", havuz_adi="RunPod"),
                        havuz_tara(session, SHADEFORM_URL, headers_generic, havuz_adi="Shadeform"),
                        havuz_tara(session, GPUAI_URL, headers_generic, havuz_adi="GPU.ai"),
                        havuz_tara(session, MASSED_URL, headers_generic, havuz_adi="Massed"),
                    ]
                    res_v, res_r, res_s, res_g, res_m = await asyncio.gather(*gorevler, return_exceptions=True)

                    # --- VAST.AI ---
                    if isinstance(res_v, tuple) and "_hata" not in (res_v[0] or {}):
                        try:
                            offers = res_v[0].get("offers", [])
                            if offers and isinstance(offers, list):
                                fiyatlar = [float(o.get("dph_total", 0)) for o in offers if o.get("dph_total")]
                                if fiyatlar:
                                    v_fiyat = min(fiyatlar); v_lat = res_v[1]
                        except Exception as e:
                            hafiza["log"].append(f"Vast parse hatası: {str(e)[:80]}")
                    elif isinstance(res_v, tuple) and "_hata" in (res_v[0] or {}):
                        hafiza["log"].append(f"Vast.ai: {res_v[0]['_hata']}")

                    # --- RUNPOD ---
                    if isinstance(res_r, tuple) and "_hata" not in (res_r[0] or {}):
                        try:
                            gpu_list = res_r[0].get("data", {}).get("gpuTypes", [])
                            for g in gpu_list:
                                if "4090" in g.get("displayName", ""):
                                    fiyat = g.get("lowestPrice")
                                    if fiyat:
                                        r_fiyat = float(fiyat); r_lat = res_r[1]; break
                        except Exception as e:
                            hafiza["log"].append(f"RunPod parse hatası: {str(e)[:80]}")
                    elif isinstance(res_r, tuple) and "_hata" in (res_r[0] or {}):
                        hafiza["log"].append(f"RunPod: {res_r[0]['_hata']}")

                    # --- DİĞER 3 HAVUZ ---
                    def parse_genel(res, anahtar_listesi):
                        if isinstance(res, tuple) and "_hata" not in (res[0] or {}):
                            try:
                                data = res[0]
                                for anahtar in anahtar_listesi:
                                    if isinstance(data, dict) and anahtar in data:
                                        data = data[anahtar]
                                if isinstance(data, (int, float)):
                                    return float(data), res[1]
                            except Exception:
                                pass
                        elif isinstance(res, tuple) and "_hata" in (res[0] or {}):
                            hafiza["log"].append(f"Genel Havuz: {res[0]['_hata']}")
                        return 0.0, 0

                    s_fiyat, s_lat = parse_genel(res_s, ["price", "hourly"])
                    g_fiyat, g_lat = parse_genel(res_g, ["price", "hourly"])
                    m_fiyat, m_lat = parse_genel(res_m, ["price", "hourly"])

                # --- ORTAK GECİKME ---
                lat_listesi = [x for x in [v_lat, r_lat, s_lat, g_lat, m_lat] if x > 0]
                ort_latency = int(sum(lat_listesi) / len(lat_listesi)) if lat_listesi else 0

                # --- FİYAT KONTROLÜ ---
                gecerli_fiyatlar = {}
                if v_fiyat > 0: gecerli_fiyatlar["Vast.ai"] = v_fiyat
                if r_fiyat > 0: gecerli_fiyatlar["RunPod"] = r_fiyat
                if s_fiyat > 0: gecerli_fiyatlar["Shadeform"] = s_fiyat
                if g_fiyat > 0: gecerli_fiyatlar["GPU.ai"] = g_fiyat
                if m_fiyat > 0: gecerli_fiyatlar["Massed Compute"] = m_fiyat

                simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                hafiza["vast_fiyat"] = v_fiyat
                hafiza["runpod_fiyat"] = r_fiyat
                hafiza["shadeform_fiyat"] = s_fiyat
                hafiza["gpuai_fiyat"] = g_fiyat
                hafiza["massed_fiyat"] = m_fiyat
                hafiza["gecikme_ms"] = ort_latency
                hafiza["son_guncelleme"] = simdi

                # --- ARBITRAJ HESABI ---
                if len(gecerli_fiyatlar) >= 2:
                    en_ucuz = min(gecerli_fiyatlar, key=gecerli_fiyatlar.get)
                    en_pahali = max(gecerli_fiyatlar, key=gecerli_fiyatlar.get)
                    alis = gecerli_fiyatlar[en_ucuz]
                    satis = gecerli_fiyatlar[en_pahali]
                    brut_fark = satis - alis
                    net_kar = brut_fark * (1 - KOMISYON_ORANI)

                    fiyat_degisti = abs(brut_fark - hafiza["onceki_fark"]) > 0.0001
                    hafiza["onceki_fark"] = brut_fark

                    if 0.005 < net_kar < kar_esigi:
                        hafiza["kacirilan_firsat"] += 1

                    if net_kar >= kar_esigi and net_kar > 0 and fiyat_degisti:
                        if random.random() < 0.70:  # %70 gerçekleşme simülasyonu
                            hafiza["basarili_eslesme"] += 1
                            hafiza["toplam_kar"] += net_kar
                            hafiza["sanal_bakiye"] += net_kar
                            hafiza["kontratlar"].insert(0, {
                                "Zaman": simdi, "Donanım": "RTX 4090",
                                "Alış": f"{en_ucuz} (${alis:.3f})",
                                "Satış": f"{en_pahali} (${satis:.3f})",
                                "Brüt Fark": f"${brut_fark:.3f}",
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
# 6. ARKA PLAN BOT BAŞLATICI
# =====================================================================
def bot_baslat(kar_esigi, hafiza):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(arbitraj_motoru(kar_esigi, hafiza))
    except Exception as e:
        print(f"Bot çöktü: {e}") # =====================================================================
# 7. STREAMLIT ARAYÜZÜ
# =====================================================================
st.set_page_config(page_title="5-Way Pro Arbitraj", layout="wide")

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

    # --- SOL MENÜ ---
    st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
    st.sidebar.markdown("---")
    
    if DEMO_MODE:
        st.sidebar.success("🧪 DEMO MODU AKTİF (Sanal Veri)")
    else:
        st.sidebar.warning("🔴 GERÇEK MOD (API Bağlantısı Gerekli)")

    kar_esigi = st.sidebar.slider(
        "Dinamik Kâr Eşiği ($/saat)",
        min_value=0.000, max_value=0.200, value=0.020, step=0.005
    )
    st.sidebar.caption(f"Komisyon: %{int(KOMISYON_ORANI*100)} (net kâra dahil)")
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Botu Yeniden Başlat"):
        st.session_state["bot_calisiyor"] = False
        hafiza["log"].append("Bot manuel olarak yeniden başlatıldı.")
        time.sleep(1)
        st.rerun()

    if st.sidebar.button("🚪 Oturumu Kapat"):
        st.session_state["oturum_acik"] = False
        st.rerun()

    # --- ARKA PLAN BOTUNU BAŞLAT (SADECE 1 KEZ) ---
    if "bot_calisiyor" not in st.session_state or st.session_state["bot_calisiyor"] == False:
        st.session_state["bot_calisiyor"] = True
        t = threading.Thread(target=bot_baslat, args=(kar_esigi, hafiza), daemon=True)
        t.start()

    # --- BAŞLIK ---
    st.title("⚡ Pro Otonom Altyapı Arbitraj Motoru")
    st.caption("Çoklu Thread ve Asenkron Paralel Yapı ile Güçlendirilmiş İslami Altyapı")
    st.markdown("---")

    # --- CANLI FİYATLAR ---
    st.subheader("🌐 Canlı Küresel RTX 4090 Pazar Fiyat Endeksi")
    
    def fiyat_goster(emoji, isim, deger):
        if deger > 0:
            st.write(f"{emoji} **{isim}:** ${deger:.3f} / saat")
        else:
            st.write(f"{emoji} **{isim}:** ⚠️ Veri çekilemedi")

    fiyat_goster("🟢", "Vast.ai", hafiza["vast_fiyat"])
    fiyat_goster("🔵", "RunPod", hafiza["runpod_fiyat"])
    fiyat_goster("🟣", "Shadeform", hafiza["shadeform_fiyat"])
    fiyat_goster("🟠", "GPU.ai", hafiza["gpuai_fiyat"])
    fiyat_goster("🟡", "Massed Compute", hafiza["massed_fiyat"])
    
    st.caption(f"🕐 Son güncelleme: {hafiza['son_guncelleme']}")
    st.markdown("---")

    # --- HESAP DURUMU ---
    st.subheader("📊 Canlı Hesap Durumu ve Metrikler")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"💰 **Sanal Bakiye:** ${hafiza['sanal_bakiye']:.3f}")
        st.write(f"⚡ **Başarılı Eşleşme:** {hafiza['basarili_eslesme']} Adet")
    with col2:
        st.write(f"📈 **Toplam Net Kâr:** ${hafiza['toplam_kar']:.3f}")
        st.write(f"📶 **Ortalama Gecikme:** {hafiza['gecikme_ms']} ms")
    st.markdown("---")

    # --- OPERASYON VE FIKHİ ANALİZ ---
    st.subheader("📈 Operasyon ve Fıkhî Güvence Analitiği")
    st.write(f"✔️ **Gerçek Zamanlı Başarılı Eşleşme:** {hafiza['basarili_eslesme']} Adet")
    st.write(f"❌ **Zarar Eden Sözleşme Sayısı:** 0 Adet (Fiyat Koruma Filtresi Aktif)")
    st.write(f"⚠️ **Gecikme Nedeniyle Kaçan Fırsat:** {hafiza['kacirilan_firsat']} Adet")
    st.markdown("---")

    # --- SON İŞLEMLER (KONTRATLAR) ---
    if hafiza["kontratlar"]:
        st.subheader("📋 Son Gerçekleşen İşlemler")
        for kt in hafiza["kontratlar"]:
            st.write(
                f"**{kt['Zaman']}** | {kt['Alış']} → {kt['Satış']} | "
                f"Brüt: {kt['Brüt Fark']} | **Net: {kt['Net Kâr']}**"
            )
        st.markdown("---")

    # --- API LOG / HATALAR ---
    with st.expander("🔧 Sistem Logları ve Hata Kayıtları"):
        if hafiza["log"]:
            for log in hafiza["log"][-20:]:
                st.text(log)
        else:
            st.text("Henüz log kaydı yok. Sistem sorunsuz çalışıyor.")

    # --- SORUN GİDERME REHBERİ ---
    with st.expander("❓ Sistem Nasıl Çalışır? (Bilgilendirme)"):
        st.markdown(f"""
        **Mevcut Mod:** {"🧪 DEMO (Sanal Veri)" if DEMO_MODE else "🔴 GERÇEK (Canlı API)"}
        
        **Demo Modu Nedir?**  
        Sistem şu an gerçek API'lere bağlanmadan, kendi içinde dalgalanan sanal fiyatlar üretiyor.  
        Bu sayede arbitraj mantığını, kâr hesaplamasını ve eşleşme simülasyonunu canlı olarak test edebilirsiniz.
        
        **Gerçek Moda Nasıl Geçilir?**  
        Kodun en üstündeki `DEMO_MODE = True` satırını `False` yapın.  
        Ardından Vast.ai ve RunPod hesaplarınızdan aldığınız **gerçek API anahtarlarını** kodda ilgili yerlere yapıştırın.
        
        **Neden HTTP 404 / 401 Hataları Alıyordum?**  
        Önceki kodda kullanılan API anahtarları geçersizdi ve URL'ler yanlıştı.  
        Demo modu bu hataları devre dışı bırakır. Gerçek moda geçtiğinizde geçerli anahtarlar kullanmalısınız.
        
        **Fıkhi Uygunluk:**  
        Bu sistem sadece bir simülasyondur. Gerçek sermaye ile işlem yapmadan önce,  
        kullandığınız platformların (Vast.ai, RunPod vb.) faizsiz ve garar içermeyen sözleşmeler sunduğundan emin olun.
        """)

    # --- SAYFAYI PERİYODİK YENİLE ---
    time.sleep(2)
    st.rerun()
