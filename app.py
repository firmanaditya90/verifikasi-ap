import streamlit as st
import pandas as pd
import os
from datetime import date

# -----------------------------
# Konfigurasi
# -----------------------------
st.set_page_config(page_title="AP Verification System", layout="wide")
DB_PATH = "db.csv"
PASSWORD = "apteam123"

# -----------------------------
# Helper Functions
# -----------------------------
def ensure_db():
    if not os.path.exists(DB_PATH):
        pd.DataFrame(columns=["no_spm"]).to_csv(DB_PATH, index=False)

def load_data():
    ensure_db()
    return pd.read_csv(DB_PATH, keep_default_na=False)

def save_row(row: dict):
    ensure_db()
    df = pd.read_csv(DB_PATH, keep_default_na=False)
    if row["no_spm"] in df["no_spm"].values:
        df = df[df["no_spm"] != row["no_spm"]]
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)

def load_row(no_spm: str):
    df = load_data()
    if no_spm in df["no_spm"].values:
        return df[df["no_spm"] == no_spm].iloc[0].to_dict()
    return None

def format_rupiah(x):
    try:
        return f"Rp {float(x):,.0f}"
    except:
        return x

# -----------------------------
# Halaman Publik (View Only)
# -----------------------------
st.sidebar.title("🔍 Navigasi")
page = st.sidebar.radio("Menu", ["Lihat Data", "Login Verifikator"])

if page == "Lihat Data":
    st.title("📊 Daftar SPM (View Only)")
    df = load_data()
    if df.empty:
        st.info("Belum ada data tersimpan.")
    else:
        st.dataframe(df)

# -----------------------------
# Halaman Login Verifikator
# -----------------------------
if page == "Login Verifikator":
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
        else:
            st.stop()

    # -----------------------------
    # Setelah Login
    # -----------------------------
    st.title("🗂️ AP Verification Workspace")

    choice = st.radio("Pilih Aksi", ["Input Baru", "Edit Verifikasi"])

    # -----------------------------
    # Input Baru
    # -----------------------------
    if choice == "Input Baru":
        st.subheader("📥 Input Baru")
        nama_verifikator = st.text_input("Nama Verifikator")
        no_spm = st.text_input("Nomor SPM")

        if no_spm:
            tabs = st.tabs([
                "📄 Kontrak", "📝 Berita Acara", "📑 Dokumen Penagihan",
                "🔍 3-Way Matching", "✅ Status Transaksi"
            ])

            # ---- Tab Kontrak ----
            with tabs[0]:
                judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan")
                tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan", value=date.today())
                col1, col2 = st.columns(2)
                mulai = col1.date_input("Tanggal Mulai Pekerjaan", value=date.today())
                selesai = col2.date_input("Tanggal Selesai Pekerjaan", value=date.today())

                dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0, format="%.0f")
                ppn = dpp * 0.11
                total = dpp + ppn
                st.info(f"PPN (11%): {format_rupiah(ppn)}")
                st.info(f"Total Nilai Pekerjaan: {format_rupiah(total)}")

                jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan")
                jaminan_nilai, jaminan_mulai, jaminan_selesai = None, None, None
                if jaminan:
                    jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0, format="%.0f")
                    colj1, colj2 = st.columns(2)
                    jaminan_mulai = colj1.date_input("Masa Berlaku - Mulai", value=date.today())
                    jaminan_selesai = colj2.date_input("Masa Berlaku - Selesai", value=date.today())

            # Tab lain bisa ditambahkan mirip format di atas...

            if st.button("💾 Simpan"):
                row = {
                    "nama_verifikator": nama_verifikator,
                    "no_spm": no_spm,
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
                }
                save_row(row)
                st.success(f"✅ Data SPM {no_spm} berhasil disimpan/diupdate!")

    # -----------------------------
    # Edit Verifikasi
    # -----------------------------
    elif choice == "Edit Verifikasi":
        df = load_data()
        if df.empty:
            st.warning("Belum ada data tersimpan.")
            st.stop()
        no_spm = st.selectbox("Pilih Nomor SPM", df["no_spm"].unique())
        data_lama = load_row(no_spm)

        nama_verifikator = st.text_input("Nama Verifikator", value=data_lama.get("nama_verifikator", ""))

        tabs = st.tabs([
            "📄 Kontrak", "📝 Berita Acara", "📑 Dokumen Penagihan",
            "🔍 3-Way Matching", "✅ Status Transaksi"
        ])

        # ---- Tab Kontrak ----
        with tabs[0]:
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan", value=data_lama.get("judul_kontrak", ""))
            tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan", value=pd.to_datetime(data_lama.get("tgl_kontrak")))
            col1, col2 = st.columns(2)
            mulai = col1.date_input("Tanggal Mulai Pekerjaan", value=pd.to_datetime(data_lama.get("mulai")))
            selesai = col2.date_input("Tanggal Selesai Pekerjaan", value=pd.to_datetime(data_lama.get("selesai")))

            dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0,
                                  value=float(data_lama.get("dpp", 0)), format="%.0f")
            ppn = dpp * 0.11
            total = dpp + ppn
            st.info(f"PPN (11%): {format_rupiah(ppn)}")
            st.info(f"Total Nilai Pekerjaan: {format_rupiah(total)}")

            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan", value=bool(data_lama.get("jaminan", False)))
            jaminan_nilai, jaminan_mulai, jaminan_selesai = None, None, None
            if jaminan:
                jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0,
                                                value=float(data_lama.get("jaminan_nilai", 0)), format="%.0f")
                colj1, colj2 = st.columns(2)
                jaminan_mulai = colj1.date_input("Masa Berlaku - Mulai", value=pd.to_datetime(data_lama.get("jaminan_mulai")))
                jaminan_selesai = colj2.date_input("Masa Berlaku - Selesai", value=pd.to_datetime(data_lama.get("jaminan_selesai")))

        if st.button("💾 Update"):
            row = {
                "nama_verifikator": nama_verifikator,
                "no_spm": no_spm,
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
            }
            save_row(row)
            st.success(f"✅ Data SPM {no_spm} berhasil diperbarui!")
