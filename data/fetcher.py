import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta, time


def turkiye_saati():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3)))


def piyasa_acik_mi():
    su_an = turkiye_saati()
    if su_an.weekday() >= 5:
        return False
    return time(9, 40) <= su_an.time() <= time(18, 30)


def toplu_veri_cek(hisse_listesi, periyot="5d", aralik="15m", grup_boyutu=40):
    tum_sonuclar = {}
    for baslangic in range(0, len(hisse_listesi), grup_boyutu):
        grup = hisse_listesi[baslangic:baslangic + grup_boyutu]
        grup_uzantili = [hisse + ".IS" for hisse in grup]
        try:
            ham_veri = yf.download(
                grup_uzantili,
                period=periyot,
                interval=aralik,
                group_by='ticker',
                threads=True,
                progress=False,
                auto_adjust=True,
                timeout=30
            )
            if ham_veri is None or ham_veri.empty:
                continue
            if len(grup_uzantili) == 1:
                tum_sonuclar[grup_uzantili[0]] = ham_veri
            else:
                ust_seviye = ham_veri.columns.get_level_values(0).unique().tolist()
                for hisse_kodu in grup_uzantili:
                    if hisse_kodu in ust_seviye:
                        alt_veri = ham_veri[hisse_kodu].dropna()
                        if not alt_veri.empty and len(alt_veri) >= 30:
                            tum_sonuclar[hisse_kodu] = alt_veri
        except Exception:
            continue
    return tum_sonuclar


def bist_endeks_verisi():
    try:
        endeks = yf.Ticker("XU100.IS")
        return endeks.history(period="1d")
    except Exception:
        return None
