import streamlit as st
import pandas as pd
import plotly.express as px
from utils.services import is_database_available, get_clean_database, update_keterangan_top_kuadran
from utils.format import to_rupiah
from utils.ui import pilih_kategori


# ====== Konfigurasi Halaman Kuadran ======
st.set_page_config(page_title="Kuadran - Dashboard Data Collection", layout="wide", page_icon="📈")
st.title("🍀 Kuadran")

# ====== Ambil data dari Google Sheets ======
if not is_database_available():
    st.page_link("home.py", label="Home", icon="🏠")
    st.stop()

from sidebar import menu
menu()

df = get_clean_database()

# ====== Filter ====== 
bulan_target, tahun_target, segmen_target = pilih_kategori()

df_filtered = df.copy()

# Filter segmen (kecuali user pilih Semua Segmen)
if segmen_target != "-Semua-":
    df_filtered = df_filtered[df_filtered["Segmen"] == segmen_target]
else:
    segmen_target = "Semua Segmen"

# Filter bulan/tahun
if bulan_target != 0:  # user pilih bulan tertentu
    tanggal_target = f"{bulan_target}/{tahun_target}"
    df_filtered = df_filtered[df_filtered["Bulan Tahun"] == tanggal_target]
else:  # user pilih "semua bulan"
    # pastikan format "Bulan Tahun" -> ambil bagian setelah "/"
    df_filtered = df_filtered[df_filtered["Bulan Tahun"].str.split("/").str[1] == str(tahun_target)]
    tanggal_target = f"Semua Bulan {tahun_target}"


# Abaikan pelanggan dengan saldo akhir <= 0
df_filtered = df_filtered[df_filtered["Saldo Akhir"].astype(float) > 0]

# Cek Filtering
# st.dataframe(df_filtered)

# ====== Summary Total ======
total_pelanggan = len(df_filtered)
total_tunggakan = df_filtered["Saldo Akhir"].sum(skipna=True)

# Urutan kuadran
order = ["Kuadran 1", "Kuadran 2", "Kuadran 3", "Kuadran 4"]
# Definisikan warna tetap per Kuadran
kuadran_colors = {
    "Kuadran 1": "#89C4E9",
    "Kuadran 2": "#FF727C",  
    "Kuadran 3": "#00527E",  
    "Kuadran 4": "#AD1F2B",  
# E63946 RED
}

st.divider()
st.markdown(f"<h2 style='text-align: center; font-weight: bold;'>Ringkasan {segmen_target} — {tanggal_target}</h2>", unsafe_allow_html=True)
m1, m2 = st.columns(2)

with m1:
    st.metric("Total Pelanggan", total_pelanggan)

    # Data jumlah pelanggan per kuadran
    pie_data = (
        df_filtered.groupby("Kuadran", dropna=True)["IdNumber"]
        .count()
        .reset_index(name="Jumlah Pelanggan")
    )

    if not pie_data.empty:
        # pie_data = pie_data.sort_values("Kuadran").reset_index(drop=True)
        pie_data["Kuadran"] = pie_data["Kuadran"].apply(lambda q: f"Kuadran {q}")
        # pie_data["Kuadran"] = pd.Categorical(pie_data["Kuadran"], categories=order, ordered=True)
        # pie_data = pie_data.sort_values("Kuadran")

        fig = px.pie(
            pie_data,
            values="Jumlah Pelanggan",
            names="Kuadran",
            title="Proporsi Jumlah Pelanggan per Kuadran",
            hole=0.3,
            color="Kuadran",
            color_discrete_map=kuadran_colors,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data Proporsi Jumlah Pelanggan per Kuadran.")


with m2:
    st.metric("Total Tunggakan", to_rupiah(total_tunggakan))

    # Data total saldo akhir per kuadran
    pie_data = (
        df_filtered.groupby("Kuadran", dropna=True)["Saldo Akhir"]
        .sum()
        .reset_index()
    )
    # st.dataframe(pie_data, use_container_width=True)
    if not pie_data.empty:
        # pie_data = pie_data.sort_values("Kuadran").reset_index(drop=True)
        pie_data["Kuadran"] = pie_data["Kuadran"].apply(lambda q: f"Kuadran {q}")
        # pie_data["Kuadran"] = pd.Categorical(pie_data["Kuadran"], categories=order, ordered=False)
        # pie_data = pie_data.sort_values("Kuadran")

        fig = px.pie(
            pie_data,
            values="Saldo Akhir",
            names="Kuadran",
            title="Proporsi Jumlah Tunggakan per Kuadran",
            hole=0.3,
            color="Kuadran",
            color_discrete_map=kuadran_colors,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data Proporsi Jumlah Tunggakan per Kuadran.")


# ====== Komponen Kuadran ======
def format_saldo(value: float) -> str:
    """Format angka jadi singkat (contoh: 1.2M, 500JT, 8.3K)."""
    if pd.isna(value):
        return ""
    if value >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f} M"
    elif value >= 1_000_000:
        return f"{value/1_000_000:.1f} JT"
    else:
        return str(int(value))

def render_kuadran(dfq: pd.DataFrame, kuadran_num: int, judul: str):
    with st.container(border=True):
        st.markdown(f" #### {judul}")

        if dfq.empty:
            st.info("Tidak ada data di kuadran ini.")
            return None

        jml = len(dfq)
        persen_plg = (jml / total_pelanggan * 100) if total_pelanggan else 0.0

        total_nom = dfq["Saldo Akhir"].sum(skipna=True)
  
        persen_nom = (total_nom / total_tunggakan * 100) if total_tunggakan else 0.0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"Jumlah pelanggan: **{jml}** ({persen_plg:.1f}%)")
        with col2:
            st.markdown(f"Total tunggakan: **{format_saldo(total_nom)}** ({persen_nom:.1f}%)")

        # Top 3 by Saldo Akhir
        top3 = dfq.sort_values("Saldo Akhir", ascending=False).head(3).copy()
        top3["Saldo"] = top3["Saldo Akhir"].apply(format_saldo)

        edited_top3 = st.data_editor(
            top3[["IdNumber", "BP Name", "Saldo", "AM", "Keterangan"]],
            hide_index=True,
            use_container_width=True,
            disabled=["IdNumber", "BP Name", "Saldo", "AM" ],  # biar yg tampil cuma view
            key=f"editor_{kuadran_num}"
        )

        # hasil edit tetap update ke kolom "Keterangan", sedangkan "Saldo Akhir" asli tidak terganggu
        return edited_top3




