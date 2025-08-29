import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from sidebar import menu
from utils.services import get_raw_values, is_database_available
from utils.format import cast_to_number



st.set_page_config(page_title="Collection Performance - Dashboard Data Collection", layout="wide", page_icon="📈")
st.title("📊 Collection Performance")

# Pastikan link ada di session_state
is_database_available()
menu()

def get_data_collection(link_data, sheet_name):
    df = get_raw_values(link_data, sheet_name)
    df["DGS"] = cast_to_number(df["DGS"])
    df["DPS"] = cast_to_number(df["DPS"])
    df["DSS"] = cast_to_number(df["DSS"])
    df["RBS"] = cast_to_number(df["RBS"])
    df["Rata-rata"] = cast_to_number(df["Rata-rata"])
    return df

# def plot_collection_performance(df, title):
#     # Ubah ke long format biar bisa plot banyak line sekaligus
#     df = df.melt(id_vars="BULAN", var_name="Segmen", value_name="Persentase")

#     # Plot line chart
#     fig = px.line(
#         df,
#         x="BULAN",
#         y="Persentase",
#         color="Segmen",
#         markers=True,
#         title=f"Collection Performance {title}"
#     )

#     fig.update_layout(yaxis_ticksuffix="%")

#     st.plotly_chart(fig, use_container_width=False)

import plotly.graph_objects as go

# Definisikan warna manual per segmen
segmen_colors = {
    "DGS": "#89C4E9",
    "DPS": "#FF727C",
    "DSS": "#9E0000",
    "RBS": "#00527E"
}

def plot_collection_performance(df, title):
    df_long = df.melt(id_vars="BULAN", var_name="Segmen", value_name="Persentase")

    fig = go.Figure()

    # Tambahkan Rata-rata sebagai area abu-abu
    df_avg = df_long[df_long["Segmen"] == "Rata-rata"]
    fig.add_trace(
        go.Scatter(
            x=df_avg["BULAN"],
            y=df_avg["Persentase"],
            mode="lines",
            name="Rata-rata",
            line=dict(color="#fde8bd", width=2, dash="dot"), 
            fill="tozeroy",
            fillcolor="rgba(253,240,213,0.3)" 
        )
    )

    # Tambahkan segmen 
    for segmen in df_long["Segmen"].unique():
        if segmen == "Rata-rata":
            continue
        df_seg = df_long[df_long["Segmen"] == segmen]
        fig.add_trace(
            go.Scatter(
                x=df_seg["BULAN"],
                y=df_seg["Persentase"],
                mode="lines+markers",
                name=segmen,
                line=dict(color=segmen_colors.get(segmen, None))  # warna sesuai mapping
            )
        )

    fig.update_layout(
        title=f"Collection Performance {title}",
        yaxis=dict(ticksuffix="%"),
        legend=dict(title="Segmen")
    )

    st.plotly_chart(fig, use_container_width=True)



df_cr = get_data_collection(st.session_state["database_gsheet_url"], "DATA COLLECTION CR")
df_cyc = get_data_collection(st.session_state["database_gsheet_url"], "DATA COLLECTION CYC")
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Collection Ratio (CR)")
    plot_collection_performance(df_cr, "CR")
    st.dataframe(df_cr.T)
with col2:
    st.markdown("#### Current Year Collection (CYC)")
    plot_collection_performance(df_cyc, "CYC")
    st.dataframe(df_cyc.T)