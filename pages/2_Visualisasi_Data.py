import streamlit as st
import pandas as pd
from utils.helpers import pilih_kategori
from utils.google_utils import get_client
import plotly.express as px

st.set_page_config(page_title="Visualisasi", layout="wide")
st.title("📊 Visualisasi Data")

# Pastikan link ada di session_state
if "spreadsheet_database_url" not in st.session_state or not st.session_state["spreadsheet_database_url"]:
    st.error("❌ Belum ada link database! Silakan masukkan di halaman Home dulu.")
    st.stop()

# --- Helper: format & konversi angka ---
def to_number(series: pd.Series, allow_parentheses: bool = False) -> pd.Series:
    s = series.astype(str).str.strip()
    if allow_parentheses:
        # (123) -> -123 untuk kolom aging
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    # Bersihkan Rupiah & pemisah ribuan gaya Indonesia
    s = (
        s.str.replace("Rp", "", regex=False)
         .str.replace(".", "", regex=False)     # hapus titik ribuan
         .str.replace(",", ".", regex=False)    # koma -> titik desimal
         .str.replace(r"[^\d\.\-]", "", regex=True)  # buang karakter lain
    )
    return pd.to_numeric(s, errors="coerce")

def rupiah(n: float | int) -> str:
    try:
        x = float(n)
    except Exception:
        return "Rp 0"
    # Format ribuan pakai titik
    s = f"{int(round(x)):,}".replace(",", ".")
    return f"Rp {s}"

# ====== Ambil data dari Google Sheets ======
link_spreadsheet = st.session_state["spreadsheet_database_url"]
nama_worksheet = st.session_state["worksheet_database_name"]

client = get_client()
ws = client.open_by_url(link_spreadsheet).worksheet(nama_worksheet)
raw = ws.get_all_values()

# DataFrame dengan header baris pertama
df = pd.DataFrame(raw[1:], columns=raw[0])

# Konversi numeric
aging_cols = ["0-3 Bulan","4-6 Bulan","7-12 Bulan","13-24 Bulan","> 24 Bulan"]
df[aging_cols] = df[aging_cols].apply(lambda s: to_number(s, allow_parentheses=True))
df["Saldo Akhir"] = to_number(df["Saldo Akhir"], allow_parentheses=False)
df["Lama Tunggakan"] = to_number(df["Lama Tunggakan"], allow_parentheses=False)
df["Kuadran"] = pd.to_numeric(df["Kuadran"], errors="coerce").astype("Int64")

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
    "Kuadran 1": "#1f77b4",
    "Kuadran 2": "#d62728",  
    "Kuadran 3": "#d9e7fd",  
    "Kuadran 4": "#ff7f7f",  
}

st.markdown(f"### Ringkasan {segmen_target} — {tanggal_target}")
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
    st.metric("Total Tunggakan", rupiah(total_tunggakan))

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


# ====== CSS Card ======
st.markdown("""
<style>
.card {
  background-color: #ffffff;
  padding: 1.2rem;
  margin-bottom: 1rem;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
.card h4 { margin: 0 0 .5rem 0; font-size: 1.05rem; font-weight: 700; }
.card p { margin: .2rem 0; }
.top3 { font-size: .92rem; color: #444; }
.viewmore { margin-top: .5rem; }
</style>
""", unsafe_allow_html=True)

# ====== Komponen Kuadran ======
def render_kuadran(dfq: pd.DataFrame, kuadran_num: int, judul: str):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<h4>{judul}</h4>", unsafe_allow_html=True)

    if dfq.empty:
        st.info("Tidak ada data di kuadran ini.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    jml = len(dfq)
    persen_plg = (jml / total_pelanggan * 100) if total_pelanggan else 0.0

    total_nom = dfq["Saldo Akhir"].sum(skipna=True)
    persen_nom = (total_nom / total_tunggakan * 100) if total_tunggakan else 0.0

    st.markdown(f"<p>Jumlah pelanggan: <b>{jml}</b> ({persen_plg:.1f}%)</p>", unsafe_allow_html=True)
    st.markdown(f"<p>Total tunggakan: <b>{rupiah(total_nom)}</b> ({persen_nom:.1f}%)</p>", unsafe_allow_html=True)

    # Top 3 by Saldo Akhir
    top3 = dfq.sort_values("Saldo Akhir", ascending=False).head(3)
    st.markdown("<p><b>Top 3:</b></p>", unsafe_allow_html=True)
    for _, row in top3.iterrows():
        nama = row["BP Name"]
        tungg = rupiah(row["Saldo Akhir"])
        lama = int(row["Lama Tunggakan"]) if pd.notna(row["Lama Tunggakan"]) else 0
        st.markdown(f"<p class='top3'>- {nama} — {tungg} — {lama} bulan</p>", unsafe_allow_html=True)

    # View More
    if st.button(f"View More Kuadran {kuadran_num}", key=f"view_{kuadran_num}", use_container_width=True):
        show_cols = ["IdNumber", "BP Name", "AM", "Saldo Akhir", "Lama Tunggakan"]
        show_cols = [c for c in show_cols if c in dfq.columns]
        df_show = dfq.sort_values("Saldo Akhir", ascending=False)[show_cols].copy()
        # Format saldo untuk tampilan tabel
        df_show["Saldo Akhir"] = dfq.sort_values("Saldo Akhir", ascending=False)["Saldo Akhir"].apply(rupiah).values
        st.table(df_show)
        st.caption(
            f"Total pelanggan kuadran {kuadran_num}: {jml} "
            f"({persen_plg:.1f}%) • Total tunggakan kuadran: {rupiah(total_nom)} "
            f"({persen_nom:.1f}% dari total)."
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ====== Grid 2x2 Kuadran ======
c1, c2 = st.columns(2)
with c1:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 1], 1, "Kuadran 1 — Baru menunggak & tunggakan besar")
with c2:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 2], 2, "Kuadran 2 — Tunggakan lama & tunggakan besar")

c3, c4 = st.columns(2)
with c3:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 3], 3, "Kuadran 3 — Baru menunggak & tunggakan kecil")
with c4:
    render_kuadran(df_filtered[df_filtered["Kuadran"] == 4], 4, "Kuadran 4 — Tunggakan lama & tunggakan kecil")
