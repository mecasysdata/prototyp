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

import streamlit as st
import pandas as pd
import numpy as np
import joblib

# --- 2. NAČÍTANIE MODELU A ENCODERA ---
@st.cache_resource
def load_assets():
    model = joblib.load('model_stv.pkl')
    encoder = joblib.load('encoder_stv.pkl')
    return model, encoder

try:
    model, encoder = load_assets()
except Exception as e:
    st.error(f"Nepodarilo sa načítať modelové súbory. Skontroluj, či sú 'model_stv.pkl' a 'encoder_stv.pkl' v koreňovom priečinku. Chyba: {e}")

# --- 3. DIZAJN A LOGO ---
col1, col2 = st.columns([1, 3])
with col1:
    try:
        st.image("logo.png", width=120)
    except:
        st.write("Logo")
with col2:
    st.title("Systém predikcie výroby")
    st.write("Výpočet predpokladaného času na komponent (v minútach)")

st.divider()

# --- 4. VSTUPNÉ POLIA (Inputs) ---
st.subheader("Technické parametre dielu")

col_a, col_b = st.columns(2)

with col_a:
    v_narocnost = st.number_input("Výrobná náročnosť (v_narocnost)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
    pocet_kusov = st.number_input("Celkový počet kusov", min_value=1, value=100)
    hmotnost_kg = st.number_input("Hmotnosť kusu (kg)", min_value=0.0, value=1.5, step=0.1)

with col_b:
    plocha_m2 = st.number_input("Plocha dielu (m2)", min_value=0.0, value=0.15, format="%.4f")
    geo_koef = st.number_input("Geometrický koeficient", min_value=0.0, value=1.0, step=0.1)
    
    # Tu zoznam kategórií - ideálne by mal zodpovedať tomu, čo máš v datasete
    kategorie = ['KRYT', 'RAM', 'DRZIAK', 'PROFIL', 'PLECH', 'OTHER_NEREZ', 'OTHER_OCEL'] 
    subcat = st.selectbox("Podkategória (SUBCATEGORY_clean)", kategorie)

# --- 5. VÝPOČET A PREDIKCIA ---
st.divider()

if st.button("🚀 Vypočítať predpokladaný čas", use_container_width=True):
    
    # A. Príprava dát do formátu, aký videl model pri trénovaní
    input_df = pd.DataFrame([{
        'v_narocnost': v_narocnost,
        'log_pocet_kusov': np.log1p(pocet_kusov), # Aplikujeme logaritmus ako v Bunke 2
        'hmotnost_kg': hmotnost_kg,
        'SUBCATEGORY_clean': subcat,
        'plocha_m2': plocha_m2,
        'geometricky_koeficient': geo_koef
    }])

    # B. Transformácia cez Target Encoder
    try:
        X_encoded = encoder.transform(input_df)
        
        # C. Predikcia
        predikcia = model.predict(X_encoded)[0]
        
        # D. Zobrazenie výsledku
        st.success(f"### Odhadovaný čas: {predikcia:.2f} minút / kus")
        
        # Informatívne metriky
        m1, m2 = st.columns(2)
        m1.metric("Celkový čas pre zákazku", f"{round(predikcia * pocet_kusov / 60, 2)} hod")
        m2.metric("Logistický koeficient", f"{round(np.log1p(pocet_kusov), 2)}")

    except Exception as e:
        st.error(f"Chyba pri výpočte: {e}")

st.sidebar.info("Tento model bol natrénovaný s R2 skóre 0.71 a presnosťou ±38 min.")
