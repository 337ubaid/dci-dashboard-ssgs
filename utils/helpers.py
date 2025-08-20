import streamlit as st
from datetime import datetime

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
