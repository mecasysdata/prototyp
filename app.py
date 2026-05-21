import streamlit as st
import pandas as pd
import requests
import datetime

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

@st.cache_data
def load_customers():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_zak = load_customers()

# ak sme práve pridali nového zákazníka, doplníme ho do zoznamu
zakaznici = df_zak["zakaznik"].tolist()
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc not in zakaznici:
        zakaznici.append(fc)

zakaznici.append("+ Pridať nového zákazníka")

# zistíme default index pre selectbox
default_index = 0
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc in zakaznici:
        default_index = zakaznici.index(fc)

# ======= RIADOK 1 – všetko v jednom riadku =======
col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 1.5, 2, 1, 1.5, 1, 0.8])

with col1:
    date = st.date_input("Dátum", datetime.date.today())

with col2:
    cp_nazov = st.text_input("Označenie CP")

with col3:
    vybrany = st.selectbox("Zákazník", zakaznici, index=default_index)

with col4:
    if vybrany != "+ Pridať nového zákazníka":
        # bezpečné – zákazník existuje v tabuľke
        krajina_input = df_zak.loc[df_zak["zakaznik"] == vybrany, "krajina"]
        if len(krajina_input) > 0:
            krajina_input = st.text_input("Krajina zákazníka", krajina_input.values[0], disabled=True)
        else:
            krajina_input = st.text_input("Krajina zákazníka", "", disabled=True)
    else:
        krajina_input = None


# tieto tri polia sú v TOM ISTOM RIADKU, len sa zobrazia, keď treba
novy_zak = None
nova_krajina = None

if vybrany == "+ Pridať nového zákazníka":
    with col5:
        novy_zak = st.text_input("Nový zákazník")
    with col6:
        nova_krajina = st.text_input("Krajina nového zákazníka")
    with col7:
        if st.button("Uložiť"):
            if novy_zak and nova_krajina:
                payload = {
                    "zakaznik": novy_zak,
                    "krajina": nova_krajina
                }
                r = requests.post(APP_SCRIPT_URL, json=payload)
                if r.status_code == 200:
                    st.session_state["force_customer"] = novy_zak
                    st.success("Zákazník bol uložený.")
                    st.cache_data.clear()
                    st.experimental_rerun()
                else:
                    st.error("Nepodarilo sa uložiť zákazníka.")
            else:
                st.error("Vyplň všetky polia.")

st.divider()
