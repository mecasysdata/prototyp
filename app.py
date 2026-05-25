import streamlit as st
import pandas as pd
import requests
import datetime
import math
import gdown
import os
import joblib
import numpy as np
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- FUNKCIA NA NAČÍTANIE MODELOV ---
@st.cache_resource
def load_model_from_drive(file_id, filename):
    if not os.path.exists(filename):
        url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url, filename, quiet=False)
    return joblib.load(filename)

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="MEC Calculation")

# --- CONSTANTS ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acY_ua2e_fVqEcfxMBe5wnjue/pub?gid=0&single=true&output=csv"
APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwNR33wxSNXJFo9-o2otM-mdKQE22s3i3y5n08dY7eogGhhKDTasiPn3zaOoSihppTq/exec"

# Apps Script pre ukladanie CP (ten, čo si posielala pre Hárok1)
CP_APP_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwx7sAeUheQf1dm2r6k7jTslD9ufhq2yk1OWZXWjxVkeZOttVI949GIiPGx8l1B3cIP/exec"

# --- INIT SESSION STATE ---
if "predicted_time" not in st.session_state:
    st.session_state.predicted_time = 0.0
if "time_confirmed" not in st.session_state:
    st.session_state.time_confirmed = False
if "predicted_price" not in st.session_state:
    st.session_state.predicted_price = 0.0
if "price_confirmed" not in st.session_state:
    st.session_state.price_confirmed = False
if "kosik" not in st.session_state:
    st.session_state.kosik = []
if "last_item_name" not in st.session_state:
    st.session_state.last_item_name = ""
if "note_text" not in st.session_state:
    st.session_state.note_text = ""

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
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc not in zakaznici:
        zakaznici.append(fc)
zakaznici.append("+ Pridať nového zákazníka")

default_index = 0
if "force_customer" in st.session_state:
    fc = st.session_state["force_customer"]
    if fc in zakaznici:
        default_index = zakaznici.index(fc)

# ============================
# RIADOK 1
# ============================
col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.6, 1.2, 1.6, 1.2, 0.8])
with col1:
    date = st.date_input("Dátum", datetime.date.today())
with col2:
    cp_nazov = st.text_input("Označenie CP")
with col3:
    vybrany = st.selectbox("Zákazník", zakaznici, index=default_index)
with col4:
    krajina_input = ""
    if vybrany != "+ Pridať nového zákazníka":
        k_df = df_zak.loc[df_zak["zakaznik"] == vybrany, "krajina"]
        krajina_input = k_df.values[0] if len(k_df) > 0 else ""
    st.text_input("Krajina zákazníka", krajina_input, disabled=True)

if vybrany == "+ Pridať nového zákazníka":
    with col5:
        novy_zak = st.text_input("Nový zákazník")
    with col6:
        nova_krajina = st.text_input("Krajina nového zákazníka")
    with col7:
        if st.button("Uložiť"):
            if novy_zak and nova_krajina:
                r = requests.post(APP_SCRIPT_URL, json={"zakaznik": novy_zak, "krajina": nova_krajina})
                if r.status_code == 200:
                    st.session_state["force_customer"] = novy_zak
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Chyba")

st.divider()

# ============================
# RIADOK 2 – ITEM + STV/KR
# ============================
col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([1.6, 1, 1, 1, 1, 1, 1, 1, 1])
with col1:
    item = st.text_input("ITEM")
with col2:
    pocet_kusov = st.number_input("Počet kusov", min_value=1, step=1)
with col3:
    narocnost = st.selectbox("Náročnosť", [1, 2, 3, 4, 5])
# --- FIX: Reset predikcie pri zmene náročnosti ---
if "last_narocnost" not in st.session_state:
    st.session_state.last_narocnost = narocnost

if st.session_state.last_narocnost != narocnost:
    st.session_state.last_narocnost = narocnost
    st.session_state.predicted_time = 0.0
    st.session_state.time_confirmed = False


