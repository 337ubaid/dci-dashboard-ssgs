import streamlit as st
import pandas as pd

import numpy as np
from utils.services import get_raw_values

def cast_to_number(
        data, 
        exclude: list | None = None
        ) -> pd.DataFrame | pd.Series:
    """
    Konversi Series/DataFrame ke numerik.
    Bersihkan format Rp, titik ribuan, koma desimal.

    Parameters
    ----------
    data : pd.Series | pd.DataFrame
        Data yang ingin dibersihkan (satu kolom atau banyak kolom).
    exclude : list, optional
        Daftar nama kolom yang tidak ingin dikonversi (hanya berlaku kalau input DataFrame).

    Returns
    -------
    pd.Series | pd.DataFrame
        Data yang sudah dikonversi ke numerik.

    Apply
    -------
    Series
        df["Cols_Name"] = cast_to_number(df["Cols_Name"])

    DataFrame
        df = cast_to_number(df)
    """
    
    DEFAULT_EXCLUDE = ["BP Name", "AM", "Keterangan", "Segmen", "Bulan Tahun", "Last Updated"]

    
    def _clean(series: pd.Series) -> pd.Series:
        s = series.astype(str).str.strip()

        s = (
            s.str.replace("Rp", "", regex=False)
             .str.replace(".", "", regex=False)     # hapus titik ribuan
             .str.replace(",", ".", regex=False)    # koma -> titik desimal
             .str.replace(r"[^\d\.\-]", "", regex=True)  # buang karakter lain
        )
        return pd.to_numeric(s, errors="coerce").fillna(0)

    if isinstance(data, pd.Series):
        return _clean(data)
    
    elif isinstance(data, pd.DataFrame):
        df_clean = data.copy()
        if exclude is None:
            exclude = DEFAULT_EXCLUDE
        for col in df_clean.columns:
            if col not in exclude:
                df_clean[col] = _clean(df_clean[col])
        return df_clean
    
    else:
        raise TypeError("Input harus pd.Series atau pd.DataFrame")


def to_rupiah(n: float | int) -> str:
    """
    Konversi angka ke format mata uang Rupiah.

    Parameters
    ----------
    n : float atau int
        Angka yang ingin diformat.

    Returns
    -------
    str
        String dalam format Rupiah, contoh:
        - 1000   -> "Rp 1.000"
        - 125000 -> "Rp 125.000"
        - "abc"  -> "Rp 0" (jika input tidak valid)

    Notes
    -----
    - Pembulatan dilakukan ke bilangan bulat terdekat.
    - Pemisah ribuan menggunakan titik (.)
    - Prefix default adalah "Rp"
    """
    try:
        x = float(n)
    except Exception:
        return "Rp 0"

    # Format ribuan pakai titik (.)
    s = f"{int(round(x)):,}".replace(",", ".")
    return f"Rp {s}"


def get_batas_kuadran(segmen_target: str):
    df = get_raw_values(st.session_state["database_gsheet_url"], "Batas Kuadran")
    if df.empty:
        st.warning("❌ Data batas kuadran tidak ditemukan.")
        return None

    df_filtered = df[df["Segmen"] == segmen_target]
    if df_filtered.empty:
        st.warning(f"❌ Data batas kuadran untuk segmen '{segmen_target}' tidak ditemukan.")
        return None

    row = df_filtered.iloc[0]

    # Bersihkan nominal: hilangkan Rp dan titik ribuan
    row = cast_to_number(row)

    return row["Batas Nominal"], row["Batas Waktu (bulan)"]

def tentukan_kuadran(df, segmen):
    batas_nominal, batas_waktu = get_batas_kuadran(segmen)

    st.success(f"✅ Berhasil pilih Segmen **{segmen}**, dengan Batas Nominal **{to_rupiah(batas_nominal)}** dan Lama Tunggakan **{batas_waktu:.0f} bulan**")

    def cek_kuadran(row):
        if row["Saldo Akhir"] >= batas_nominal and row["Lama Tunggakan"] >= batas_waktu:
            return 1
        elif row["Saldo Akhir"] < batas_nominal and row["Lama Tunggakan"] >= batas_waktu:
            return 2
        elif row["Saldo Akhir"] >= batas_nominal and row["Lama Tunggakan"] < batas_waktu:
            return 3
        else:
            return 4

    df["Kuadran"] = df.apply(cek_kuadran, axis=1)
    return df

