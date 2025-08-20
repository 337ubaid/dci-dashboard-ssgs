import streamlit as st

# Set konfigurasi halaman utama
st.set_page_config(
    page_title="Dashboard Data Collection",
    layout="wide"
)

st.title("📈 Dashboard Data Collection")
st.write("""
Selamat datang!  
Gunakan menu di sidebar untuk:
1. **Upload Data** dari Spreadsheet ke Spreadsheet  
2. **Visualisasi Data**
3. **Tanggungan per AM** 🚀 Coming Soon
""")

# Input link database dari user
link = st.text_input("Masukkan link Spreadsheet Database:", 
                     value=st.session_state.get("spreadsheet_url", ""))
nama_worksheet_asal = st.text_input("Masukkan nama Worksheet sumber:", 
                                     value=st.session_state.get("worksheet_name", ""))

# Simpan ke session_state
if st.button("✅ Simpan Link"):
    st.session_state["spreadsheet_database_url"] = link
    st.session_state["worksheet_database_name"] = nama_worksheet_asal
    st.success("Link spreadsheet dan nama worksheet berhasil disimpan!")

# Tampilkan link aktif
if "spreadsheet_database_url" in st.session_state and st.session_state["spreadsheet_database_url"]:
    st.info(f"Database aktif: {st.session_state['spreadsheet_database_url']} di sheet {st.session_state['worksheet_database_name']}")
else:
    st.warning("Belum ada link database yang disimpan.")