with col4:
    tvar = st.selectbox("Tvar položky", ["STV", "KR"])

dp = s = v = 0.0
d_mm = l_mm = 0.0
if tvar == "STV":
    with col5:
        dp = st.number_input("D/P (mm)", min_value=0.0, step=0.1)
    with col6:
        s = st.number_input("S (mm)", min_value=0.0, step=0.1)
    with col7:
        v = st.number_input("V (mm)", min_value=0.0, step=0.1)
else:
    with col5:
        d_mm = st.number_input("D (mm)", min_value=0.0, step=0.1)
    with col6:
        l_mm = st.number_input("L (mm)", min_value=0.0, step=0.1)

st.divider()

# ============================
# LOAD POLOTOVARY
# ============================
POL_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQf4EiqZt1grkazJgfYWVhG0M8FGLNCjaGk6dcXhO3r04JQuZ9Qxv1jelDo3c8hBLy7Ny5C1pZqvbfS/pub?gid=0&single=true&output=csv"

@st.cache_data
def load_polotovary():
    df = pd.read_csv(POL_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_pol = load_polotovary()

# ============================
# RIADOK 3 – Opravená logika cien
# ============================
col1, col2, col3, col4, col5 = st.columns([1.2, 1.6, 2.4, 1.2, 1.2])

with col1:
    material = st.selectbox("Materiál", sorted(df_pol["material"].dropna().unique().tolist()), key="mat_select")

with col2:
    akosti = sorted(df_pol[df_pol["material"] == material]["akost"].dropna().unique().tolist())
    akost_vyber = st.multiselect("Akosť", akosti, key="akost_select")

with col3:
    df_filtered = df_pol[df_pol["akost"].isin(akost_vyber)]
    if tvar == "KR":
        df_filtered = df_filtered[df_filtered["tvar"].isin(["KR", "6HR", "TR"])]

    polozky_dict = {
        idx: f"[{r['akost']}] {r['názov']} | {r['rozmer1']}x{r['rozmer2']}x{r['rozmer3']} | Cena: {r['cena']} €/bm"
        for idx, r in df_filtered.iterrows()
    }
    polozky_dict["new"] = "+ Pridať nový polotovar"

    polotovar_key = st.selectbox(
        "Polotovar",
        list(polozky_dict.keys()),
        format_func=lambda x: polozky_dict[x],
        key="polotovar_select"
    )

# --- ZÍSKANIE CENY ---
if polotovar_key != "new":
    r = df_filtered.loc[polotovar_key]
    cena_bm = float(r["cena"])
else:
    cena_bm = 0.0

# --- VÝPOČET DĹŽKY ---
dlzka_mm = l_mm if tvar == "KR" else dp

# --- VÝPOČET CENY ---
cena_mat_ks = round(cena_bm * (dlzka_mm / 1000), 4)

# --- UI (bez session_state konfliktu) ---
with col4:
    st.write("Cena €/bm")
    st.write(round(cena_bm, 4))

with col5:
    st.write("Cena mat/ks")
    st.write(round(cena_mat_ks, 4))

# ============================
# BOX – Pridať nový polotovar
# ============================

material_list = sorted(df_pol["material"].dropna().unique().tolist())

if polotovar_key == "new":
    st.markdown("### ➕ Pridať nový polotovar")

    with st.container():
        box1, box2, box3, box4 = st.columns([1.2, 1.2, 1.2, 1.2])
        box5, box6, box7, box8 = st.columns([1.2, 1.2, 1.2, 1.2])

        with box1:
            novy_material = st.selectbox(
                "Materiál (nový)",
                material_list,
                index=material_list.index(material),
                key="novy_material"
            )

        with box2:
            nova_akost = st.text_input(
                "Akosť (nová)",
                value=akost_vyber[0] if akost_vyber else "",
                key="nova_akost"
            )

        with box3:
            novy_nazov = st.text_input("Názov (nový)", key="novy_nazov")

        with box4:
            novy_tvar = st.selectbox("Tvar (nový)", ["STV", "KR", "6HR", "TR"], key="novy_tvar")

        with box5:
            r1 = st.text_input("Rozmer 1", key="r1_new")

        with box6:
            r2 = st.text_input("Rozmer 2", key="r2_new")

        with box7:
            r3 = st.text_input("Rozmer 3", key="r3_new")

        with box8:
            cena = st.number_input("Cena €/bm", min_value=0.0, step=0.1, key="cena_new")

        ulozit = st.button("Uložiť nový polotovar", key="ulozit_polotovar")

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
                    new_polotovar_label = f"[{nova_akost}] {novy_nazov} | {r1}x{r2}x{r3} | Cena: {cena} €/bm"

                    st.session_state["force_akost"] = nova_akost
                    st.session_state["force_polotovar"] = new_polotovar_label

                    st.success("Polotovar bol uložený.")
                    st.cache_data.clear()
                    st.experimental_rerun()
                else:
                    st.error("Nepodarilo sa uložiť polotovar.")
            else:
                st.error("Vyplň všetky polia.")

# ============================
# LOAD KOOPERÁCIE (HÁROK)
# ============================

KOOP_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRXlw1ybqaKDNFzTXEBQXtyZDSrLeauZ6l_1jZGuq5_KU8RPjrz4M_B5RGIAF9XTca8mSCSflH6pZE8/pub?gid=1711993868&single=true&output=csv"

@st.cache_data
def load_kooperacie():
    df = pd.read_csv(KOOP_URL)
    df.columns = df.columns.str.lower().str.strip()
    return df

df_kooperacie = load_kooperacie()

# ============================
# SUBCATEGORY + HUSTOTY – FUNKCIE A DÁTA PRE RIADOK 4
# ============================
def urci_subcategory(akost, material, nazov_materialu):
    ak = str(akost).replace(" ", "").replace(",", ".")

    vynimky = {
        "1.3505": "TOOL",
        "1.35": "TOOL",
        "1.4308": "AUST",
        "1.4408": "AUST",
        "1.47": "STAIN-SPEC",
        "1.48": "STAIN-SPEC",
        "1.0619": "UNALL",
        "1.07": "UNALL",
        "1.11": "UNALL",
        "1.12": "UNALL",
        "2.4": "NI-SPEC",
        "1.39": "ALLOYED",
        "1.29": "TOOL",
    }

    for prefix, sub in vynimky.items():
        if ak.startswith(prefix):
            return sub

    if ak.startswith(tuple(f"1.{i:02d}" for i in range(0, 15))):
        return "UNALL"

    if ak.startswith(tuple(f"1.{i:02d}" for i in range(15, 65))):
        return "LOWAL"

    if ak.startswith(tuple(f"1.{i:02d}" for i in range(65, 90))):
        return "ALLOYED"

    if ak.startswith(tuple(f"1.{i:02d}" for i in range(20, 33))):
        return "TOOL"

    if ak.startswith(tuple(f"1.{i:02d}" for i in range(33, 39))):
        return "HSS"

    if ak.startswith("1.4462"):
        return "DUPX"

    if ak.startswith("1.44"):
        return "DUPX"

    if ak.startswith("1.43") or ak.startswith("1.45"):
        return "AUST"

    if ak.startswith("1.41"):
        return "MART"

    if ak.startswith("1.40"):
        return "FERR"

    if ak.startswith(("1.46", "1.47", "1.48", "1.49")):
        return "STAIN-SPEC"

    if ak.startswith(("2.00", "2.01")):
        return "CU"
    if ak.startswith(("2.02", "2.03", "2.04", "2.05")):
        return "BRASS"
    if ak.startswith(("2.09", "2.10", "2.11", "2.12", "2.13")):
        return "BRONZE"
    if ak.startswith(("3.0", "3.1", "3.2", "3.3", "3.4", "3.5")):
        return "ALU"
    if ak.startswith("3.7"):
        return "TI"
    if ak.startswith("2.4"):
        return "NI-SPEC"

    plast_map = {
        "POM": "POM",
        "PEEK": "PEEK",
        "PET": "PET",
        "PC": "PC",
        "PVC": "PVC",
        "PTFE": "PTFE",
        "PUR": "PUR",
        "PMMA": "PMMA",
        "RUBBER": "RUBBER",
        "PA": "PA",
        "PP": "PP",
        "PE": "PE",
    }

    naz = str(nazov_materialu).upper()

    for key in plast_map:
        if naz == key or naz.startswith(key):
            return plast_map[key]

    return "UNKNOWN"

hustoty = {
    "UNALL": 7900,
    "LOWAL": 7900,
    "ALLOYED": 7900,
    "TOOL": 7900,
    "HSS": 7900,
    "AUST": 8000,
    "MART": 8000,
    "DUPX": 8000,
    "FERR": 8000,
    "STAIN-SPEC": 8000,
    "CU": 9000,
    "BRASS": 9000,
    "BRONZE": 9000,
    "ALU": 2900,
    "TI": 4500,
    "NI-SPEC": 8500,
    "POM": 1500,
    "PE": 1000,
    "PA": 1200,
    "PP": 1000,
    "PEEK": 1400,
    "PET": 1700,
    "PC": 1500,
    "PVC": 1700,
    "PTFE": 3000,
    "PUR": 2000,
    "PMMA": 1600,
    "RUBBER": 7900,
    "CAST-GG": 7150,
    "CAST-GGG": 7250,
    "CAST-TEMP": 7400,
}

# ============================
# RIADOK 4 – všetko vedľa seba
# ============================

col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.4])

