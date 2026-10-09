import streamlit as st
from data.fetcher import toplu_veri_cek, piyasa_acik_mi, turkiye_saati

st.title("BIST Pro - Test")
st.caption(turkiye_saati().strftime('%Y-%m-%d %H:%M:%S'))

if piyasa_acik_mi():
    st.success("PIYASA ACIK")
else:
    st.warning("PIYASA KAPALI")

hisseler = ["THYAO", "GARAN", "ASELS", "BIMAS", "FROTO"]

with st.spinner("Veri cekiliyor..."):
    veriler = toplu_veri_cek(hisseler)

st.write("Cekilen: " + str(len(veriler)))

for kod, veri in veriler.items():
    fiyat = round(veri['Close'].iloc[-1], 2)
    st.write(kod + " - " + str(fiyat) + " TL")
