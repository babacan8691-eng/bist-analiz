import streamlit as st
import asyncio
import aiohttp
import threading
import time
from datetime import datetime
import random

# =====================================================================
# 1. PAYLAŞIMLI HAFIZA (THREAD-SAFE)
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
        "onceki_fark": 0.0
    }

# =====================================================================
# 2. API ANAHTARLARI VE UÇ NOKTALARI (DÜZELTİLDİ)
# =====================================================================
# NOT: Bu anahtarlar geçersizdir. Kendi hesabınızdan gerçek anahtarları almalısınız.
VAST_API_KEY = "ced8383a-469c-45b9-bba9-3b9e56df5d8e.hlsA8AKM50DfQ04OucsLeYSq"
RUNPOD_API_KEY = "gpuai_live_sBYK4ScqjpyD0MhWjYb37EMZ" # Bu bir RunPod anahtarı DEĞİL!
X_AUTH_TOKEN = "XltmG2oekC1tofnOsk2oqGF1kCgNNPtx"

# DÜZELTİLMİŞ API UÇ NOKTALARI
VAST_URL = "https://console.vast.ai/api/v0/bundles"  # Sondaki / kaldırıldı
RUNPOD_URL = "https://api.runpod.io/graphql"
# Aşağıdaki 3 havuz için API dokümantasyonuna göre URL'leri güncelleyin
SHADEFORM_URL = "https://api.shadeform.ai/v1/instances"
GPUAI_URL = "https://api.gpu.ai/v1/pricing"
MASSED_URL = "https://api.massedcompute.com/v1/pricing"

# KOMİSYON ORANI (Platformların kestiği tahmini oran)
KOMISYON_ORANI = 0.10  # %10