with col1:
    kooperacia = st.checkbox("Koop.", key="koop_checkbox")

with col2:
    subcategory = urci_subcategory(akost_vyber[0] if akost_vyber else "", material, material)

with col3:
    hustota_default = hustoty.get(subcategory, 1000)
    hustota = st.number_input("Hustota", value=float(hustota_default), step=10.0)

if tvar == "KR":
    D_m = d_mm / 1000
    L_m = l_mm / 1000
    objem = math.pi * (D_m / 2) ** 2 * L_m
    plocha = (math.pi * D_m * L_m + 2 * math.pi * (D_m / 2) ** 2) * 100
else:
    s_m = s / 1000
    v_m = v / 1000
    L_m = dp / 1000
    objem = s_m * v_m * L_m
    plocha = 2 * (s_m * v_m + s_m * L_m + v_m * L_m) * 100

hmotnost = objem * hustota

with col4:
    st.write("Objem (m³)")
    st.write(round(objem, 6))

with col5:
    st.write("Hmotnosť (kg)")
    st.write(round(hmotnost, 3))

with col6:
    st.write("Plocha (dm²)")
    st.write(round(plocha, 2))

if kooperacia:
    df_koop = df_kooperacie[df_kooperacie["material"] == material]
    druhy = df_koop["druh"].unique().tolist()

    with col1:
        vyber_koop = st.selectbox("Typ", druhy)

    riadok = df_koop[df_koop["druh"] == vyber_koop].iloc[0]

    jednotka = riadok["jednotka"]
    tarifa = float(riadok["tarifa"])
    min_zakazka = float(riadok["minimalna zakazka"])

    if jednotka == "kg":
        cena_ks = hmotnost * tarifa
    elif jednotka == "dm2":
        cena_ks = plocha * tarifa
    else:
        cena_ks = 0.0

    cena_spolu = cena_ks * pocet_kusov

    if cena_spolu < min_zakazka:
        cena_ks = min_zakazka / pocet_kusov
