# Serial Python Minimalis: Tutorial #01-Python Dasar

**Penulis:** Ahmad R. T. Nugraha (@fisikawan.gendeng), Nabilla S. Bachtiar, dan M. S. Ukhtary  
**Versi:** 21 Januari 2026

---

Seri tutorial "Python Minimalis" ini ditujukan bagi para pelajar fisika secara khusus dan sains secara umum agar dapat "secukupnya" menguasai pemrograman dalam bahasa Python untuk keperluan komputasi numerik. Karena "minimalis", paradigma pemrograman yang ditekankan adalah pemrograman prosedural walaupun Python mendukung teknik lebih lanjut seperti pemrograman berorientasi objek (*object-oriented programming*/OOP).

Sebelum memulai pemrograman numerik, kita perlu menyiapkan kelengkapan "persenjataan" kita. Pemrograman Python untuk keperluan kita ini membutuhkan dua komponen utama: **interpreter** (mesin penerjemah kode) dan **integrated development environment** (IDE) atau tempat menulis kode. Kombinasi yang direkomendasikan adalah *interpreter* **Python** dari situs web resminya dan IDE **Visual Studio Code (VS Code)**. Jika "malas" menginstal di komputer sendiri, kita masih bisa menggunakan lingkungan pemrograman Python berbasis *cloud* seperti `Google Colab`.

## 1. Instalasi Python dan Kelengkapannya

Untuk pemrograman Python yang profesional, kita tidak disarankan menginstal pustaka (*library*) secara global di sistem komputer karena dapat menyebabkan konflik versi. Praktik terbaik (*best practice*) adalah dengan menggunakan **virtual environment** (`venv`), yakni semacam "ruang isolasi" tempat kita bisa menginstal Python dan paket-paket tertentu (seperti NumPy atau Jupyter) khusus untuk satu proyek saja tanpa mengganggu sistem utama.

### Langkah 1: Instalasi Python & VS Code

Pastikan dua komponen dasar berikut ini terinstal:
1.  **Python** dari [python.org](https://python.org) untuk pengguna Windows.  
    *Penting:* Saat instalasi, pastikan mencentang opsi **"Add Python to PATH"**. Sementara itu, bagi pengguna Linux (Debian/Ubuntu), jalankan:
    ```bash
    sudo apt install python3 python3-venv
    ```
2.  **Visual Studio Code (VS Code).** Unduh dari [code.visualstudio.com](https://code.visualstudio.com) dan lakukan instalasi standar.

### Langkah 2: Membuat Folder Proyek & Virtual Environment

1.  Buat folder baru, misal bernama `PythonMinimalis`.
2.  Buka folder tersebut menggunakan VS Code (*File > Open Folder*).
3.  Buka Terminal di VS Code (`Ctrl + ` `).
4.  Ketik perintah berikut untuk membuat `venv`:
    ```bash
    python -m venv .venv
    ```

### Langkah 3: Aktivasi Environment

Sebelum menginstal paket, kita harus "masuk" ke dalam lingkungan virtual.

* **Linux/macOS:**
    ```bash
    source .venv/bin/activate
    ```
* **Windows (PowerShell):**
    ```powershell
    .venv\Scripts\Activate.ps1
    ```

> **Masalah Umum di Windows: UnauthorizedAccess** > Jika muncul pesan error merah terkait script execution, jalankan perintah ini di terminal:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
> Lalu coba jalankan perintah aktivasi lagi.

Jika berhasil, akan muncul tanda **`(.venv)`** di sebelah kiri baris perintah terminal.

### Langkah 4: Instalasi Paket Ilmiah

Jalankan perintah berikut:
```bash
pip install numpy scipy matplotlib jupyter
```