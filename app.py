# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from streamlit_lottie import st_lottie

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AP 3-Way Matching", page_icon="📑", layout="wide")
DATA_FOLDER = "data"
DB_PATH = os.path.join(DATA_FOLDER, "db.csv")
ADMIN_PASSWORD = "apteam123"   # ganti sesuai kebutuhan

# ---------------- UTIL ----------------
def ensure_data_folder():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(DB_PATH):
        df = pd.DataFrame(columns=[
            "created_at","nama_verifikator","no_spm",
            # Tab1 - Kontrak
            "judul_kontrak","tgl_kontrak","mulai","selesai","dpp","ppn","total","jaminan",
            # Tab2 - BA
            "tgl_ba","progress",
            # Tab3 - DokPen
            "judul_tagihan","syarat_progress","syarat_persen","tgl_dok","inv_dpp","inv_ppn","inv_total",
            "faktur_no","faktur_tgl","faktur_dpp","faktur_ppn",
            # Matching results
            "match_tgl_ba_range","match_nilai_invoice","match_tgl_faktur_invoice","match_ppn_faktur_invoice",
            "match_overall",
            # Status & visibility
            "approved","approved_at","notapproved_reason","notapproved_at",
            "visibility"  # 'public' or 'private'
        ])
        df.to_csv(DB_PATH, index=False)

def load_db():
    ensure_data_folder()
    return pd.read_csv(DB_PATH, parse_dates=["created_at","faktur_tgl","tgl_kontrak","mulai","selesai","tgl_ba","tgl_dok"], keep_default_na=False)

def save_row(row: dict):
    ensure_data_folder()
    df = pd.DataFrame([row])
    if os.path.exists(DB_PATH):
        df.to_csv(DB_PATH, mode="a", header=False, index=False)
    else:
        df.to_csv(DB_PATH, index=False)

def compute_matching(row):
    """Return dict of matching results (True/False) and overall."""
    res = {}
    try:
        # a. tanggal BA in range kontrak
        res["match_tgl_ba_range"] = (pd.to_datetime(row["mulai"]) <= pd.to_datetime(row["tgl_ba"]) <= pd.to_datetime(row["selesai"]))
    except Exception:
        res["match_tgl_ba_range"] = False
    try:
        # c. nilai invoice = total kontrak
        res["match_nilai_invoice"] = float(row.get("inv_total", 0)) == float(row.get("total", 0))
    except Exception:
        res["match_nilai_invoice"] = False
    try:
        # d. tanggal faktur == tanggal invoice (tgl_dok)
        res["match_tgl_faktur_invoice"] = pd.to_datetime(row.get("faktur_tgl")) == pd.to_datetime(row.get("tgl_dok"))
    except Exception:
        res["match_tgl_faktur_invoice"] = False
    try:
        # e. PPN faktur == PPN invoice
        res["match_ppn_faktur_invoice"] = float(row.get("faktur_ppn",0)) == float(row.get("inv_ppn",0))
    except Exception:
        res["match_ppn_faktur_invoice"] = False
    # overall: semua harus True
    res["match_overall"] = all([res["match_tgl_ba_range"], res["match_nilai_invoice"],
                                res["match_tgl_faktur_invoice"], res["match_ppn_faktur_invoice"]])
    return res

def load_lottie(url: str):
    try:
        r = requests.get(url)
    except Exception:
        return None
    if r.status_code != 200:
        return None
    return r.json()

# ---------------- HEADER ----------------
st.markdown("<h2 style='text-align: center;'>📑 Sistem Verifikasi 3-Way Matching</h2>", unsafe_allow_html=True)
lottie_json = load_lottie("https://assets5.lottiefiles.com/packages/lf20_q5pk6p1k.json")
if lottie_json:
    st_lottie(lottie_json, height=120, key="intro")
st.markdown("Selamat datang di sistem verifikasi **Account Payable** berbasis digitalisasi 🚀")