else:
    cena_ks = 0.0

vstupne_naklady_ks = cena_mat_ks + cena_ks

with col7:
    st.write("Vstupné €/ks")
    st.write(round(vstupne_naklady_ks, 3))

st.divider()

# ========================================================
# 5. RIADOK – AI PREDIKCIE (FINALIZOVANÁ LOGIKA)
# ========================================================

# ID MODELOV
ID_MODELS = {
    "KR": {"CAS": "1Xtqsn4B-go8czEXO99oGsDGgpt8_PUmU", "CENA": "1KwQyinwdW82CM0EN_7UshnDdHtv65X3p"},
    "STV": {"CAS": "18nIcgJdvfHHN2ToLufUi-PTQwPwYopfW", "CENA": "1IbYUvNlcKwhm7fx-WbLQ5_jtP_hDsVud"}
}

# VALID MAP PODĽA TVOJICH ZOZNAMOV
VALID_MAP = {
    "STV": {
        "CAS": {
            "SUBCATS": [
                'ALU', 'TOOL', 'UNALL', 'ALLOYED', 'POM',
                'AUST', 'FERR', 'DUPX', 'BRONZE', 'PA',
                'OTHER', 'PET'
            ]
        },
        "CENA": {
            "SUBCATS": [
                'AUST', 'ALU', 'DUPX', 'UNALL', 'TOOL',
                'OTHER_SUBCAT', 'ALLOYED', 'BRASS', 'BRONZE',
                'PA', 'POM', 'FERR', 'PET'
            ],
            "COUNTRIES": [
                'SK', 'FR', 'DE', 'CZ', 'SUI', 'PT', 'LAT',
                'EN', 'CN', 'HU', 'RO', 'Unknown'
            ]
        }
    },
    "KR": {
        "CAS": {
            "SUBCATS": [
                'LOWAL', 'TOOL', 'BRASS', 'ALU', 'UNALL',
                'AUST', 'ALLOYED', 'PET', 'FERR', 'HSS',
                'BRONZE', 'POM', 'MART', 'PA', 'OTHER',
                'PE', 'PEEK', 'PVC'
            ]
        },
        "CENA": {
            "SUBCATS": [
                'ALLOYED', 'AUST', 'TOOL', 'UNALL', 'ALU',
                'POM', 'PE', 'OTHER', 'HSS', 'LOWAL', 'PA',
                'BRONZE', 'MART', 'BRASS', 'PEEK', 'FERR',
                'PVC', 'PET'
            ],
            "COUNTRIES": [
                'SK', 'FR', 'PT', 'DE', 'SUI', 'EN', 'CZ',
                'LAT', 'AT', 'NL', 'SWE', 'HU', 'RO'
            ]
        }
    }
}

