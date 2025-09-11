import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe

@st.cache_resource
def get_client():
    """
    Create and return an authenticated Google Sheets client using gspread.
    Return:
    -------
    gspread.Client
        An authorized gspread client instance connected with the given 
        service account credentials.
    """
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
    """
    Ambil nilai mentah dari worksheet Google Sheets.
    Param:
        - link_spreadsheet (str): URL Spreadsheet (default ambil dari st.session_state)
        - nama_worksheet (str): nama tab worksheet (default "DATABASE")
    Return:
        - DataFrame dengan data mentah dari worksheet
    """

    # ====== Ambil data dari Google Sheets ======
    worksheet_name = get_worksheet(link_spreadsheet, nama_worksheet)
    raw_all_values = worksheet_name.get_all_values()

    if not raw_all_values:
        st.warning(f"Sheet {nama_worksheet} kosong.")
        return pd.DataFrame()

    # DataFrame dengan header baris pertama
    df = pd.DataFrame(raw_all_values[1:], columns=raw_all_values[0])
    return df


def get_clean_database():
    """
    Ambil database bersih dari DataFrame yang sudah dibersihkan.
    Return:
        - DataFrame bersih (tanpa 0 dan minus)
    """
    st.session_state["df_database_clean"] = st.session_state["df_database"].query("`Saldo Akhir` > 0").reset_index(drop=True)
    return st.session_state["df_database_clean"]


def is_database_available():
    """
    Mengecek ketersediaan database Google Sheet dan menyiapkan data bersih di session_state.

    Fungsi ini akan:
    1. Mengecek apakah `df_database` sudah ada di `st.session_state`.
       - Jika belum ada, akan mengambil data mentah dari Google Sheet berdasarkan 
         `st.session_state["database_gsheet_url"]` dan opsional `database_sheet_name`.
    2. Menyimpan hasil query dataframe bersih (`df_database_clean`) hanya sekali,
       dengan filter `Saldo Akhir > 0`.
    3. Menampilkan pesan error atau warning melalui Streamlit jika data tidak bisa dimuat
       atau jika URL database belum tersedia.

    Returns
    -------
    bool
        True  : jika database tersedia dan sudah dimuat ke dalam `st.session_state`.
        False : jika database gagal dimuat atau link database belum diset.
    """
   
    # 🔹 Cek apakah URL database tersedia
    if "database_gsheet_url" not in st.session_state or not st.session_state["database_gsheet_url"]:
        st.warning("⚠️ Silakan masukkan link database di halaman Home dulu.")
        return False

    # 🔹 Cek apakah data sudah ada di session_state
    if "df_database" not in st.session_state or st.session_state["df_database"] is None:
        try:
            # Ambil data mentah dari Google Sheet
            st.session_state["df_database"] = get_raw_values(
                st.session_state["database_gsheet_url"],
                st.session_state.get("database_sheet_name", "DATABASE")
            )

            # Simpan dataframe bersih (hanya sekali)
            if "df_database_clean" not in st.session_state:
                st.session_state["df_database_clean"] = (
                    st.session_state["df_database"]
                    .query("`Saldo Akhir` > 0")
                    .reset_index(drop=True)
                )

        except Exception as e:
            st.error(f"Gagal memuat data: {e}")
            return False

    return True


def update_keterangan_top_kuadran(df_edited: pd.DataFrame) -> None:
    """
    Update kolom 'Keterangan' di Google Sheet sesuai hasil edit di Streamlit.

    Pencocokan dilakukan berdasarkan kombinasi:
    - IdNumber
    - Segmen
    - Bulan Tahun

    Parameters
    ----------
    client : gspread.Client
        Client gspread yang sudah terautentikasi.
    df_edited : pd.DataFrame
        DataFrame hasil edit dari Streamlit (harus memiliki kolom
        'IdNumber', 'Segmen', 'Bulan Tahun', dan 'Keterangan').

    Returns
    -------
    None

    Notes
    -----
    - Data awal sheet diambil dari `st.session_state["df_database"]`
      untuk memastikan konsistensi dengan session Streamlit.
    - Index +2 karena:
        * Index DataFrame mulai dari 0
        * Baris pertama di Google Sheet adalah header
    - Hanya kolom 'Keterangan' yang diperbarui.
    """
    # Ambil worksheet dan dataframe sheet dari session
    ws = get_worksheet(
        st.session_state["database_gsheet_url"],
        st.session_state["database_sheet_name"]
    )
    df_sheet = st.session_state["df_database"]

    if "Keterangan" not in df_sheet.columns:
        st.error("Kolom 'Keterangan' tidak ditemukan di database sheet.")
        return

    # Loop hasil edit
    for _, row in df_edited.iterrows():
        mask = (
            (df_sheet["IdNumber"] == row["IdNumber"]) &
            (df_sheet["Segmen"] == row["Segmen"]) &
            (df_sheet["Bulan Tahun"] == row["Bulan Tahun"])
        )

        if mask.any():
            idx = df_sheet[mask].index[0]  # ambil index pertama yang cocok
            cell_row = idx + 2  # +2 karena index 0-based & baris header
            col_ket = df_sheet.columns.get_loc("Keterangan") + 1  # +1 karena gspread kolom 1-based

            ws.update_cell(cell_row, col_ket, row["Keterangan"])


def update_database(bulan, segmen, df_baru):
    """
    Ganti data di worksheet berdasarkan Bulan/Tahun & Segmen.
    - Hapus baris lama secara batch
    - Upload data baru
    - Sortir ulang
    """
    worksheet = get_worksheet()
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


@st.dialog("Konfirmasi Upload Data")
def confirm_update_database(df_upload, tanggal_target, segmen_target):
    st.write(
        f"⚠️ Anda akan mengunggah **{len(df_upload)} baris data** dari [{st.session_state['upload_sheet_name']}]({st.session_state['upload_gsheet_url']})"
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
        st.switch_page("home.py") 

    if st.button("❌ Batal", use_container_width=True):
        st.info("Upload dibatalkan.")
        st.rerun()  # refresh agar dialog tertutup