# ---------------- LAYOUT: top menu for listing ----------------
st.sidebar.title("🔎 View Data")
view_mode = st.sidebar.selectbox("Pilih Tampilan Data", ["Public Listing (no password)", "Admin Listing (password)"])
st.sidebar.markdown("---")

# ---------------- PUBLIC LISTING (no password) ----------------
if view_mode == "Public Listing (no password)":
    st.header("📂 Public Listing (Tanpa Password)")
    df_all = load_db()
    if df_all.empty:
        st.info("Belum ada data.")
    else:
        # hanya tampilkan yang visibility == 'public'
        df_public = df_all[df_all["visibility"] == "public"].copy()
        if df_public.empty:
            st.info("Tidak ada data publik.")
        else:
            st.dataframe(df_public.sort_values("created_at", ascending=False).reset_index(drop=True))
    st.markdown("---")
    st.info("Untuk lihat semua (termasuk private), pilih 'Admin Listing' di sidebar dan masukkan password.")

# ---------------- ADMIN LISTING (butuh password) ----------------
else:
    st.header("🔐 Admin Listing")
    pw = st.text_input("Masukkan Admin Password", type="password")
    if st.button("Masuk Admin"):
        if pw == ADMIN_PASSWORD:
            st.success("Login Admin berhasil. Menampilkan semua data.")
            df_all = load_db()
            if df_all.empty:
                st.info("Belum ada data.")
            else:
                st.dataframe(df_all.sort_values("created_at", ascending=False).reset_index(drop=True))
                # simple tools: cari berdasarkan SPM
                spm_search = st.text_input("Cari Nomor SPM (ketik lalu Enter)")
                if spm_search:
                    filtered = df_all[df_all["no_spm"].astype(str).str.contains(spm_search, case=False, na=False)]
                    st.dataframe(filtered)
        else:
            st.error("Password admin salah.")

st.markdown("---")
st.sidebar.markdown("⚙️ Untuk input / edit, gunakan halaman utama (di bawah).")

# ---------------- MAIN: Login Verifikator untuk Input / Edit ----------------
if "verif_logged" not in st.session_state:
    st.session_state.verif_logged = False

st.header("🖊️ Form Input / Edit (Verifikator)")
pw_ver = st.text_input("🔑 Masukkan Password Verifikator (untuk input/edit)", type="password", key="pwver")
if st.button("Login Verifikator"):
    if pw_ver == ADMIN_PASSWORD:
        st.session_state.verif_logged = True
        st.success("Login verifikator berhasil.")
    else:
        st.error("Password verifikator salah.")
        st.session_state.verif_logged = False

if not st.session_state.verif_logged:
    st.info("Silakan login verifikator untuk input atau edit data.")
    st.stop()

# ---------------- Setelah verifikator login: aksi Input Baru atau Edit ----------------
mode = st.radio("Pilih Aksi", ["Input Baru", "Edit Verifikasi"], horizontal=True)

# load existing DB for SPM list
db = load_db()
existing_spms = list(db["no_spm"].unique()) if not db.empty else []

