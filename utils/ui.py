
import streamlit as st
from datetime import datetime
from utils.services import update_database

def pilih_kategori():
    """
    Komponen UI untuk memilih Segmen, Bulan, dan Tahun.

    Fungsi ini menampilkan 3 buah dropdown (Streamlit selectbox):
    1. **Segmen**: pilihan segmen bisnis (misalnya DGS, DPS, DSS, RBS, atau semua).
    2. **Bulan** : pilihan bulan (Januari–Desember atau "-Semua-").
    3. **Tahun** : pilihan tahun (tahun sekarang dan tahun sebelumnya).

    Returns
    -------
    tuple
        (bulan_target: int, tahun_target: int, segmen_target: str)
        - `bulan_target` : nomor bulan (1–12) atau `0` untuk "-Semua-"
        - `tahun_target` : tahun dalam format integer (mis. 2025)
        - `segmen_target`: string segmen yang dipilih
    """
    col1, col2, col3 = st.columns(3)

    # Pilihan segmen
    segmen_target = col1.selectbox(
        "Pilih Segmen",
        ["-Semua-", "DGS", "DPS", "DSS", "RBS"]
    )

    # Mapping bulan
    bulan_dict = {
        0: "-Semua-",
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    # Pilihan bulan
    bulan_target = col2.selectbox(
        "Pilih Bulan",
        list(bulan_dict.keys()),
        format_func=lambda x: bulan_dict[x]
    )

    # Pilihan tahun (hanya tahun sekarang & tahun sebelumnya)
    tahun_sekarang = datetime.now().year
    tahun_target = col3.selectbox(
        "Pilih Tahun",
        [tahun_sekarang, tahun_sekarang - 1]
    )

    return bulan_target, tahun_target, segmen_target

def confirm_upload_dialog(df_upload, tanggal_target, segmen_target):
    st.write(
        f"⚠️ Anda akan mengunggah **{len(df_upload)} baris data** "
        f"untuk segmen **{segmen_target}** di bulan **{tanggal_target}**."
    )
    st.write("Apakah Anda yakin ingin melanjutkan?")
    
    # Tombol ditumpuk (1 kolom penuh)
    if st.button("✅ Ya, Upload Sekarang", use_container_width=True):
        update_database(
             tanggal_target, segmen_target, df_upload
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