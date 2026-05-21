import streamlit as st
import pandas as pd
import requests
import datetime
import math

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

novy_zak = None
nova_krajina = None

with col5:
    if vybrany == "+ Pridať nového zákazníka":
        novy_zak = st.text_input("Nový zákazník")

with col6:
    if vybrany == "+ Pridať nového zákazníka":
        nova_krajina = st.text_input("Krajina nového zákazníka")

with col7:
    if vybrany == "+ Pridať nového zákazníka":
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
dp = s = v = 0.0
d_mm = l_mm = 0.0

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

# ============================
# RIADOK 3 – Materiál • Akosť • Polotovar • Cena/bm • Cena/ks
# ============================

col1, col2, col3, col4, col5 = st.columns([1.2, 1.6, 2.4, 1.2, 1.2])

# --- 1. Materiál ---
with col1:
    material_list = sorted(df_pol["material"].dropna().unique().tolist())
    material = st.selectbox("Materiál", material_list, key="mat_select")

# --- 2. Akosť ---
with col2:
    akosti = sorted(df_pol[df_pol["material"] == material]["akost"].dropna().unique().tolist())

    force_akost = st.session_state.get("force_akost", None)

    if force_akost and force_akost in akosti:
        default_akosti = [force_akost]
        st.session_state["force_akost"] = None
    else:
        default_akosti = []

    akost_vyber = st.multiselect("Akosť", akosti, default=default_akosti, key="akost_select")

# --- 3. Polotovar ---
with col3:

    df_filtered = df_pol[df_pol["akost"].isin(akost_vyber)]

    if tvar == "KR":
        df_filtered = df_filtered[df_filtered["tvar"].isin(["KR", "6HR", "TR"])]

    polozky = []

    force_pol = st.session_state.get("force_polotovar", None)

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

        if force_pol and force_pol in polozky:
            polotovar = st.selectbox("Polotovar", polozky, index=polozky.index(force_pol), key="polotovar_select")
            st.session_state["force_polotovar"] = None
        else:
            polotovar = st.selectbox("Polotovar", polozky, key="polotovar_select")

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
    cena_bm = st.number_input("Cena €/bm", value=cena_bm, disabled=True, key="cena_bm")

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

    st.number_input("Cena mat/ks", value=cena_mat_ks, disabled=True, key="cena_mat_ks")

st.divider()

# ============================
# BOX – Pridať nový polotovar
# ============================

if polotovar == "+ Pridať nový polotovar":

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
        "1.29": "TOOL"
    }
    for prefix, sub in vynimky.items():
        if ak.startswith(prefix):
            return sub

    if ak.startswith(("1.00", "1.01", "1.02", "1.03", "1.04", "1.05", "1.06", "1.07", "1.08", "1.09", "1.10", "1.11", "1.12", "1.13", "1.14")):
        return "UNALL"

    if ak.startswith("1.43") or ak.startswith("1.44") or ak.startswith("1.45"):
        return "AUST"
    if ak.startswith("1.41"):
        return "MART"
    if ak.startswith("1.4462") or ak.startswith("1.44"):
        return "DUPX"
    if ak.startswith("1.40"):
        return "FERR"
    if ak.startswith(("1.46", "1.47", "1.48", "1.49")):
        return "STAIN-SPEC"
    if ak.startswith(("1.33", "1.34", "1.35", "1.36", "1.37", "1.38")):
        return "HSS"
    if ak.startswith(("1.20", "1.21", "1.22", "1.23", "1.24", "1.25", "1.26", "1.27", "1.28", "1.29", "1.30", "1.31", "1.32")):
        return "TOOL"
    if ak.startswith(("1.65", "1.66", "1.67", "1.68", "1.69", "1.70", "1.71", "1.72", "1.73", "1.74", "1.75", "1.76", "1.77", "1.78", "1.79", "1.80", "1.81", "1.82", "1.83", "1.84", "1.85", "1.86", "1.87", "1.88", "1.89")):
        return "ALLOYED"

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
        "PE": "PE"
    }

    naz = nazov_materialu.upper()

    for key in plast_map:
        if naz == key:
            return plast_map[key]

    for key in plast_map:
        if naz.startswith(key):
            return plast_map[key]

    return "UNKNOWN"


hustoty = {
    "UNALL": 7900, "LOWAL": 7900, "ALLOYED": 7900, "TOOL": 7900, "HSS": 7900,
    "AUST": 8000, "MART": 8000, "DUPX": 8000, "FERR": 8000, "STAIN-SPEC": 8000,
    "CU": 9000, "BRASS": 9000, "BRONZE": 9000, "ALU": 2900, "TI": 4500, "NI-SPEC": 8500,
    "POM": 1500, "PE": 1000, "PA": 1200, "PP": 1000, "PEEK": 1400, "PET": 1700,
    "PC": 1500, "PVC": 1700, "PTFE": 3000, "PUR": 2000, "PMMA": 1600, "RUBBER": 7900,
    "CAST-GG": 7150, "CAST-GGG": 7250, "CAST-TEMP": 7400
}

