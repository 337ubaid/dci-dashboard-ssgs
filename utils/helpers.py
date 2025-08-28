import streamlit as st
import pandas as pd
from datetime import datetime
from utils.google_utils import get_raw_values, get_worksheet

def get_clean_database():
    st.session_state["df_database_clean"] = st.session_state["df_database"].query("`Saldo Akhir` > 0").reset_index(drop=True)
    return st.session_state["df_database_clean"]

def update_dataframe_kuadran_top_gsheet(client, df_edited: pd.DataFrame):
    """
    Update kolom 'Keterangan' di Google Sheet sesuai hasil edit di Streamlit.
    Match berdasarkan IdNumber, Segmen, Bulan Tahun.
    """

    # ambil semua data dari sheet jadi dataframe
    ws = get_worksheet(st.session_state["database_gsheet_url"], st.session_state["database_sheet_name"])
    df_sheet = st.session_state["df_database"]

    for _, row in df_edited.iterrows():
        mask = (
            (df_sheet["IdNumber"] == row["IdNumber"]) &
            (df_sheet["Segmen"] == row["Segmen"]) &
            (df_sheet["Bulan Tahun"] == row["Bulan Tahun"])
        )
        if mask.any():
            idx = df_sheet[mask].index[0]  # ambil index pertama
            cell_row = idx + 2  # +2 karena index mulai dari 0 dan baris 1 header
            col_ket = df_sheet.columns.get_loc("Keterangan") + 1
            ws.update_cell(cell_row, col_ket, row["Keterangan"])


def is_database_available():
    # kalau df_database belum ada, ambil dari Google Sheet
    if "df_database" not in st.session_state or st.session_state["df_database"] is None:
        try:
            st.session_state["df_database"] = get_raw_values(
                st.session_state["database_gsheet_url"],
                st.session_state.get("database_sheet_name", "DATABASE")
            )

            # Buat dataframe bersih hanya sekali
            if "df_database_clean" not in st.session_state:
                st.session_state["df_database_clean"] = st.session_state["df_database"].query("`Saldo Akhir` > 0").reset_index(drop=True)

            df_database_clean = st.session_state["df_database_clean"]
        except Exception as e:
            st.error(f"Gagal memuat data: {e}")
            return False
    
    if "database_gsheet_url" not in st.session_state or not st.session_state["database_gsheet_url"]:
        st.warning("⚠️ Silakan masukkan link database di halaman Home dulu.")
        return False

    return True

def pilih_kategori():
    """
    UI helper untuk memilih bulan, tahun, dan segmen.
    Return:
        tuple (str, str): ("Bulan/Tahun", "Segmen")
    """

    col1, col2, col3 = st.columns(3)

    segmen_target = col1.selectbox("Pilih Segmen", ["-Semua-", "DGS", "DPS", "DSS", "RBS"])
    
    bulan_dict = {0:"-Semua-",
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
        5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
        9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }

    bulan_target = col2.selectbox(
        "Pilih Bulan", 
        list(bulan_dict.keys()), 
        format_func=lambda x: bulan_dict[x]
    )

    tahun_sekarang = datetime.now().year
    tahun_target = col3.selectbox("Pilih Tahun", [tahun_sekarang, tahun_sekarang - 1])


    return bulan_target, tahun_target, segmen_target

def uppercase(string: str) -> str:
    return string.upper() if string else ""

def to_rupiah(n: float | int) -> str:
    try:
        x = float(n)
    except Exception:
        return "Rp 0"
    # Format ribuan pakai titik
    s = f"{int(round(x)):,}".replace(",", ".")
    return f"Rp {s}"


