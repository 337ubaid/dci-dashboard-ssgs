import streamlit as st
import pandas as pd
from utils.helpers import pilih_kategori
from utils.google_utils import get_client
import plotly.express as px


st.set_page_config(page_title="Tanggungan per AM", layout="wide")

st.title("👤 Tanggungan per AM")

nama = st.text_input("Masukkan Nama AM")
bulan_target, tahun_target, segmen_target = pilih_kategori()
tanggal_target = f"{bulan_target}/{tahun_target}"

# --- Helper: format & konversi angka ---
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

def rupiah(n: float | int) -> str:
    try:
        x = float(n)
    except Exception:
        return "Rp 0"
    # Format ribuan pakai titik
    s = f"{int(round(x)):,}".replace(",", ".")
    return f"Rp {s}"

def search_AM(nama, tanggal_target, segmen_target):
    # ====== Ambil data dari Google Sheets ======
    link_spreadsheet = st.session_state["spreadsheet_database_url"]
    nama_worksheet = st.session_state["worksheet_database_name"]

    client = get_client()
    ws = client.open_by_url(link_spreadsheet).worksheet(nama_worksheet)
    raw = ws.get_all_values()

    # DataFrame dengan header baris pertama
    df = pd.DataFrame(raw[1:], columns=raw[0])

    # Konversi numeric
    aging_cols = ["0-3 Bulan","4-6 Bulan","7-12 Bulan","13-24 Bulan","> 24 Bulan"]
    df[aging_cols] = df[aging_cols].apply(lambda s: to_number(s, allow_parentheses=True))
    df["Saldo Akhir"] = to_number(df["Saldo Akhir"], allow_parentheses=False)
    df["Lama Tunggakan"] = to_number(df["Lama Tunggakan"], allow_parentheses=False)
    df["Kuadran"] = pd.to_numeric(df["Kuadran"], errors="coerce").astype("Int64")

    # --- Filter global untuk segmen dan tanggal ---
    df_filtered = df.copy()

    if segmen_target != "-Semua-":
        df_filtered = df_filtered[df_filtered["Segmen"] == segmen_target]

    if bulan_target != 0:  # filter bulan tertentu
        tanggal_target = f"{bulan_target}/{tahun_target}"
        df_filtered = df_filtered[df_filtered["Bulan Tahun"] == tanggal_target]
    else:  # semua bulan, tapi tahun sesuai
        df_filtered = df_filtered[df_filtered["Bulan Tahun"].str.split("/").str[1] == str(tahun_target)]
        tanggal_target = f"Semua Bulan/{tahun_target}"

     # Filter nama AM
    df_am = df_filtered[df_filtered["AM"].str.contains(nama, case=False, na=False)]

    # # df_filtered = df_filtered[df_filtered["AM"].str.contains(nama, case=False, na=False)]
    # df_filtered = df_filtered[df_filtered["Segmen"] == segmen_target]
    # df_filtered = df_filtered[df_filtered["Bulan Tahun"] == tanggal_target]
    
    # Abaikan pelanggan dengan saldo akhir <= 0
    df_am = df_am[df_am["Saldo Akhir"].astype(float) > 0]
    df_filtered = df_filtered[df_filtered["Saldo Akhir"].astype(float) > 0]
    
    # --- Show Result ---
    st.subheader("📊 Hasil Pencarian")
    st.write(f"Jumlah Pelanggan: **{len(df_am)}**")


    if not df_am.empty:
        # Pastikan numeric
        df_am["Saldo Akhir"] = pd.to_numeric(df_am["Saldo Akhir"], errors="coerce").fillna(0)
        df_filtered["Saldo Akhir"] = pd.to_numeric(df_filtered["Saldo Akhir"], errors="coerce").fillna(0)

        total_pelanggan_am = df_am["IdNumber"].nunique()
        total_pelanggan_all = df_filtered["IdNumber"].nunique()

        total_saldo_am = df_am["Saldo Akhir"].sum()
        total_saldo_all = df_filtered["Saldo Akhir"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Pelanggan (AM)", total_pelanggan_am)
            st.metric("Total Pelanggan (Filter)", total_pelanggan_all)

            # Chart perbandingan pelanggan AM vs total
            pie_pelanggan = pd.DataFrame({
                "Kategori": ["AM Dipilih", "Lainnya"],
                "Pelanggan": [total_pelanggan_am, total_pelanggan_all - total_pelanggan_am]
            })

            fig1 = px.pie(
                pie_pelanggan,
                values="Pelanggan",
                names="Kategori",
                title="Proporsi Jumlah Pelanggan AM dibanding Total",
                hole=0.3,
                color="Kategori",
                color_discrete_map={"AM Dipilih": "#1f77b4", "Lainnya": "#d9e7fd"}
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.metric("Total Saldo Akhir (AM)", rupiah(total_saldo_am))
            st.metric("Total Saldo Akhir (Filter)", rupiah(total_saldo_all))

            # Chart perbandingan saldo AM vs total
            pie_saldo = pd.DataFrame({
                "Kategori": ["AM Dipilih", "Lainnya"],
                "Saldo Akhir": [total_saldo_am, total_saldo_all - total_saldo_am]
            })

            fig2 = px.pie(
                pie_saldo,
                values="Saldo Akhir",
                names="Kategori",
                title="Proporsi Saldo Akhir AM dibanding Total",
                hole=0.3,
                color="Kategori",
                color_discrete_map={"AM Dipilih": "#d62728", "Lainnya": "#ff7f7f"}
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df_am, use_container_width=True)
    else:
        st.info("Tidak ada data sesuai filter yang dipilih.")


if st.button("🔍 Cari Tanggungan"):
    # Logika untuk mencari tanggungan per AM
    st.write(f"Mencari tanggungan untuk **{nama}** di **{segmen_target}** pada **{tanggal_target}**...")
    search_AM(nama, tanggal_target, segmen_target)