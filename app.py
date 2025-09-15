# app.py
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="AP Verification System", layout="wide")
DB_PATH = "db.csv"
PASSWORD = "apteam123"

# -----------------------------
# Helpers
# -----------------------------
def ensure_db():
    """Create DB with full columns if not exists."""
    if not os.path.exists(DB_PATH):
        cols = [
            "nama_verifikator","no_spm",
            # Tab1 - Kontrak
            "judul_kontrak","tgl_kontrak","mulai","selesai","dpp","ppn","total",
            "jaminan","jaminan_nilai","jaminan_mulai","jaminan_selesai",
            # Tab2 - Berita Acara
            "tgl_ba","progress",
            # Tab3 - Dokumen Penagihan
            "judul_tagihan","syarat_progress","syarat_persen",
            "tgl_invoice","dpp_inv","ppn_inv","total_inv",
            "faktur_no","faktur_tgl","faktur_dpp","faktur_ppn",
            # Tab4 - matching results
            "match_tgl_ba_range","match_nilai_invoice","match_tgl_faktur_invoice","match_ppn_faktur_invoice","match_overall",
            # Tab5 - status
            "approved","alasan","tgl_status",
            # meta
            "last_updated"
        ]
        pd.DataFrame(columns=cols).to_csv(DB_PATH, index=False)

def load_data():
    ensure_db()
    return pd.read_csv(DB_PATH, dtype=str, keep_default_na=False)