def get_valid_subcat_for_time(subcat):
    allowed = VALID_MAP[tvar]["CAS"]["SUBCATS"]
    return subcat if subcat in allowed else "OTHER"

def get_valid_subcat_for_price(subcat):
    if tvar == "KR":
        allowed = VALID_MAP["KR"]["CENA"]["SUBCATS"]
        fallback = "OTHER"
    else:
        allowed = VALID_MAP["STV"]["CENA"]["SUBCATS"]
        fallback = "OTHER_SUBCAT"
    return subcat if subcat in allowed else fallback

def get_valid_country(country):
    allowed = VALID_MAP[tvar]["CENA"]["COUNTRIES"]
    c = str(country).strip().upper()
    return c if c in allowed else ("Unknown" if "Unknown" in allowed else c)

cols = st.columns([1, 1.2, 0.8, 1.2, 1, 1.2, 0.8, 1.2])

# 1) PREDIKCIA ČASU
with cols[0]:
    if st.button("🚀 Predikuj čas"):
        try:
            model = load_model_from_drive(ID_MODELS[tvar]["CAS"], f"model_{tvar.lower()}_cas.pkl")["model"]

            if tvar == "KR":
                geom_koef = l_mm / d_mm if d_mm > 0 else 0
                data = pd.DataFrame({
                    "hmotnost_kg": [hmotnost],
                    "plocha_m2": [plocha / 100],
                    "geom_koef": [geom_koef],
                    "log_pocet_kusov": [np.log1p(pocet_kusov)],
                    "subcategory_clean": [get_valid_subcat_for_time(subcategory)],
                    "narocnost": [narocnost]
                })
            else:
                d_val = dp if dp > 0 else np.nan
                geom_koef = ((s + v) / d_val) if d_val and not math.isinf((s + v) / d_val) else 0
                data = pd.DataFrame({
                    "v_narocnost": [narocnost],
                    "hmotnost_kg": [hmotnost],
                    "plocha_m2": [plocha / 100],
                    "geom_koef": [geom_koef],
                    "log_pocet_kusov": [np.log1p(pocet_kusov)],
                    "subcategory_clean": [get_valid_subcat_for_time(subcategory)]
                })

            st.session_state.predicted_time = round(np.expm1(model.predict(data))[0], 2)
            st.session_state.time_confirmed = False
            st.rerun()
        except Exception as e:
            st.error(f"Chyba času: {e}")

