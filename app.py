import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# -----------------------------
# Konfigurasi
# -----------------------------
st.set_page_config(page_title="AP Verification System", layout="wide")
DB_PATH = "db.csv"
PASSWORD = "apteam123"

# -----------------------------
# Kolom standar database
# -----------------------------
ALL_COLUMNS = [
    "last_updated", "nama_verifikator", "no_spm",
    # Kontrak
    "judul_kontrak", "tgl_kontrak", "mulai", "selesai", "dpp", "ppn", "total",
    "jaminan", "jaminan_nilai", "jaminan_mulai", "jaminan_selesai",
    # Berita Acara
    "tgl_ba", "progress",
    # Dokumen Penagihan
    "judul_tagihan", "syarat_progress", "syarat_persen",
    "tgl_invoice", "dpp_invoice", "ppn_invoice", "total_invoice",
    "faktur_no", "faktur_tgl", "faktur_dpp", "faktur_ppn",
    # Matching
    "match_tanggal", "match_syarat", "match_nilai", "match_faktur_tgl", "match_faktur_ppn", "kesimpulan",
    # Status
    "approved", "tgl_approve", "catatan"
]

# -----------------------------
# Helper Functions
# -----------------------------
def ensure_db():
    if not os.path.exists(DB_PATH):
        pd.DataFrame(columns=ALL_COLUMNS).to_csv(DB_PATH, index=False)

def load_data():
    ensure_db()
    df = pd.read_csv(DB_PATH, keep_default_na=False)
    for col in ALL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[ALL_COLUMNS]

