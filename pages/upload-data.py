import streamlit as st
import traceback
import datetime
from utils.services import is_database_available, get_raw_values, confirm_update_database
from utils.ui import pilih_kategori
from utils.format import validasi_data_upload

st.set_page_config(page_title="Update CYC - Dashboard Data Collection", layout="wide", page_icon="📈")
st.title("📤 Update Database CYC ke Google Sheets")

# Pastikan link ada di session_state
# ====== Ambil data dari Google Sheets ======
if not is_database_available():
    st.page_link("home.py", label="Home", icon="🏠")
    st.stop()

from sidebar import menu
menu()

st.session_state["upload_gsheet_url"] = st.text_input("Masukkan link Spreadsheet CYC:")
st.session_state["upload_sheet_name"] = st.text_input("Masukkan nama Worksheet CYC:")

bulan_target, tahun_target, segmen_target = pilih_kategori()
tanggal_target = f"{bulan_target}/{tahun_target}"

if st.button("🔄 Proses Data"):
    try:
        # Ambil semua values

        df = get_raw_values(st.session_state["upload_gsheet_url"], st.session_state["upload_sheet_name"])

        st.write("### Data Mentah")
        st.dataframe(df, use_container_width=True)

        df = validasi_data_upload(df, tanggal_target, segmen_target)
        st.write("### Data Setelah Validasi")
        st.dataframe(df, use_container_width=True)
    
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


st.write("---")

st.write(datetime.datetime.now())