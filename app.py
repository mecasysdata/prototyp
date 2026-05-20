import streamlit as st
import pandas as pd
import datetime
import re
import math

#logo - vrchná časť aplikácie -úvod
col_logo, col_title = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.write("🖼️ Logo")
with col_title:
    st.title("MEC Calculation")

st.divider()
