import streamlit as st
import pandas as pd
import requests
import datetime

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="MEC Calculation")

# --- CONSTANTS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

# --- LOGO A NÁZOV ---
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo.png", width=150)
    except:
        st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")

st.divider()

# --- LOAD CUSTOMERS ---
@st.cache_data
def load_customers():
    df = pd.read_csv(SHEET_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_zak = load_customers()

# --- BUILD CUSTOMER LIST ---
zakaznici = df_zak["zakaznik"].tolist()

# ak bol práve pridaný nový zákazník → zobraz ho v selectboxe
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc not in zakaznici:
        zakaznici.append(fc)

zakaznici.append("+ Pridať nového zákazníka")

# default index
default_index = 0
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc in zakaznici:
        default_index = zakaznici.index(fc)

# ============================
# RIADOK 1 – všetko v jednom riadku
# ============================

col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.6, 1.2, 1.6, 1.2, 0.8])

with col1:
    date = st.date_input("Dátum", datetime.date.today())

with col2:
    cp_nazov = st.text_input("Označenie CP")

with col3:
    vybrany = st.selectbox("Zákazník", zakaznici, index=default_index)

with col4:
    if vybrany != "+ Pridať nového zákazníka":
        krajina_input = df_zak.loc[df_zak["zakaznik"] == vybrany, "krajina"]
        if len(krajina_input) > 0:
            krajina_input = st.text_input("Krajina zákazníka", krajina_input.values[0], disabled=True)
        else:
            krajina_input = st.text_input("Krajina zákazníka", "", disabled=True)
    else:
        krajina_input = None

# --- NOVÝ ZÁKAZNÍK (v tom istom riadku) ---
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
                payload = {"zakaznik": novy_zak, "krajina": nova_krajina}
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

# ============================
# RIADOK 2 – ITEM + STV/KR parametre
# ============================

col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns(
    [1.6, 1, 1, 1, 1, 1, 1, 1, 1]
)

with col1:
    item = st.text_input("ITEM")

with col2:
    pocet_kusov = st.number_input("Počet kusov", min_value=1, step=1)

with col3:
    narocnost = st.selectbox("Náročnosť", [1, 2, 3, 4, 5])

with col4:
    tvar = st.selectbox("Tvar položky", ["STV", "KR"])

# --- STV ---
if tvar == "STV":
    with col5:
        dp = st.number_input("D/P (mm)", min_value=0.0, step=0.1)
    with col6:
        s = st.number_input("S (mm)", min_value=0.0, step=0.1)
    with col7:
        v = st.number_input("V (mm)", min_value=0.0, step=0.1)

    with col8:
        st.write("")
    with col9:
        st.write("")

# --- KR ---
if tvar == "KR":
    with col5:
        d_mm = st.number_input("D (mm)", min_value=0.0, step=0.1)
    with col6:
        l_mm = st.number_input("L (mm)", min_value=0.0, step=0.1)

    with col7:
        st.write("")
    with col8:
        st.write("")
    with col9:
        st.write("")

st.divider()

# ============================
# LOAD SEMI-FINISHED PRODUCTS (HÁROK 1)
# ============================

POL_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?gid=0&single=true&output=csv"

