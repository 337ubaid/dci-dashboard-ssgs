import streamlit as st
import pandas as pd
import plotly.express as px
from utils.google_utils import get_raw_values
from utils.helpers import is_database_available, pilih_kategori, to_rupiah
from utils.validation import to_number
from sidebar import menu


# ===============================
# Konfigurasi Halaman
# ===============================
st.set_page_config(page_title="Tanggungan tiap AM", layout="wide", page_icon="👤")
st.title("👤 Tanggungan tiap AM")

# Pastikan link tersedia
is_database_available()
menu()


# ===============================
# Fungsi Helper
# ===============================
@st.cache_data
def load_and_clean_data():
    """Ambil data dari Google Sheets dan lakukan pembersihan/konversi angka."""
    df = get_raw_values()

    aging_cols = ["0-3 Bulan", "4-6 Bulan", "7-12 Bulan", "13-24 Bulan", "> 24 Bulan"]
    df[aging_cols] = df[aging_cols].apply(lambda s: to_number(s, allow_parentheses=True))
    df["Saldo Akhir"] = to_number(df["Saldo Akhir"], allow_parentheses=False)
    df["Lama Tunggakan"] = to_number(df["Lama Tunggakan"], allow_parentheses=False)
    df["Kuadran"] = pd.to_numeric(df["Kuadran"], errors="coerce").astype("Int64")
    return df


def filter_data(df, nama_am, bulan, tahun, segmen):
    """Filter dataframe berdasarkan segmen, bulan/tahun, dan AM."""
    # Filter segmen
    if segmen != "-Semua-":
        df = df[df["Segmen"] == segmen]

    # Filter tanggal
    if bulan != 0:
        tanggal_label = f"{bulan}/{tahun}"
        df = df[df["Bulan Tahun"] == tanggal_label]
    else:
        df = df[df["Bulan Tahun"].str.split("/").str[1] == str(tahun)]
        tanggal_label = f"Semua Bulan/{tahun}"

    # Filter nama AM
    if nama_am:
        df_am = df[df["AM"].str.contains(nama_am, case=False, na=False)]
    else:
        df_am = df.copy()

    # Abaikan pelanggan dengan saldo akhir <= 0
    df = df[df["Saldo Akhir"] > 0]
    df_am = df_am[df_am["Saldo Akhir"] > 0]

    return df, df_am, tanggal_label


def create_pie_chart(data, value_col, name_col, title, colors):
    """Buat pie chart Plotly dengan tema konsisten."""
    return px.pie(
        data,
        values=value_col,
        names=name_col,
        title=title,
        hole=0.3,
        color=name_col,
        color_discrete_map=colors
    )


def show_result(df, df_am, nama_am, segmen, tanggal):
    """Tampilkan hasil visualisasi perbandingan AM vs total."""
    if df_am.empty:
        st.info("Tidak ada data sesuai filter yang dipilih.")
        return

    total_pelanggan_am = df_am["IdNumber"].nunique()
    total_pelanggan_all = df["IdNumber"].nunique()
    total_saldo_am = df_am["Saldo Akhir"].sum()
    total_saldo_all = df["Saldo Akhir"].sum()

    col1, col2 = st.columns(2)

    # --- Kolom 1: Pelanggan
    with col1:
        st.metric("Total Pelanggan AM", total_pelanggan_am)
        st.metric("Total Pelanggan Hasil Filter", total_pelanggan_all)

        pie_pelanggan = pd.DataFrame({
            "Kategori": ["AM Dipilih", "Lainnya"],
            "Pelanggan": [total_pelanggan_am, total_pelanggan_all - total_pelanggan_am]
        })
        fig1 = create_pie_chart(
            pie_pelanggan, "Pelanggan", "Kategori",
            "Proporsi Jumlah Pelanggan AM dibanding Total",
            {"AM Dipilih": "#1f77b4", "Lainnya": "#d9e7fd"}
        )
        st.plotly_chart(fig1, use_container_width=True)

    # --- Kolom 2: Saldo
    with col2:
        st.metric("Total Saldo Akhir AM", to_rupiah(total_saldo_am))
        st.metric("Total Saldo Akhir Hasil Filter", to_rupiah(total_saldo_all))

        pie_saldo = pd.DataFrame({
            "Kategori": ["AM Dipilih", "Lainnya"],
            "Saldo Akhir": [total_saldo_am, total_saldo_all - total_saldo_am]
        })
        fig2 = create_pie_chart(
            pie_saldo, "Saldo Akhir", "Kategori",
            "Proporsi Saldo Akhir AM dibanding Total",
            {"AM Dipilih": "#d62728", "Lainnya": "#ff7f7f"}
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(df_am, use_container_width=True)


# ===============================
# Main App
# ===============================
nama_am = st.text_input("Masukkan Nama AM")
bulan, tahun, segmen = pilih_kategori()

if st.button("🔍 Cari Tanggungan"):
    st.write(f"Mencari tanggungan untuk **{nama_am or 'Semua AM'}** di **{segmen}** pada **{tahun}**...")
    df = load_and_clean_data()
    df_filtered, df_am, tanggal_label = filter_data(df, nama_am, bulan, tahun, segmen)
    show_result(df_filtered, df_am, nama_am, segmen, tanggal_label)
