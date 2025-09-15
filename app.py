import streamlit as st
import pandas as pd
import os
from datetime import datetime, date

DB_PATH = "verifikasi_ap.csv"
PASSWORD = "apteam"

# ---------------- UTIL ----------------
def ensure_db():
    if not os.path.exists(DB_PATH):
        df = pd.DataFrame(columns=ALL_COLUMNS)
        df.to_csv(DB_PATH, index=False)

def load_data():
    if os.path.exists(DB_PATH):
        df = pd.read_csv(DB_PATH, dtype=str).fillna("")
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    return pd.DataFrame(columns=ALL_COLUMNS)

def save_row(row: dict):
    ensure_db()
    df = load_data()
    df["no_spm"] = df["no_spm"].astype(str).str.strip()
    row["no_spm"] = str(row["no_spm"]).strip()
    df = df[df["no_spm"] != row["no_spm"]]  # replace jika ada
    row["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DB_PATH, index=False)

def format_rupiah(val):
    try:
        return f"Rp {int(float(val)):,}".replace(",", ".")
    except:
        return val

ALL_COLUMNS = [
    "last_updated", "nama_verifikator", "no_spm",
    # Kontrak
    "judul_kontrak", "tgl_kontrak", "mulai", "selesai",
    "dpp", "ppn", "total",
    "jaminan", "jaminan_nilai", "jaminan_mulai", "jaminan_selesai",
    # Berita Acara
    "tgl_ba", "progress",
    # Dokumen Penagihan
    "judul_tagihan", "syarat_progress", "syarat_persen",
    "tgl_invoice", "dpp_invoice", "ppn_invoice", "total_invoice",
    "faktur_no", "faktur_tgl", "faktur_dpp", "faktur_ppn",
    # Matching
    "kesimpulan",
    # Status
    "approved", "alasan", "tgl_approve"
]

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
            st.stop()
    else:
        st.stop()

# ---------------- MENU ----------------
st.sidebar.title("📂 Menu")
menu = st.sidebar.radio("Pilih menu:", ["Input Baru", "Edit Verifikasi", "Lihat Data Publik"])

df = load_data()

# ---------------- INPUT BARU / EDIT ----------------
if menu in ["Input Baru", "Edit Verifikasi"]:
    nama = st.text_input("👤 Nama Verifikator")
    if menu == "Input Baru":
        no_spm = st.text_input("📑 Nomor SPM")
        data_lama = {}
    else:
        existing = df["no_spm"].unique().tolist()
        no_spm = st.selectbox("📑 Pilih Nomor SPM", existing)
        data_lama = df[df["no_spm"] == str(no_spm)].iloc[0].to_dict() if no_spm else {}

    tabs = st.tabs([
        "📜 Dasar Kontrak",
        "📝 Berita Acara",
        "📂 Dokumen Penagihan",
        "🔎 3-Way Matching",
        "✅ Status Transaksi"
    ])

    # ---- Tab Kontrak ----
    with tabs[0]:
        judul_kontrak = st.text_input("Judul Kontrak/Pekerjaan", data_lama.get("judul_kontrak", ""))
        tgl_kontrak = st.date_input("Tanggal Kontrak", value=pd.to_datetime(data_lama.get("tgl_kontrak", date.today())))
        mulai = st.date_input("Tanggal Mulai", value=pd.to_datetime(data_lama.get("mulai", date.today())))
        selesai = st.date_input("Tanggal Selesai", value=pd.to_datetime(data_lama.get("selesai", date.today())))

        dpp = st.number_input("DPP", value=float(data_lama.get("dpp", 0)))
        ppn = round(dpp * 0.11, 2)
        total = dpp + ppn
        st.write(f"PPN (11%): {format_rupiah(ppn)}")
        st.write(f"Total Nilai Pekerjaan: {format_rupiah(total)}")

        jaminan = st.checkbox("Jaminan Pelaksanaan", value=(data_lama.get("jaminan", "") == "ya"))
        jaminan_nilai, jaminan_mulai, jaminan_selesai = "", "", ""
        if jaminan:
            jaminan_nilai = st.number_input("Nilai Jaminan", value=float(data_lama.get("jaminan_nilai", 0)))
            jaminan_mulai = st.date_input("Mulai Berlaku", value=pd.to_datetime(data_lama.get("jaminan_mulai", date.today())))
            jaminan_selesai = st.date_input("Selesai Berlaku", value=pd.to_datetime(data_lama.get("jaminan_selesai", date.today())))

    # ---- Tab Berita Acara ----
    with tabs[1]:
        tgl_ba = st.date_input("Tanggal Berita Acara", value=pd.to_datetime(data_lama.get("tgl_ba", date.today())))
        progress = st.text_input("Progress Pekerjaan", data_lama.get("progress", ""))

    # ---- Tab Dokumen Penagihan ----
    with tabs[2]:
        judul_tagihan = st.text_input("Judul Tagihan", data_lama.get("judul_tagihan", ""))
        syarat_progress = st.text_input("Progress sesuai kontrak", data_lama.get("syarat_progress", ""))
        syarat_persen = st.text_input("Nilai % sesuai kontrak", data_lama.get("syarat_persen", ""))

        tgl_invoice = st.date_input("Tanggal Dokumen Penagihan", value=pd.to_datetime(data_lama.get("tgl_invoice", date.today())))
        dpp_invoice = st.number_input("DPP Invoice", value=float(data_lama.get("dpp_invoice", 0)))
        ppn_invoice = round(dpp_invoice * 0.11, 2)
        total_invoice = dpp_invoice + ppn_invoice
        st.write(f"PPN (11%): {format_rupiah(ppn_invoice)}")
        st.write(f"Total Invoice: {format_rupiah(total_invoice)}")

        faktur_no = st.text_input("Nomor Faktur Pajak", data_lama.get("faktur_no", ""))
        faktur_tgl = st.date_input("Tanggal Faktur Pajak", value=pd.to_datetime(data_lama.get("faktur_tgl", date.today())))
        faktur_dpp = st.number_input("DPP Faktur", value=float(data_lama.get("faktur_dpp", 0)))
        faktur_ppn = st.number_input("PPN Faktur", value=float(data_lama.get("faktur_ppn", 0)))

    # ---- Tab Matching ----
    with tabs[3]:
        match_tanggal = "✅" if (mulai <= tgl_ba <= selesai) else "❌"
        match_syarat = "✅" if syarat_progress != "" else "❌"
        match_nilai = "✅" if abs(total - total_invoice) < 1 else "❌"
        match_faktur_tgl = "✅" if faktur_tgl == tgl_invoice else "❌"
        match_faktur_ppn = "✅" if abs(ppn_invoice - faktur_ppn) < 1 else "❌"
        kesimpulan = "OK" if all(x == "✅" for x in [match_tanggal, match_syarat, match_nilai, match_faktur_tgl, match_faktur_ppn]) else "Perlu dicek"

        st.subheader("📊 Ringkasan 3-Way Matching")
        summary = pd.DataFrame([
            ["Tanggal BA vs Kontrak", match_tanggal, f"BA: {tgl_ba}, Kontrak: {mulai} s.d {selesai}"],
            ["Syarat Penagihan", match_syarat, f"{syarat_progress} ({syarat_persen}%)"],
            ["Nilai Kontrak vs Invoice", match_nilai, f"Kontrak: {format_rupiah(total)}, Invoice: {format_rupiah(total_invoice)}"],
            ["Tanggal Faktur vs Invoice", match_faktur_tgl, f"Invoice: {tgl_invoice}, Faktur: {faktur_tgl}"],
            ["PPN Faktur vs Invoice", match_faktur_ppn, f"Invoice: {format_rupiah(ppn_invoice)}, Faktur: {format_rupiah(faktur_ppn)}"],
        ], columns=["Pemeriksaan", "Status", "Detail"])

        def highlight_status(val):
            if val == "✅":
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif val == "❌":
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            return ""

        st.dataframe(summary.style.applymap(highlight_status, subset=["Status"]))
        if kesimpulan == "OK":
            st.success(f"Kesimpulan Sistem: **{kesimpulan}**")
        else:
            st.error(f"Kesimpulan Sistem: **{kesimpulan}**")

    # ---- Tab Status ----
    with tabs[4]:
        approved = st.checkbox("Disetujui", value=(data_lama.get("approved", "") == "ya"))
        alasan = ""
        tgl_approve = date.today()
        if approved:
            tgl_approve = st.date_input("Tanggal Approve", value=pd.to_datetime(data_lama.get("tgl_approve", date.today())))
        else:
            alasan = st.text_area("Alasan Tidak Approve", data_lama.get("alasan", ""))
            tgl_approve = st.date_input("Tanggal Tidak Approve", value=pd.to_datetime(data_lama.get("tgl_approve", date.today())))

    # ---- Tombol Simpan ----
    if st.button("💾 Simpan"):
        row = {
            "nama_verifikator": nama,
            "no_spm": no_spm,
            "judul_kontrak": judul_kontrak, "tgl_kontrak": str(tgl_kontrak),
            "mulai": str(mulai), "selesai": str(selesai),
            "dpp": dpp, "ppn": ppn, "total": total,
            "jaminan": "ya" if jaminan else "tidak",
            "jaminan_nilai": jaminan_nilai, "jaminan_mulai": str(jaminan_mulai), "jaminan_selesai": str(jaminan_selesai),
            "tgl_ba": str(tgl_ba), "progress": progress,
            "judul_tagihan": judul_tagihan, "syarat_progress": syarat_progress, "syarat_persen": syarat_persen,
            "tgl_invoice": str(tgl_invoice), "dpp_invoice": dpp_invoice, "ppn_invoice": ppn_invoice, "total_invoice": total_invoice,
            "faktur_no": faktur_no, "faktur_tgl": str(faktur_tgl), "faktur_dpp": faktur_dpp, "faktur_ppn": faktur_ppn,
            "kesimpulan": kesimpulan,
            "approved": "ya" if approved else "tidak",
            "alasan": alasan, "tgl_approve": str(tgl_approve)
        }
        save_row(row)
        st.success("✅ Data berhasil disimpan!")

# ---------------- LIHAT DATA PUBLIK ----------------
elif menu == "Lihat Data Publik":
    st.subheader("📊 Data Verifikasi (Publik)")

    if not df.empty:
        df_show = df.copy()
        df_show["total"] = df_show["total"].apply(format_rupiah)
        df_show["approved_badge"] = df_show["approved"].apply(lambda x: "✅ Approved" if x == "ya" else "❌ Tidak Approved")
        df_show["kesimpulan_badge"] = df_show["kesimpulan"].apply(lambda x: "🟢 OK" if x == "OK" else "🔴 Perlu dicek")

        tampil = df_show[["last_updated", "no_spm", "nama_verifikator", "judul_kontrak", "total", "kesimpulan_badge", "approved_badge"]]
        tampil = tampil.sort_values("last_updated", ascending=False)

        def highlight_badge(val):
            if "✅" in val or "🟢" in val:
                return "background-color: #d4edda; color: #155724; font-weight: bold;"
            elif "❌" in val or "🔴" in val:
                return "background-color: #f8d7da; color: #721c24; font-weight: bold;"
            return ""

        st.dataframe(tampil.style.applymap(highlight_badge, subset=["kesimpulan_badge", "approved_badge"]))
    else:
        st.info("Belum ada data tersimpan.")
