import streamlit as st

def menu():
    """
    Fungsi untuk menampilkan menu di sidebar.
    """

    with st.sidebar:
        st.title("Menu")
        st.page_link("home.py", label="Home", icon=":material/home:")
        st.subheader("Visualisasi Data")
        st.page_link("pages/visualisasi-kuadran.py", label="Kuadran", icon="🍀")
        st.page_link("pages/tanggungan-tiap-am.py", label="Tanggungan tiap AM", icon="👤")
        st.page_link("pages/leaderboard-am.py", label="Leaderboard AM", icon="🏆")
        st.page_link("pages/collection-performance.py", label="Collection Performance", icon="📈")
        # st.page_link("pages/saldo_akhir_per_bulan.py", label="Saldo Akhir per Bulan")
        st.subheader("Modifikasi Database")
        st.page_link("pages/upload-data.py", label="Upload CYC", icon="📤")
        st.page_link("pages/edit-batas-kuadran.py", label="Edit Batas Kuadran", icon="✏️")