if mode == "Input Baru":
    st.subheader("📥 Input Baru")
    # dasar verifikator
    nama_verifikator = st.text_input("Nama Verifikator")
    no_spm = st.text_input("Nomor SPM (unik)")

    # ---- Tabbed forms ----
    tabs = st.tabs(["Kontrak", "Berita Acara", "Dokumen Penagihan", "3-Way Matching Preview", "Status Transaksi"])
    with tabs[0]:
        st.markdown("### Dasar Pekerjaan / Kontrak")
        judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan")
        tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan")
        col1, col2 = st.columns(2)
        mulai = col1.date_input("Tanggal Mulai Pekerjaan")
        selesai = col2.date_input("Tanggal Selesai Pekerjaan")
        col3, col4, col5 = st.columns(3)
        dpp = col3.number_input("DPP", min_value=0.0, format="%.2f")
        ppn = col4.number_input("PPN", min_value=0.0, format="%.2f")
        total = col5.number_input("Total Nilai Pekerjaan", min_value=0.0, format="%.2f")
        jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan")

    with tabs[1]:
        st.markdown("### Berita Acara")
        tgl_ba = st.date_input("Tanggal Berita Acara")
        progress = st.text_area("Progress Pekerjaan")

    with tabs[2]:
        st.markdown("### Dokumen Penagihan")
        judul_tagihan = st.text_input("Judul Tagihan")
        syarat_progress = st.text_input("Syarat dalam kontrak (progress)")
        syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0, max_value=100, step=1)
        tgl_dok = st.date_input("Tanggal Dokumen Penagihan")
        c1,c2,c3 = st.columns(3)
        inv_dpp = c1.number_input("Invoice DPP", min_value=0.0, format="%.2f")
        inv_ppn = c2.number_input("Invoice PPN", min_value=0.0, format="%.2f")
        inv_total = c3.number_input("Total Invoice", min_value=0.0, format="%.2f")
        st.markdown("#### Faktur Pajak")
        f1,f2 = st.columns(2)
        faktur_no = f1.text_input("Nomor Faktur Pajak")
        faktur_tgl = f2.date_input("Tanggal Faktur Pajak")
        f3,f4 = st.columns(2)
        faktur_dpp = f3.number_input("Faktur Pajak DPP", min_value=0.0, format="%.2f")
        faktur_ppn = f4.number_input("Faktur Pajak PPN", min_value=0.0, format="%.2f")

    with tabs[3]:
        st.markdown("### Preview 3-Way Matching (bersifat preview sebelum simpan)")
        preview_row = {
            "mulai": str(mulai), "selesai": str(selesai), "tgl_ba": str(tgl_ba),
            "inv_total": inv_total, "total": total,
            "faktur_tgl": str(faktur_tgl), "tgl_dok": str(tgl_dok),
            "faktur_ppn": faktur_ppn, "inv_ppn": inv_ppn
        }
        match_res = compute_matching(preview_row)
        st.write("a) Tanggal BA dalam range kontrak:", "✅" if match_res["match_tgl_ba_range"] else "❌")
        st.write("b) Syarat penagihan sesuai kontrak:", "TBD (cek manual)" )
        st.write("c) Nilai invoice sesuai kontrak:", "✅" if match_res["match_nilai_invoice"] else "❌")
        st.write("d) Tanggal Faktur = Tanggal Invoice:", "✅" if match_res["match_tgl_faktur_invoice"] else "❌")
        st.write("e) PPN Faktur = PPN Invoice:", "✅" if match_res["match_ppn_faktur_invoice"] else "❌")
        st.write("f) Kesimpulan sistem:", "MATCH" if match_res["match_overall"] else "NOT MATCH")

    with tabs[4]:
        st.markdown("### Status Transaksi (sebelum simpan)")
        approved = st.checkbox("Disetujui (Approve)")
        alasan = ""
        if not approved:
            alasan = st.text_area("Jika tidak disetujui, isi alasan (wajib jika tidak approve)")
        visibility = st.radio("Visibility data:", ["public","private"], index=0, horizontal=True)

    # ---- Tombol Simpan ----
    if st.button("💾 Simpan Data"):
        # validasi minimal
        if not nama_verifikator or not no_spm:
            st.error("Nama Verifikator dan Nomor SPM harus diisi.")
        else:
            # prepare row
            row = {
                "created_at": datetime.now().isoformat(),
                "nama_verifikator": nama_verifikator,
                "no_spm": no_spm,
                "judul_kontrak": judul_kontrak,
                "tgl_kontrak": str(tgl_kontrak),
                "mulai": str(mulai),
                "selesai": str(selesai),
                "dpp": dpp,
                "ppn": ppn,
                "total": total,
                "jaminan": bool(jaminan),
                "tgl_ba": str(tgl_ba),
                "progress": progress,
                "judul_tagihan": judul_tagihan,
                "syarat_progress": syarat_progress,
                "syarat_persen": syarat_persen,
                "tgl_dok": str(tgl_dok),
                "inv_dpp": inv_dpp,
                "inv_ppn": inv_ppn,
                "inv_total": inv_total,
                "faktur_no": faktur_no,
                "faktur_tgl": str(faktur_tgl),
                "faktur_dpp": faktur_dpp,
                "faktur_ppn": faktur_ppn,
                # placeholders untuk matching fields; akan diisi
                "match_tgl_ba_range": "",
                "match_nilai_invoice": "",
                "match_tgl_faktur_invoice": "",
                "match_ppn_faktur_invoice": "",
                "match_overall": "",
                "approved": bool(approved),
                "approved_at": datetime.now().isoformat() if approved else "",
                "notapproved_reason": alasan if not approved else "",
                "notapproved_at": datetime.now().isoformat() if not approved else "",
                "visibility": visibility
            }
            # compute matching
            matches = compute_matching(row)
            row["match_tgl_ba_range"] = matches["match_tgl_ba_range"]
            row["match_nilai_invoice"] = matches["match_nilai_invoice"]
            row["match_tgl_faktur_invoice"] = matches["match_tgl_faktur_invoice"]
            row["match_ppn_faktur_invoice"] = matches["match_ppn_faktur_invoice"]
            row["match_overall"] = matches["match_overall"]

            # save
            save_row(row)
            st.success(f"Data SPM {no_spm} disimpan. (visibility={visibility})")
            # refresh db in memory
            db = load_db()
            existing_spms = list(db["no_spm"].unique())

