

# ==================== DERIN TEKNOLOJI MODULLERI ====================

POZ_KELIMELER = ["yukselis", "artis", "rekor", "kar", "buyume", "guclu", "pozitif", "kazanc", "ihale", "anlasma", "yatirim", "genisleme", "hedef", "basari", "onay", "kabul", "sozlesme", "ortaklik", "siparis", "temettu", "prim"]
NEG_KELIMELER = ["dusus", "azalis", "zarar", "kriz", "iflas", "kayip", "zayif", "negatif", "risk", "borc", "ceza", "sorusturma", "dava", "konkordato", "temerrut", "iptal", "durdurma", "uyari", "not indirimi", "satis baskisi"]


def lstm_tahmin(g):
    """LSTM benzeri agirlikli bellek ile 5 adim sonra tahmin."""
    if len(g) < 30:
        return 0.0, 50.0
    s = g['Close'].tail(30).values
    agirlik = np.array([np.exp(-0.15 * i) for i in range(30)])
    agirlik = agirlik / agirlik.sum()
    hafiza = float(np.sum(s * agirlik))
    son = float(s[-1])
    egim = (son - hafiza) / hafiza * 100 if hafiza > 0 else 0
    hf = g['High'].tail(30).values
    lf = g['Low'].tail(30).values
    vol = float(np.std((hf - lf) / s) * 100)
    tahmin_yuzde = egim * 0.6 + (1 if egim > 0 else -1) * vol * 0.2
    guven = min(95, max(30, 100 - vol * 2))
    return round(tahmin_yuzde, 2), round(guven, 1)


def nlp_duygu(basliklar, hisse):
    """Türkçe finansal haber duygu analizi."""
    if not basliklar:
        return 0.0, 0
    skor = 0
    bulunan = 0
    for h in basliklar:
        b = h.lower()
        if hisse.lower() not in b and hisse not in b:
            continue
        bulunan += 1
        for k in POZ_KELIMELER:
            if k in b:
                skor += 1
        for k in NEG_KELIMELER:
            if k in b:
                skor -= 1
    if bulunan == 0:
        return 0.0, 0
    return round(skor / bulunan, 2), bulunan


def rl_portfoy_agi(g):
    """Pekiştirmeli ogrenme proxy - Q-degeri."""
    if len(g) < 20:
        return 0.0, 0.0
    ret = g['Close'].pct_change().tail(20).fillna(0).values
    odul = np.sum(ret)
    ceza = np.sum(np.minimum(ret, 0))
    q = odul * 0.7 + ceza * 0.3
    sharpe = np.mean(ret) / (np.std(ret) + 1e-9) * np.sqrt(252 * 25)
    return round(q * 100, 2), round(sharpe, 2)


def gnn_manipulasyon(g, emsaller_dict):
    """GNN benzeri korelasyon anomalisi."""
    if len(g) < 20 or not emsaller_dict:
        return 0.0
    kend = g['Close'].pct_change().tail(20).dropna().values
    if len(kend) < 5:
        return 0.0
    korelasyonlar = []
    for _, em in list(emsaller_dict.items())[:10]:
        if len(em) < 20:
            continue
        e = em['Close'].pct_change().tail(20).dropna().values
        n = min(len(kend), len(e))
        if n < 5:
            continue
        a = kend[-n:]
        b = e[-n:]
        if np.std(a) == 0 or np.std(b) == 0:
            continue
        k = np.corrcoef(a, b)[0, 1]
        if not np.isnan(k):
            korelasyonlar.append(k)
    if not korelasyonlar:
        return 0.0
    ort = np.mean(korelasyonlar)
    sapma = abs(ort - 0.5)
    return round(sapma * 100, 1)


def gan_stres_test(g):
    """Bootstrap ile sentetik senaryo - %95 VaR."""
    if len(g) < 30:
        return 0.0
    ret = g['Close'].pct_change().dropna().tail(50).values
    if len(ret) < 10:
        return 0.0
    np.random.seed(42)
    ornek = np.random.choice(ret, size=(100, 10), replace=True)
    yol = np.prod(1 + ornek, axis=1)
    var_95 = np.percentile(yol, 5) - 1
    return round(var_95 * 100, 2)


def hibrit_skor(lstm_y, lstm_g, nlp_s, rl_q, rl_sh, gnn, gan):
    """Tum derin teknoloji skorlarini birlestirir."""
    sk = 50
    sk += lstm_y * 5
    if lstm_y > 0:
        sk += (lstm_g - 50) * 0.15
    sk += nlp_s * 8
    sk += min(15, max(-15, rl_q * 0.3))
    sk += min(10, max(-10, rl_sh * 2))
    sk -= gnn * 0.3
    sk += gan * 2 if gan > -3 else 0
    sk = max(0, min(100, sk))
    if sk >= 72:
        seviye = "YUKSEK POZITIF"
    elif sk >= 58:
        seviye = "POZITIF"
    elif sk <= 28:
        seviye = "YUKSEK NEGATIF"
    elif sk <= 42:
        seviye = "NEGATIF"
    else:
        seviye = "NOTR"
    return round(sk, 1), seviye


