import streamlit as st
import pandas as pd
import datetime
import re
import math

#logo - vrchná časť aplikácie -úvod
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=130)
    except: st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")

st.divider()

ZÁKAZNÍK (Defenzívna logika) ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    datum = st.date_input("Dátum", datetime.date.today())
with col2:
    ponuka = st.text_input("Označenie CP")

# Predpokladáme, že stĺpec v sheet_url sa volá 'zakaznik' (po našom lower() čistení)
zoznam_zakaznikov = sorted(df['zakaznik'].dropna().unique()) if 'zakaznik' in df.columns else []
moznosti_zakaznikov = ["+ Pridať nového zákazníka"] + zoznam_zakaznikov

with col3:
    vyber = st.selectbox("Názov Zákazníka", moznosti_zakaznikov)

zakaznik = ""
krajina_hodnota = ""
lojalita = 0.5

if vyber == "+ Pridať nového zákazníka":
    with col3: 
        zakaznik = st.text_input("Meno nového zákazníka", key="new_cust_name")
    with col4:
        krajina_hodnota = st.text_input("Krajina Zákazníka (manuálne)", key="new_cust_country")
else:
    # Bezpečné vytiahnutie riadku bez .iloc[0] na prázdno
    filter_zak = df[df['zakaznik'] == vyber]
    if not filter_zak.empty:
        data_zakaznika = filter_zak.iloc[0]
        zakaznik = vyber
        krajina_hodnota = str(data_zakaznika.get('krajina', 'Neznáma'))
        lojalita = float(data_zakaznika.get('lojalita', 0.5))
    else:
        st.warning(f"Zákazník {vyber} nemá v tabuľke priradené dáta.")
    
    with col4: 
        st.text_input("Krajina Zákazníka", value=krajina_hodnota, disabled=True, key="disabled_country")

st.divider()
