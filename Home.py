import streamlit as st
from sidebar import menu
from utils.helpers import uppercase

# Set konfigurasi halaman utama
st.set_page_config(
    page_title="Dashboard Data Collection",
    layout="wide"
)

# Judul & Isi Homepage
st.title("📈 Dashboard Data Collection")
st.write("""
Selamat datang!  
Gunakan menu di sidebar untuk:
1. **Visualisasi Kuadran**   
2. **Tanggungan tiap AM** 
3. **Leaderboard AM** 🚀 Coming Soon
4. **Collection Performance** 🚀 Coming Soon
5. **Saldo Akhir tiap Bulan** 🚀 Coming Soon
6. **Upload & Update Database**
7. **Edit Batas Kuadran**
""")

# Input link database dari user
link = st.text_input("Masukkan link Spreadsheet Database:", 
                     value=st.session_state.get("spreadsheet_url", ""))
nama_worksheet_asal = uppercase("DATABASE")

# Simpan ke session_state
if st.button("✅ Simpan Link"):
    st.session_state["spreadsheet_database_url"] = link
    st.session_state["worksheet_database_name"] = nama_worksheet_asal
    st.success("Link spreadsheet dan nama worksheet berhasil disimpan!")

# Tampilkan link aktif
if "spreadsheet_database_url" in st.session_state and st.session_state["spreadsheet_database_url"]:
    st.info(f"Database aktif: {st.session_state['spreadsheet_database_url']} di sheet {st.session_state['worksheet_database_name']}")
    
    # Set sidebar
    menu()
else:
    st.warning("Silakan masukkan link database dan simpan terlebih dahulu untuk mengakses Dashboard")