def derin_teknoloji_hesapla(hs, g, tum_veriler, haber_listesi):
    """Tum derin teknoloji metriklerini tek cagri ile hesaplar."""
    lstm_y, lstm_g = lstm_tahmin(g)
    nlp_s, nlp_adet = nlp_duygu(haber_listesi, hs)
    rl_q, rl_sh = rl_portfoy_agi(g)
    emsaller = {}
    idx = tum_veriler.index(hs + ".IS") if (hs + ".IS") in tum_veriler.index else -1
    if idx >= 0:
        bas = max(0, idx - 3)
        son = min(len(tum_veriler), idx + 4)
        for h2 in list(tum_veriler.keys())[bas:son]:
            if h2 != hs + ".IS":
                emsaller[h2] = tum_veriler[h2]
    gnn = gnn_manipulasyon(g, emsaller)
    gan = gan_stres_test(g)
    hb_sk, hb_sv = hibrit_skor(lstm_y, lstm_g, nlp_s, rl_q, rl_sh, gnn, gan)
    return {
        "LSTM_Yon": lstm_y,
        "LSTM_Guven": lstm_g,
        "NLP_Skor": nlp_s,
        "NLP_Haber": nlp_adet,
        "RL_Q": rl_q,
        "RL_Sharpe": rl_sh,
        "GNN_Manip": gnn,
        "GAN_VaR": gan,
        "HibritSkor": hb_sk,
        "HibritSeviye": hb_sv
    } 