if st.session_state.get("predicted_time", 0) > 0:
    with cols[1]:
        st.info(f"Čas: {st.session_state.predicted_time} h")
        new_time = st.number_input("Uprav čas (h)", value=st.session_state.predicted_time, step=0.1)
        if st.button("✅ Potvrdiť čas"):
            st.session_state.predicted_time = new_time
            st.session_state.time_confirmed = True
            st.rerun()

# 2) PREDIKCIA CENY
with cols[4]:
    if st.button("💰 Predikuj cenu", disabled=not st.session_state.get("time_confirmed", False)):
        try:
            model = load_model_from_drive(ID_MODELS[tvar]["CENA"], f"model_{tvar.lower()}_cena.pkl")["model"]

            log_pocet = np.log1p(pocet_kusov)
            log_cas = np.log1p(st.session_state.predicted_time)

            if tvar == "KR":
                geom_koef = l_mm / d_mm if d_mm > 0 else 0
                data_cena = pd.DataFrame({
                    "hmotnost_kg": [hmotnost],
                    "plocha_m2": [plocha / 100],
                    "geom_koef": [geom_koef],
                    "log_pocet_kusov": [log_pocet],
                    "cena_material_predpoklad": [vstupne_naklady_ks],
                    "log_cas": [log_cas],
                    "subcategory_clean": [get_valid_subcat_for_price(subcategory)],
                    "zakaznik_krajina": [get_valid_country(krajina_input)]
                })
            else:
                data_cena = pd.DataFrame({
                    "log_pocet_kusov": [log_pocet],
                    "cena_material_predpoklad": [vstupne_naklady_ks],
                    "log_cas": [log_cas],
                    "hmotnost_kg": [hmotnost],
                    "SUBCATEGORY_clean": [get_valid_subcat_for_price(subcategory)],
                    "zakaznik_krajina": [get_valid_country(krajina_input)]
                })

            st.session_state.predicted_price = round(np.expm1(model.predict(data_cena))[0], 2)
            st.session_state.price_confirmed = False
            st.rerun()
        except Exception as e:
            st.error(f"Chyba ceny: {e}")

if st.session_state.get("predicted_price", 0) > 0:
    with cols[5]:
        st.success(f"Cena: {st.session_state.predicted_price} €")
        new_price = st.number_input("Uprav cenu (€/ks)", value=st.session_state.predicted_price, step=0.1)
        if st.button("✅ Potvrdiť cenu"):
            st.session_state.predicted_price = new_price
            st.session_state.price_confirmed = True
            st.rerun()

# ========================================================
# ========================================================
# KOŠÍK + PDF + ULOŽENIE DO SHEETU
# ========================================================

