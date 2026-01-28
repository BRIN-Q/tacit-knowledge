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

#### Tabel 3: Beberapa fungsi dan konstanta yang disediakan oleh modul `math`. Sudut diasumsikan dalam radian.

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

Meskipun fungsi trigonometri dalam `math` dan NumPy menggunakan radian alih-alih derajat, ada beberapa metode praktis untuk saling konversi antara keduanya:

Input:
```python
np.degrees(np.pi/2)
```
Output:
```bash
90.0
```
Input:
```python
np.sin(np.radians(30))
```
Output:
```bash
0.49999999999999994
```
Perhatikan kembali presisi yang terbatas pada contoh tersebut. Kita tahu nilai eksak dari $\sin(30^\circ)$ adalah $0.5$, tetapi representasi oleh komputer dapat berupa angka $0.49999999999999994$ seperti pada contoh.

Fungsi `math.log` and `np.log` memberikan logaritma natural (basis $e$). Ada pula varian `math.log10` dan `np.log10` yang terpisah:

Input:
```python
np.log(10)
```
Output:
```bash
2.302585092994046
```
Input:
```python
1 / np.log10(np.e)
```
Output:
```bash
2.302585092994046
```

#### Fungsi Bawaan Lainnya

Ada beberapa fungsi bawaan yang berguna (yaitu, yang tidak memerlukan paket seperti `math` atau NumPy untuk diimpor):

* `abs` mengembalikan nilai absolut dari argumennya.
* `round` membulatkan angka ke presisi tertentu dalam digit desimal (atau ke bilangan bulat terdekat jika tidak ada presisi yang ditentukan).

## 3. Pendefinisian Bilangan

Berbeda dengan beberapa bahasa pemrograman lain, Python tidak mengharuskan pengguna/pemrogram untuk mendeklarasikan tipe bilangan sebelum digunakan. Angka-angka yang terlihat oleh *interpreter* sebagai bilangan bulat akan diperlakukan sebagai objek `int`, sementara yang tampak seperti bilangan riil akan menjadi objek `float`. Namun, tipe data ini adalah bilangan tanpa dimensi. Jika ada besaran fisis yang diwakili tipe-tipe data tersebut, pemrogram bertanggung jawab untuk menjaga sendiri satuannya.

Bilangan bulat dalam Python bisa sebesar apapun yang diizinkan memori komputer. Untuk mendefinisikan bilangan bulat yang sangat besar, akan sangat mudah memisahkan kelompok digit dengan karakter garis bawah, `_`.

Input:
```python
# Konstanta Avogadro (mol-1): nilai eksak berdasarkan definisi.
602_214_076_000_000_000_000_000
```
Output:
```bash
602214076000000000000000
```

Bilangan titik kambang (*floating point*) dapat ditulis dengan titik desimal `.`, dan boleh disertai pengelompokan digit opsional untuk memperjelas:

Input:
```python
# Konstanta Gas (J.K-1.mol-1): nilai eksak berdasarkan definisi.
8.31_446_261_815_324
```
Output:
```bash
8.31446261815324
```

Selain itu, dalam notasi ilmiah, kita bisa menggunakan karakter `e` (atau `E`) yang memisahkan mantisa (digit signifikan) dan eksponen:

Input:
```python
# Konstanta Boltzmann (J.K-1): nilai eksak berdasarkan definisi.
1.380649e-23
```
Output:
```bash
1.380649e-23
```

Bilangan kompleks dapat ditulis sebagai jumlah dari bagian riil dan imajiner. Bagian imajiner dalam Python ditandai dengan akhiran `j` (bukan `i`) mengikuti konvensi dalam *engineering*:

Input:
```python
1 + 4j
```
Output:
```bash
(1+4j)
```

Cara lain, kita bisa secara eksplisit memberikan sepasang nilai pada fungsi `complex`:

Input:
```python
complex(-2, 3)
```
Output:
```bash
(-2+3j)
```

Dalam bilangan kompleks, bagian riil dan imajiner direpresentasikan dalam bentuk titik kambang *floating point* dan dapat diperoleh secara terpisah menggunakan atribut `.real` dan `.imag`. Fungsi bawaan `abs` mengembalikan besaran (magnitudo) bilangan kompleks:

Input:
```python
(3 + 4j).real
```
Output:
```bash
3.0
```

Input:
```python
(3 + 4j).imag
```
Output:
```bash
4.0
```

Input:
```python
abs(3 + 4j)
```
Output:
```bash
5.0
```
## 4. Variabel

Ketika memecahkan suatu masalah numerik tertentu, kita perlu menyimpan angka-angka dalam program sehingga dapat digunakan berulang kali dan dirujuk dengan nama yang mudah. Untuk mencapai tujuan tersebut, kita perlu mendefinisikan "variabel". Dalam Python, variabel dapat dianggap sebagai label yang disematkan pada objek (misalnya suatu bilangan `int` atau `float`). Ada beberapa aturan penting terkait penamaan variabel:

