import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def get_worksheet(link_spreadsheet=None, nama_worksheet="DATABASE"):
    """
    Ambil worksheet tertentu dari Google Spreadsheet.
    Param:
        - link_spreadsheet (str): URL Spreadsheet (default ambil dari st.session_state)
        - nama_worksheet (str): nama tab worksheet (default "DATABASE")
    Return:
        - worksheet object
    """
    if link_spreadsheet is None:
        link_spreadsheet = st.session_state.get("database_gsheet_url", "")
    if nama_worksheet is None:
        nama_worksheet = st.session_state.get("database_sheet_name", "DATABASE")

    if not link_spreadsheet:
        raise ValueError("❌ Link spreadsheet tidak ditemukan.")
    
    client = get_client()
    return client.open_by_url(link_spreadsheet).worksheet(nama_worksheet)


def get_raw_values(link_spreadsheet=None, nama_worksheet="DATABASE"):
    
    if link_spreadsheet is None:
        link_spreadsheet = st.session_state.get("database_gsheet_url", "")
    if nama_worksheet is None:
        nama_worksheet = st.session_state.get("database_sheet_name", "DATABASE")

    # ====== Ambil data dari Google Sheets ======
    ws = get_worksheet(link_spreadsheet, nama_worksheet)
    raw = ws.get_all_values()

    if not raw:
        st.warning(f"Sheet {nama_worksheet} kosong.")
        return pd.DataFrame()

    # DataFrame dengan header baris pertama
    df = pd.DataFrame(raw[1:], columns=raw[0])
    return df

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


def update_google_sheet(worksheet, df_update: pd.DataFrame):
    """
    worksheet: gspread worksheet object
    df_update: dataframe hasil edit
    """
    sheet_values = worksheet.get_all_records()
    df_sheet = pd.DataFrame(sheet_values)

    # update lokal dulu
    df_sheet = update_dataframe_kuadran_top3(df_sheet, df_update)

    # clear lalu replace (cara aman)
    worksheet.clear()
    worksheet.update([df_sheet.columns.values.tolist()] + df_sheet.values.tolist())
