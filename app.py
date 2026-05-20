import streamlit as st
import pandas as pd
import numpy as np
import joblib

import streamlit as st
import pandas as pd
import requests
from datetime import date

# -----------------------------
# GOOGLE SHEETS – ZÁKAZNÍCI
# -----------------------------
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acYua2efVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

# Načítanie zákazníkov
df_zak = pd.read_csv(SHEET_URL)
zoznam_zakaznikov = df_zak["zakaznik"].dropna().unique().tolist()

# -----------------------------
# UI – HLAVNÁ SEKCIA
# -----------------------------
st.header("🧾 MEC Calculation – Základné údaje")

# 1) DÁTUM
datum = st.date_input(
    "Dátum",
    value=date.today(),
    format="YYYY/MM/DD"
)

# 2) OZNAČENIE CP
oznacenie_cp = st.text_input(
    "Označenie CP",
    placeholder="Zadaj označenie cenovej ponuky"
)

# 3) ZÁKAZNÍK
st.subheader("Zákazník")

vyber_zakaznika = st.selectbox(
    "Názov zákazníka",
    options=zoznam_zakaznikov + ["➕ Pridať nového zákazníka"]
)

# 4) KRAJINA ZÁKAZNÍKA
if vyber_zakaznika == "➕ Pridať nového zákazníka":
    novy_zakaznik = st.text_input("Názov nového zákazníka")
    nova_krajina = st.text_input("Krajina zákazníka")

    if st.button("Uložiť nového zákazníka"):
        payload = {
            "zakaznik": novy_zakaznik,
            "krajina": nova_krajina,
            "vyhra": 0,
            "prehra": 0,
            "lojalita": 0.5
        }
        r = requests.post(APP_SCRIPT_URL, json=payload)

        if r.status_code == 200:
            st.success("Nový zákazník bol uložený.")
        else:
            st.error("Nepodarilo sa uložiť zákazníka.")

    krajina = nova_krajina

else:
    # automatické doplnenie krajiny
    krajina = df_zak.loc[df_zak["zakaznik"] == vyber_zakaznika, "krajina"].values[0]
    st.text_input("Krajina zákazníka", krajina, disabled=True)

# 5) ITEM
item = st.text_input("ITEM (názov dielu)")

# 6) POČET KUSOV
pocet_kusov = st.number_input(
    "Počet kusov",
    min_value=1,
    step=1
)

# 7) NÁROČNOSŤ
vnarocnost = st.selectbox(
    "Náročnosť (1–5)",
    options=[1, 2, 3, 4, 5]
)

# 8) TVAR POLOŽKY
tvar = st.selectbox(
    "Tvar položky",
    options=["STV", "KR"]
)

# 9–11) ROZMERY PODĽA TVARU
st.subheader("Rozmery")

if tvar == "KR":
    d = st.number_input("D (mm)", min_value=0.0, step=0.1)
    l = st.number_input("L (mm)", min_value=0.0, step=0.1)

else:
    dp = st.number_input("D/P (mm)", min_value=0.0, step=0.1)
    s = st.number_input("S (mm)", min_value=0.0, step=0.1)
    v = st.number_input("V (mm)", min_value=0.0, step=0.1)

# 12) MATERIÁL
material = st.selectbox(
    "Materiál",
    options=["PLAST", "NEREZ", "OCEĽ", "FAREBNÉ KOVY", "LIATINA"]
)