* Nama variabel boleh mengandung huruf, angka, dan karakter garis bawah (sering digunakan untuk mengindikasikan subskrip).
* Nama variabel tidak boleh diawali dengan angka.
* Variabel tidak boleh memiliki nama yang sama dengan salah satu dari kata-kata kunci tercadang (*reserved keywords*) yang dikhususkan dalam bahasa Python, seperti dapat dilihat pada Tabel 1.

Sebagian besar editor kode modern sudah memiliki fitur sorotan sintaksis yang akan memberikan peringatan saat ada kata-kata kunci khusus yang digunakan. Perhatikan perbedaan antara pemberian nilai atau penugasan (*assignment*) yang valid:

Input:
```python
# Konstanta Avogadro (mol-1): nilai eksak berdasarkan definisi.
N_A = 602_214_076_000_000_000_000_000
```

dan yang invalid:

Input:
```python
import = 0
```

Output:
```
  File "/tmp/ipython-input-2269274265.py", line 1
    import = 0
           ^
SyntaxError: invalid syntax
```

Upaya pemberian nilai ke variabel bernama `import` gagal dilakukan (muncul `SyntaxError`) karena `import` adalah salah satu kata kunci tercadang. Kata kunci ini merupakan bagian dari sintaksis Python yang digunakan untuk mengimpor modul, seperti yang sudah pernah kita lakukan.

Pada praktiknya, kata kunci tercadang jarang menjadi nama variabel yang mungkin dipilih, dengan pengecualian `lambda` (belakangan akan kita lihat), yang bisa dipilih untuk merepresentasikan panjang gelombang (*wavelength*). Namun, kita sarankan menggunakan nama lain seperti `lam` dalam kasus ini. Tabel 4 juga memuat tiga kata kunci khusus yang tidak dapat diubah: `True` dan `False`, yang mewakili konsep logika Boolean, serta `None`, yang digunakan untuk menyatakan nilai kosong atau ketiadaan.

### Tabel 4: Kata kunci tercadang (*reserved keywords*) dalam Python 3.

| | | | | |
| :--- | :--- | :--- | :--- | :--- |
| `and` | `as` | `assert` | `async` | `await` |
| `break` | `class` | `continue` | `def` | `del` |
| `elif` | `else` | `except` | `finally` | `for` |
| `from` | `global` | `if` | `import` | `in` |
| `is` | `lambda` | `nonlocal` | `not` | `or` |
| `pass` | `raise` | `return` | `try` | `while` |
| `with` | `yield` | `False` | `True` | `None` |

Nama variabel yang dipilih dengan baik dapat membuat kode Python sangat jelas dan ekspresif:

Input:
```python
# Konstanta Boltzmann (J.K-1): nilai eksak berdasarkan definisi.
k_B = 1.380649e-23
R = N_A * k_B   # konstanta gas (J.K-1.mol-1)
```

Pada pernyataan terakhir, sisi kanan tanda `=`, yaitu ekspresi $N_A * k_B$, dievaluasi terlebih dahulu dan nama variabel `R` disematkan pada hasil perhitungan ini.

Kita bisa juga memodifikasi nilai yang terkait dengan nama variabel:

Input:
```python
n = 1000
n = n + 1
```
Ekspresi $n = n + 1$ tidaklah merepresentasikan persamaan matematika analitik yang valid karena mustahil untuk diselesaikan. Namun, dalam "cara pikir" komputer, pernyataan ini merupakan instruksi untuk mengambil nilai $n$ yang sebelumnya telah ditetapkan, kemudian tambahkan angka satu padanya, dan akhirnya ditetapkan ulang dengan memberi nama $n$ kembali pada hasilnya. Nilai sebelumnya yang sebesar $1.000$ langsung "dilupakan". Memori komputer yang digunakan untuk penyimpanannya dibebaskan dan dapat digunakan untuk keperluan lain. Ekspresi seperti pada contoh sangat umum dalam pemrograman apapun sehingga beberapa bahasa pemrograman, termasuk Python, menyediakan jalan pintas (disebut "penugasan yang diperluas" atau *augmented assignment*):

Input:
```python
n = 1000
n = n += 1
```

Cara penulisan di atas akan memberikan hasil yang sama dengan sebelumnya. Ada sintaksis serupa untuk operator lain, seperti pengurangan (`-=`) dan perkalian (`*=`).

Jalan pintas lain yang berguna dan difasilitasi Python adalah penggunaan nilai yang dipisahkan koma untuk menetapkan beberapa variabel sekaligus, misalnya:

Input:
```python
a, b, c = 42, -1, 0.5
```

Untuk selanjutnya, kita akan sebaik-baiknya memberikan nama variabel yang bermakna pada objek agar kode lebih bersifat "*self-documenting*" dan kita bisa meminimalkan penggunaan komentar penjelas.