def vytvor_cp_riadok():
    cas_min = round(st.session_state.predicted_time * 60, 2)
    jednotkova_cena = st.session_state.predicted_price
    cena_polozky_spolu = round(jednotkova_cena * pocet_kusov, 2)

    return {
        "Dátum CP": date.strftime("%d.%m.%Y"),
        "Číslo CP": cp_nazov,
        "Zákazník": vybrany,
        "Krajina": krajina_input,
        "ITEM": item,
        "Tvar": tvar,
        "Materiál": material,
        "Akosť": ", ".join(akost_vyber) if akost_vyber else "",
        "Rozmer D / DP": dp if tvar == "STV" else d_mm,
        "Rozmer L / S": s if tvar == "STV" else l_mm,
        "Rozmer V": v if tvar == "STV" else 0.0,
        "Hustota": hustota,
        "Hmotnosť kusu (kg)": round(hmotnost, 3),
        "Náročnosť": narocnost,
        "J.cena materiálu (€/bm)": round(cena_bm, 4),
        "Náklad materiál (€/ks)": round(cena_mat_ks, 4),
        "Náklad kooperácia (€/ks)": round(cena_ks, 4),
        "Vstupné náklady (€/ks)": round(vstupne_naklady_ks, 4),
        "Čas (min)": cas_min,
        "Jednotková cena (€/ks)": jednotkova_cena,
        "Počet kusov": pocet_kusov,
        "Cena položky spolu (€)": cena_polozky_spolu,
    }


# Tlačidlo "Pridať do košíka"
with cols[7]:
    can_add = (
        st.session_state.get("time_confirmed", False)
        and st.session_state.get("price_confirmed", False)
        and item.strip() != ""
    )
    if st.button("🧺 Pridať do košíka", disabled=not can_add):
        st.session_state.kosik.append(vytvor_cp_riadok())
        st.session_state.predicted_time = 0.0
        st.session_state.time_confirmed = False
        st.session_state.predicted_price = 0.0
        st.session_state.price_confirmed = False
        st.success("Položka bola pridaná do košíka.")
        st.rerun()

st.divider()

# Zobrazenie košíka
if st.session_state.kosik:
    st.subheader("Košík – položky v cenovej ponuke")
    df_kosik = pd.DataFrame(st.session_state.kosik)
    st.dataframe(df_kosik, use_container_width=True)
    celkova_cena = df_kosik["Cena položky spolu (€)"].sum()
    st.markdown(f"### Celková cena ponuky: **{round(celkova_cena, 2)} €**")

# Poznámka pre zákazníka
st.session_state.note_text = st.text_area("Poznámka pre zákazníka (NOTE v PDF)", value=st.session_state.note_text)


# ========================================================
# PDF FUNKCIE
# ========================================================

def generate_customer_pdf(kosik, cp_nazov, date, zakaznik, krajina, note_text, total_price):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "MECASYS s.r.o.")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Oravská Polhora 455")
    y -= 14
    c.drawString(40, y, "029 47 Oravská Polhora")
    y -= 14
    c.drawString(40, y, "Slovenská republika")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, f"Price offer: {cp_nazov}")
    y -= 14
    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Date: {date.strftime('%d.%m.%Y')}")
    y -= 14
    c.drawString(40, y, f"Customer: {zakaznik}")
    y -= 14
    c.drawString(40, y, f"Country: {krajina}")
    y -= 20

    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "ITEM")
    c.drawString(220, y, "Qty")
    c.drawString(280, y, "Price/pcs")
    c.drawString(370, y, "Total")
    y -= 14
    c.setFont("Helvetica", 10)

    for r in kosik:
        if y < 120:
            c.showPage()
            y = height - 40
        c.drawString(40, y, r["ITEM"])
        c.drawString(220, y, str(r["Počet kusov"]))
        c.drawString(280, y, f"{round(r['Jednotková cena (€/ks)'], 2)} €")
        c.drawString(370, y, f"{round(r['Cena položky spolu (€)'], 2)} €")
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, f"Total price without VAT: {round(total_price, 2)} €")
    y -= 20

    if note_text:
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "NOTE:")
        y -= 14
        c.setFont("Helvetica", 10)
        for line in note_text.split("\n"):
            if y < 80:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line)
            y -= 14

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# ========================================================
# INTERNÉ PDF – TABUĽKA (VARIANTA B)
# ========================================================

