import pandas as pd
import plotly.express as px
import streamlit as st
from utils.google_utils import get_raw_values
from sidebar import menu
from utils.helpers import is_database_available

st.set_page_config(page_title="Collection Performance", layout="wide", page_icon="🏆")
st.title("📊 Collection Performance")

# Pastikan link ada di session_state
is_database_available()
menu()


def plot_collection_performance(df):
    # Ubah ke long format biar bisa plot banyak line sekaligus
    df = df.melt(id_vars="BULAN", var_name="Segmen", value_name="Persentase")

    # Plot line chart
    fig = px.line(
        df,
        x="BULAN",
        y="Persentase",
        color="Segmen",
        markers=True,
        title="Collection Performance per Segmen"
    )

    fig.update_layout(yaxis_ticksuffix="%")

    st.plotly_chart(fig, use_container_width=False)

data = {
    "BULAN": ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL"],
    "DGS": [96.82, 89.87, 88.85, 92.57, 96.12, 96.77, 98.19],
    "DPS": [57.57, 69.20, 72.20, 82.39, 87.52, 91.31, 92.23],
    "DSS": [52.91, 52.66, 52.04, 53.53, 53.26, 62.59, 67.77],
    "RBS": [5.90, 13.02, 18.05, 23.28, 27.64, 31.46, 35.25],
    "Rata-rata": [53.3, 56.19, 57.79, 62.94, 66.13, 70.53, 73.36]
}
df = pd.DataFrame(data)

st.subheader("Collection Performance")
df_cr = get_raw_values("DATA COLLECTION CR")
df_cyc = get_raw_values("DATA COLLECTION CYC")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### CR")
    st.dataframe(df_cr)
    plot_collection_performance(df)
with col2:
    st.markdown("#### CYC")
    st.dataframe(df_cyc)

st.subheader("Remaining Balance")






df = pd.DataFrame(data)
st.dataframe(df)    

# Ubah ke long format biar bisa plot banyak line sekaligus
df_long = df.melt(id_vars="BULAN", var_name="Segmen", value_name="Persentase")

# Plot line chart
fig = px.line(
    df_long,
    x="BULAN",
    y="Persentase",
    color="Segmen",
    markers=True,
    title="Collection Performance per Segmen"
)

fig.update_layout(yaxis_ticksuffix="%")

st.plotly_chart(fig, use_container_width=False)