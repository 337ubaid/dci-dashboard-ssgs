import streamlit as st
import pandas as pd


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

def cast_numeric_cols(df):
    """
    Konversi semua kolom numerik (kecuali kolom teks) menjadi float.
    Bersihkan format: hapus .00/,00 di akhir, hapus Rp, titik, koma, spasi.
    """
    exclude = ["BP Name", "AM", "Keterangan", "Segmen", "Bulan Tahun", "Last Update"]

    for col in df.columns:
        if col in exclude:
            continue  # skip kolom teks

        # pastikan kolom jadi string
        s = df[col].fillna("").astype(str).str.strip()
        print(s)
        
        # 1️⃣ Hapus kurung
        s = s.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        print(s)

        # 2️⃣ Hapus desimal .00 atau ,00 di akhir
        s = s.str.replace(r"[.,]00$", "", regex=True)
        print(s)

        # 3️⃣ Hapus Rp, titik, koma, spasi
        s = s.str.replace(r"[Rp\s\.,]", "", regex=True)
        print(s)

        # Konversi ke float
        df[col] = pd.to_numeric(s, downcast="signed", errors="coerce")

    return df


def validasi_data(df_upload, tanggal_target, segmen_target):
    """
    Validasi dataframe sebelum diupload ke Google Sheets.
    Tambahkan kolom 'Segmen' dan 'Bulan Tahun'.
    """
    errors = []
    kolom_diperlukan = [
        "IdNumber", "0-3 Bulan", "4-6 Bulan", "7-12 Bulan",
        "13-24 Bulan", "> 24 Bulan", "Saldo Akhir", "Keterangan"
    ]

    # Pastikan kolom Keterangan ada
    if "Keterangan" not in df_upload.columns:
        df_upload["Keterangan"] = "-"
    else:
        df_upload["Keterangan"] = df_upload["Keterangan"].fillna("-")

    # Validasi kolom duplikat
    kolom_ganda = df_upload.columns[df_upload.columns.duplicated()].tolist()
    if kolom_ganda:
        errors.append(f"\n❌ Ada kolom duplikat: {kolom_ganda}")

    # Validasi kolom wajib
    kolom_hilang = [kol for kol in kolom_diperlukan if kol not in df_upload.columns]
    if kolom_hilang:
        errors.append(f"\n❌ Kolom berikut tidak ditemukan: {kolom_hilang}")

    if errors:
        st.error("Terjadi kesalahan validasi:\n" + "\n".join(errors))
        st.stop()

    # Cast otomatis ke numerik (kecuali kolom teks)
    df_upload = cast_numeric_cols(df_upload)

    # Tambahkan kolom tambahan
    if segmen_target != "--Semua--":
        df_upload["Segmen"] = segmen_target

    df_upload["Bulan Tahun"] = tanggal_target

    sheet_header = [
        "Bulan Tahun", "Segmen", "IdNumber", "BP Name", "AM",
        "0-3 Bulan", "4-6 Bulan", "7-12 Bulan", "13-24 Bulan", "> 24 Bulan",
        "Saldo Akhir", "Keterangan"
    ]

    # Pastikan semua kolom ada agar reindex tidak error
    for col in sheet_header:
        if col not in df_upload.columns:
            df_upload[col] = "-"

    return df_upload.reindex(columns=sheet_header)

