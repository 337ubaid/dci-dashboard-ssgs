import streamlit as st
from sidebar import menu
from utils.services import get_client, get_raw_values, get_clean_database
from utils.format import cast_to_number


# ====== Konfigurasi Homepage ======
st.set_page_config(
    page_title="Dashboard Data Collection", layout="wide", page_icon="📈")
st.title("📈 Dashboard Data Collection")

st.markdown("### Selamat datang!")

# ====== Input link database dari user ======
link = st.text_input(
    "Masukkan link Spreadsheet Database:", 
    value=st.session_state.get("database_gsheet_url", ""),
    placeholder="https://docs.google.com/spreadsheets/..."
)
database_sheet_name = "DATABASE"

# ====== Tombol simpan link ======
if st.button("✅ Simpan Link", type="primary") and link:
    st.session_state["database_gsheet_url"] = link
    st.session_state["database_sheet_name"] = database_sheet_name
    st.session_state.pop("df_database", None)         # reset agar data di-reload
    st.session_state.pop("df_database_clean", None)   # reset hasil filter

# ====== Kalau link database sudah ada ======
if st.session_state.get("database_gsheet_url"):
    st.success("Link Google Sheet berhasil disimpan!")

    # Inisialisasi client Google Sheets
    if "client" not in st.session_state:
        st.session_state["client"] = get_client()

    # Inisialisasi database
    if "df_database" not in st.session_state:
        df = get_raw_values(
            st.session_state["database_gsheet_url"],
            st.session_state["database_sheet_name"]
        )
        df = cast_to_number(df)
        st.session_state["df_database"] = df

    # Get database raw dan bersih
    df_database = st.session_state["df_database"]
    df_database_clean = get_clean_database()

    # Ambil judul sheet
    sh_title = st.session_state["client"].open_by_url(
        st.session_state["database_gsheet_url"]
    ).title

    st.info(
        f"📄 Database aktif di GSheet: [**{sh_title}**]({st.session_state['database_gsheet_url']}) "
        f"dengan sheet: {st.session_state['database_sheet_name']}"
    )

    # Show sidebar menu
    menu()

else:
    st.warning("⚠️ Silakan masukkan link database dan simpan terlebih dahulu untuk mengakses Dashboard")

# Panduan penggunaan
st.write("""     
Gunakan menu di sidebar untuk:
1. **Visualisasi Kuadran**   
2. **Tanggungan tiap AM** 
3. **Leaderboard AM** 🚀 Coming Soon
4. **Collection Performance** 🚀 Coming Soon
5. **Saldo Akhir tiap Bulan** 🚀 Coming Soon
6. **Upload & Update Database**
7. **Edit Batas Kuadran**
""")

# Debug session_state
# st.dataframe(st.session_state["df_database_clean"])
# st.dataframe(st.session_state["df_database"])
# st.write("### Debug session_state")
# st.json(st.session_state)