# ---------------- EDIT VERIFIKASI ----------------
else:
    st.subheader("✏️ Edit Verifikasi")
    db = load_db()
    if db.empty:
        st.info("Belum ada data untuk di-edit.")
    else:
        spm_selected = st.selectbox("Pilih Nomor SPM untuk diedit", options=db["no_spm"].unique())
        if spm_selected:
            # load latest record for that SPM
            record = db[db["no_spm"] == spm_selected].sort_values("created_at").iloc[-1].to_dict()

            st.markdown("### Data terpilih (muat ke form)")
            st.write(f"Nomor SPM: {record.get('no_spm')}, Input oleh: {record.get('nama_verifikator')}, Tanggal: {record.get('created_at')}")
            # show editable fields (you can expand as needed)
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan", value=record.get("judul_kontrak",""))
            tgl_kontrak = st.date_input("Tanggal Kontrak Pekerjaan", value=pd.to_datetime(record.get("tgl_kontrak")).date() if record.get("tgl_kontrak") else None)
            col1, col2 = st.columns(2)
            mulai = col1.date_input("Tanggal Mulai Pekerjaan", value=pd.to_datetime(record.get("mulai")).date() if record.get("mulai") else None)
            selesai = col2.date_input("Tanggal Selesai Pekerjaan", value=pd.to_datetime(record.get("selesai")).date() if record.get("selesai") else None)
            col3, col4, col5 = st.columns(3)
            dpp = col3.number_input("DPP", value=float(record.get("dpp") or 0.0), format="%.2f")
            ppn = col4.number_input("PPN", value=float(record.get("ppn") or 0.0), format="%.2f")
            total = col5.number_input("Total Nilai Pekerjaan", value=float(record.get("total") or 0.0), format="%.2f")
            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan", value=bool(record.get("jaminan")))
            # BA
            tgl_ba = st.date_input("Tanggal Berita Acara", value=pd.to_datetime(record.get("tgl_ba")).date() if record.get("tgl_ba") else None)
            progress = st.text_area("Progress Pekerjaan", value=record.get("progress",""))
            # Dokumen Penagihan
            judul_tagihan = st.text_input("Judul Tagihan", value=record.get("judul_tagihan",""))
            syarat_progress = st.text_input("Syarat dalam kontrak (progress)", value=record.get("syarat_progress",""))
            syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0, max_value=100, value=int(record.get("syarat_persen") or 0))
            tgl_dok = st.date_input("Tanggal Dokumen Penagihan", value=pd.to_datetime(record.get("tgl_dok")).date() if record.get("tgl_dok") else None)
            c1,c2,c3 = st.columns(3)
            inv_dpp = c1.number_input("Invoice DPP", value=float(record.get("inv_dpp") or 0.0), format="%.2f")
            inv_ppn = c2.number_input("Invoice PPN", value=float(record.get("inv_ppn") or 0.0), format="%.2f")
            inv_total = c3.number_input("Total Invoice", value=float(record.get("inv_total") or 0.0), format="%.2f")
            faktur_no = st.text_input("Nomor Faktur Pajak", value=record.get("faktur_no",""))
            faktur_tgl = st.date_input("Tanggal Faktur Pajak", value=pd.to_datetime(record.get("faktur_tgl")).date() if record.get("faktur_tgl") else None)
            faktur_dpp = st.number_input("Faktur Pajak DPP", value=float(record.get("faktur_dpp") or 0.0), format="%.2f")
            faktur_ppn = st.number_input("Faktur Pajak PPN", value=float(record.get("faktur_ppn") or 0.0), format="%.2f")
            approved = st.checkbox("Disetujui (Approve)", value=bool(record.get("approved")))
            alasan = st.text_area("Alasan jika tidak disetujui", value=record.get("notapproved_reason",""))
            visibility = st.radio("Visibility data:", ["public","private"], index=0 if record.get("visibility","public")=="public" else 1, horizontal=True)

            if st.button("💾 Simpan Perubahan"):
                # create new row as "updated" record (append new row)
                row = {
                    "created_at": datetime.now().isoformat(),
                    "nama_verifikator": record.get("nama_verifikator",""),
                    "no_spm": record.get("no_spm",""),
                    "judul_kontrak": judul_kontrak,
                    "tgl_kontrak": str(tgl_kontrak),
                    "mulai": str(mulai),
                    "selesai": str(selesai),
                    "dpp": dpp,
                    "ppn": ppn,
                    "total": total,
                    "jaminan": bool(jaminan),
                    "tgl_ba": str(tgl_ba),
                    "progress": progress,
                    "judul_tagihan": judul_tagihan,
                    "syarat_progress": syarat_progress,
                    "syarat_persen": syarat_persen,
                    "tgl_dok": str(tgl_dok),
                    "inv_dpp": inv_dpp,
                    "inv_ppn": inv_ppn,
                    "inv_total": inv_total,
                    "faktur_no": faktur_no,
                    "faktur_tgl": str(faktur_tgl),
                    "faktur_dpp": faktur_dpp,
                    "faktur_ppn": faktur_ppn,
                    "match_tgl_ba_range": "",
                    "match_nilai_invoice": "",
                    "match_tgl_faktur_invoice": "",
                    "match_ppn_faktur_invoice": "",
                    "match_overall": "",
                    "approved": bool(approved),
                    "approved_at": datetime.now().isoformat() if approved else "",
                    "notapproved_reason": alasan if not approved else "",
                    "notapproved_at": datetime.now().isoformat() if not approved else "",
                    "visibility": visibility
                }
                matches = compute_matching(row)
                row["match_tgl_ba_range"] = matches["match_tgl_ba_range"]
                row["match_nilai_invoice"] = matches["match_nilai_invoice"]
                row["match_tgl_faktur_invoice"] = matches["match_tgl_faktur_invoice"]
                row["match_ppn_faktur_invoice"] = matches["match_ppn_faktur_invoice"]
                row["match_overall"] = matches["match_overall"]

                save_row(row)
                st.success("Perubahan disimpan sebagai versi baru (riwayat tetap tersimpan).")
