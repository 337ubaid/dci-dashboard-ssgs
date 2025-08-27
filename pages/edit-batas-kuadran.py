import streamlit as st
import pandas as pd
from utils.google_utils import get_client
from utils.helpers import is_database_available
from sidebar import menu

st.set_page_config(page_title="Modifikasi Batas Kuadran", layout="centered")
st.title("📊 Modifikasi Batas Kuadran")


is_database_available()
menu()

st.warning("⚠️ Halaman ini masih dalam pengembangan. Sementara, batas kuadran ini.")


link_spreadsheet = st.session_state["database_gsheet_url"]
nama_worksheet = "Batas Kuadran"

client = get_client()
ws = client.open_by_url(link_spreadsheet).worksheet(nama_worksheet)
raw = ws.get_all_values()

# --- Helper: format & konversi angka ---
def to_number(series: pd.Series, allow_parentheses: bool = False) -> pd.Series:
    s = series.astype(str).str.strip()
    if allow_parentheses:
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    s = (
        s.str.replace("Rp", "", regex=False)
         .str.replace(".", "", regex=False)     
         .str.replace(",", ".", regex=False)    
         .str.replace(r"[^\d\.\-]", "", regex=True)
    )
    return pd.to_numeric(s, errors="coerce")

# === DEFINISI DIALOG KONFIRMASI ===
@st.dialog("Konfirmasi Upload Data")
def confirm_upload(df):
    st.dataframe(st.session_state["edited_df"])
    st.write("Apakah Anda yakin ingin memperbarui data?")
    
    if st.button("Ya, Upload!"):
        replace_batas_kuadran(st.session_state["edited_df"])
        st.session_state["editing"] = False
        st.success(" ✅ Data berhasil diperbarui!")
        st.rerun()

    if st.button("Batal"):
        st.session_state["editing"] = False
        st.rerun()

def replace_batas_kuadran(df: pd.DataFrame):
    ws.update([df.columns.values.tolist()] + df.values.tolist())

# ---------------- STATE ----------------
if "editing" not in st.session_state:
    st.session_state["editing"] = False
if "edited_df" not in st.session_state:
    st.session_state["edited_df"] = None

df = pd.DataFrame(raw[1:], columns=raw[0])

# ---------------- UI ----------------
if not st.session_state["editing"]:
    st.dataframe(df)
    if st.button("✏️ Edit Data"):
        st.session_state["editing"] = True
        st.rerun()

else:
    st.session_state["edited_df"] = st.data_editor(df)
    st.warning("Anda sedang Mengedit!")

    if st.button("✅ Yakin Ganti"):
        confirm_upload(df)
