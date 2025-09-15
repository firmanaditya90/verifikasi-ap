import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_lottie import st_lottie
import requests

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="AP 3-Way Matching",
    page_icon="📑",
    layout="wide"
)

PASSWORD = "apteam123"  # Ganti sesuai kebutuhan

# ---------------- UTIL ----------------
def load_lottie(url: str):
    """Load animasi Lottie dari URL"""
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ---------------- HEADER ----------------
st.markdown("<h2 style='text-align: center;'>📑 Sistem Verifikasi 3-Way Matching</h2>", unsafe_allow_html=True)

lottie_json = load_lottie("https://assets5.lottiefiles.com/packages/lf20_q5pk6p1k.json")
if lottie_json:
    st_lottie(lottie_json, height=180, key="intro")

st.markdown("### Selamat datang di sistem verifikasi **Account Payable** berbasis digitalisasi 🚀")

# ---------------- LOGIN ----------------
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
            st.stop()   # stop kalau salah
    else:
        st.stop()       # stop kalau belum klik login

# ---------------- MENU ----------------
st.sidebar.title("🔧 Menu Utama")
choice = st.sidebar.radio("Pilih Aksi", ["Input Baru", "Edit Verifikasi"])

if choice == "Input Baru":
    st.subheader("📥 Input Baru")
    nama_verifikator = st.text_input("Nama Verifikator")
    no_spm = st.text_input("Nomor SPM")
    if nama_verifikator and no_spm:
        st.success("✅ Data dasar siap, lanjut ke tab formulir...")
else:
    st.subheader("✏️ Edit Verifikasi")
    nama_verifikator = st.text_input("Nama Verifikator")
    # sementara pilih dummy, nanti bisa connect ke database
    no_spm = st.selectbox("Pilih Nomor SPM yang sudah ada", ["SPM001", "SPM002", "SPM003"])

# ---------------- TABS ----------------
tabs = st.tabs([
    "📄 Kontrak", 
    "📝 Berita Acara", 
    "📑 Dokumen Penagihan",
    "🔍 3-Way Matching", 
    "✅ Status Transaksi"
])

# ---- Tab 1: Kontrak ----
with tabs[0]:
    st.markdown("### Dasar Pekerjaan / Kontrak Perjanjian")
    judul = st.text_input("Judul Kontrak / Pekerjaan")
    tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan")
    col1, col2 = st.columns(2)
    mulai = col1.date_input("Tanggal Mulai Pekerjaan")
    selesai = col2.date_input("Tanggal Selesai Pekerjaan")
    col3, col4, col5 = st.columns(3)
    dpp = col3.number_input("DPP", min_value=0)
    ppn = col4.number_input("PPN", min_value=0)
    total = col5.number_input("Total Nilai Pekerjaan", min_value=0)
    jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan")

# ---- Tab 2: Berita Acara ----
with tabs[1]:
    st.markdown("### Berita Acara Progress / Selesai Pekerjaan")
    tgl_ba = st.date_input("Tanggal Berita Acara")
    progress = st.text_area("Progress Pekerjaan")

# ---- Tab 3: Dokumen Penagihan ----
with tabs[2]:
    st.markdown("### Dokumen Penagihan")
    judul_tagihan = st.text_input("Judul Tagihan")
    syarat_progress = st.text_input("Progress pekerjaan (syarat kontrak)")
    syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0, max_value=100)
    tgl_dok = st.date_input("Tanggal Dokumen Penagihan")
    col1, col2, col3 = st.columns(3)
    inv_dpp = col1.number_input("Invoice DPP", min_value=0)
    inv_ppn = col2.number_input("Invoice PPN", min_value=0)
    inv_total = col3.number_input("Total Invoice", min_value=0)
    st.markdown("#### Faktur Pajak")
    col4, col5 = st.columns(2)
    faktur_no = col4.text_input("Nomor Faktur Pajak")
    faktur_tgl = col5.date_input("Tanggal Faktur Pajak")
    col6, col7 = st.columns(2)
    faktur_dpp = col6.number_input("Faktur Pajak DPP", min_value=0)
    faktur_ppn = col7.number_input("Faktur Pajak PPN", min_value=0)

# ---- Tab 4: 3-Way Matching ----
with tabs[3]:
    st.markdown("### 🔍 Hasil 3-Way Matching (Otomatis)")
    checks = []
    if "tgl_ba" in locals() and "mulai" in locals() and "selesai" in locals():
        if mulai <= tgl_ba <= selesai:
            checks.append("✅ Tanggal BA dalam range kontrak")
        else:
            checks.append("❌ Tanggal BA di luar kontrak")

    if "inv_total" in locals() and "total" in locals():
        if inv_total == total:
            checks.append("✅ Nilai invoice sesuai kontrak")
        else:
            checks.append("❌ Nilai invoice tidak sesuai kontrak")

    if "faktur_tgl" in locals() and "tgl_dok" in locals():
        if faktur_tgl == tgl_dok:
            checks.append("✅ Tanggal faktur = tanggal invoice")
        else:
            checks.append("❌ Tanggal faktur ≠ tanggal invoice")

    if "faktur_ppn" in locals() and "inv_ppn" in locals():
        if faktur_ppn == inv_ppn:
            checks.append("✅ PPN faktur = PPN invoice")
        else:
            checks.append("❌ PPN faktur ≠ PPN invoice")

    if checks:
        st.write("\n".join(checks))
    else:
        st.info("⚠️ Isi data di tab sebelumnya untuk melihat hasil matching")

# ---- Tab 5: Status Transaksi ----
with tabs[4]:
    st.markdown("### Status Transaksi")
    approved = st.checkbox("Disetujui (Approve)")
    if approved:
        st.success(f"✅ Approved pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        alasan = st.text_area("Alasan tidak disetujui")
        if alasan:
            st.error(f"❌ Tidak disetujui. Alasan: {alasan}")
