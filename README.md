# asistenresearch

Alat & catatan riset dari sesi Claude Code, buat dipakai bareng sesi Cowork.
**Repo ini PUBLIK**: yang masuk ke sini cuma script dan catatan umum. Gak ada data akun,
setelan live, EA, atau data tick.

## Isi
| berkas | gunanya |
|---|---|
| `tools/unduh_dukascopy.py` | unduh tick XAUUSD dari Dukascopy, 1 berkas CSV per bulan (format ekspor tick MT5, jam UTC) |
| `tools/KLIK_UNDUH_DUKASCOPY.bat` | tombol klik buat script di atas. Kalau putus, klik lagi, dia lanjut sendiri |
| `catatan/BACA_DULU_DATA_DUKASCOPY.md` | hal yang wajib diinget sebelum datanya dipakai (UTC vs jam broker, beda sama harga broker) |

## Catatan
- Data tick-nya **gak** di-upload ke sini karena kegedean (GitHub batasnya 100 MB per berkas).
- Kenapa gak pakai `npx dukascopy-node`: dari Indonesia DNS dukascopy.com diblokir ISP.
  Penjelasannya ada di kepala `unduh_dukascopy.py`.
