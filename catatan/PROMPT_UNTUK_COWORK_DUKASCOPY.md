# Prompt buat sesi Cowork: cara download tick XAUUSD Dukascopy

Salin semua isi di dalam kotak di bawah, terus tempel ke sesi Cowork.

---

```
Konteks dari sesi Claude Code (24 Nov 2026): gue udah berhasil download tick XAUUSD
dari Dukascopy. Begini caranya, plus jebakan yang udah ketemu.

SUMBER DATA
Dukascopy nyimpen 1 berkas per JAM:
  https://datafeed.dukascopy.com/datafeed/XAUUSD/{TAHUN}/{BULAN-1, 2 digit}/{TGL}/{JAM}h_ticks.bi5
  (BULAN mulai dari 00 = Januari. Contoh 10 Nov 2026 jam 13 UTC = .../2026/10/10/13h_ticks.bi5)
Isinya dikompres LZMA. Sesudah dibuka, tiap 20 byte = 1 tick (big-endian):
  uint32 milidetik-dari-awal-jam, uint32 ask, uint32 bid, float vol_ask, float vol_bid
Harga XAUUSD = angka / 1000 (2077255 -> 2077.255).
Berkas kosong (0 byte) = jam tanpa tick (weekend / jeda harian). 404 = belum ada.

KENAPA `npx dukascopy-node` GAGAL DI LAPTOP ALIF ("fetch failed")
1. ISP Indonesia ngebajak DNS dukascopy.com ke IP blokir 103.x.
   Obatnya: cari IP asli lewat DNS Cloudflare (DoH):
   https://cloudflare-dns.com/dns-query?name=datafeed.dukascopy.com&type=A
   (header accept: application/dns-json). Hasil 24 Nov: 194.8.15.180, 16.62.244.190, 16.62.187.25
2. Filter ISP kadang motong koneksi TLS (ConnectionReset) kalau liat nama "dukascopy"
   di SNI. Obatnya: konek ke IP TANPA SNI, kirim header Host: datafeed.dukascopy.com.
   Sertifikat tetap dicek: wajib sah, dan subjectAltName wajib *.dukascopy.com.
3. Server ngebatesin: 8 koneksi barengan -> HTTP 429/503. Pakai 2 koneksi, dan
   koneksinya DIPAKAI ULANG (keep-alive). Buka koneksi baru 3-20 detik, request
   di koneksi lama ~0,2 detik. Kalau kena 429, semua koneksi rehat bareng 30 detik+.
Kalau lu jalan di server luar Indonesia, nomor 1-2 kemungkinan gak kejadian,
coba `npx dukascopy-node -i xauusd -from 2026-11-20 -to 2026-11-21 -t tick -f csv` dulu.

SCRIPT YANG UDAH JADI
https://github.com/ardiansyahsline/asistenresearch -> tools/unduh_dukascopy.py
  python -I unduh_dukascopy.py 2026-11-20 2026-11-20      (1 hari)
  python -I unduh_dukascopy.py 2020-01                    (2020 s/d kemarin)
Hasil: 1 CSV per bulan, format ekspor tick MT5 (tab):
  <DATE> <TIME> <BID> <ASK> <LAST> <VOLUME> <FLAGS>, harga 3 desimal, FLAGS=6.
Bisa lanjut sendiri kalau putus (tiap jam disimpan di _CACHE).

HASIL TES (bukti ini jalan)
- 20 Nov 2026: 839.760 tick, 24 jam, 73 detik, 0 kena 429, 36,8 MB
- 10 Nov 2026: 534.766 tick, 275 detik (4 koneksi putus, otomatis diulang)
- Diadu sama tick Vantage 10 Nov 2026 (rilis CPI): kalau jam Dukascopy ditambah 2 jam,
  bid-nya beda cuma $0,08-0,11. Data terbukti cocok.

JEBAKAN YANG WAJIB DIPEGANG
- Jam Dukascopy = UTC. Jam server Vantage = UTC+2 (bulan Nov; musim panas AS bisa +3).
  Lupa geser = semua analisa per jam meleset 2 jam.
- Ini harga Dukascopy, bukan broker. Spread & jumlah tick beda. Pakai buat periode
  yang gak ada data broker (2020 - Mar 2025), jangan dipakai buat gantiin data Vantage.
- Kecepatan di laptop Alif ~1-5 menit per hari data. 6 tahun = belasan jam, gak bisa 1 jam.
  Kalau perlu cepat, unduh cuma hari/periode yang mau dites.
- 1 hari tick sekarang ~37 MB. 6 tahun bisa puluhan GB, jangan diunduh semua kalau gak perlu.
```