def save_row_replace(row: dict):
    """Save row: replace existing no_spm if present, else append."""
    ensure_db()
    df = pd.read_csv(DB_PATH, dtype=str, keep_default_na=False)
    # normalize keys to string
    row_norm = {k: "" if v is None else v for k, v in row.items()}
    if row_norm.get("no_spm") in df["no_spm"].values:
        df = df[df["no_spm"] != row_norm.get("no_spm")]
    df = pd.concat([df, pd.DataFrame([row_norm])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)

def load_row(no_spm: str):
    df = load_data()
    sel = df[df["no_spm"] == str(no_spm)]
    if sel.empty:
        return None
    # return latest (last) record for that SPM
    return sel.iloc[-1].to_dict()

def parse_date_safe(val, default=date.today()):
    """Return a datetime.date object when possible, else default."""
    if val is None or val == "" or (isinstance(val, float) and pd.isna(val)):
        return default
    try:
        # if it's already a date/datetime
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        # try pandas
        parsed = pd.to_datetime(val, errors="coerce")
        if pd.isna(parsed):
            return default
        return parsed.date()
    except Exception:
        return default

def format_rp_str(x):
    try:
        x_f = float(x)
        return f"Rp {x_f:,.0f}"
    except Exception:
        return str(x)

def compute_matching_from_values(m):
    """m is dict with keys: mulai, selesai, tgl_ba, total (kontrak), total_inv, faktur_tgl, faktur_ppn, inv_ppn"""
    res = {}
    try:
        mulai = pd.to_datetime(m.get("mulai"), errors="coerce")
        selesai = pd.to_datetime(m.get("selesai"), errors="coerce")
        tgl_ba = pd.to_datetime(m.get("tgl_ba"), errors="coerce")
        res["match_tgl_ba_range"] = not (pd.isna(mulai) or pd.isna(selesai) or pd.isna(tgl_ba)) and (mulai <= tgl_ba <= selesai)
    except Exception:
        res["match_tgl_ba_range"] = False
    try:
        total = float(m.get("total") or 0)
        total_inv = float(m.get("total_inv") or 0)
        res["match_nilai_invoice"] = (abs(total - total_inv) < 0.01)  # tolerance
    except Exception:
        res["match_nilai_invoice"] = False
    try:
        faktur_tgl = pd.to_datetime(m.get("faktur_tgl"), errors="coerce")
        tgl_invoice = pd.to_datetime(m.get("tgl_invoice"), errors="coerce")
        res["match_tgl_faktur_invoice"] = not (pd.isna(faktur_tgl) or pd.isna(tgl_invoice)) and (faktur_tgl.date() == tgl_invoice.date())
    except Exception:
        res["match_tgl_faktur_invoice"] = False
    try:
        faktur_ppn = float(m.get("faktur_ppn") or 0)
        inv_ppn = float(m.get("ppn_inv") or 0)
        res["match_ppn_faktur_invoice"] = abs(faktur_ppn - inv_ppn) < 0.01
    except Exception:
        res["match_ppn_faktur_invoice"] = False
    res["match_overall"] = all([res["match_tgl_ba_range"], res["match_nilai_invoice"], res["match_tgl_faktur_invoice"], res["match_ppn_faktur_invoice"]])
    return res

# -----------------------------
# UI - Public view or login
# -----------------------------
st.sidebar.title("Navigasi")
page = st.sidebar.radio("Menu", ["Lihat Data (Publik)", "Workspace Verifikator"])

if page == "Lihat Data (Publik)":
    st.title("📊 Daftar SPM (Publik)")
    df = load_data()
    if df.empty:
        st.info("Belum ada data.")
    else:
        # show subset columns for public view
        show_cols = ["no_spm","judul_kontrak","total","total_inv","approved","tgl_status","last_updated"]
        existing = [c for c in show_cols if c in df.columns]
        st.dataframe(df[existing].fillna("").sort_values("last_updated", ascending=False).reset_index(drop=True))

# -----------------------------
# Workspace (requires login)
# -----------------------------
if page == "Workspace Verifikator":
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        pw = st.text_input("Masukkan password verifikator", type="password")
        if st.button("Login"):
            if pw == PASSWORD:
                st.session_state.logged_in = True
                st.success("Login berhasil")
            else:
                st.error("Password salah")
                st.stop()
        else:
            st.stop()

    st.title("🗂️ Workspace Verifikator")
    action = st.radio("Aksi", ["Input Baru", "Edit Verifikasi", "Lihat Semua Data"], horizontal=True)

    # -----------------------------
    # Input Baru
    # -----------------------------
    if action == "Input Baru":
        st.header("📥 Input Baru")
        nama_verifikator = st.text_input("Nama Verifikator")
        no_spm = st.text_input("Nomor SPM (unik)")

        if not no_spm:
            st.info("Masukkan Nomor SPM untuk memulai input.")
            st.stop()

        # Tabs for input
        tabs = st.tabs(["📄 Kontrak", "📝 Berita Acara", "📑 Dokumen Penagihan", "🔍 3-Way Matching", "✅ Status Transaksi"])

        # Tab Kontrak
        with tabs[0]:
            st.subheader("Dasar Pekerjaan / Kontrak")
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan")
            tgl_kontrak = st.date_input("Tanggal Kontrak", value=date.today())
            c1, c2 = st.columns(2)
            mulai = c1.date_input("Tanggal Mulai Pekerjaan", value=date.today())
            selesai = c2.date_input("Tanggal Selesai Pekerjaan", value=date.today())

            dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0, format="%.0f")
            ppn = round(dpp * 0.11, 2)
            total = round(dpp + ppn, 2)
            st.write(f"PPN (11%): {format_rp_str(ppn)}")
            st.write(f"Total kontrak: {format_rp_str(total)}")

            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan")
            jaminan_nilai = ""
            jaminan_mulai = ""
            jaminan_selesai = ""
            if jaminan:
                jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0, format="%.0f")
                jj1, jj2 = st.columns(2)
                jaminan_mulai = jj1.date_input("Jaminan Mulai", value=date.today())
                jaminan_selesai = jj2.date_input("Jaminan Selesai", value=date.today())

        # Tab Berita Acara
        with tabs[1]:
            st.subheader("Berita Acara")
            tgl_ba = st.date_input("Tanggal Berita Acara", value=date.today())
            progress = st.text_area("Progress Pekerjaan")

        # Tab Dokumen Penagihan
        with tabs[2]:
            st.subheader("Dokumen Penagihan")
            judul_tagihan = st.text_input("Judul Tagihan")
            syarat_progress = st.text_input("Syarat dalam kontrak (progress)")
            syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0.0, max_value=100.0, step=1.0)

            tgl_invoice = st.date_input("Tanggal Dokumen Penagihan", value=date.today())
            dpp_inv = st.number_input("DPP Invoice (Rp)", min_value=0.0, step=1000.0, format="%.0f")
            ppn_inv = round(dpp_inv * 0.11, 2)
            total_inv = round(dpp_inv + ppn_inv, 2)
            st.write(f"PPN Invoice: {format_rp_str(ppn_inv)}")
            st.write(f"Total Invoice: {format_rp_str(total_inv)}")

            st.markdown("**Faktur Pajak**")
            faktur_no = st.text_input("Nomor Faktur Pajak")
            faktur_tgl = st.date_input("Tanggal Faktur Pajak", value=date.today())
            faktur_dpp = st.number_input("DPP Faktur (Rp)", min_value=0.0, step=1000.0, format="%.0f")
            faktur_ppn = round(faktur_dpp * 0.11, 2)
            st.write(f"PPN Faktur: {format_rp_str(faktur_ppn)}")

        # Tab Matching (preview)
        with tabs[3]:
            st.subheader("3-Way Matching (Preview)")
            preview = {
                "mulai": str(mulai),
                "selesai": str(selesai),
                "tgl_ba": str(tgl_ba),
                "total": total,
                "total_inv": total_inv,
                "faktur_tgl": str(faktur_tgl),
                "tgl_invoice": str(tgl_invoice),
                "faktur_ppn": faktur_ppn,
                "ppn_inv": ppn_inv
            }
            mres = compute_matching_from_values(preview)
            st.write("a) Tanggal BA dalam range kontrak:", "✅" if mres["match_tgl_ba_range"] else "❌")
            st.write("b) Syarat penagihan sesuai kontrak: (cek manual)")
            st.write("c) Nilai invoice sesuai kontrak:", "✅" if mres["match_nilai_invoice"] else "❌")
            st.write("d) Tanggal Faktur = Tanggal Invoice:", "✅" if mres["match_tgl_faktur_invoice"] else "❌")
            st.write("e) PPN Faktur = PPN Invoice:", "✅" if mres["match_ppn_faktur_invoice"] else "❌")
            st.write("f) Kesimpulan:", "MATCH" if mres["match_overall"] else "NOT MATCH")

        # Tab Status
        with tabs[4]:
            st.subheader("Status Transaksi")
            approved = st.checkbox("Disetujui (Approve)?")
            alasan = ""
            if not approved:
                alasan = st.text_area("Alasan jika tidak disetujui")
            tgl_status = date.today() if approved or alasan else ""

        # Save button
        if st.button("💾 Simpan Data"):
            # prepare row; store dates as ISO string
            row = {
                "nama_verifikator": nama_verifikator or "",
                "no_spm": no_spm,
                "judul_kontrak": judul_kontrak or "",
                "tgl_kontrak": tgl_kontrak.isoformat() if isinstance(tgl_kontrak, date) else str(tgl_kontrak),
                "mulai": mulai.isoformat(),
                "selesai": selesai.isoformat(),
                "dpp": f"{dpp:.2f}",
                "ppn": f"{ppn:.2f}",
                "total": f"{total:.2f}",
                "jaminan": str(bool(jaminan)),
                "jaminan_nilai": f"{jaminan_nilai:.2f}" if jaminan and jaminan_nilai != "" else "",
                "jaminan_mulai": jaminan_mulai.isoformat() if jaminan and isinstance(jaminan_mulai, date) else "",
                "jaminan_selesai": jaminan_selesai.isoformat() if jaminan and isinstance(jaminan_selesai, date) else "",
                "tgl_ba": tgl_ba.isoformat(),
                "progress": progress or "",
                "judul_tagihan": judul_tagihan or "",
                "syarat_progress": syarat_progress or "",
                "syarat_persen": f"{syarat_persen:.2f}",
                "tgl_invoice": tgl_invoice.isoformat(),
                "dpp_inv": f"{dpp_inv:.2f}",
                "ppn_inv": f"{ppn_inv:.2f}",
                "total_inv": f"{total_inv:.2f}",
                "faktur_no": faktur_no or "",
                "faktur_tgl": faktur_tgl.isoformat(),
                "faktur_dpp": f"{faktur_dpp:.2f}",
                "faktur_ppn": f"{faktur_ppn:.2f}",
                # matching results
                "match_tgl_ba_range": str(mres["match_tgl_ba_range"]),
                "match_nilai_invoice": str(mres["match_nilai_invoice"]),
                "match_tgl_faktur_invoice": str(mres["match_tgl_faktur_invoice"]),
                "match_ppn_faktur_invoice": str(mres["match_ppn_faktur_invoice"]),
                "match_overall": str(mres["match_overall"]),
                # status
                "approved": str(bool(approved)),
                "alasan": alasan or "",
                "tgl_status": tgl_status.isoformat() if isinstance(tgl_status, date) else "",
                "last_updated": datetime.now().isoformat()
            }
            save_row_replace(row)
            st.success(f"Data SPM {no_spm} berhasil disimpan / diperbarui.")

    # -----------------------------
    # Edit Verifikasi
    # -----------------------------
    elif action == "Edit Verifikasi":
        st.header("✏️ Edit Verifikasi")
        df = load_data()
        if df.empty:
            st.info("Belum ada data untuk diedit.")
            st.stop()

        no_spm = st.selectbox("Pilih Nomor SPM", df["no_spm"].unique())
        if not no_spm:
            st.stop()

        data = load_row(no_spm)
        if not data:
            st.error("Data tidak ditemukan.")
            st.stop()

        # Prefill fields using parse_date_safe or safe conversion
        nama_verifikator = st.text_input("Nama Verifikator", value=data.get("nama_verifikator", ""))

        tabs = st.tabs(["📄 Kontrak", "📝 Berita Acara", "📑 Dokumen Penagihan", "🔍 3-Way Matching", "✅ Status Transaksi"])

        # Tab Kontrak
        with tabs[0]:
            judul_kontrak = st.text_input("Judul Kontrak / Pekerjaan", value=data.get("judul_kontrak", ""))
            tgl_kontrak_val = parse_date_safe(data.get("tgl_kontrak"))
            tgl_kontrak = st.date_input("Tanggal Kontrak", value=tgl_kontrak_val)

            mulai_val = parse_date_safe(data.get("mulai"))
            selesai_val = parse_date_safe(data.get("selesai"))
            c1, c2 = st.columns(2)
            mulai = c1.date_input("Tanggal Mulai Pekerjaan", value=mulai_val)
            selesai = c2.date_input("Tanggal Selesai Pekerjaan", value=selesai_val)

            dpp_val = float(data.get("dpp") or 0)
            dpp = st.number_input("DPP (Rp)", min_value=0.0, step=1000.0, value=dpp_val, format="%.0f")
            ppn = round(dpp * 0.11, 2)
            total = round(dpp + ppn, 2)
            st.write(f"PPN (11%): {format_rp_str(ppn)}")
            st.write(f"Total kontrak: {format_rp_str(total)}")

            jaminan_flag = True if data.get("jaminan", "").lower() in ["true","1","yes"] else False
            jaminan = st.checkbox("Jaminan Pelaksanaan dipersyaratkan", value=jaminan_flag)
            jaminan_nilai = ""
            jaminan_mulai = ""
            jaminan_selesai = ""
            if jaminan:
                jaminan_nilai_val = float(data.get("jaminan_nilai") or 0)
                jaminan_nilai = st.number_input("Nilai Jaminan (Rp)", min_value=0.0, step=1000.0, value=jaminan_nilai_val, format="%.0f")
                jj1, jj2 = st.columns(2)
                jaminan_mulai = jj1.date_input("Jaminan Mulai", value=parse_date_safe(data.get("jaminan_mulai")))
                jaminan_selesai = jj2.date_input("Jaminan Selesai", value=parse_date_safe(data.get("jaminan_selesai")))

        # Tab Berita Acara
        with tabs[1]:
            tgl_ba = st.date_input("Tanggal Berita Acara", value=parse_date_safe(data.get("tgl_ba")))
            progress = st.text_area("Progress Pekerjaan", value=data.get("progress", ""))

        # Tab Dokumen Penagihan
        with tabs[2]:
            judul_tagihan = st.text_input("Judul Tagihan", value=data.get("judul_tagihan", ""))
            syarat_progress = st.text_input("Syarat dalam kontrak (progress)", value=data.get("syarat_progress", ""))
            syarat_persen = float(data.get("syarat_persen") or 0)
            syarat_persen = st.number_input("Nilai % dalam kontrak", min_value=0.0, max_value=100.0, step=1.0, value=syarat_persen)

            tgl_invoice = st.date_input("Tanggal Dokumen Penagihan", value=parse_date_safe(data.get("tgl_invoice")))
            dpp_inv_val = float(data.get("dpp_inv") or 0)
            dpp_inv = st.number_input("DPP Invoice (Rp)", min_value=0.0, step=1000.0, value=dpp_inv_val, format="%.0f")
            ppn_inv = round(dpp_inv * 0.11, 2)
            total_inv = round(dpp_inv + ppn_inv, 2)
            st.write(f"PPN Invoice: {format_rp_str(ppn_inv)}")
            st.write(f"Total Invoice: {format_rp_str(total_inv)}")

            faktur_no = st.text_input("Nomor Faktur Pajak", value=data.get("faktur_no", ""))
            faktur_tgl = st.date_input("Tanggal Faktur Pajak", value=parse_date_safe(data.get("faktur_tgl")))
            faktur_dpp_val = float(data.get("faktur_dpp") or 0)
            faktur_dpp = st.number_input("DPP Faktur (Rp)", min_value=0.0, step=1000.0, value=faktur_dpp_val, format="%.0f")
            faktur_ppn = round(faktur_dpp * 0.11, 2)
            st.write(f"PPN Faktur: {format_rp_str(faktur_ppn)}")

        # Tab Matching
        with tabs[3]:
            st.subheader("3-Way Matching (Computed)")
            preview = {
                "mulai": str(mulai),
                "selesai": str(selesai),
                "tgl_ba": str(tgl_ba),
                "total": total,
                "total_inv": total_inv,
                "faktur_tgl": str(faktur_tgl),
                "tgl_invoice": str(tgl_invoice),
                "faktur_ppn": faktur_ppn,
                "ppn_inv": ppn_inv
            }
            mres = compute_matching_from_values(preview)
            st.write("a) Tanggal BA dalam range kontrak:", "✅" if mres["match_tgl_ba_range"] else "❌")
            st.write("b) Syarat penagihan sesuai kontrak: (cek manual)")
            st.write("c) Nilai invoice sesuai kontrak:", "✅" if mres["match_nilai_invoice"] else "❌")
            st.write("d) Tanggal Faktur = Tanggal Invoice:", "✅" if mres["match_tgl_faktur_invoice"] else "❌")
            st.write("e) PPN Faktur = PPN Invoice:", "✅" if mres["match_ppn_faktur_invoice"] else "❌")
            st.write("f) Kesimpulan:", "MATCH" if mres["match_overall"] else "NOT MATCH")

        # Tab Status
        with tabs[4]:
            approved_flag = True if data.get("approved", "").lower() in ["true","1","yes"] else False
            approved = st.checkbox("Disetujui (Approve)?", value=approved_flag)
            alasan_val = data.get("alasan", "")
            alasan = ""
            if not approved:
                alasan = st.text_area("Alasan jika tidak disetujui", value=alasan_val)
            tgl_status_val = parse_date_safe(data.get("tgl_status")) if data.get("tgl_status") else date.today()
            tgl_status = tgl_status_val if (approved or alasan) else ""

        # Update button
        if st.button("💾 Update Data"):
            mres_after = compute_matching_from_values({
                "mulai": str(mulai),
                "selesai": str(selesai),
                "tgl_ba": str(tgl_ba),
                "total": total,
                "total_inv": total_inv,
                "faktur_tgl": str(faktur_tgl),
                "tgl_invoice": str(tgl_invoice),
                "faktur_ppn": faktur_ppn,
                "ppn_inv": ppn_inv
            })
            row = {
                "nama_verifikator": nama_verifikator or data.get("nama_verifikator",""),
                "no_spm": no_spm,
                "judul_kontrak": judul_kontrak or "",
                "tgl_kontrak": tgl_kontrak.isoformat() if isinstance(tgl_kontrak, date) else str(tgl_kontrak),
                "mulai": mulai.isoformat(),
                "selesai": selesai.isoformat(),
                "dpp": f"{dpp:.2f}",
                "ppn": f"{ppn:.2f}",
                "total": f"{total:.2f}",
                "jaminan": str(bool(jaminan)),
                "jaminan_nilai": f"{jaminan_nilai:.2f}" if jaminan and jaminan_nilai != "" else "",
                "jaminan_mulai": jaminan_mulai.isoformat() if jaminan and isinstance(jaminan_mulai, date) else "",
                "jaminan_selesai": jaminan_selesai.isoformat() if jaminan and isinstance(jaminan_selesai, date) else "",
                "tgl_ba": tgl_ba.isoformat(),
                "progress": progress or "",
                "judul_tagihan": judul_tagihan or "",
                "syarat_progress": syarat_progress or "",
                "syarat_persen": f"{syarat_persen:.2f}",
                "tgl_invoice": tgl_invoice.isoformat(),
                "dpp_inv": f"{dpp_inv:.2f}",
                "ppn_inv": f"{ppn_inv:.2f}",
                "total_inv": f"{total_inv:.2f}",
                "faktur_no": faktur_no or "",
                "faktur_tgl": faktur_tgl.isoformat(),
                "faktur_dpp": f"{faktur_dpp:.2f}",
                "faktur_ppn": f"{faktur_ppn:.2f}",
                # matching
                "match_tgl_ba_range": str(mres_after["match_tgl_ba_range"]),
                "match_nilai_invoice": str(mres_after["match_nilai_invoice"]),
                "match_tgl_faktur_invoice": str(mres_after["match_tgl_faktur_invoice"]),
                "match_ppn_faktur_invoice": str(mres_after["match_ppn_faktur_invoice"]),
                "match_overall": str(mres_after["match_overall"]),
                # status
                "approved": str(bool(approved)),
                "alasan": alasan or "",
                "tgl_status": tgl_status.isoformat() if isinstance(tgl_status, date) else "",
                "last_updated": datetime.now().isoformat()
            }
            save_row_replace(row)
            st.success(f"Data SPM {no_spm} berhasil diperbarui.")

    # -----------------------------
    # Lihat Semua Data
    # -----------------------------
    elif action == "Lihat Semua Data":
        st.header("📚 Semua Data SPM")
        df = load_data()
        if df.empty:
            st.info("Belum ada data.")
        else:
            st.dataframe(df.fillna("").sort_values("last_updated", ascending=False).reset_index(drop=True))