def hesapla(hs, v, kset, tum_veriler, haber_listesi):
    if v is None or v.empty or len(v) < 30:
        return None, None
    g = v.dropna()
    if len(g) < 30:
        return None, None
    sf = float(g['Close'].iloc[-1])
    gb = float(g['Close'].iloc[-min(25, len(g))])
    gd = ((sf - gb) / gb) * 100 if gb > 0 else 0
    sma20 = float(g['Close'].rolling(20).mean().iloc[-1])
    rv = rsi(g['Close']).iloc[-1]
    r = float(rv) if not pd.isna(rv) else 50
    e1 = g['Close'].ewm(span=12, adjust=False).mean()
    e2 = g['Close'].ewm(span=26, adjust=False).mean()
    mh = float((e1 - e2 - (e1 - e2).ewm(span=9, adjust=False).mean()).iloc[-1])
    hm = g['Volume'].rolling(20).mean().iloc[-1]
    ho = float(hm) if not pd.isna(hm) else 1
    hr = float(g['Volume'].iloc[-1]) / ho if ho > 0 else 1
    av = atr_f(g['High'], g['Low'], g['Close']).iloc[-1]
    a = float(av) if not pd.isna(av) else 0
    sk = 50
    yr = []
    if sf > sma20:
        sk += 12
        yr.append("SMA20+")
    if gd > 0:
        sk += 10
    if r < 40:
        sk += 10
        yr.append("RSI dusuk")
    elif r > 70:
        sk -= 12
        yr.append("RSI yuksek")
    if mh > 0:
        sk += 10
        yr.append("MACD+")
    if hr > 1.3:
        sk += 8
        yr.append("Hacim+")
    sk = max(20, min(95, sk))
    if sk >= 70 and gd > 0:
        sn = "GUCLU AL"
        tp = "YUKSELIS BEKLENIYOR"
    elif sk >= 55:
        sn = "AL"
        tp = "YUKSELIS EGILIMI"
    elif sk < 35:
        sn = "SAT"
        tp = "DUSUS BEKLENIYOR"
    elif sk < 45:
        sn = "ZAYIF"
        tp = "ZAYIF"
    else:
        sn = "BEKLE"
        tp = "BEKLE"
    if a > 0:
        sl = round(sf - a * 2, 2)
        hd = round(sf + a * 3, 2)
        ro = round((hd - sf) / (sf - sl), 2) if (sf - sl) > 0 else 0
    else:
        sl = 0
        hd = 0
        ro = 0
    hz = hs + ".IS"
    y15, g15, b15 = tahmin_15(g)
    v5 = float((g['High'] - g['Low']).iloc[-5:].mean())
    v20 = float((g['High'] - g['Low']).iloc[-20:].mean())
    vrej = "YUKSEK" if v5 > v20 * 1.3 else ("DUSUK" if v5 < v20 * 0.7 else "NORMAL")
    obv_s = (np.sign(g['Close'].diff()) * g['Volume']).fillna(0).cumsum()
    ofi = float(obv_s.iloc[-1] - obv_s.iloc[-5]) / 1e6 if len(obv_s) >= 5 else 0
    gv_ = garch_vol(g['Close'])
    trend_str = "Yuk" if gd > 0 else "Dus"
    dt = derin_teknoloji_hesapla(hs, g, tum_veriler, haber_listesi)
    km_skor, km_sinyal, km_renk, km_neden = karar_motoru(sk, r, mh, hr, vrej, ofi, gv_, y15, g15, trend_str)
    ht_skor = dt["HibritSkor"]
    dt_renk = "#1b5e20" if ht_skor >= 72 else ("#2e7d32" if ht_skor >= 58 else ("#b71c1c" if ht_skor <= 28 else ("#c62828" if ht_skor <= 42 else "#e65100")))
    ana = {
        "Hisse": hs,
        "Katilim": "EVET" if hz in kset else "HAYIR",
        "Guc": round(sk, 1),
        "Sinyal": sn,
        "Yorum": " | ".join(yr) if yr else "Notr",
        "RSI": f"{r:.1f}",
        "MACD": f"{mh:.3f}",
        "Trend": trend_str,
        "Getiri": f"%{gd:.2f}",
        "Hacim": f"{hr:.2f}x",
        "Fiyat": f"{sf:.2f} TL",
        "SL": f"{sl} TL",
        "Hedef": f"{hd} TL",
        "RO": f"{ro:.2f}",
        "Tahmin": tp,
        "Tahmin15": y15,
        "Guven15": f"%{g15}",
        "Beklenti15": f"%{b15}",
        "VolRejim": vrej,
        "OFI": round(ofi, 2),
        "GARCH": gv_,
        "KararSkor": km_skor,
        "KararSinyal": km_sinyal,
        "KararRenk": km_renk,
        "KararNeden": km_neden,
        "LSTM_Yon": dt["LSTM_Yon"],
        "LSTM_Guven": dt["LSTM_Guven"],
        "NLP_Skor": dt["NLP_Skor"],
        "NLP_Haber": dt["NLP_Haber"],
        "RL_Q": dt["RL_Q"],
        "RL_Sharpe": dt["RL_Sharpe"],
        "GNN_Manip": dt["GNN_Manip"],
        "GAN_VaR": dt["GAN_VaR"],
        "HibritSkor": ht_skor,
        "HibritSeviye": dt["HibritSeviye"],
        "HibritRenk": dt_renk
    }
    s25 = g.iloc[-min(25, len(g)):]
    gh = float(s25['High'].max())
    gl = float(s25['Low'].min())
    kp = (sf - gl) / (gh - gl) if (gh - gl) > 0 else 0.5
    ay = (a / sf) * 100 if sf > 0 else 0
    gs = 50
    if kp > 0.75:
        gs += 15
    elif kp < 0.25:
        gs -= 10
    if gd > 2:
        gs += 10
    elif gd < -2:
        gs -= 10
    if hr > 1.5:
        gs += 8
    if mh > 0:
        gs += 7
    if r > 65:
        gs -= 5
    elif r < 35:
        gs += 8
    gs = max(0, min(100, gs))
    if gs >= 70:
        os = "GECE TASI"
        bg = "YUKARI"
        tg = round(ay * 0.6, 2)
    elif gs >= 55:
        os = "ZAYIF TASI"
        bg = "NOTR"
        tg = round(ay * 0.3, 2)
    elif gs < 35:
        os = "GECE TASIMA"
        bg = "ASAGI"
        tg = round(-ay * 0.5, 2)
    else:
        os = "BEKLE"
        bg = "NOTR"
        tg = 0
    if kp > 0.75:
        yorum_on = "Zirve"
    elif kp < 0.25:
        yorum_on = "Dip"
    else:
        yorum_on = "Notr"
    onc = {
        "Hisse": hs,
        "Kapanis": f"{sf:.2f} TL",
        "GapSkor": round(gs, 1),
        "Overnight": os,
        "GapYon": bg,
        "Gap%": f"%{tg}",
        "Yorum": yorum_on
    }
    return ana, onc for k, v in [('g', False), ('s', 0), ('l', '-'), ('m', False), ('haber', []), ('gecmis', {}), ('son_gonderim', '-')]:
    if k not in st.session_state:
        st.session_state[k] = v

