import sqlite3
import tkinter as tk
from contextlib import contextmanager
from tkinter import ttk, messagebox

DB_NAME = "mahasiswa.db"
DAFTAR_PRODI = ["Informatika", "Sistem Informasi", "Manajemen", "Akuntansi"]


# Membuat koneksi database
@contextmanager
def koneksi():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# Membuat tabel mahasiswa
def buat_tabel():
    with koneksi() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS mahasiswa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nama TEXT NOT NULL,
                nim TEXT NOT NULL UNIQUE,
                prodi TEXT NOT NULL,
                alamat TEXT,
                angkatan INTEGER
            )
        """)

        # Memeriksa kolom angkatan pada database lama
        kolom = [
            row[1] for row in conn.execute(
                "PRAGMA table_info(mahasiswa)"
            )
        ]

        if "angkatan" not in kolom:
            conn.execute("""
                ALTER TABLE mahasiswa
                ADD COLUMN angkatan INTEGER
            """)


buat_tabel()

# Membuat jendela aplikasi
root = tk.Tk()
root.title("Aplikasi Data Mahasiswa")
root.geometry("1050x680")

judul = ttk.Label(
    root,
    text="APLIKASI DATA MAHASISWA",
    font=("Arial", 18, "bold")
)
judul.pack(pady=15)


# Membuat formulir input
form = ttk.LabelFrame(root, text="Formulir Mahasiswa", padding=15)
form.pack(fill="x", padx=15, pady=10)

ttk.Label(form, text="Nama").grid(row=0, column=0, padx=5, pady=5)
entry_nama = ttk.Entry(form, width=30)
entry_nama.grid(row=0, column=1, padx=5, pady=5)

ttk.Label(form, text="NIM").grid(row=0, column=2, padx=5, pady=5)
entry_nim = ttk.Entry(form, width=30)
entry_nim.grid(row=0, column=3, padx=5, pady=5)

ttk.Label(form, text="Program Studi").grid(row=1, column=0, padx=5, pady=5)
combo_prodi = ttk.Combobox(
    form,
    values=DAFTAR_PRODI,
    state="readonly",
    width=27
)
combo_prodi.grid(row=1, column=1, padx=5, pady=5)

ttk.Label(form, text="Alamat").grid(row=1, column=2, padx=5, pady=5)
entry_alamat = ttk.Entry(form, width=30)
entry_alamat.grid(row=1, column=3, padx=5, pady=5)

ttk.Label(form, text="Angkatan").grid(row=2, column=0, padx=5, pady=5)
entry_angkatan = ttk.Entry(form, width=30)
entry_angkatan.grid(row=2, column=1, padx=5, pady=5)


# Membuat tabel untuk menampilkan data
kolom = ("id", "nama", "nim", "prodi", "alamat", "angkatan")
tabel = ttk.Treeview(root, columns=kolom, show="headings")

judul_kolom = {
    "id": "ID",
    "nama": "Nama",
    "nim": "NIM",
    "prodi": "Program Studi",
    "alamat": "Alamat",
    "angkatan": "Angkatan"
}

for key in kolom:
    tabel.heading(key, text=judul_kolom[key])
    tabel.column(key, width=140, anchor="center")

tabel.pack(fill="both", expand=True, padx=15, pady=10)

id_terpilih = None


# Menampilkan data dari database
def tampilkan_data(kata_kunci=""):
    for item in tabel.get_children():
        tabel.delete(item)

    with koneksi() as conn:
        if kata_kunci.strip():
            pola = f"%{kata_kunci.strip()}%"

            rows = conn.execute("""
                SELECT id, nama, nim, prodi, alamat, angkatan
                FROM mahasiswa
                WHERE nama LIKE ? OR nim LIKE ?
                ORDER BY id DESC
            """, (pola, pola)).fetchall()

        else:
            rows = conn.execute("""
                SELECT id, nama, nim, prodi, alamat, angkatan
                FROM mahasiswa
                ORDER BY id DESC
            """).fetchall()

    for row in rows:
        tabel.insert("", tk.END, values=row)


# Mengosongkan formulir
def bersihkan_form():
    global id_terpilih
    id_terpilih = None

    entry_nama.delete(0, tk.END)
    entry_nim.delete(0, tk.END)
    combo_prodi.set("")
    entry_alamat.delete(0, tk.END)
    entry_angkatan.delete(0, tk.END)

    tabel.selection_remove(tabel.selection())
    entry_nama.focus_set()


# Mengambil dan memvalidasi data dari formulir
def ambil_form():
    nama = entry_nama.get().strip()
    nim = entry_nim.get().strip()
    prodi = combo_prodi.get().strip()
    alamat = entry_alamat.get().strip()
    angkatan_teks = entry_angkatan.get().strip()

    if not nama or not nim or not prodi:
        messagebox.showwarning(
            "Validasi",
            "Nama, NIM, dan Program Studi wajib diisi."
        )
        return None

    if angkatan_teks:
        try:
            angkatan = int(angkatan_teks)
            if angkatan < 1900 or angkatan > 2100:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Validasi",
                "Angkatan harus berupa tahun yang valid."
            )
            return None
    else:
        angkatan = None

    return nama, nim, prodi, alamat, angkatan


# Menyimpan data mahasiswa
def simpan_data():
    data = ambil_form()

    if data is None:
        return

    try:
        with koneksi() as conn:
            conn.execute("""
                INSERT INTO mahasiswa
                (nama, nim, prodi, alamat, angkatan)
                VALUES (?, ?, ?, ?, ?)
            """, data)

        messagebox.showinfo("Berhasil", "Data berhasil disimpan.")
        tampilkan_data(entry_cari.get())
        bersihkan_form()

    except sqlite3.IntegrityError:
        messagebox.showerror("NIM Duplikat", "NIM sudah terdaftar.")

    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


# Mengambil ID data yang dipilih
def isi_form_dari_tabel(event=None):
    global id_terpilih

    pilihan = tabel.selection()

    if not pilihan:
        return

    id_terpilih = int(tabel.item(pilihan[0], "values")[0])

    with koneksi() as conn:
        row = conn.execute("""
            SELECT nama, nim, prodi, alamat, angkatan
            FROM mahasiswa
            WHERE id = ?
        """, (id_terpilih,)).fetchone()

    if row is None:
        return

    entry_nama.delete(0, tk.END)
    entry_nim.delete(0, tk.END)
    combo_prodi.set("")
    entry_alamat.delete(0, tk.END)
    entry_angkatan.delete(0, tk.END)

    entry_nama.insert(0, row[0])
    entry_nim.insert(0, row[1])
    combo_prodi.set(row[2])
    entry_alamat.insert(0, row[3] or "")

    if row[4] is not None:
        entry_angkatan.insert(0, str(row[4]))


# Mengubah data mahasiswa
def ubah_data():
    if id_terpilih is None:
        messagebox.showwarning(
            "Pilih Data",
            "Pilih data yang akan diubah."
        )
        return

    data = ambil_form()

    if data is None:
        return

    try:
        with koneksi() as conn:
            conn.execute("""
                UPDATE mahasiswa
                SET nama = ?, nim = ?, prodi = ?, alamat = ?, angkatan = ?
                WHERE id = ?
            """, (*data, id_terpilih))

        tampilkan_data(entry_cari.get())
        bersihkan_form()

        messagebox.showinfo("Berhasil", "Data berhasil diperbarui.")

    except sqlite3.IntegrityError:
        messagebox.showerror(
            "NIM Duplikat",
            "NIM sudah digunakan mahasiswa lain."
        )

    except sqlite3.Error as error:
        messagebox.showerror("Kesalahan Database", str(error))


# Menghapus data mahasiswa
def hapus_data():
    if id_terpilih is None:
        messagebox.showwarning(
            "Pilih Data",
            "Pilih data yang akan dihapus."
        )
        return

    with koneksi() as conn:
        row = conn.execute(
            "SELECT nama FROM mahasiswa WHERE id = ?",
            (id_terpilih,)
        ).fetchone()

    nama = row[0] if row else "mahasiswa ini"

    konfirmasi = messagebox.askyesno(
        "Konfirmasi",
        f"Apakah Anda yakin ingin menghapus data {nama}?"
    )

    if not konfirmasi:
        return

    with koneksi() as conn:
        conn.execute(
            "DELETE FROM mahasiswa WHERE id = ?",
            (id_terpilih,)
        )

    tampilkan_data(entry_cari.get())
    bersihkan_form()

    messagebox.showinfo("Berhasil", "Data berhasil dihapus.")


# Mencari mahasiswa berdasarkan nama atau NIM
def cari_data():
    tampilkan_data(entry_cari.get())


# Menampilkan seluruh data mahasiswa
def tampilkan_semua():
    entry_cari.delete(0, tk.END)
    tampilkan_data()


# Membuat bagian pencarian
frame_cari = ttk.LabelFrame(
    root,
    text="Pencarian Mahasiswa",
    padding=10
)
frame_cari.pack(fill="x", padx=15, pady=5)

entry_cari = ttk.Entry(frame_cari, width=40)
entry_cari.pack(side="left", padx=5)

ttk.Button(
    frame_cari,
    text="Cari",
    command=cari_data
).pack(side="left", padx=5)

ttk.Button(
    frame_cari,
    text="Tampilkan Semua",
    command=tampilkan_semua
).pack(side="left", padx=5)


# Menghubungkan fungsi dengan tombol
baris_tombol = ttk.Frame(root)
baris_tombol.pack(fill="x", padx=15, pady=10)

ttk.Button(
    baris_tombol,
    text="Simpan Data",
    command=simpan_data
).pack(side="left", padx=4)

ttk.Button(
    baris_tombol,
    text="Ubah Data",
    command=ubah_data
).pack(side="left", padx=4)

ttk.Button(
    baris_tombol,
    text="Hapus Data",
    command=hapus_data
).pack(side="left", padx=4)

ttk.Button(
    baris_tombol,
    text="Refresh",
    command=tampilkan_semua
).pack(side="left", padx=4)

ttk.Button(
    baris_tombol,
    text="Bersihkan Form",
    command=bersihkan_form
).pack(side="left", padx=4)


# Menjalankan aplikasi
tabel.bind("<<TreeviewSelect>>", isi_form_dari_tabel)

tampilkan_data()
root.mainloop()