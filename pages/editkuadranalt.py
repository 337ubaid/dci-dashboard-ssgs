import streamlit as st
import pandas as pd
from utils.google_utils import get_client
from utils.helpers import is_database_available, pilih_kategori, to_rupiah, update_dataframe_kuadran_top_gsheet
from sidebar import menu

# ==============================
# Konfigurasi halaman
# ==============================
st.set_page_config(page_title="Tanggungan tiap AM", layout="wide")
st.title("📊 Visualisasi Kuadran")
menu()

# ==============================
# INIT SESSION STATE
# ==============================
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "edited_top3_all" not in st.session_state:
    st.session_state.edited_top3_all = {}
if "df_database_clean" not in st.session_state:
    # contoh dummy kalau belum ada data
    st.session_state.df_database_clean = pd.DataFrame(
        columns=["IdNumber", "Bulan Tahun", "Segmen", "BP Name", "Saldo Akhir", "Keterangan"]
    )

# ==============================
# FUNGSI RENDER KUADRAN
# ==============================
def render_kuadran(dfq: pd.DataFrame, kuadran_num: int, judul: str):
    with st.container(border=True):
        st.markdown(f" #### {judul}")

        if dfq.empty:
            st.info("Tidak ada data di kuadran ini.")
            return

        jml = len(dfq)
        total_nom = dfq["Saldo Akhir"].sum(skipna=True)

        st.markdown(f"- Jumlah pelanggan: **{jml}**")
        st.markdown(f"- Total tunggakan: **{to_rupiah(total_nom)}**")

        top3 = dfq.sort_values("Saldo Akhir", ascending=False).head(3)

        if st.session_state.edit_mode:
            edited_top3 = st.data_editor(
                top3[["IdNumber", "Bulan Tahun", "Segmen", "BP Name", "Saldo Akhir", "Keterangan"]],
                hide_index=True,
                use_container_width=True,
                disabled=["IdNumber", "Bulan Tahun", "Segmen", "BP Name", "Saldo Akhir"],
                key=f"editor_{kuadran_num}"
            )
            # simpan hasil edit sementara ke session
            st.session_state.edited_top3_all[kuadran_num] = edited_top3
        else:
            st.dataframe(
                top3[["IdNumber", "Bulan Tahun", "Segmen", "BP Name", "Saldo Akhir", "Keterangan"]],
                hide_index=True,
                use_container_width=True
            )

# ==============================
# TOMBOL GLOBAL EDIT / SIMPAN
# ==============================
col_edit, col_save = st.columns([1, 1])

if not st.session_state.edit_mode:
    if col_edit.button("✏️ Edit Top 3 Kuadran", use_container_width=True):
        st.session_state.edit_mode = True
else:
    st.warning("⚠️ Sedang dalam mode edit. Pastikan tekan SIMPAN setelah selesai.")

    if col_save.button("💾 Simpan Semua Perubahan", use_container_width=True):
        try:
            # update session_state df pusat
            for kuadran_num, df_ed in st.session_state.edited_top3_all.items():
                for _, row in df_ed.iterrows():
                    mask = (
                        (st.session_state["df_database_clean"]["IdNumber"] == row["IdNumber"]) &
                        (st.session_state["df_database_clean"]["Segmen"] == row["Segmen"]) &
                        (st.session_state["df_database_clean"]["Bulan Tahun"] == row["Bulan Tahun"])
                    )
                    st.session_state["df_database_clean"].loc[mask, "Keterangan"] = row["Keterangan"]

            # update ke spreadsheet
            client = st.session_state["client"] if "client" in st.session_state else get_client()
            for _, df_ed in st.session_state.edited_top3_all.items():
                update_dataframe_kuadran_top_gsheet(client=client, df_edited=df_ed)

            st.toast("✅ Semua perubahan tersimpan di session & Google Sheet", icon="✅")
            st.session_state.edit_mode = False  # keluar dari mode edit
            st.session_state.edited_top3_all = {}
        except Exception as e:
            st.error(f"Gagal update ke spreadsheet: {e}")

# ==============================
# RENDER CONTOH KUADRAN
# ==============================
df = st.session_state.df_database_clean

col1, col2 = st.columns(2)
with col1:
    render_kuadran(df, 1, "Kuadran 1 - High Value, Long Tenor")
    render_kuadran(df, 2, "Kuadran 2 - Low Value, Long Tenor")
with col2:
    render_kuadran(df, 3, "Kuadran 3 - High Value, Short Tenor")
    render_kuadran(df, 4, "Kuadran 4 - Low Value, Short Tenor")