# ====== Grid 2x2 Kuadran ======
st.divider()
st.markdown(f"<h2 style='text-align: center; font-weight:bold'>Kuadran {segmen_target} — {tanggal_target}</h2>", unsafe_allow_html=True)
# st.markdown("### Dataframe Kuadran")
# st.dataframe(df_filtered)
# TODO bikin tombol edit di kanan pojok ujung dan beri info kalo user sedang mengedit, kalo user submit edit maka akan memperbauri df pusat

c1, c2 = st.columns(2)
with c1:
    edit1 = render_kuadran(df_filtered[df_filtered["Kuadran"] == 1], 1, "Kuadran 1 — Baru Mengunggak & Nominal Besar")
with c2:
    edit2 = render_kuadran(df_filtered[df_filtered["Kuadran"] == 2], 2, "Kuadran 2 — Tunggakan Lama & Nominal Besar")

c3, c4 = st.columns(2)
with c3:
    edit3 = render_kuadran(df_filtered[df_filtered["Kuadran"] == 3], 3, "Kuadran 3 — Baru Menunggak & Nominal Kecil")
with c4:
    edit4 = render_kuadran(df_filtered[df_filtered["Kuadran"] == 4], 4, "Kuadran 4 — Tunggakan Lama & Nominal Kecil")

if st.button("💾 Simpan Semua Perubahan", use_container_width=True):
    try:
        # Gabungkan hasil edit dari semua kuadran (abaikan yang None)
        df_all_edited = pd.concat(
            [df for df in [edit1, edit2, edit3, edit4] if df is not None],
            ignore_index=True
        )

        # Update ke session_state df_database_clean
        for _, row in df_all_edited.iterrows():
            mask = (
                (st.session_state["df_database_clean"]["IdNumber"] == row["IdNumber"]) &
                (st.session_state["df_database_clean"]["Segmen"] == row["Segmen"]) &
                (st.session_state["df_database_clean"]["Bulan Tahun"] == row["Bulan Tahun"])
            )
            st.session_state["df_database_clean"].loc[mask, "Keterangan"] = row["Keterangan"]

        # Update ke Google Sheet
        update_keterangan_top_kuadran(df_edited=df_all_edited)
        st.toast("✅ Semua perubahan berhasil disimpan!")

    except Exception as e:
        st.error(f"Gagal menyimpan perubahan: {e}")

st.divider()



# ====== Tabel Lengkap Kuadran View MORE======
st.markdown(
    """
    <style>
    /* Pusatkan tab (sudah ada di kode Anda) */
    .stTabs [role="tablist"] {
        justify-content: center;
    }

    /* Ubah ukuran font tab */
    .stTabs [role="tab"] {
        font-size: 18px;
        font-weight: 600; /* optional: bikin bold */
        padding: 8px 16px; /* optional: lebih lega */
    }
    </style>
    """,
    unsafe_allow_html=True
)


with st.expander("View More"):
    tab_names = ["Kuadran 1", "Kuadran 2", "Kuadran 3", "Kuadran 4"]
    tabs = st.tabs(tab_names)

    for i, tab in enumerate(tabs, start=1):  # start=1 biar sesuai kuadran
        with tab:
            st.dataframe(
                df_filtered[df_filtered["Kuadran"] == i]
                .sort_values("Saldo Akhir", ascending=False)
                .reset_index(drop=True),
                use_container_width=True,
                height=600
            )