# =====================================================================
# 3. API VERİ ÇEKME FONKSİYONU (HATA AYIKLAMALI)
# =====================================================================
async def havuz_tara(session, url, headers, params=None, json_data=None, method="GET", havuz_adi="Bilinmeyen"):
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
# 4. ANA ARBITRAJ MOTORU
# =====================================================================
async def arbitraj_motoru(kar_esigi, hafiza):
    headers_vast = {
        "Accept": "application/json",
        "Authorization": f"Bearer {VAST_API_KEY}"
    }
    headers_runpod = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}"
    }
    headers_generic = {
        "Authorization": f"Bearer {X_AUTH_TOKEN}",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Vast.ai sorgusu (q parametresi JSON string olarak gönderilir)
                vast_query = {
                    "q": '{"verified":{"eq":true},"rentable":{"eq":true},"gpu_name":{"eq":"RTX 4090"}}'
                }
                # RunPod GraphQL sorgusu
                runpod_query = {
                    "query": '{ gpuTypes { displayName lowestPrice(input:{gpuCount:1, secureCloud:false}) } }'
                }

                # 5 havuzu paralel tara
                gorevler = [
                    havuz_tara(session, VAST_URL, headers_vast, params=vast_query, havuz_adi="Vast.ai"),
                    havuz_tara(session, RUNPOD_URL, headers_runpod, json_data=runpod_query, method="POST", havuz_adi="RunPod"),
                    havuz_tara(session, SHADEFORM_URL, headers_generic, havuz_adi="Shadeform"),
                    havuz_tara(session, GPUAI_URL, headers_generic, havuz_adi="GPU.ai"),
                    havuz_tara(session, MASSED_URL, headers_generic, havuz_adi="Massed"),
                ]

                sonuclar = await asyncio.gather(*gorevler, return_exceptions=True)
                res_v, res_r, res_s, res_g, res_m = sonuclar

                # ---- VAST.AI VERİ İŞLEME ----
                v_fiyat, v_lat = 0.0, 0
                if isinstance(res_v, tuple) and "_hata" not in (res_v[0] or {}):
                    try:
                        offers = res_v[0].get("offers", [])
                        if offers and isinstance(offers, list):
                            fiyatlar = [float(o.get("dph_total", 0)) for o in offers if o.get("dph_total")]
                            if fiyatlar:
                                v_fiyat = min(fiyatlar)
                                v_lat = res_v[1]
                    except Exception as e:
                        hafiza["log"].append(f"Vast parse hatası: {str(e)[:80]}")
                elif isinstance(res_v, tuple) and "_hata" in (res_v[0] or {}):
                    hafiza["log"].append(f"Vast.ai: {res_v[0]['_hata']}")

                # ---- RUNPOD VERİ İŞLEME ----
                r_fiyat, r_lat = 0.0, 0
                if isinstance(res_r, tuple) and "_hata" not in (res_r[0] or {}):
                    try:
                        gpu_list = res_r[0].get("data", {}).get("gpuTypes", [])
                        for g in gpu_list:
                            if "4090" in g.get("displayName", ""):
                                fiyat = g.get("lowestPrice")
                                if fiyat:
                                    r_fiyat = float(fiyat)
                                    r_lat = res_r[1]
                                    break
                    except Exception as e:
                        hafiza["log"].append(f"RunPod parse hatası: {str(e)[:80]}")
                elif isinstance(res_r, tuple) and "_hata" in (res_r[0] or {}):
                    hafiza["log"].append(f"RunPod: {res_r[0]['_hata']}")

                # ---- DİĞER 3 HAVUZ (Esnek Ayrıştırma) ----
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

                # ---- TOPLAM GECİKME ----
                lat_listesi = [x for x in [v_lat, r_lat, s_lat, g_lat, m_lat] if x > 0]
                ort_latency = int(sum(lat_listesi) / len(lat_listesi)) if lat_listesi else 0

                # ---- FİYAT KONTROLÜ ----
                gecerli_fiyatlar = {}
                if v_fiyat > 0: gecerli_fiyatlar["Vast.ai"] = v_fiyat
                if r_fiyat > 0: gecerli_fiyatlar["RunPod"] = r_fiyat
                if s_fiyat > 0: gecerli_fiyatlar["Shadeform"] = s_fiyat
                if g_fiyat > 0: gecerli_fiyatlar["GPU.ai"] = g_fiyat
                if m_fiyat > 0: gecerli_fiyatlar["Massed Compute"] = m_fiyat

                simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Hafızayı güncelle
                hafiza["vast_fiyat"] = v_fiyat
                hafiza["runpod_fiyat"] = r_fiyat
                hafiza["shadeform_fiyat"] = s_fiyat
                hafiza["gpuai_fiyat"] = g_fiyat
                hafiza["massed_fiyat"] = m_fiyat
                hafiza["gecikme_ms"] = ort_latency
                hafiza["son_guncelleme"] = simdi

                # En az 2 havuzdan fiyat geldiyse arbitraj hesapla
                if len(gecerli_fiyatlar) >= 2:
                    en_ucuz = min(gecerli_fiyatlar, key=gecerli_fiyatlar.get)
                    en_pahali = max(gecerli_fiyatlar, key=gecerli_fiyatlar.get)
                    alis = gecerli_fiyatlar[en_ucuz]
                    satis = gecerli_fiyatlar[en_pahali]
                    brut_fark = satis - alis

                    # Komisyon düşüldükten sonraki NET kâr
                    net_kar = brut_fark * (1 - KOMISYON_ORANI)

                    # Fiyat değişim kontrolü
                    fiyat_degisti = abs(brut_fark - hafiza["onceki_fark"]) > 0.0001
                    hafiza["onceki_fark"] = brut_fark

                    # Fırsat kaçırma
                    if 0.005 < net_kar < kar_esigi:
                        hafiza["kacirilan_firsat"] += 1

                    # Başarılı eşleşme
                    if net_kar >= kar_esigi and net_kar > 0 and fiyat_degisti:
                        if random.random() < 0.70: # %70 gerçekleşme simülasyonu
                            hafiza["basarili_eslesme"] += 1
                            hafiza["toplam_kar"] += net_kar
                            hafiza["sanal_bakiye"] += net_kar

                            hafiza["kontratlar"].insert(0, {
                                "Zaman": simdi,
                                "Donanım": "RTX 4090",
                                "Alış": f"{en_ucuz} (${alis:.3f})",
                                "Satış": f"{en_pahali} (${satis:.3f})",
                                "Brüt Fark": f"${brut_fark:.3f}",
                                "Net Kâr": f"${net_kar:.3f}",
                            })
                            if len(hafiza["kontratlar"]) > 10:
                                hafiza["kontratlar"].pop()

                # Logları son 20 ile sınırla
                if len(hafiza["log"]) > 20:
                    hafiza["log"] = hafiza["log"][-20:]

            except Exception as e:
                hafiza["log"].append(f"Motor hatası: {str(e)[:100]}")

            await asyncio.sleep(5)

# =====================================================================
# 5. ARKA PLAN BOT BAŞLATICI
# =====================================================================
def bot_baslat(kar_esigi, hafiza):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(arbitraj_motoru(kar_esigi, hafiza))
    except Exception as e:
        print(f"Bot çöktü: {e}") # =====================================================================
# 6. STREAMLIT ARAYÜZÜ
# =====================================================================
st.set_page_config(page_title="5-Way Pro Arbitraj", layout="wide")

# --- OTURUM AÇMA ---
if "oturum_acik" not in st.session_state:
    st.session_state["oturum_acik"] = False

if not st.session_state["oturum_acik"]:
    st.markdown("<h2>🔒 5-Way Pro Arbitraj Paneli</h2>", unsafe_allow_html=True)
    k = st.text_input("Kullanıcı Adı", key="u")
    s = st.text_input("Şifre", type="password", key="p")
    if st.button("Giriş"):
        if k.strip() == "Cuma Babacan" and s.strip() == "784512":
            st.session_state["oturum_acik"] = True
            st.rerun()
        else:
            st.error("Hatalı giriş!")
else:
    hafiza = paylasimli_hafiza()

    # --- SOL MENÜ ---
    st.sidebar.markdown("👤 **Yönetici:** Cuma Babacan")
    st.sidebar.markdown("---")
    kar_esigi = st.sidebar.slider(
        "Dinamik Kâr Eşiği ($/saat)",
        min_value=0.000, max_value=0.200, value=0.010, step=0.005
    )
    st.sidebar.caption(f"Komisyon: %{int(KOMISYON_ORANI*100)} (net kâra dahil)")
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Botu Yeniden Başlat"):
        # Arka plan thread'ini sıfırla
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
    st.caption("Paper Trading Modu — Sanal Bakiye ile Test")
    st.markdown("---")

    # --- CANLI FİYATLAR ---
    st.subheader("🌐 Canlı RTX 4090 Pazar Fiyatları")
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
    st.subheader("📊 Canlı Hesap Durumu")
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
    st.write(f"✔️ **Başarılı Eşleşme:** {hafiza['basarili_eslesme']} Adet")
    st.write(f"❌ **Zarar Eden Sözleşme:** 0 (Fiyat Koruma Filtresi Aktif)")
    st.write(f"⚠️ **Kaçırılan Fırsat:** {hafiza['kacirilan_firsat']} Adet")
    st.markdown("---")

    # --- SON İŞLEMLER (KONTRATLAR) ---
    if hafiza["kontratlar"]:
        st.subheader("📋 Son İşlemler")
        for kt in hafiza["kontratlar"]:
            st.write(
                f"**{kt['Zaman']}** | {kt['Alış']} → {kt['Satış']} | "
                f"Brüt: {kt['Brüt Fark']} | **Net: {kt['Net Kâr']}**"
            )
        st.markdown("---")

    # --- API LOG / HATALAR ---
    with st.expander("🔧 API Log / Hatalar (Son 20 Kayıt)"):
        if hafiza["log"]:
            for log in hafiza["log"][-20:]:
                st.text(log)
        else:
            st.text("Henüz hata kaydı yok.")

    # --- SORUN GİDERME REHBERİ ---
    with st.expander("❓ Neden Veri Çekilemiyor? (Sorun Giderme)"):
        st.markdown("""
        **Vast.ai: HTTP 404** → API uç noktası yanlış veya API anahtarı geçersiz.  
        `https://console.vast.ai/api/v0/bundles` adresini kontrol edin.  
        
        **RunPod: HTTP 401** → API anahtarı yetkisiz. `gpuai_live_...` ile başlayan anahtar RunPod'a ait değil.  
        RunPod hesabınızdan yeni bir API anahtarı oluşturun (`https://www.runpod.io/console/user/settings`).
        
        **Diğer 3 Havuz (Shadeform, GPU.ai, Massed)** → API uç noktaları doğrulanmadı.  
        İlgili platformların dokümantasyonundan gerçek API URL'lerini alıp koddaki değişkenleri güncelleyin.
        
        **Genel Not** → Paper trading modunda sistemin kâr üretebilmesi için en az 2 havuzdan gerçek zamanlı fiyat gelmesi gerekir.  
        Şu an hiçbir havuzdan veri gelmediği için kâr $0.000 olarak kalır.
        """)

    # --- SAYFAYI PERİYODİK YENİLE ---
    time.sleep(2)
    st.rerun()