from reportlab.lib.pagesizes import landscape

def generate_internal_pdf(kosik, cp_nazov, date, zakaznik, krajina, total_price):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "MECASYS – INTERNAL COSTING")
    y -= 20

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"CP: {cp_nazov}   Date: {date.strftime('%d.%m.%Y')}")
    y -= 14
    c.drawString(40, y, f"Customer: {zakaznik}   Country: {krajina}")
    y -= 20

    # Hlavička tabuľky
    c.setFont("Helvetica-Bold", 8)
    headers = [
        "ITEM", "Qty", "Tvar", "D/DP", "L/S", "V",
        "Mat €/bm", "Mat/ks", "Koop/ks", "Vstup/ks",
        "Čas (min)", "Cena/ks", "Cena spolu"
    ]
    x_positions = [40, 120, 160, 200, 240, 280, 320, 380, 440, 500, 560, 620, 680]

    for x, h in zip(x_positions, headers):
        c.drawString(x, y, h)
    y -= 12

    c.setFont("Helvetica", 8)

    for r in kosik:
        if y < 60:
            c.showPage()
            y = height - 40
            c.setFont("Helvetica-Bold", 8)
            for x, h in zip(x_positions, headers):
                c.drawString(x, y, h)
            y -= 12
            c.setFont("Helvetica", 8)

        row = [
            r["ITEM"],
            str(r["Počet kusov"]),
            r["Tvar"],
            str(r["Rozmer D / DP"]),
            str(r["Rozmer L / S"]),
            str(r["Rozmer V"]),
            str(r["J.cena materiálu (€/bm)"]),
            str(r["Náklad materiál (€/ks)"]),
            str(r["Náklad kooperácia (€/ks)"]),
            str(r["Vstupné náklady (€/ks)"]),
            str(r["Čas (min)"]),
            str(r["Jednotková cena (€/ks)"]),
            str(r["Cena položky spolu (€)"]),
        ]

        for x, cell in zip(x_positions, row):
            c.drawString(x, y, cell)

        y -= 12

    y -= 16
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, f"Total offer price: {round(total_price, 2)} €")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ========================================================
# ========================================================
# JEDNO TLAČIDLO – ULOŽIŤ CP + STIAHNUŤ ZIP
# ========================================================

import zipfile

# Poistka – ak by sa session_state resetol
if "kosik" not in st.session_state:
    st.session_state.kosik = []

if st.session_state.kosik:

    def prepare_zip() -> io.BytesIO | None:
        # Uloženie CP do Google Sheet
        r = requests.post(CP_APP_SCRIPT_URL, json=st.session_state.kosik)
        if r.status_code != 200:
            st.error("Chyba pri ukladaní ponuky do Google Sheet.")
            return None

        # Výpočet celkovej ceny
        df_kosik = pd.DataFrame(st.session_state.kosik)
        total_price = df_kosik["Cena položky spolu (€)"].sum()

        # PDF pre zákazníka
        pdf_customer = generate_customer_pdf(
            st.session_state.kosik,
            cp_nazov,
            date,
            vybrany,
            krajina_input,
            st.session_state.note_text,
            total_price
        )

        # Interné PDF
        pdf_internal = generate_internal_pdf(
            st.session_state.kosik,
            cp_nazov,
            date,
            vybrany,
            krajina_input,
            total_price
        )

        # Vytvorenie ZIP balíka
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"{cp_nazov}_customer.pdf", pdf_customer.getvalue())
            zipf.writestr(f"{cp_nazov}_internal.pdf", pdf_internal.getvalue())

        zip_buffer.seek(0)
        return zip_buffer

    zip_data = prepare_zip()
    if zip_data is not None:
        st.download_button(
            label="💾 Uložiť CP + stiahnuť ZIP",
            data=zip_data,
            file_name=f"{cp_nazov}_PDF_balík.zip",
            mime="application/zip"
        )