if not st.session_state.g:
    st.title("BIST Pro Giris")
    with st.form("f"):
        c1, c2 = st.columns(2)
        u = c1.text_input("Kullanici")
        p = c2.text_input("Sifre", type="password")
        if st.form_submit_button("Gir"):
            if u.strip() == "Cuma Babacan" and p.strip() == "784512":
                st.session_state.g = True
                st.rerun()
            else:
                st.error("Hatali!")
    st.stop()

pk = piyasa_acik_mi()
if pk:
    st_autorefresh(interval=60000, key="y")

st.title("BIST Pro Terminali - Deep Tech Edition")
st.caption("Son: " + turkiye_saati().strftime('%Y-%m-%d %H:%M:%S') + " | 15 dk Gecikmeli | Derin Teknoloji Aktif")

if pk:
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

with st.spinner("Veri yukleniyor ve derin teknoloji hesaplaniyor..."):
    hl = H.split(",")
    ks = set(x + ".IS" for x in K.split(","))
    hv = toplu_veri_cek(hl)
    if not st.session_state.haber:
        st.session_state.haber = haber_cek()
    hb = st.session_state.haber
    sat, onc = [], []
    for x in hl:
        kod = x + ".IS"
        if kod in hv:
            a, o = hesapla(x, hv[kod], ks, hv, hb)
            if a:
                sat.append(a)
            if o:
                onc.append(o)
    if not st.session_state.m:
        st.session_state.s += 1
        st.session_state.l = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.m = False

bd, bdeg = "-", "0"
try:
    bv = bist_endeks_verisi()
    if bv is not None and not bv.empty:
        bf = float(bv['Close'].iloc[-1])
        bd = f"{bf:.2f}"
        bdeg = f"%{((bf - float(bv['Open'].iloc[-1])) / float(bv['Open'].iloc[-1])) * 100:.2f}"
except Exception:
    pass

c1, c2, c3, c4 = st.columns(4)
c1.metric("BIST 100", bd, bdeg)
c2.metric("VIOP", "Denge", "0")
c3.metric("Taranan", str(len(hl)), "0")
c4.metric("Cekim", str(st.session_state.s), "Son: " + st.session_state.l)

cc1, cc2 = st.columns([3, 1])
with cc1:
    sd = st.checkbox("Sadece Islam'a Uygun", value=True)
with cc2:
    mb = st.button("Manuel Cek", use_container_width=True, type="primary")
if mb:
    st.cache_data.clear()
    st.session_state.m = True
    st.session_state.s += 1
    st.session_state.l = turkiye_saati().strftime("%H:%M:%S")
    st.session_state.haber = []
    st.rerun() t1, t2, t3, t4, t5, t6, t7 = st.tabs(["Karar", "Trend", "Mum", "Risk", "Overnight", "Haber & Pairs", "Derin Teknoloji"])

