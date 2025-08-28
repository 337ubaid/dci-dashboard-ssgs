import streamlit as st
import pandas as pd
import traceback
from sidebar import menu
from utils.services import is_database_available, get_raw_values, get_worksheet, confirm_update_database
from utils.ui import pilih_kategori
from utils.format import validasi_dataframe

st.set_page_config(page_title="Upload Data - Dashboard Data Collection", layout="wide", page_icon="📈")
st.title("📤 Upload Data ke Google Sheets")


# Pastikan link ada di session_state
is_database_available()
menu()

st.session_state["upload_gsheet_url"] = st.text_input("Masukkan link Spreadsheet sumber:")
st.session_state["upload_sheet_name"] = st.text_input("Masukkan nama Worksheet sumber:")

bulan_target, tahun_target, segmen_target = pilih_kategori()
tanggal_target = f"{bulan_target}/{tahun_target}"

if st.button("🔄 Proses Data"):
    try:
        # Ambil semua values

        df = get_raw_values(st.session_state["upload_gsheet_url"], st.session_state["upload_sheet_name"])

        df = validasi_dataframe(df, tanggal_target, segmen_target)
        
        st.session_state.df_upload = df

    except Exception as e:
        st.error(f"❌ Error membaca file: {e}")
        st.error(f"⚠️ Pastikan nama kolom di file sesuai template.")
        st.error(f"Error type: {type(e).__name__}")
        st.code(traceback.format_exc())


# === TAMPILKAN HASIL PROSES DATA ===
if "df_upload" in st.session_state:
    st.success(f"✅ {len(st.session_state.df_upload)} baris berhasil diproses dari [{st.session_state["upload_sheet_name"]}]({st.session_state["upload_gsheet_url"]})")
    st.dataframe(st.session_state.df_upload, use_container_width=True)

    if st.button("🚀 Upload Data ke Spreadsheet"):
        confirm_update_database(
            st.session_state.df_upload,
            tanggal_target,
            segmen_target,
        )