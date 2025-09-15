import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="AP 3-Way Matching",
    page_icon="📑",
    layout="wide"
)

PASSWORD = "apteam123"  # Ganti sesuai kebutuhan
DB_PATH = "db.csv"

# ---------------- DATA UTILS ----------------
def ensure_db():
    if not os.path.exists(DB_PATH):
        pd.DataFrame(columns=["no_spm"]).to_csv(DB_PATH, index=False)

def save_row(row: dict):
    ensure_db()
    df = pd.read_csv(DB_PATH, keep_default_na=False)

    if row["no_spm"] in df["no_spm"].values:
        # replace row dengan SPM sama
        df = df[df["no_spm"] != row["no_spm"]]
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        # append baru
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    df.to_csv(DB_PATH, index=False)

def load_data():
    ensure_db()
    return pd.read_csv(DB_PATH, keep_default_na=False)

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

menu_umum = st.sidebar.radio("📑 Menu Umum", ["Lihat Data Publik", "Login Tim Verifikator"])

if menu_umum == "Login Tim Verifikator" and not st.session_state.logged_in:
    pw = st.sidebar.text_input("🔑 Password", type="password")
    if st.sidebar.button("Login"):
        if pw == PASSWORD:
            st.session_state.logged_in = True
            st.sidebar.success("✅ Login berhasil")
        else:
            st.sidebar.error("❌ Password salah")

# ---------------- MODE LOGIN ----------------
if st.session_state.logged_in:

    st.title("📑 Sistem Verifikasi 3-Way Matching - Tim Verifikator")

    choice = st.sidebar.radio("🔧 Menu Utama", ["Input Baru", "Edit Verifikasi", "Lihat Semua Data"])

    if choice in ["Input Baru", "Edit Verifikasi"]:
        nama_verifikator = st.text_input("Nama Verifikator")
        if choice == "Input Baru":
            no_spm = st.text_input("Nomor SPM")
        else:
            df = load_data()
            if df.empty:
                st.warning("Belum ada data.")
                st.stop()
            no_spm = st.selectbox("Pilih Nomor SPM", df["no_spm"].unique())

        tabs = st.tabs([
            "📄 Kontrak", 
            "📝 Berita Acara", 
            "📑 Dokumen Penagihan",
            "🔍 3-Way Matching", 
            "✅ Status Transaksi"
        ])

        # ---- Tab 1: Kontrak ----
        with tabs[0]:
            st.subheader("Dasar Pekerjaan / Kontrak Perjanjian")
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan")
            tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan")
            col1, col2 = st.columns(2)
            mulai = col1.date_input("Tanggal Mulai Pekerjaan")
            selesai = col2.date_input("Tanggal Selesai Pekerjaan")

            # Input DPP, auto hitung PPN & total
            dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0, format="%.0f")
            ppn = dpp * 0.11
            total = dpp + ppn
            st.info(f"PPN (11%): Rp {ppn:,.0f}")
            st.info(f"Total Nilai Pekerjaan: Rp {total:,.0f}")

            # Jaminan
            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan")
            jaminan_nilai, jaminan_mulai, jaminan_selesai = None, None, None
            if jaminan:
                jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0, format="%.0f")
                colj1, colj2 = st.columns(2)
                jaminan_mulai = colj1.date_input("Masa Berlaku - Mulai")
                jaminan_selesai = colj2.date_input("Masa Berlaku - Selesai")

        # ---- Tab 2: Berita Acara ----
        with tabs[1]:
            tgl_ba = st.date_input("Tanggal Berita Acara")
            progress = st.text_area("Progress Pekerjaan")

        # ---- Tab 3: Dokumen Penagihan ----
        with tabs[2]:
            judul_tagihan = st.text_input("Judul Tagihan")
            syarat_progress = st.text_input("Progress pekerjaan (syarat kontrak)")
            syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0, max_value=100)
            tgl_dok = st.date_input("Tanggal Dokumen Penagihan")

            st.markdown("#### Invoice")
            inv_dpp = st.number_input("Invoice DPP (Rp)", min_value=0.0, step=1000.0, format="%.0f")
            inv_ppn = inv_dpp * 0.11
            inv_total = inv_dpp + inv_ppn
            st.info(f"PPN (11%): Rp {inv_ppn:,.0f}")
            st.info(f"Total Invoice: Rp {inv_total:,.0f}")

            st.markdown("#### Faktur Pajak")
            col4, col5 = st.columns(2)
            faktur_no = col4.text_input("Nomor Faktur Pajak")
            faktur_tgl = col5.date_input("Tanggal Faktur Pajak")
            faktur_dpp = inv_dpp
            faktur_ppn = inv_ppn

        # ---- Tab 4: Matching ----
        with tabs[3]:
            st.subheader("Hasil 3-Way Matching")
            checks = []
            if mulai <= tgl_ba <= selesai:
                checks.append("✅ Tanggal BA dalam range kontrak")
            else:
                checks.append("❌ Tanggal BA di luar kontrak")

            if inv_total == total:
                checks.append("✅ Nilai invoice sesuai kontrak")
            else:
                checks.append("❌ Nilai invoice tidak sesuai kontrak")

            if faktur_tgl == tgl_dok:
                checks.append("✅ Tanggal faktur = tanggal invoice")
            else:
                checks.append("❌ Tanggal faktur ≠ tanggal invoice")

            if faktur_ppn == inv_ppn:
                checks.append("✅ PPN faktur = PPN invoice")
            else:
                checks.append("❌ PPN faktur ≠ PPN invoice")

            st.write("\n".join(checks))

        # ---- Tab 5: Status ----
        with tabs[4]:
            st.subheader("Status Transaksi")
            approved = st.checkbox("Disetujui (Approve)")
            alasan = None
            if approved:
                st.success(f"✅ Approved pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                alasan = st.text_area("Alasan tidak disetujui")

        # ---- Tombol Simpan ----
        if st.button("💾 Simpan Data"):
            row = {
                "no_spm": no_spm,
                "nama_verifikator": nama_verifikator,
                "judul_kontrak": judul_kontrak,
                "tgl_kontrak": tgl_kontrak,
                "mulai": mulai,
                "selesai": selesai,
                "dpp": dpp,
                "ppn": ppn,
                "total": total,
                "jaminan": jaminan,
                "jaminan_nilai": jaminan_nilai,
                "jaminan_mulai": jaminan_mulai,
                "jaminan_selesai": jaminan_selesai,
                "tgl_ba": tgl_ba,
                "progress": progress,
                "judul_tagihan": judul_tagihan,
                "syarat_progress": syarat_progress,
                "syarat_persen": syarat_persen,
                "tgl_dok": tgl_dok,
                "inv_dpp": inv_dpp,
                "inv_ppn": inv_ppn,
                "inv_total": inv_total,
                "faktur_no": faktur_no,
                "faktur_tgl": faktur_tgl,
                "faktur_dpp": faktur_dpp,
                "faktur_ppn": faktur_ppn,
                "approved": approved,
                "alasan": alasan,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_row(row)
            st.success("✅ Data berhasil disimpan")

    elif choice == "Lihat Semua Data":
        st.subheader("📊 Data Semua SPM")
        df = load_data()
        st.dataframe(df)

# ---------------- MODE PUBLIK ----------------
elif menu_umum == "Lihat Data Publik":
    st.title("📊 Data Publik - List SPM")
    df = load_data()
    if df.empty:
        st.info("Belum ada data.")
    else:
        st.dataframe(df[["no_spm", "judul_kontrak", "inv_total", "approved", "timestamp"]])
