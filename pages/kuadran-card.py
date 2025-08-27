import streamlit as st
import pandas as pd
import plotly.express as px
from utils.google_utils import get_raw_values
from utils.helpers import is_database_available, pilih_kategori, to_rupiah
from utils.validation import to_number
from sidebar import menu


# ================================
# Konfigurasi Halaman
# ================================
st.set_page_config(page_title="Visualisasi Kuadran", layout="wide", page_icon="🍀")
st.title("🍀 Visualisasi Kuadran")

# ================================
# Cek database
# ================================
if not is_database_available():
    st.page_link("home.py", label="Home", icon="🏠")
    st.stop()

df = st.session_state["df_database_clean"]

# Sidebar menu
menu()

# ================================
# Konversi kolom numeric
# ================================
aging_cols = ["0-3 Bulan", "4-6 Bulan", "7-12 Bulan", "13-24 Bulan", "> 24 Bulan"]
df[aging_cols] = df[aging_cols].apply(lambda s: to_number(s, allow_parentheses=True))
df["Saldo Akhir"] = to_number(df["Saldo Akhir"], allow_parentheses=False)
df["Lama Tunggakan"] = to_number(df["Lama Tunggakan"], allow_parentheses=False)
df["Kuadran"] = pd.to_numeric(df["Kuadran"], errors="coerce").astype("Int64")

# ================================
# Filter kategori (bulan, tahun, segmen)
# ================================
bulan_target, tahun_target, segmen_target = pilih_kategori()
df_filtered = df.copy()

if segmen_target != "-Semua-":
    df_filtered = df_filtered[df_filtered["Segmen"] == segmen_target]
else:
    segmen_target = "Semua Segmen"

if bulan_target != 0:
    tanggal_target = f"{bulan_target}/{tahun_target}"
    df_filtered = df_filtered[df_filtered["Bulan Tahun"] == tanggal_target]
else:
    df_filtered = df_filtered[df_filtered["Bulan Tahun"].str.split("/").str[1] == str(tahun_target)]
    tanggal_target = f"Semua Bulan {tahun_target}"

# Hanya ambil pelanggan dengan saldo > 0
df_filtered = df_filtered[df_filtered["Saldo Akhir"].astype(float) > 0]

# ================================
# Summary Total
# ================================
total_pelanggan = len(df_filtered)
total_tunggakan = df_filtered["Saldo Akhir"].sum(skipna=True)

st.markdown(f"### Ringkasan {segmen_target} — {tanggal_target}")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.metric("Total Pelanggan", total_pelanggan)

        pie_data = (
            df_filtered.groupby("Kuadran", dropna=True)["IdNumber"]
            .count()
            .reset_index(name="Jumlah Pelanggan")
        )
        if not pie_data.empty:
            pie_data["Kuadran"] = pie_data["Kuadran"].apply(lambda q: f"Kuadran {q}")
            fig = px.pie(
                pie_data,
                values="Jumlah Pelanggan",
                names="Kuadran",
                hole=0.3,
                title="Proporsi Jumlah Pelanggan",
                color="Kuadran",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data proporsi pelanggan.")

with col2:
    with st.container(border=True):
        st.metric("Total Tunggakan", to_rupiah(total_tunggakan))

        pie_data = (
            df_filtered.groupby("Kuadran", dropna=True)["Saldo Akhir"]
            .sum()
            .reset_index()
        )
        if not pie_data.empty:
            pie_data["Kuadran"] = pie_data["Kuadran"].apply(lambda q: f"Kuadran {q}")
            fig = px.pie(
                pie_data,
                values="Saldo Akhir",
                names="Kuadran",
                hole=0.3,
                title="Proporsi Tunggakan",
                color="Kuadran",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data proporsi tunggakan.")

# ================================
# Komponen Kuadran
# ================================
def render_kuadran(dfq: pd.DataFrame, kuadran_num: int, judul: str):
    with st.container(border=True):
        st.subheader(judul)

        if dfq.empty:
            st.info("Tidak ada data di kuadran ini.")
            return

        jml = len(dfq)
        persen_plg = (jml / total_pelanggan * 100) if total_pelanggan else 0.0
        total_nom = dfq["Saldo Akhir"].sum(skipna=True)
        persen_nom = (total_nom / total_tunggakan * 100) if total_tunggakan else 0.0

        st.markdown(
            f"- **Jumlah pelanggan:** {jml} ({persen_plg:.1f}%)\n"
            f"- **Total tunggakan:** {to_rupiah(total_nom)} ({persen_nom:.1f}%)"
        )

        # ================================
        # Top 3 by Saldo Akhir + editable
        # ================================
        top3 = dfq.sort_values("Saldo Akhir", ascending=False).head(3).copy()
        top3["Saldo Akhir (Rp)"] = top3["Saldo Akhir"].apply(to_rupiah)
        top3["Keterangan"] = top3.get("Keterangan", pd.Series([""] * len(top3)))

        edited_top3 = st.data_editor(
            top3[["BP Name", "Saldo Akhir (Rp)", "Lama Tunggakan", "Keterangan"]],
            column_config={
                "BP Name": st.column_config.TextColumn("Nama", disabled=True),
                "Saldo Akhir (Rp)": st.column_config.TextColumn(disabled=True),
                "Lama Tunggakan": st.column_config.NumberColumn("Lama Tunggakan (bulan)", disabled=True),
                "Keterangan": st.column_config.TextColumn("Keterangan (editable)")
            },
            hide_index=True,
            use_container_width=True,
            key=f"top3_{kuadran_num}"
        )

        # Simpan hasil edit ke session_state
        st.session_state[f"top3_{kuadran_num}"] = edited_top3

# ================================
# Grid 2x2 Kuadran
# ================================
st.markdown(f"### Detail Kuadran {segmen_target} — {tanggal_target}")

c1, c2 = st.columns(2)
with c1:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 1], 1, "Kuadran 1 — Baru menunggak & nominal besar")
with c2:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 2], 2, "Kuadran 2 — Tunggakan lama & nominal besar")

c3, c4 = st.columns(2)
with c3:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 3], 3, "Kuadran 3 — Baru menunggak & nominal kecil")
with c4:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 4], 4, "Kuadran 4 — Tunggakan lama & nominal kecil")
