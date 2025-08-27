import streamlit as st
import pandas as pd
import traceback
from utils.helpers import is_database_available, pilih_kategori
from utils.validation import validasi_data
from utils.google_utils import get_client, replace_bulan_segmen
from sidebar import menu

st.set_page_config(page_title="Upload Data", layout="wide", page_icon="📤")
st.title("📤 Upload Data ke Google Sheets")


# Pastikan link ada di session_state
is_database_available()
menu()

link_spreadsheet = st.text_input("Masukkan link Spreadsheet sumber:")
nama_worksheet_asal = st.text_input("Masukkan nama Worksheet sumber:")

client = get_client()
workbook_tujuan = client.open_by_url(st.session_state["database_gsheet_url"])
worksheet_tujuan = workbook_tujuan.worksheet(st.session_state["database_sheet_name"])
workbook_asal = client.open_by_url(link_spreadsheet) if link_spreadsheet else None

bulan_target, tahun_target, segmen_target = pilih_kategori()
tanggal_target = f"{bulan_target}/{tahun_target}"

if st.button("🔄 Proses Data"):
    try:
        # Ambil semua values
        values = workbook_asal.worksheet(nama_worksheet_asal).get_all_values()

        # Baris pertama = header
        headers = values[0]

        # Cek duplikat dan rename
        seen = {}
        unique_headers = []
        for h in headers:
            if h in seen:
                seen[h] += 1
                unique_headers.append(f"{h}_{seen[h]}")  # tambahkan suffix
            else:
                seen[h] = 0
                unique_headers.append(h)

        # Sisa baris = data
        rows = values[1:]

        # Masukkan ke DataFrame
        df = pd.DataFrame(rows, columns=unique_headers)

        # df = st.dataframe(df, use_container_width=True)

        df = validasi_data(df, tanggal_target, segmen_target)
        st.session_state.df_upload = df

    except Exception as e:
        st.error(f"❌ Error membaca file: {e}")
        st.error(f"⚠️ Pastikan nama kolom di file sesuai template.")
        st.error(f"Error type: {type(e).__name__}")
        st.code(traceback.format_exc())


# === DEFINISI DIALOG KONFIRMASI ===
@st.dialog("Konfirmasi Upload Data")
def confirm_upload_dialog(df_upload, worksheet_tujuan, tanggal_target, segmen_target):
    st.write(
        f"⚠️ Anda akan mengunggah **{len(df_upload)} baris data** "
        f"untuk segmen **{segmen_target}** di bulan **{tanggal_target}**."
    )
    st.write("Apakah Anda yakin ingin melanjutkan?")
    
    # Tombol ditumpuk (1 kolom penuh)
    if st.button("✅ Ya, Upload Sekarang", use_container_width=True):
        replace_bulan_segmen(
            worksheet_tujuan, tanggal_target, segmen_target, df_upload
        )
        st.success("✅ Data berhasil diunggah ke Google Sheets!")

        # Hapus dataframe dari session_state biar bersih
        if "df_upload" in st.session_state:
            del st.session_state["df_upload"]
            
        # Redirect ke halaman utama (Home.py)
        st.switch_page("Home.py") 

    if st.button("❌ Batal", use_container_width=True):
        st.info("Upload dibatalkan.")
        st.rerun()  # refresh agar dialog tertutup


# === TAMPILKAN HASIL PROSES DATA ===
if "df_upload" in st.session_state:
    st.success(f"✅ {len(st.session_state.df_upload)} baris berhasil diproses.")
    st.dataframe(st.session_state.df_upload, use_container_width=True)

    if st.button("🚀 Upload Data ke Spreadsheet"):
        confirm_upload_dialog(
            st.session_state.df_upload,
            worksheet_tujuan,
            tanggal_target,
            segmen_target,
        )