import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from config import SCOPES

def get_raw_values(nama_worksheet="DATABASE"):
    # ====== Ambil data dari Google Sheets ======
    link_spreadsheet = st.session_state["spreadsheet_database_url"]
    nama_worksheet = nama_worksheet

    client = get_client()
    ws = client.open_by_url(link_spreadsheet).worksheet(nama_worksheet)
    raw = ws.get_all_values()

    # DataFrame dengan header baris pertama
    df = pd.DataFrame(raw[1:], columns=raw[0])
    # df = df[df["Saldo Akhir"].astype(float) > 0]
    return df

def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def replace_bulan_segmen(worksheet, bulan, segmen, df_baru):
    """
    Ganti data di worksheet berdasarkan Bulan/Tahun & Segmen.
    - Hapus baris lama secara batch
    - Upload data baru
    - Sortir ulang
    """
    all_values = worksheet.get_all_values()

    if not all_values:
        st.warning("Sheet masih kosong. Data baru akan ditambahkan.")
        last_row = 1
    else:
        col_bulan = [row[0] for row in all_values]
        col_segmen = [row[1] for row in all_values]

        rows_to_delete = [
            i+1 for i, (bulan_val, segmen_val) in enumerate(zip(col_bulan, col_segmen))
            if bulan_val == bulan and segmen_val == segmen
        ]

        if rows_to_delete:
            start, end = min(rows_to_delete), max(rows_to_delete)
            worksheet.delete_rows(start, end)
            st.info(f"🗑️ {len(rows_to_delete)} baris dihapus untuk {segmen} - {bulan}.")
        else:
            st.info(f"⚠️ Tidak ada data untuk {segmen} - {bulan}.")

        last_row = len(worksheet.get_all_values()) + 1

    set_with_dataframe(worksheet, df_baru, row=last_row, include_column_header=False)
    st.success(f"✅ {len(df_baru)} baris baru ditambahkan.")

    worksheet.sort((1, "des"), (2, "asc"), (11, "des"))
    st.info("📌 Data disortir berdasarkan Tanggal & Segmen.")
