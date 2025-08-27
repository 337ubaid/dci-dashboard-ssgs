import streamlit as st
from sidebar import menu
from utils.helpers import uppercase
from utils.google_utils import get_client, get_raw_values
from utils.validation import cast_numeric_cols

# Konfigurasi halaman utama
st.set_page_config(
    page_title="Dashboard Data Collection",
    layout="wide"
)

# Judul & Isi Homepage
st.title("📈 Dashboard Data Collection")
st.markdown("### Selamat datang!")

# Input link database dari user
link = st.text_input(
    "Masukkan link Spreadsheet Database:", 
    value=st.session_state.get("database_gsheet_url", ""),
    placeholder="https://docs.google.com/spreadsheets/..."
)
database_sheet_name = uppercase("DATABASE")

# Tombol simpan link
if st.button("✅ Simpan Link") and link:
    st.session_state["database_gsheet_url"] = link
    st.session_state["database_sheet_name"] = database_sheet_name
    st.session_state.pop("df_database", None)         # reset agar data di-reload
    st.session_state.pop("df_database_clean", None)   # reset hasil filter

# Kalau link database sudah ada
if st.session_state.get("database_gsheet_url"):
    st.success("Link spreadsheet berhasil disimpan!")

    # Client hanya dibuat sekali
    if "client" not in st.session_state:
        st.session_state["client"] = get_client()

    # Ambil data hanya sekali
    if "df_database" not in st.session_state:
        df = get_raw_values(
            st.session_state["database_gsheet_url"],
            st.session_state["database_sheet_name"]
        )
        df = cast_numeric_cols(df)
        st.session_state["df_database"] = df

    df_database = st.session_state["df_database"]

    # Buat dataframe bersih hanya sekali
    if "df_database_clean" not in st.session_state:
        st.session_state["df_database_clean"] = df_database.query("`Saldo Akhir` > 0").reset_index(drop=True)

    df_database_clean = st.session_state["df_database_clean"]
    # st.dataframe(df_database_clean)

    # Ambil judul sheet (sekali saja untuk ditampilkan)
    sh_title = st.session_state["client"].open_by_url(
        st.session_state["database_gsheet_url"]
    ).title

    st.info(
        f"📄 Database aktif di GSheet: [**{sh_title}**]({st.session_state['database_gsheet_url']}) "
        f"dengan sheet: {st.session_state['database_sheet_name']}"
    )

    # Sidebar menu
    menu()

    # # Debugging & monitoring
    # st.write("### Tipe Data Kolom")
    # st.dataframe(df_database.dtypes.astype(str).reset_index().rename(
    #     columns={"index": "Kolom", 0: "Tipe Data"}
    # ))

    # st.write("### Preview Data Bersih")
    # st.dataframe(df_database_clean)

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

# Debug session_state (opsional, bisa dimatikan)
st.write("### Debug session_state")
st.json(st.session_state)
