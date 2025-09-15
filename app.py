import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

st.set_page_config(page_title="AP 3-Way Matching", page_icon="📑", layout="wide")

# ---- Load Animasi Digital ----
def load_lottie(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_json = load_lottie("https://assets5.lottiefiles.com/packages/lf20_q5pk6p1k.json")

# ---- Header ----
st.title("📑 Sistem Verifikasi 3-Way Matching")
if lottie_json:
    st_lottie(lottie_json, height=200, key="intro")

st.markdown("Selamat datang di sistem verifikasi **Account Payable** berbasis digitalisasi 🚀")

# ---- Login ----
PASSWORD = "apteam123"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    pw = st.text_input("🔑 Masukkan Password", type="password")
    if st.button("Login"):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Login berhasil")
        else:
            st.error("❌ Password salah")
    st.stop()

# ---- Menu ----
choice = st.radio("Pilih Aksi", ["Input Baru", "Edit Verifikasi"])

if choice == "Input Baru":
    st.subheader("📥 Input Baru")
    nama_verifikator = st.text_input("Nama Verifikator")
    no_spm = st.text_input("Nomor SPM")
    if nama_verifikator and no_spm:
        st.success("✅ Data dasar siap, lanjut ke tab formulir...")
else:
    st.subheader("✏️ Edit Verifikasi")
    nama_verifikator = st.text_input("Nama Verifikator")
    no_spm = st.selectbox("Pilih Nomor SPM yang sudah ada", ["SPM001", "SPM002"])  # contoh dummy

# ---- Placeholder Tabs ----
tabs = st.tabs([
    "Kontrak", "Berita Acara", "Dokumen Penagihan",
    "3-Way Matching", "Status Transaksi"
])

with tabs[0]:
    st.info("Form Kontrak akan ditaruh di sini")
with tabs[1]:
    st.info("Form Berita Acara akan ditaruh di sini")
with tabs[2]:
    st.info("Form Dokumen Penagihan akan ditaruh di sini")
with tabs[3]:
    st.info("Logika 3-Way Matching otomatis akan ditaruh di sini")
with tabs[4]:
    st.info("Status Approve / Not Approve akan ditaruh di sini")