# ============================
# RIADOK 4 – všetko vedľa seba
# ============================

col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.2, 1.2, 1.2, 1.2, 1.4])

# 1) KOOPERÁCIA – ÁNO / NIE
with col1:
    kooperacia = st.checkbox("Koop.", key="koop_checkbox")

# 2) SUBCATEGORY
with col2:
    subcategory = urci_subcategory(akost_vyber[0] if akost_vyber else "", material, material)
    st.write("**SUBCAT:**", subcategory)

# 3) HUSTOTA
with col3:
    hustota_default = hustoty.get(subcategory, 1000)
    hustota = st.number_input("Hustota", value=float(hustota_default), step=10.0)

# 4) GEOMETRIA – OBJEM, HMOTNOSŤ, PLOCHA

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

# 5) KOOPERÁCIA – výber + výpočet ceny

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

# 6) Vstupné náklady / ks

vstupne_naklady_ks = cena_mat_ks + cena_ks

with col7:
    st.write("Vstupné €/ks")
    st.write(round(vstupne_naklady_ks, 3))

st.divider()

# ============================================================
# 5) LOAD KR CENA MODEL Z GOOGLE DRIVE (RIEŠENIE B)
# ============================================================

import requests
import joblib
import io

def download_from_drive(file_id: str) -> bytes:
    """
    Spoľahlivé stiahnutie veľkého súboru z Google Drive.
    Obchádza 'virus scan' stránku a vráti čisté binárne dáta.
    """
    session = requests.Session()
    URL = "https://drive.google.com/uc?export=download"

    # prvý request – môže vrátiť warning stránku
    response = session.get(URL, params={'id': file_id}, stream=True)
    token = None

    # hľadáme token, ktorý Google pridá pri veľkých súboroch
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value

    # ak existuje token, musíme potvrdiť sťahovanie
    if token:
        response = session.get(URL, params={'id': file_id, 'confirm': token}, stream=True)

    return response.content


@st.cache_resource
def load_model_from_drive(file_id: str):
    """
    Stiahne model z Google Drive a načíta ho cez joblib.load().
    """
    raw_data = download_from_drive(file_id)
    return joblib.load(io.BytesIO(raw_data))


# ID KR CENA modelu
KR_CENA_ID = "1UT9SQzfWVnONGsPQLwxh8yxE4kJymjam"

# načítanie modelu
kr_cena_package = load_model_from_drive(KR_CENA_ID)
kr_cena_model = kr_cena_package["model"]
kr_cena_metadata = kr_cena_package["metadata"]


# ============================================================
# 6) FEATURE ENGINEERING PRE KR CENA (IDENTICKÉ AKO V TRÉNINGU)
# ============================================================

# plocha v m2
plocha_m2 = (np.pi * (d_mm ** 2) / 4) / 1_000_000

# objem v m3
objem_m3 = plocha_m2 * (l_mm / 1000)

# hmotnosť v kg
hmotnost_kg = objem_m3 * hustota

# geometrický koeficient
geom_koef = l_mm / d_mm if d_mm > 0 else 0

# log počet kusov
log_pocet_kusov = np.log1p(pocet_kusov)

# subcategory_clean (rovnaké ako pri KR čase)
subcategory_clean = subcategory if subcategory in TRAINED_SUBCATS else "OTHER"

# log predikovaného času z KR čas modelu
log_predikovany_cas = np.log1p(predikovany_cas_min)


# ============================================================
# 7) PREDIKCIA KR CENA (ČISTO MODEL – BEZ ÚPRAV)
# ============================================================

X_cena = pd.DataFrame([{
    "hmotnost_kg": hmotnost_kg,
    "plocha_m2": plocha_m2,
    "geom_koef": geom_koef,
    "log_pocet_kusov": log_pocet_kusov,
    "cena_material_predpoklad": cena_material_predpoklad,
    "log_predikovany_cas": log_predikovany_cas,
    "subcategory_clean": subcategory_clean,
    "zakaznik_krajina": zakaznik_krajina
}])

log_pred_cena = kr_cena_model.predict(X_cena)[0]
kr_cena_eur = float(np.expm1(log_pred_cena))


# ============================================================
# 8) VÝSTUP
# ============================================================

st.subheader("Predikovaná KR cena (model-only)")
st.metric("Cena [€]", f"{kr_cena_eur:,.2f}".replace(",", " "))

