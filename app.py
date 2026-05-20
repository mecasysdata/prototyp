import streamlit as st
import pandas as pd
import datetime

# ---------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------
st.set_page_config(layout="wide", page_title="MEC Calculation")

# ---------------------------------------------------------
# 2. SESSION STATE
# ---------------------------------------------------------
if "kosik" not in st.session_state:
    st.session_state.kosik = []

if "stary_item" not in st.session_state:
    st.session_state.stary_item = ""

if "aktualny_pocet_kusov" not in st.session_state:
    st.session_state.aktualny_pocet_kusov = 1

# ---------------------------------------------------------
# 3. LOAD DATA (Google Sheets)
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Chyba pri načítaní dát: {e}")
        return pd.DataFrame()

# STABILNÝ CSV LINK (export)
SHEET_URL = "https://docs.google.com/spreadsheets/d/2PACX-1vSuHQWbpryWNerWr8aKKheHbzTPhXI6lS7YH1sL5zwFIIzLfpTZz47acYua2efVqEcfxMBe5wnjue/export?format=csv&gid=0"

df = load_data(SHEET_URL)

if df.empty:
    st.error("❌ Nepodarilo sa načítať zákazníkov. Skontroluj Google Sheet.")
    st.stop()

# ---------------------------------------------------------
# 4. LOGO + HLAVIČKA
# ---------------------------------------------------------
col_logo, col_title = st.columns([1, 5])

with col_logo:
    try:
        st.image("logo.png", width=140)
    except:
        st.write("🖼️ Logo")

with col_title:
    st.title("MEC Calculation")

st.divider()

# ---------------------------------------------------------
# 5. ZÁKLADNÉ ÚDAJE (Dátum, CP, Zákazník, Krajina)
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

# DÁTUM
with col1:
    datum = st.date_input("Dátum", datetime.date.today(), format="YYYY/MM/DD")

# CP
with col2:
    cp = st.text_input("Označenie CP")

# ZÁKAZNÍK
zoznam_zak = sorted(df["zakaznik"].dropna().unique())
moznosti = ["+ Pridať nového zákazníka"] + zoznam_zak

with col3:
    vyber = st.selectbox("Názov zákazníka", moznosti)

# KRAJINA
zakaznik = ""
krajina = ""
lojalita = 0.5

if vyber == "+ Pridať nového zákazníka":
    with col3:
        zakaznik = st.text_input("Meno nového zákazníka")
    with col4:
        krajina = st.text_input("Krajina zákazníka")
else:
    zakaznik = vyber
    riadok = df[df["zakaznik"] == vyber].iloc[0]
    krajina = riadok.get("krajina", "")
    lojalita = float(riadok.get("lojalita", 0.5))

    with col4:
        st.text_input("Krajina zákazníka", krajina, disabled=True)

st.divider()

# ---------------------------------------------------------
# 6. ITEM + GEOMETRIA (bez výpočtov)
# ---------------------------------------------------------
col5, col6, col7, col8, col9, col10, col11 = st.columns(7)

# ITEM
with col5:
    item = st.text_input("ITEM")

# RESET LOGIKA PRI ZMENE ITEMU
if item != st.session_state.stary_item:
    st.session_state.aktualny_pocet_kusov = 1
    st.session_state.stary_item = item

# POČET KUSOV
with col6:
    pocet = st.number_input("Počet kusov", min_value=1, value=st.session_state.aktualny_pocet_kusov)
    st.session_state.aktualny_pocet_kusov = pocet

# NÁROČNOSŤ
with col7:
    narocnost = st.selectbox("Náročnosť", [1, 2, 3, 4, 5])

# TVAR
with col8:
    tvar = st.selectbox("Tvar položky", ["STV", "KR"])

# ROZMERY
d = l = s = v = 0.0

if tvar == "KR":
    with col9:
        d = st.number_input("D (mm)", min_value=0.0, step=0.1)
    with col10:
        l = st.number_input("L (mm)", min_value=0.0, step=0.1)
else:
    with col9:
        d = st.number_input("D/P (mm)", min_value=0.0, step=0.1)
    with col10:
        s = st.number_input("S (mm)", min_value=0.0, step=0.1)
    with col11:
        v = st.number_input("V (mm)", min_value=0.0, step=0.1)

st.divider()

# ---------------------------------------------------------
# 7. MATERIÁL (pevný zoznam)
# ---------------------------------------------------------
col_m1, col_m2 = st.columns([2, 4])

with col_m1:
    material = st.selectbox(
        "Materiál",
        ["PLAST", "NEREZ", "OCEĽ", "FAREBNÉ KOVY", "LIATINA"]
    )

# (Ďalšie polia ako akosť, polotovar, hustota pôjdu až v ďalšom kroku)