def _sanitize_text_column(df: pd.DataFrame, colname: str, default: str = "-") -> pd.DataFrame:
    """Pastikan kolom teks ada, dan isi yang kosong/NaN diganti default."""
    if colname not in df.columns:
        df[colname] = default
    else:
        df[colname] = df[colname].astype(str)
        df[colname] = df[colname].replace(["nan", "None"], "")
        df[colname] = df[colname].str.strip().replace("", default)
        df[colname] = df[colname].fillna(default)
    return df

def validasi_data_upload(df_upload: pd.DataFrame, tanggal_target: str, segmen_target: str) -> pd.DataFrame:
    """
    Validasi dataframe sebelum diupload ke Google Sheets.
    - Tambahkan kolom 'Segmen' dan 'Bulan Tahun'
    - Pastikan tidak ada kolom wajib yang hilang
    - Cast kolom angka ke numerik
    """

    errors = []
    kolom_wajib = [
        "IdNumber", "0-3 Bulan", "4-6 Bulan", "7-12 Bulan",
        "13-24 Bulan", "> 24 Bulan", "Saldo Akhir", "Keterangan"
    ]
    # Pastikan kolom teks tertentu aman
    df_upload = _sanitize_text_column(df_upload, "Keterangan")
    df_upload = _sanitize_text_column(df_upload, "AM")

    # Cek kolom duplikat
    kolom_ganda = df_upload.columns[df_upload.columns.duplicated()].tolist()
    if kolom_ganda:
        errors.append(f"❌ Ada kolom duplikat: {kolom_ganda}")

    # Cek kolom wajib
    kolom_hilang = [kol for kol in kolom_wajib if kol not in df_upload.columns]
    if kolom_hilang:
        errors.append(f"❌ Kolom berikut tidak ditemukan: {kolom_hilang}")

    if errors:
        st.error("Terjadi kesalahan validasi:\n" + "\n".join(errors))
        st.stop()

    # Cast otomatis ke numerik (skip kolom teks)
    df_upload = cast_to_number(df_upload)

    # Tambahkan kolom tambahan
    df_upload["Segmen"] = segmen_target if segmen_target != "--Semua--" else "-"
    df_upload["Bulan Tahun"] = tanggal_target
    df_upload["Lama Tunggakan"] = np.select(
            [
                df_upload["> 24 Bulan"] > 0,
                df_upload["13-24 Bulan"] > 0,
                df_upload["7-12 Bulan"] > 0,
                df_upload["4-6 Bulan"] > 0,
                df_upload["0-3 Bulan"] > 0,
            ],
            [25, 24, 12, 6, 3],
            default=0
        )
    
    df_upload = tentukan_kuadran(df_upload, segmen_target)
    df_upload["Last Updated"] = pd.to_datetime("now").strftime("%d/%m/%Y %H:%M:%S")

    # Susunan kolom final
    sheet_header = [
        "Bulan Tahun", "Segmen", "IdNumber", "BP Name", "AM",
        "0-3 Bulan", "4-6 Bulan", "7-12 Bulan", "13-24 Bulan", "> 24 Bulan",
        "Saldo Akhir", "Keterangan", "Lama Tunggakan", "Kuadran", "Last Updated"
    ]

    # Pastikan semua kolom ada
    for col in sheet_header:
        if col not in df_upload.columns:
            if col in ["0-3 Bulan", "4-6 Bulan", "7-12 Bulan", "13-24 Bulan", "> 24 Bulan", "Saldo Akhir"]:
                df_upload[col] = 0
            else:
                df_upload[col] = "-"

    # Reindex sesuai header
    return df_upload.reindex(columns=sheet_header)
