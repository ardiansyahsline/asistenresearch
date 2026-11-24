# Data tick XAUUSD Dukascopy — 2020-01 s/d 2026-11-23

Dibikin 24 Nov 2026 (sesi Claude Code) buat dikasih ke sesi Cowork.

## Isi
| berkas | isi |
|---|---|
| `XAUUSD_YYYY_MM.csv` | tick 1 bulan, format ekspor tick MT5 (tab) |
| `XAUUSD_2026_11_SEBAGIAN.csv` | bulan berjalan, cuma s/d 23 Nov 2026 |
| `RINGKASAN_BULAN.csv` | per bulan: jumlah tick, jam pertama/terakhir, bid min/max, spread median, jam kosong |
| `KEMAJUAN.txt` | log unduhan |
| `_CACHE\` | mentahan per jam (.bi5). Boleh dihapus kalau semua bulan udah jadi. |

## ⚠️ Yang WAJIB diinget sebelum dipakai (biar gak jadi "angka bohong")
1. **Jam = UTC.** Data Vantage/MT5 di folder `DATA TICK\` pakai jam server broker
   (biasanya UTC+2, UTC+3 pas musim panas AS). Geser dulu sebelum dibanding / digabung.
2. **Ini harga Dukascopy, BUKAN harga broker lu.** Spread & jumlah tick beda dari Vantage.
   Hasil backtest di data ini ≠ hasil di broker live. Pakai buat uji di periode yang
   gak ada data broker-nya (2020 – Mar 2025), bukan buat ganti data Vantage.
3. Harga 3 desimal (`2077.255`). Kolom `<LAST>` & `<VOLUME>` sengaja kosong, `<FLAGS>`=6
   (bid+ask), sama kayak ekspor MT5.
4. `jam_senkam_kosong` di ringkasan: wajar ~1 jam/hari (jeda harian emas) + hari libur.
   Kalau satu bulan angkanya jauh lebih gede dari bulan lain → ada bolong, cek dulu.

## Cara ngulang / nyambung
Klik `C:\scalping\02_Tools\KLIK_UNDUH_DUKASCOPY.bat`. Bulan yang udah jadi dilewat,
jam yang udah ke-cache gak diunduh ulang. Script: `02_Tools\unduh_dukascopy.py`
(kenapa gak pakai `npx dukascopy-node`: DNS diblokir ISP — rinciannya di kepala script).
