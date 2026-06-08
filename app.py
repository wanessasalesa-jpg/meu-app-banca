import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("Sistema Crivo")
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="Escalacao", ttl=0)
st.write(df.head())
