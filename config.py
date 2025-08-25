import streamlit as st
"""
File konfigurasi untuk koneksi Google Sheets.
Ubah nilai di sini kalau spreadsheet/worksheet berubah.
"""

CREDENTIALS_FILE = st.secrets["gcp_service_account"]

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Default spreadsheet & worksheet tujuan upload
SPREADSHEET_ID = st.secrets["spreadsheet_database"]["spreadsheet_id"]
WORKSHEET_NAME = st.secrets["spreadsheet_database"]["worksheet_name"]