@st.cache_data
def load_polotovary():
    df = pd.read_csv(POL_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_pol = load_polotovary()

st.subheader("Výber materiálu a polotovaru")

# ============================
# RIADOK 3 – Materiál • Akosť • Polotovar • Cena/bm • Cena/ks
# ============================

col1, col2, col3, col4, col5 = st.columns([1.2, 1.6, 2.4, 1.2, 1.2])

# --- 1. Materiál ---
with col1:
    material_list = sorted(df_pol["material"].dropna().unique().tolist())
    material = st.selectbox("Materiál", material_list)

# --- 2. Akosť (multiselect) ---
with col2:
    akosti = sorted(df_pol[df_pol["material"] == material]["akost"].dropna().unique().tolist())
    akost_vyber = st.multiselect("Akosť", akosti)

# --- 3. Polotovar ---
with col3:

    df_filtered = df_pol[df_pol["akost"].isin(akost_vyber)]

    # filter podľa tvaru položky (z riadku 2)
    if tvar == "KR":
        df_filtered = df_filtered[df_filtered["tvar"].isin(["KR", "6HR", "TR"])]

    polozky = []

    if df_filtered.empty:
        st.warning("Pre túto akosť neexistuje žiadny polotovar. Pridaj nový.")
        polotovar = "+ Pridať nový polotovar"
        vybrany_pol = None
    else:
        for _, r in df_filtered.iterrows():
            nazov = (
                f"[{r['akost']}] {r['názov']} | "
                f"{r['rozmer1']}x{r['rozmer2']}x{r['rozmer3']} | "
                f"Cena: {r['cena']} €/bm"
            )
            polozky.append(nazov)

        polozky.append("+ Pridať nový polotovar")
        polotovar = st.selectbox("Polotovar", polozky)

        # nájdenie vybraného riadku
        if polotovar != "+ Pridať nový polotovar":
            akost_sel = polotovar.split("]")[0].replace("[", "")
            vybrany_pol = df_filtered[df_filtered["akost"] == akost_sel].iloc[0]
        else:
            vybrany_pol = None

# --- 4. Cena za bm ---
with col4:
    if vybrany_pol is not None:
        cena_bm = float(vybrany_pol["cena"])
    else:
        cena_bm = 0.0
    cena_bm = st.number_input("Cena €/bm", value=cena_bm, disabled=True)

# --- 5. Cena materiál / ks ---
with col5:
    if vybrany_pol is not None:
        if tvar == "KR":
            dlzka_mm = l_mm
        else:
            dlzka_mm = dp

        cena_mat_ks = round(cena_bm * (dlzka_mm / 1000), 4)
    else:
        cena_mat_ks = 0.0

    st.number_input("Cena mat/ks", value=cena_mat_ks, disabled=True)

st.divider()

# ============================
# BOX – Pridať nový polotovar (možnosť C)
# ============================

if polotovar == "+ Pridať nový polotovar":

    st.markdown("### ➕ Pridať nový polotovar")

    with st.container():
        box1, box2, box3, box4 = st.columns([1.2, 1.2, 1.2, 1.2])
        box5, box6, box7, box8 = st.columns([1.2, 1.2, 1.2, 1.2])

        with box1:
            novy_material = st.selectbox("Materiál", material_list, index=material_list.index(material))

        with box2:
            nova_akost = st.text_input("Akosť", value=akost_vyber[0] if akost_vyber else "")

        with box3:
            novy_nazov = st.text_input("Názov")

        with box4:
            novy_tvar = st.selectbox("Tvar", ["STV", "KR", "6HR", "TR"])

        with box5:
            r1 = st.text_input("Rozmer 1")

        with box6:
            r2 = st.text_input("Rozmer 2")

        with box7:
            r3 = st.text_input("Rozmer 3")

        with box8:
            cena = st.number_input("Cena €/bm", min_value=0.0, step=0.1)

        ulozit = st.button("Uložiť nový polotovar")

        if ulozit:
            if novy_material and nova_akost and novy_nazov and novy_tvar and r1 and r2 and r3 and cena:

                payload = {
                    "Názov": novy_nazov,
                    "Akost": nova_akost,
                    "Material": novy_material,
                    "Cena": cena,
                    "Tvar": novy_tvar,
                    "Rozmer1": r1,
                    "Rozmer2": r2,
                    "Rozmer3": r3
                }

                r = requests.post(
                    "https://script.google.com/macros/s/AKfycbzyZxjTplhk010oq7ozvovAGx5lRx72PjqUvoJUrNazx_jRfq7lqfQgbeHYG9O-NCcX/exec",
                    json=payload
                )

                if r.status_code == 200:
                    st.success("Polotovar bol uložený.")
                    st.cache_data.clear()
                    st.experimental_rerun()
                else:
                    st.error("Nepodarilo sa uložiť polotovar.")
            else:
                st.error("Vyplň všetky polia.")

