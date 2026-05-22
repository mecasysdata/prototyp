import streamlit as st
import pandas as pd
import requests
import datetime
import math
import gdown
import os
import joblib
import numpy as np

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

    # --- VÝNIMKY ---
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

    # --- OCEĽ ---
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

    # --- NEREZ (poradie dôležité) ---
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

    # --- FAREBNÉ KOVY ---
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

    # --- PLASTY ---
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

# 5. RIADOK – AI PREDIKCIE (FINALIZOVANÁ LOGIKA)
# ========================================================

# ID MODELOV
ID_MODELS = {
    "KR": {"CAS": "1Xtqsn4B-go8czEXO99oGsDGgpt8_PUmU", "CENA": "1KwQyinwdW82CM0EN_7UshnDdHtv65X3p"},
    "STV": {"CAS": "18nIcgJdvfHHN2ToLufUi-PTQwPwYopfW", "CENA": "1IbYUvNlcKwhm7fx-WbLQ5_jtP_hDsVud"}
}

# VALIDÁCIA (Univerzálna pre KR aj STV podľa dohody)
ALLOWED_SUBCATS = ['ALLOYED', 'AUST', 'TOOL', 'UNALL', 'ALU', 'POM', 'PE', 'OTHER', 'HSS', 'LOWAL', 'PA', 'BRONZE', 'MART', 'BRASS', 'PEEK', 'FERR', 'PVC', 'PET']
ALLOWED_COUNTRIES = ['SK', 'FR', 'PT', 'DE', 'SUI', 'EN', 'CZ', 'LAT', 'AT', 'NL', 'SWE', 'HU', 'RO']

def get_valid_subcat(subcat):
    return subcat if subcat in ALLOWED_SUBCATS else 'OTHER'

def get_valid_country(country):
    return country if country in ALLOWED_COUNTRIES else 'OTHER'

# Inicializácia Session State
for key in ["time_confirmed", "predicted_time", "predicted_price"]:
    if key not in st.session_state: st.session_state[key] = 0.0 if key != "time_confirmed" else False

# Rozdelenie do 8 stĺpcov pre jeden riadok
cols = st.columns([1, 1.2, 0.8, 1.2, 1, 1.2, 0.8, 1.2])

with cols[0]:
    if st.button("🚀 Predikuj čas"):
        try:
            model_id = ID_MODELS[tvar]["CAS"]
            m_data = load_model_from_drive(model_id, f"model_{tvar.lower()}_cas.pkl")
            model = m_data["model"]
            
            data = pd.DataFrame({
                "hmotnost_kg": [hmotnost], 
                "plocha_m2": [plocha/100],
                "geom_koef": [l_mm/d_mm if d_mm>0 else 0] if tvar == "KR" else [((s+v)/dp) if dp>0 else 0],
                "log_pocet_kusov": [np.log1p(pocet_kusov)],
                "subcategory_clean": [get_valid_subcat(subcategory)],
                "v_narocnost": [narocnost]
            })
            st.session_state.predicted_time = round(np.expm1(model.predict(data))[0], 2)
            st.session_state.time_confirmed = False
        except Exception as e: st.error(f"Chyba času: {e}")

with cols[1]:
    vyr_cas_input = st.number_input("Čas (min)", value=st.session_state.predicted_time, step=0.1)
with cols[2]:
    if st.button("✅ Potvrdiť"):
        st.session_state.predicted_time = vyr_cas_input
        st.session_state.time_confirmed = True

with cols[4]:
    if st.button("💰 Predikuj cenu", disabled=not st.session_state.time_confirmed):
        try:
            model_id = ID_MODELS[tvar]["CENA"]
            m_data = load_model_from_drive(model_id, f"model_{tvar.lower()}_cena.pkl")
            model = m_data["model"]

            # Dynamické nastavenie názvu stĺpca podľa typu tvaru
            subcat_col_name = "SUBCATEGORY_clean" if tvar == "KR" else "subcategory_clean"
            
            # Dáta pre CENA model (obsahujú krajinu pre oba typy STV aj KR)
            data_cena = pd.DataFrame({
                "hmotnost_kg": [hmotnost], 
                "plocha_m2": [plocha/100],
                "geom_koef": [l_mm/d_mm if d_mm > 0 else 0] if tvar == "KR" else [((s+v)/dp) if dp > 0 else 0],
                "log_pocet_kusov": [np.log1p(pocet_kusov)],
                "cena_material_predpoklad": [vstupne_naklady_ks],
                "log_cas": [np.log1p(st.session_state.predicted_time)],
                subcat_col_name: [get_valid_subcat(subcategory)], # Použijeme dynamický názov,
                "zakaznik_krajina": [get_valid_country(krajina_input)]
            })
            st.session_state.predicted_price = round(np.expm1(model.predict(data_cena))[0], 2)
        except Exception as e: st.error(f"Chyba ceny: {e}")

with cols[5]:
    vyr_cena_input = st.number_input("Cena (€)", value=st.session_state.predicted_price, step=0.1)
with cols[6]:
    if st.button("💾 Uložiť"):
        st.success("Uložené")


        st.success("Uložené")

