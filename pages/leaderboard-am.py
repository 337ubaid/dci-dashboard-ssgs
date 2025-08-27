import pandas as pd
import streamlit as st
from utils.google_utils import get_raw_values
from sidebar import menu
from utils.helpers import is_database_available

st.set_page_config(page_title="Leaderboard AM", layout="wide", page_icon="🏆")
st.title("📊 Leaderboard AM")

# Pastikan link ada di session_state
is_database_available()
menu()

st.warning("⚠️ Halaman ini masih dalam pengembangan. Sementara, Anda bisa melihat total saldo akhir per AM di bawah ini.")

def to_number(series: pd.Series, allow_parentheses: bool = False) -> pd.Series:
    s = series.astype(str).str.strip()
    if allow_parentheses:
        # (123) -> -123 untuk kolom aging
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    # Bersihkan Rupiah & pemisah ribuan gaya Indonesia
    s = (
        s.str.replace("Rp", "", regex=False)
         .str.replace(".", "", regex=False)     # hapus titik ribuan
         .str.replace(",", ".", regex=False)    # koma -> titik desimal
         .str.replace(r"[^\d\.\-]", "", regex=True)  # buang karakter lain
    )
    return pd.to_numeric(s, errors="coerce")
    
# ====== Ambil data dari Google Sheets ======
df = get_raw_values()

# Pastikan saldo jadi numeric
df["Saldo Akhir"] = to_number(df["Saldo Akhir"], allow_parentheses=False)

# Group by Nama AM
leaderboard = (
    df.groupby("AM", as_index=False)["Saldo Akhir"]
      .sum()
      .sort_values(by="Saldo Akhir", ascending=False)
)

col1, col2 = st.columns(2)
with col1:

    st.dataframe(leaderboard)

# Bisa juga tampilkan top 5
st.write("### Top 5 AM")
for i, row in leaderboard.head(5).iterrows():
    st.write(f"**{row['AM']}** — Rp{row['Saldo Akhir']:,.0f}")


# import altair as alt

# chart = alt.Chart(leaderboard.head(10)).mark_bar().encode(
#     x=alt.X("Saldo Akhir:Q", title="Total Saldo Akhir"),
#     y=alt.Y("AM:N", sort="-x", title="AM"),
#     tooltip=["AM", "Saldo Akhir"]
# )
# st.altair_chart(chart, use_container_width=True)