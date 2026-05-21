import streamlit as st
import pandas as pd
import requests
import datetime

# ============================
# 1. Načítanie zákazníkov zo sheetu
# ============================
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"

@st.cache_data
def load_customers():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_zak = load_customers()

# ============================
# 2. UI – Riadok 1 (všetko v jednom riadku)
# ============================
col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1.2, 1, 1.2, 0.8])

# --- 1. Políčko: Dátum ---
with col1:
    date = st.date_input("Dátum", datetime.date.today())

# --- 2. Políčko: Označenie CP ---
with col2:
    cp_nazov = st.text_input("Označenie CP")

# --- 3. Políčko: Zákazník ---
with col3:
    zakaznici = df_zak["zakaznik"].tolist()
    zakaznici.append("+ Pridať nového zákazníka")

    vybrany = st.selectbox("Zákazník", zakaznici)

# --- 4. Políčko: Krajina zákazníka ---
with col4:
    if vybrany != "+ Pridať nového zákazníka":
        krajina_input = st.text_input(
            "Krajina zákazníka",
            df_zak.loc[df_zak["zakaznik"] == vybrany, "krajina"].values[0],
            disabled=True
        )
    else:
        krajina_input = st.text_input("Krajina zákazníka (nový)")

# --- 5. Políčko: Názov nového zákazníka (zobrazí sa len vtedy, keď treba) ---
with col5:
    if vybrany == "+ Pridať nového zákazníka":
        novy_zak = st.text_input("Nový zákazník")
    else:
        novy_zak = None

# --- 6. Tlačidlo Uložiť zákazníka (tiež len vtedy, keď treba) ---
with col6:
    if vybrany == "+ Pridať nového zákazníka":
        if st.button("Uložiť"):
            if novy_zak and krajina_input:
                payload = {
                    "zakaznik": novy_zak,
                    "krajina": krajina_input
                }

                url = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"
                r = requests.post(url, json=payload)

                if r.status_code == 200:
                    st.success("Zákazník bol uložený.")
                    st.cache_data.clear()
                    st.experimental_rerun()
                else:
                    st.error("Nepodarilo sa uložiť zákazníka.")
            else:
                st.error("Vyplň všetky polia.")
