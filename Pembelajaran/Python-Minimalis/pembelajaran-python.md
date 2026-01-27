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


> **Masalah Umum di Windows: UnauthorizedAccess** \
> Jika muncul pesan error merah terkait script execution, jalankan perintah ini di terminal:  
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`  
> Lalu coba jalankan perintah aktivasi lagi.

Jika berhasil, akan muncul tanda **`(.venv)`** di sebelah kiri baris perintah terminal.

### Langkah 4: Instalasi Paket Ilmiah

Jalankan perintah berikut:
```bash
pip install numpy scipy matplotlib jupyter
```
### Langkah 5: Menghubungkan VS Code dengan venv

Agar VS Code menggunakan Python yang ada di dalam `.venv` (bukan Python global), kita perlu melakukan konfigurasi yang tepat.

#### **A. Format Jupyter Notebook (`*.ipynb`)**

1. Buka atau buat file baru dengan akhiran `.ipynb` (misal: `catatan.ipynb`).
2. Klik tombol kernel di pojok kanan atas editor (biasanya tertulis *Select Kernel* atau *Python 3...*).
3. Pilih **Select Another Kernel...** $\rightarrow$ **Python Environments**.
4. Cari pilihan yang memiliki label **Star** ($\star$) atau yang mengarah ke folder `.venv` kita.
   *Contoh:* `Python 3.10.0 ('.venv': venv)`.

#### **B. Format Skrip Python Biasa (`*.py`)**

1. Buka atau buka file berakhiran `.py`.
2. Klik indikator versi Python di pojok kanan bawah jendela status bar VS Code.
3. Pilih *interpreter* yang mengarah ke `./.venv/Scripts/python.exe` (untuk Windows) atau `.venv` (untuk Linux/macOS).

Sekarang lingkungan kerja kita sudah ala profesional, terisolasi, dan siap untuk komputasi berat tanpa mengganggu sistem operasi utama.

## 2. Python sebagai Kalkulator

Di antara kegunaan paling sederhana pemrograman Python adalah sebagai kalkulator canggih. Kita dapat menjumlahkan, mengalikan, mengurangi angka atau bilangan, dan semacamnya. Ada tiga jenis bilangan utama dalam Python:

* **Integer** (bilangan bulat) diwakili oleh tipe `int`.
* **Bilangan riil** diwakili oleh tipe `float`. Nama `float` merujuk pada *floating-point numbers* (bilangan titik kambang), yaitu representasi perkiraan dari bilangan riil yang digunakan oleh Python (dan sebagian besar bahasa komputer modern lainnya).
* **Bilangan kompleks** (yang memiliki bagian riil dan imajiner) diwakili oleh tipe `complex`.

Dalam sesi Python interaktif seperti Jupyter Notebook, angka-angka dari tipe bilangan tersebut dapat digabungkan menggunakan operator dalam satu ekspresi yang dievaluasi dan hasilnya dikembalikan ke *prompt* (baris) keluaran. Contohnya:

Input:
```python
1 + 2
```
Output:
```bash
3
```
Input:
```python
10/4
```
Output:
```bash
2.5
```
Input:
```python
2356 * 911
```
Output:
```bash
2146316
```

(**Catatan:** Pada mode interaktif, untuk dapat memunculkan "output" yang relevan, bisa dengan klik tombol semacam `▶ Run` yang ada pada editor/lingkungan pemrograman masing-masing atau dengan jalan pintas variasi tombol kibor tertentu, seperti `CTRL`+`Enter` atau `SHIFT`+`Enter`.)

Untuk membuat kode lebih mudah dipahami, ada baiknya kita rutin menambahkan komentar. Bentuk komentar singkat dapat berupa segala sesuatu pada satu baris setelah karakter `#` yang akan diabaikan oleh *interpreter* Python. Komentar ini berguna sebagai catatan yang dapat dibaca kita sendiri atau orang lain sehingga konteks kode akan lebih jelas. Contohnya:

Input:
```python
# Entalpi fusi molar es: konversi dari kJ.mol-1 ke J.mol-1.
6.01 * 1000
```
Output:
```bash
6010.0
```
Input:
```python
6.518 / 1013.25 * 760 # tekanan atmosfer di Mars, dalam Torr
```
Output:
```bash
4.888902047865778
```

### Operator dan Urutan Operasi

Operator aljabar dasar tercantum dalam Tabel 1.  Dalam penggunaannya, penting bagi kita untuk memperhatikan urutan prioritas operasi (Tabel 2), yakni urutan operator tersebut diterjemahkan dalam sebuah ekspresi.  Contohnya:

Input:
```python
1 + 3 * 4
```
Output:
```bash
13
```

Di sini, $3*4$ dievaluasi terlebih dahulu karena operator perkalian, `*`, memiliki urutan prioritas yang lebih tinggi daripada `+` dan `*`. Hasilnya, $12$, kemudian ditambahkan pada $1$. Jika operator memiliki urutan prioritas yang sama, bagian-bagian dari ekspresi umumnya dievaluasi dari kiri ke kanan (kecuali pemangkatan atau eksponensial yang dievaluasi dari kanan ke kiri). Urutan prioritas ini dapat dianulir dengan menggunakan tanda kurung biasa:

Input:
```python
6 / 3 ** 2      # sama dengan 6 / 9
```
Output:
```bash
0.6666666666666666
```

Input:
```python
(6 / 3 ) ** 2      # sama dengan 2**2
```
Output:
```bash
4.0
```
#### Tabel 1: Operator aritmetika dasar Python.

| Simbol | Operasi |
| :--- | :--- |
| `+` | Penjumlahan |
| `-` | Pengurangan |
| `*` | Perkalian |
| `/` | Pembagian riil (*float*) |
| `//` | Pembagian bulat khusus |
| `%` | Modulus (sisa bagi) |
| `**` | Pemangkatan |

#### Tabel 2: Urutan prioritas operator aritmetika Python.

| Operator | Tingkat Prioritas |
| :--- | :--- |
| `**` | (prioritas tertinggi) |
| `*`, `/`, `//`, `%` | (pertengahan & setara) |
| `+`, `-` | (prioritas terendah) |

#### Pembagian

Perhatikan bahwa ekspresi di atas menghasilkan bilangan *floating point* meskipun kita mengoperasikan bilangan bulat. Kejadian tersebut dikarenakan operator pembagian, `/`, selalu mengembalikan `float`, bahkan ketika hasilnya adalah bilangan bulat.

Perlu diketahui bahwa ada operator pembagian khusus integer, `//`, yang mengembalikan hasil bagi bulat dari pembagian ("berapa kali angka kedua cukup dekat ke angka pertama"). Operator yang terkait, yakni `modulus`, `%`, memberikan sisa pembagiannya. Mari kita lihat contoh-contoh berikut ini.

Input:
```python
7 / 3
```
Output:
```bash
2.3333333333333335
```
Input:
```python
7 // 3
```
Output:
```bash
2
```
Input:
```python
7 % 3
```
Output:
```bash
1
```

Sebagai catatan tambahan, amati hasil dari `7 / 3`. Nilai tepatnya, $2\frac{1}{3}$, tidak dapat direpresentasikan secara eksak ketika Python memformat bilangan riil (*floating-point numbers*) yang representasinya dalam komputer memiliki presisi terbatas (sekitar 1 dalam $10^{16}$). Nilai `float` terdekat dengan jawaban yang dapat direpresentasikanlah yang dikembalikan.

#### Pustaka Matematika (`math` dan `numpy`)

Selain operator aljabar dasar, terdapat banyak fungsi matematika serta konstanta seperti $\pi$ dan $e$ yang disediakan oleh pustaka `math` dalam Python. Pustaka ini adalah modul bawaan yang disediakan di setiap instalasi Python (tidak perlu menginstal paket tambahan), tetapi harus diimpor dengan perintah: `import math`.

Fungsi-fungsi tersebut (sebagian tercantum dalam Tabel: Fungsi Modul Math) kemudian dapat digunakan dengan menambahkan awalan `math.` Contohnya:

Input:
```python
import math
math.sin(math.pi/4)
```
Output:
```bash
0.7071067811865475
```

Cara seperti di atas adalah contoh pemanggilan fungsi. Fungsi `math.sin` diberikan sebuah argumen (di sini, angka $\pi/4$) di dalam tanda kurung. Ekspresi tersebut kemudian mengembalikan hasil perhitungannya.  

Paket **NumPy**, yang awalnya bukan bawaan Python (perlu diinstal secara terpisah), menyediakan semua fungsionalitas `math` dan berbagai tambahan fitur numerik. Oleh karena itu, kita akan lebih sering menggunakannya daripada `math`. Biasanya NumPy diimpor dengan alias `np`, seperti pada contoh berikut:

Input:
```python
import numpy as np
1 / np.sqrt(2)
```
Output:
```bash
0.7071067811865475
```

#### Tabel: Beberapa fungsi dan konstanta yang disediakan oleh modul `math`. Sudut diasumsikan dalam radian.

| Fungsi/Konstanta | Deskripsi/Nilai Matematika |
| :--- | :--- |
| `math.pi` | $\pi$ |
| `math.e` | $e$ |
| `math.sqrt(x)` | $\sqrt{x}$ |
| `math.exp(x)` | $e^x$ |
| `math.log(x)` | $\ln x$ |
| `math.log10(x)` | $\log_{10} x$ |
| `math.sin(x)` | $\sin(x)$ |
| `math.cos(x)` | $\cos(x)$ |
| `math.tan(x)` | $\tan(x)$ |
| `math.asin(x)` | $\arcsin(x)$ |
| `math.acos(x)` | $\arccos(x)$ |
| `math.atan(x)` | $\arctan(x)$ |
| `math.hypot(x, y)` | jarak Euklides (*Euclidean norm*), $\sqrt{x^2+y^2}$ |
| `math.comb(n, r)` | Koefisien binomial, $\binom{n}{r} \equiv {}^nC_r$ |
| `math.degrees(x)` | Konversi $x$ dari radian ke derajat |
| `math.radians(x)` | Konversi $x$ dari derajat ke radian |