def save_row(row: dict):
    ensure_db()
    df = load_data()
    # pastikan no_spm string bersih
    df["no_spm"] = df["no_spm"].astype(str).str.strip()
    row["no_spm"] = str(row["no_spm"]).strip()
    # hapus jika sudah ada no_spm yang sama
    df = df[df["no_spm"] != row["no_spm"]]
    row["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)

def load_row(no_spm: str):
    df = load_data()
    df["no_spm"] = df["no_spm"].astype(str).str.strip()
    no_spm = str(no_spm).strip()
    if no_spm in df["no_spm"].values:
        return df[df["no_spm"] == no_spm].iloc[0].to_dict()
    return None

def format_rupiah(x):
    try:
        return f"Rp {float(x):,.0f}"
    except:
        return x

def parse_date_safe(val, default=date.today()):
    try:
        if pd.isna(val) or val == "":
            return default
        return pd.to_datetime(val).date()
    except:
        return default

def parse_float_safe(val, default=0.0):
    try:
        return float(val)
    except:
        return default

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
        # Format rupiah di tabel
        view_df = df.copy()
        for col in ["dpp", "ppn", "total", "dpp_invoice", "ppn_invoice", "total_invoice", "faktur_dpp", "faktur_ppn"]:
            view_df[col] = view_df[col].apply(format_rupiah)
        view_df["approved"] = view_df["approved"].apply(lambda x: "✅" if str(x) == "True" else "❌")
        st.dataframe(view_df.fillna("").sort_values("last_updated", ascending=False).reset_index(drop=True))

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
    # Fungsi Render Form
    # -----------------------------
    def render_form(data_lama=None):
        nama_verifikator = st.text_input("Nama Verifikator", value=(data_lama.get("nama_verifikator") if data_lama else ""))
        no_spm = st.text_input("Nomor SPM", value=(data_lama.get("no_spm") if data_lama else ""))

        if not no_spm:
            return None, None

        tabs = st.tabs([
            "📄 Kontrak", "📝 Berita Acara", "📑 Dokumen Penagihan",
            "🔍 3-Way Matching", "✅ Status Transaksi"
        ])

        # ---- Tab Kontrak ----
        with tabs[0]:
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan", value=(data_lama.get("judul_kontrak") if data_lama else ""))
            tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan", value=parse_date_safe(data_lama.get("tgl_kontrak") if data_lama else ""))
            col1, col2 = st.columns(2)
            mulai = col1.date_input("Tanggal Mulai Pekerjaan", value=parse_date_safe(data_lama.get("mulai") if data_lama else ""))
            selesai = col2.date_input("Tanggal Selesai Pekerjaan", value=parse_date_safe(data_lama.get("selesai") if data_lama else ""))

            dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0, format="%.0f",
                                  value=parse_float_safe(data_lama.get("dpp") if data_lama else 0))
            ppn = dpp * 0.11
            total = dpp + ppn
            st.info(f"PPN (11%): {format_rupiah(ppn)}")
            st.info(f"Total Nilai Pekerjaan: {format_rupiah(total)}")

            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan", value=bool(data_lama.get("jaminan") == "True") if data_lama else False)
            jaminan_nilai, jaminan_mulai, jaminan_selesai = "", "", ""
            if jaminan:
                jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0, format="%.0f",
                                                value=parse_float_safe(data_lama.get("jaminan_nilai") if data_lama else 0))
                colj1, colj2 = st.columns(2)
                jaminan_mulai = colj1.date_input("Masa Berlaku - Mulai", value=parse_date_safe(data_lama.get("jaminan_mulai") if data_lama else ""))
                jaminan_selesai = colj2.date_input("Masa Berlaku - Selesai", value=parse_date_safe(data_lama.get("jaminan_selesai") if data_lama else ""))

        # ---- Tab Berita Acara ----
        with tabs[1]:
            tgl_ba = st.date_input("Tanggal Berita Acara", value=parse_date_safe(data_lama.get("tgl_ba") if data_lama else ""))
            progress = st.text_input("Progress Pekerjaan", value=(data_lama.get("progress") if data_lama else ""))

        # ---- Tab Dokumen Penagihan ----
        with tabs[2]:
            judul_tagihan = st.text_input("Judul Tagihan", value=(data_lama.get("judul_tagihan") if data_lama else ""))
            syarat_progress = st.text_input("Syarat Progress", value=(data_lama.get("syarat_progress") if data_lama else ""))
            syarat_persen = st.number_input("Nilai % dalam Kontrak", min_value=0, max_value=100, step=1,
                                            value=int(parse_float_safe(data_lama.get("syarat_persen") if data_lama else 0)))
            tgl_invoice = st.date_input("Tanggal Dokumen Penagihan", value=parse_date_safe(data_lama.get("tgl_invoice") if data_lama else ""))
            dpp_invoice = st.number_input("DPP Invoice (Rp)", min_value=0.0, step=1000.0, format="%.0f",
                                          value=parse_float_safe(data_lama.get("dpp_invoice") if data_lama else 0))
            ppn_invoice = dpp_invoice * 0.11
            total_invoice = dpp_invoice + ppn_invoice
            st.info(f"PPN Invoice: {format_rupiah(ppn_invoice)}")
            st.info(f"Total Invoice: {format_rupiah(total_invoice)}")
            faktur_no = st.text_input("Nomor Faktur Pajak", value=(data_lama.get("faktur_no") if data_lama else ""))
            faktur_tgl = st.date_input("Tanggal Faktur Pajak", value=parse_date_safe(data_lama.get("faktur_tgl") if data_lama else ""))
            faktur_dpp = st.number_input("DPP Faktur Pajak (Rp)", min_value=0.0, step=1000.0, format="%.0f",
                                         value=parse_float_safe(data_lama.get("faktur_dpp") if data_lama else 0))
            faktur_ppn = faktur_dpp * 0.11
            st.info(f"PPN Faktur: {format_rupiah(faktur_ppn)}")

        # ---- Tab Matching ----
        with tabs[3]:
            match_tanggal = "✅" if (mulai <= tgl_ba <= selesai) else "❌"
            match_syarat = "✅" if syarat_progress != "" else "❌"
            match_nilai = "✅" if abs(total - total_invoice) < 1 else "❌"
            match_faktur_tgl = "✅" if faktur_tgl == tgl_invoice else "❌"
            match_faktur_ppn = "✅" if abs(ppn_invoice - faktur_ppn) < 1 else "❌"
            kesimpulan = "OK" if all(x == "✅" for x in [match_tanggal, match_syarat, match_nilai, match_faktur_tgl, match_faktur_ppn]) else "Perlu dicek"

            st.subheader("📊 Ringkasan Matching")
            summary = {
                "Tanggal BA vs Kontrak": [match_tanggal, f"BA: {tgl_ba}, Kontrak: {mulai} s.d {selesai}"],
                "Syarat Penagihan": [match_syarat, f"{syarat_progress} ({syarat_persen}%)"],
                "Nilai Kontrak vs Invoice": [match_nilai, f"Kontrak: {format_rupiah(total)}, Invoice: {format_rupiah(total_invoice)}"],
                "Tanggal Faktur vs Invoice": [match_faktur_tgl, f"Invoice: {tgl_invoice}, Faktur: {faktur_tgl}"],
                "PPN Faktur vs Invoice": [match_faktur_ppn, f"Invoice: {format_rupiah(ppn_invoice)}, Faktur: {format_rupiah(faktur_ppn)}"],
            }
            df_summary = pd.DataFrame(summary, index=["Status", "Detail"]).T
            st.table(df_summary)

            st.info(f"Kesimpulan Sistem: **{kesimpulan}**")

        # ---- Tab Status ----
        with tabs[4]:
            approved = st.checkbox("Approve Transaksi?", value=(data_lama.get("approved") == "True") if data_lama else False)
            tgl_approve, catatan = "", ""
            if approved:
                tgl_approve = date.today()
                st.success(f"Disetujui pada {tgl_approve}")
            else:
                catatan = st.text_area("Alasan tidak disetujui", value=(data_lama.get("catatan") if data_lama else ""))

        # Collect hasil input
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
            "tgl_ba": tgl_ba,
            "progress": progress,
            "judul_tagihan": judul_tagihan,
            "syarat_progress": syarat_progress,
            "syarat_persen": syarat_persen,
            "tgl_invoice": tgl_invoice,
            "dpp_invoice": dpp_invoice,
            "ppn_invoice": ppn_invoice,
            "total_invoice": total_invoice,
            "faktur_no": faktur_no,
            "faktur_tgl": faktur_tgl,
            "faktur_dpp": faktur_dpp,
            "faktur_ppn": faktur_ppn,
            "match_tanggal": match_tanggal,
            "match_syarat": match_syarat,
            "match_nilai": match_nilai,
            "match_faktur_tgl": match_faktur_tgl,
            "match_faktur_ppn": match_faktur_ppn,
            "kesimpulan": kesimpulan,
            "approved": approved,
            "tgl_approve": tgl_approve,
            "catatan": catatan
        }
        return no_spm, row

    # -----------------------------
    # Input Baru
    # -----------------------------
    if choice == "Input Baru":
        no_spm, row = render_form()
        if row and st.button("💾 Simpan Baru"):
            save_row(row)
            st.success(f"✅ Data SPM {no_spm} berhasil disimpan!")

    # -----------------------------
    # Edit Verifikasi
    # -----------------------------
    elif choice == "Edit Verifikasi":
        df = load_data()
        if df.empty:
            st.warning("Belum ada data tersimpan.")
            st.stop()
        no_spm_selected = st.selectbox("Pilih Nomor SPM", df["no_spm"].unique())
        data_lama = load_row(no_spm_selected)
        no_spm, row = render_form(data_lama)
        if row and st.button("💾 Update Data"):
            save_row(row)
            st.success(f"✅ Data SPM {no_spm} berhasil diperbarui!")