with t1:
    st.subheader("Karar Motoru - Tum Metrikler Birlesik Sinyal")
    st.caption("Guc, RSI, MACD, Hacim, Volatilite, OFI, GARCH, 15dk tahmin ve Derin Teknoloji birlestirilir.")
    if not sat:
        st.warning("Veri yok.")
    else:
        kdf = pd.DataFrame(sat)
        if sd:
            kdf = kdf[kdf["Katilim"] == "EVET"]
        kdf = kdf.sort_values("KararSkor", ascending=False).reset_index(drop=True)
        st.markdown("### A) Secili Hisse Karari")
        col_sec1, col_sec2 = st.columns([1, 2])
        with col_sec1:
            secili_hisse = st.selectbox("Hisse Sec", kdf["Hisse"].tolist(), key="karar_sec")
        with col_sec2:
            secili = kdf[kdf["Hisse"] == secili_hisse].iloc[0]
            sr = secili["KararRenk"]
            st.markdown(
                '<div style="background-color:' + sr + '; padding:20px; border-radius:10px; text-align:center;">'
                '<h2 style="color:white; margin:0;">' + str(secili_hisse) + ' -> ' + str(secili["KararSinyal"]) + '</h2>'
                '<p style="color:white; margin:5px 0; font-size:18px;">Skor: ' + str(secili["KararSkor"]) + '/100 | Fiyat: ' + str(secili["Fiyat"]) + '</p>'
                '<p style="color:white; margin:5px 0;">SL: ' + str(secili["SL"]) + ' | Hedef: ' + str(secili["Hedef"]) + ' | R/O: ' + str(secili["RO"]) + '</p>'
                '<p style="color:white; margin:5px 0;">Derin Teknoloji: ' + str(secili["HibritSeviye"]) + ' (Skor: ' + str(secili["HibritSkor"]) + ')</p>'
                '<p style="color:white; margin:5px 0; font-style:italic;">' + str(secili["KararNeden"]) + '</p>'
                '</div>', unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("B) Bugunun En Iyi 5 Firsati")
        def ro_ok(x):
            try:
                return float(x) > 1.5
            except Exception:
                return False
        firsatlar = kdf[(kdf["KararSkor"] >= 60) & (kdf["RO"].apply(ro_ok))].head(5)
        if not firsatlar.empty:
            kart_cols = st.columns(min(5, len(firsatlar)))
            for i in range(len(firsatlar)):
                r = firsatlar.iloc[i]
                with kart_cols[i]:
                    rk = r['KararRenk']
                    st.markdown(
                        '<div style="background-color:' + rk + '; padding:12px; border-radius:8px; color:white;">'
                        '<h4 style="margin:0;">' + str(r["Hisse"]) + '</h4>'
                        '<p style="margin:3px 0; font-size:20px; font-weight:bold;">' + str(r["KararSinyal"]) + '</p>'
                        '<p style="margin:3px 0;">Skor: ' + str(r["KararSkor"]) + '</p>'
                        '<p style="margin:3px 0;">' + str(r["Fiyat"]) + '</p>'
                        '<p style="margin:3px 0; font-size:12px;">Hedef: ' + str(r["Hedef"]) + '</p>'
                        '<p style="margin:3px 0; font-size:12px;">R/O: ' + str(r["RO"]) + '</p>'
                        '<p style="margin:3px 0; font-size:12px;">Deep: ' + str(r["HibritSkor"]) + '</p>'
                        '</div>', unsafe_allow_html=True)
        else:
            st.info("Bugun icin kriterlere uyan firsat yok.")
        st.markdown("---")
        st.subheader("C) Telegram Bildirim")
        tgl1, tgl2 = st.columns(2)
        with tgl1:
            if st.button("Bugunun En Iyi 5 Firsatini Gonder"):
                if telegram_toplu_gonder(firsatlar, "BIST Bugunun Firsatlari"):
                    st.success("Gonderildi!")
                else:
                    st.warning("Telegram token ayarlanmamis.")
        with tgl2:
            if st.button("Tum GUCLU AL Sinyallerini Gonder"):
                guclu_al = kdf[kdf["KararSinyal"] == "GUCLU AL"]
                if telegram_toplu_gonder(guclu_al, "BIST Guclu AL Sinyalleri"):
                    st.success("Gonderildi!")
                else:
                    st.warning("Telegram token ayarlanmamis.")
        st.markdown("---")
        st.subheader("D) Yeni Sinyal Degisimleri")
        gecmis_dict = st.session_state.get('gecmis', {})
        degisimler = sinyal_degisim_tespit(kdf, gecmis_dict)
        if degisimler:
            for d in degisimler[:10]:
                if "AL" in d['Yeni']:
                    ok_renk = "#1b5e20"
                elif "SAT" in d['Yeni']:
                    ok_renk = "#b71c1c"
                else:
                    ok_renk = "#e65100"
                st.markdown(
                    '<div style="background-color:' + ok_renk + '; padding:8px; border-radius:6px; margin:4px 0; color:white;">'
                    '<b>' + str(d["Hisse"]) + '</b>: ' + str(d["Eski"]) + ' -> <b>' + str(d["Yeni"]) + '</b> | Skor: ' + str(d["Skor"]) + ' | ' + str(d["Fiyat"]) +
                    '</div>', unsafe_allow_html=True)
        else:
            st.info("Onceki taramaya gore degisim yok. Ilk tarama ise bu normal.")
        st.session_state['gecmis'] = sinyal_dict_olustur(kdf)
        st.markdown("---")
        st.subheader("Karar Dagilimi")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("GUCLU AL", len(kdf[kdf["KararSinyal"] == "GUCLU AL"]))
        k2.metric("AL", len(kdf[kdf["KararSinyal"] == "AL"]))
        k3.metric("BEKLE", len(kdf[kdf["KararSinyal"] == "BEKLE"]))
        k4.metric("SAT", len(kdf[kdf["KararSinyal"] == "SAT"]))
        k5.metric("GUCLU SAT", len(kdf[kdf["KararSinyal"] == "GUCLU SAT"]))
        st.markdown("---")
        st.subheader("E) Tum Karar Skorlari")
        def rk_sinyal(v):
            if "GUCLU AL" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AL" in str(v):
                return 'background-color:#2e7d32;color:white;font-weight:bold;'
            if "GUCLU SAT" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "SAT" in str(v):
                return 'background-color:#c62828;color:white;'
            return 'background-color:#e65100;color:white;'
        kdf_goster = kdf[["Hisse", "Fiyat", "KararSkor", "KararSinyal", "KararNeden", "SL", "Hedef", "RO", "Guc", "RSI", "MACD", "Hacim", "OFI", "HibritSkor"]]
        st.dataframe(kdf_goster.style.map(rk_sinyal, subset=["KararSinyal"]), use_container_width=True, height=450)
        st.markdown("---")
        st.subheader("En Yuksek Karar Skoru 10")
        st.dataframe(kdf.head(10)[["Hisse", "Fiyat", "KararSkor", "KararSinyal", "SL", "Hedef", "RO", "HibritSkor", "KararNeden"]], use_container_width=True)
        st.markdown("---")
        st.subheader("En Dusuk Karar Skoru 10 (Riskli)")
        st.dataframe(kdf.tail(10)[["Hisse", "Fiyat", "KararSkor", "KararSinyal", "RSI", "MACD", "OFI", "GNN_Manip"]], use_container_width=True)
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("En Yuksek OFI 5 (Alici Baskisi)")
            st.dataframe(kdf.sort_values("OFI", ascending=False)[["Hisse", "OFI", "KararSkor", "KararSinyal", "HibritSkor"]].head(5), use_container_width=True)
        with colB:
            st.subheader("En Dusuk OFI 5 (Satici Baskisi)")
            st.dataframe(kdf.sort_values("OFI", ascending=True)[["Hisse", "OFI", "KararSkor", "KararSinyal", "HibritSkor"]].head(5), use_container_width=True)

with t2:
    st.subheader("Trend Matrisi")
    if not sat:
        st.warning("Veri yok.")
    else:
        df = pd.DataFrame(sat)
        df['O'] = df['Tahmin'].apply(lambda x: 1 if 'YUKSELIS' in x else (2 if 'BEKLE' in x or 'EGILIM' in x else 3))
        df = df.sort_values(by=['O', 'Guc'], ascending=[True, False]).drop(columns=['O'])
        if sd:
            df = df[df["Katilim"] == "EVET"]
        def rt(v):
            if "YUKSELIS" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "DUSUS" in str(v) or "ZAYIF" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "BEKLE" in str(v):
                return 'background-color:#e65100;color:white;font-weight:bold;'
            return ''
        def rs(v):
            if "GUCLU AL" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "AL" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "SAT" in str(v) or "ZAYIF" in str(v):
                return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'
        def rk(v):
            if v == "EVET":
                return 'color:#4CAF50;font-weight:bold;'
            return 'color:#F44336;'
        def r15(v):
            if "YUKARI" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ASAGI" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            return 'background-color:#e65100;color:white;font-weight:bold;'
        st.dataframe(df.style.map(rt, subset=["Tahmin"]).map(rs, subset=["Sinyal"]).map(rk, subset=["Katilim"]).map(r15, subset=["Tahmin15"]), use_container_width=True, height=600)
        st.markdown("---")
        st.subheader("15-25 Dakika Sonrasi Yon Dagilimi")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("YUKARI", len(df[df["Tahmin15"] == "YUKARI"]))
        m2.metric("ASAGI", len(df[df["Tahmin15"] == "ASAGI"]))
        m3.metric("YATAY", len(df[df["Tahmin15"] == "YATAY"]))
        gvv = pd.to_numeric(df['Guven15'].str.replace('%', ''), errors='coerce').mean()
        m4.metric("Ort Guven", "%" + str(round(gvv, 1) if not pd.isna(gvv) else 0))

with t3:
    st.subheader("Mum Grafigi")
    try:
        hs = st.selectbox("Hisse", hl[:80], key="mum_sec")
        kod = hs + ".IS"
        if kod in hv:
            h = hv[kod].dropna()
            h['SMA20'] = h['Close'].rolling(20).mean()
            h['BBU'] = h['Close'].rolling(20).mean() + 2 * h['Close'].rolling(20).std()
            h['BBA'] = h['Close'].rolling(20).mean() - 2 * h['Close'].rolling(20).std()
            h['RSI'] = rsi(h['Close'])
            f = go.Figure()
            f.add_trace(go.Candlestick(x=h.index, open=h['Open'], high=h['High'], low=h['Low'], close=h['Close'], name="Fiyat", increasing_line_color='#26a69a', decreasing_line_color='#ef5350'))
            f.add_trace(go.Scatter(x=h.index, y=h['BBU'], name="BBU", line=dict(color='#9c27b0', width=1, dash='dot')))
            f.add_trace(go.Scatter(x=h.index, y=h['BBA'], name="BBA", line=dict(color='#9c27b0', width=1, dash='dot')))
            f.add_trace(go.Scatter(x=h.index, y=h['SMA20'], name="SMA20", line=dict(color='#FFC107', width=1)))
            f.update_layout(title=hs, xaxis_rangeslider_visible=False, template='plotly_dark', height=450, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E')
            st.plotly_chart(f, use_container_width=True)
            fr = go.Figure()
            fr.add_trace(go.Scatter(x=h.index, y=h['RSI'], name="RSI", line=dict(color='#4CAF50')))
            fr.add_hline(y=70, line_dash="dash", line_color="red")
            fr.add_hline(y=30, line_dash="dash", line_color="green")
            fr.update_layout(title="RSI", template='plotly_dark', height=220, paper_bgcolor='#0E1117', plot_bgcolor='#1E1E1E', showlegend=False)
            st.plotly_chart(fr, use_container_width=True)
    except Exception:
        st.error("Grafik yuklenemedi")

with t4:
    st.subheader("ATR Bazli Risk")
    if sat:
        dfr = pd.DataFrame(sat)
        if sd:
            dfr = dfr[dfr["Katilim"] == "EVET"]
        def rok(x):
            try:
                return float(x) > 1.5
            except Exception:
                return False
        rdf = dfr[dfr["RO"].apply(rok)]
        st.markdown("**R/O > 1.5 olan " + str(len(rdf)) + " hisse:**")
        if not rdf.empty:
            st.dataframe(rdf[["Hisse", "Fiyat", "SL", "Hedef", "RO", "Sinyal", "Guc", "KararSinyal", "HibritSkor"]], use_container_width=True, height=500)
    else:
        st.warning("Veri yok.")

with t5:
    st.subheader("Overnight Gap Stratejisi")
    st.info("Kapanista al, acilista sat")
    if onc:
        odf = pd.DataFrame(onc)
        if sd:
            odf = odf[odf["Hisse"].apply(lambda x: (x + ".IS") in ks)]
        odf = odf.sort_values(by="GapSkor", ascending=False).reset_index(drop=True)
        def ron(v):
            if "GECE TASI" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "ZAYIF TASI" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "GECE TASIMA" in str(v):
                return 'background-color:#b71c1c;color:white;'
            return 'background-color:#e65100;color:white;'
        def rg(v):
            if "YUKARI" in str(v):
                return 'color:#4CAF50;font-weight:bold;'
            if "ASAGI" in str(v):
                return 'color:#F44336;font-weight:bold;'
            return 'color:#FFC107;'
        st.dataframe(odf.style.map(ron, subset=["Overnight"]).map(rg, subset=["GapYon"]), use_container_width=True, height=450)
        st.markdown("---")
        st.subheader("En Guclu 10")
        st.dataframe(odf.head(10)[["Hisse", "Kapanis", "GapSkor", "Overnight", "GapYon", "Gap%"]], use_container_width=True)
        st.markdown("---")
        if st.button("GECE TASI Sinyallerini Telegram'a Gonder"):
            mesaj = "<b>BIST Gece Tasi Sinyalleri</b>\n\n"
            for i in range(min(5, len(odf))):
                r = odf.iloc[i]
                mesaj += "- " + str(r['Hisse']) + " | Gap: " + str(r['GapSkor']) + " | " + str(r['Gap%']) + "\n"
            if telegram_gonder(mesaj):
                st.success("Gonderildi!")
            else:
                st.warning("Telegram token ayarlanmamis.")
    else:
        st.warning("Veri yok.")

with t6:
    st.subheader("Finansal Haberler (Paratic RSS)")
    if st.session_state.haber:
        for i, h in enumerate(st.session_state.haber[:15]):
            st.markdown("**" + h['baslik'] + "**")
            st.caption(h['tarih'] + " | " + h['link'])
    else:
        st.info("Haber verisi yuklenemedi.")
    st.markdown("---")
    st.subheader("Kointegrasyon - Pairs Trading")
    st.caption("Kointegre hisse ciftleri. |Z| > 2 = islem sinyali.")
    if sat:
        top10 = [r["Hisse"] for r in sat[:10]]
        if st.button("Top 10 Icin Pairs Analizi"):
            with st.spinner("Test ediliyor..."):
                pairs = pairs_tara(hv, top10)
            if pairs:
                st.dataframe(pd.DataFrame(pairs), use_container_width=True)
                st.info("Z>2: 1.SAT 2.AL | Z<-2: 1.AL 2.SAT")
            else:
                st.warning("Kointegre cift bulunamadi.")

with t7:
    st.subheader("Derin Teknoloji Analizi")
    st.caption("LSTM, NLP, Pekiştirmeli Ogrenme, GNN ve GAN modulleri birlesik skoru.")
    if not sat:
        st.warning("Veri yok.")
    else:
        ddf = pd.DataFrame(sat)
        if sd:
            ddf = ddf[ddf["Katilim"] == "EVET"]
        ddf = ddf.sort_values("HibritSkor", ascending=False).reset_index(drop=True)
        st.markdown("### Hibrit Deep Tech Skoru Dagilimi")
        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("YUKSEK POZITIF", len(ddf[ddf["HibritSeviye"] == "YUKSEK POZITIF"]))
        d2.metric("POZITIF", len(ddf[ddf["HibritSeviye"] == "POZITIF"]))
        d3.metric("NOTR", len(ddf[ddf["HibritSeviye"] == "NOTR"]))
        d4.metric("NEGATIF", len(ddf[ddf["HibritSeviye"] == "NEGATIF"]))
        d5.metric("YUKSEK NEGATIF", len(ddf[ddf["HibritSeviye"] == "YUKSEK NEGATIF"]))
        st.markdown("---")
        st.subheader("Tum Derin Teknoloji Metrikleri")
        def rh(v):
            if "YUKSEK POZITIF" in str(v):
                return 'background-color:#1b5e20;color:white;font-weight:bold;'
            if "POZITIF" in str(v):
                return 'background-color:#2e7d32;color:white;'
            if "YUKSEK NEGATIF" in str(v):
                return 'background-color:#b71c1c;color:white;font-weight:bold;'
            if "NEGATIF" in str(v):
                return 'background-color:#c62828;color:white;'
            return 'background-color:#e65100;color:white;'
        goster = ddf[["Hisse", "Fiyat", "HibritSkor", "HibritSeviye", "LSTM_Yon", "LSTM_Guven", "NLP_Skor", "NLP_Haber", "RL_Q", "RL_Sharpe", "GNN_Manip", "GAN_VaR", "KararSinyal"]]
        st.dataframe(goster.style.map(rh, subset=["HibritSeviye"]), use_container_width=True, height=500)
        st.markdown("---")
        colA, colB = st.columns(2)
        with colA:
            st.subheader("LSTM En Yuksek Tahmin 5")
            st.dataframe(ddf.sort_values("LSTM_Yon", ascending=False)[["Hisse", "LSTM_Yon", "LSTM_Guven", "HibritSkor", "Fiyat"]].head(5), use_container_width=True)
            st.subheader("NLP Haber Skoru En Yuksek 5")
            st.dataframe(ddf[ddf["NLP_Haber"] > 0].sort_values("NLP_Skor", ascending=False)[["Hisse", "NLP_Skor", "NLP_Haber", "HibritSkor"]].head(5), use_container_width=True)
            st.subheader("Pekiştirmeli Ogrenme En Yuksek 5")
            st.dataframe(ddf.sort_values("RL_Q", ascending=False)[["Hisse", "RL_Q", "RL_Sharpe", "HibritSkor"]].head(5), use_container_width=True)
        with colB:
            st.subheader("Manipulasyon Riski Yuksek 5")
            st.dataframe(ddf.sort_values("GNN_Manip", ascending=False)[["Hisse", "GNN_Manip", "HibritSkor", "Fiyat"]].head(5), use_container_width=True)
            st.subheader("GAN Risk En Dusuk 5 (Guvenli)")
            st.dataframe(ddf.sort_values("GAN_VaR", ascending=True)[["Hisse", "GAN_VaR", "HibritSkor", "Fiyat"]].head(5), use_container_width=True)
            st.subheader("En Yuksek Hibrit Skor 10")
            st.dataframe(ddf.head(10)[["Hisse", "Fiyat", "HibritSkor", "HibritSeviye", "KararSinyal"]], use_container_width=True)
        st.markdown("---")
        st.markdown("### Derin Teknoloji Ne Anlatiyor?")
        st.markdown("""
        - **LSTM_Yon**: Ağırlıklı bellek modeli ile 5 adım sonrası yön tahmini (% cinsinden)
        - **LSTM_Guven**: Tahmin güven yüzdesi
        - **NLP_Skor**: Türkçe finansal haber duygu analizi (-5 ile +5 arası)
        - **NLP_Haber**: Hisse ile ilgili bulunan haber sayısı
        - **RL_Q**: Pekiştirmeli öğrenme Q-değeri (getiri bazlı ödül)
        - **RL_Sharpe**: Sharpe oranı (risk ayarlı getiri)
        - **GNN_Manip**: Manipülasyon riski (0-100, yüksek = riskli)
        - **GAN_VaR**: Sentetik senaryolarda %95 VaR (kayıp tahmini)
        - **HibritSkor**: Tüm modellerin birleşik skoru (0-100)
        - **HibritSeviye**: YUKSEK POZITIF / POZITIF / NOTR / NEGATIF / YUKSEK NEGATIF
        """)

st.markdown("---")
st.caption("15 dk gecikmeli. Yatirim tavsiyesi degildir.")
