"""
Unduh tick XAUUSD dari Dukascopy (sumber yang sama dipakai dukascopy-node).

KENAPA GAK PAKAI `npx dukascopy-node` (dites 24 Nov 2026, gagal "fetch failed"):
  1. ISP Indonesia ngebajak DNS dukascopy.com -> IP blokir 103.x.
     Obat: cari IP asli lewat DNS Cloudflare (DoH).
  2. Filter ISP kadang motong jabat-tangan TLS kalau baca nama "dukascopy" di SNI.
     Obat: konek TANPA SNI. Sertifikat tetap dicek: wajib sah + milik dukascopy.com.
  3. Server ngebatesin: kebanyakan request -> HTTP 429/503. Kena 429 pas tes 8 jalur.
     Obat: 2 jalur aja, dan kalau satu kena 429 SEMUA jalur rehat bareng.

Hasil  : DATA TICK\\_DUKASCOPY\\XAUUSD_YYYY_MM.csv  (1 berkas per bulan)
Format : sama kayak ekspor tick MT5 (tab):  <DATE> <TIME> <BID> <ASK> <LAST> <VOLUME> <FLAGS>
WAKTU  : **UTC** (Dukascopy). Broker MT5 biasanya UTC+2/+3 -> geser dulu kalau mau dibanding.

TAHAN MATI DI TENGAH (laptop ini sering restart sendiri):
  - tiap jam data disimpan mentah di _CACHE\\ -> diulang gak download lagi
  - bulan ditulis ke .part dulu, baru di-rename pas lengkap
  - bulan yang belum penuh (bulan berjalan) dinamain *_SEBAGIAN.csv
  - jam yang gagal terus -> bulan itu GAK ditulis, script teriak & berhenti (gak ada bolong diem-diem)
  Tinggal jalanin ulang perintah yang sama.

Pakai:  python -I unduh_dukascopy.py  [MULAI=2020-01] [SAMPAI=kemarin, format YYYY-MM-DD]
"""
import sys, os, json, lzma, struct, socket, time, ssl, threading, datetime as dt
import urllib.request, http.client
from concurrent.futures import ThreadPoolExecutor

HOST = "datafeed.dukascopy.com"
SIMBOL = "XAUUSD"
FAKTOR = 1000.0          # harga Dukascopy XAUUSD = integer / 1000 (dicek: 2077255 -> 2077.255, Jan 2024)
FOLDER = r"C:\scalping\DATA TICK\_DUKASCOPY"
CACHE = os.path.join(FOLDER, "_CACHE")
UTAS = 2                 # 8 jalur -> kena 429. Jangan dinaikin.
IP_CADANGAN = ["194.8.15.180", "16.62.244.190"]   # IP yang pernah dikasih DoH 24 Nov 2026

def cari_ip():
    ips = []
    for _ in range(3):
        try:
            req = urllib.request.Request(f"https://cloudflare-dns.com/dns-query?name={HOST}&type=A",
                                         headers={"accept": "application/dns-json"})
            js = json.load(urllib.request.urlopen(req, timeout=20))
            ips += [a["data"] for a in js.get("Answer", []) if a["type"] == 1]
        except Exception:
            pass
    for ip in IP_CADANGAN:
        ips.append(ip)
    return list(dict.fromkeys(ips))

IPS = cari_ip()
_ctx = ssl.create_default_context()
_ctx.check_hostname = False   # nama dicek manual di _cek_sertifikat (karena gak pakai SNI)
_lokal = threading.local()
_rehat_sampai = [0.0]
_kunci = threading.Lock()
_statistik = {"req": 0, "429": 0, "err": 0}

def _cek_sertifikat(s):
    san = [v for k, v in s.getpeercert().get("subjectAltName", []) if k == "DNS"]
    if not any(n in ("dukascopy.com", "*.dukascopy.com") for n in san):
        raise ssl.SSLError(f"sertifikat bukan dukascopy: {san}")

def _koneksi(baru=False):
    c = getattr(_lokal, "c", None)
    if c is None or baru:
        if c is not None:
            try: c.close()
            except Exception: pass
        _lokal.i = getattr(_lokal, "i", threading.get_ident()) + (1 if baru else 0)
        ip = IPS[_lokal.i % len(IPS)]          # gagal -> ganti IP
        s = socket.create_connection((ip, 443), timeout=40)
        c = http.client.HTTPSConnection(ip, timeout=40, context=_ctx)
        c.sock = _ctx.wrap_socket(s, server_hostname=None)
        _cek_sertifikat(c.sock)
        _lokal.c = c
    return c

def _tunggu_rehat():
    while True:
        sisa = _rehat_sampai[0] - time.time()
        if sisa <= 0:
            return
        time.sleep(min(sisa, 5))

def ambil_mentah(t):
    """Balikin isi .bi5 (bytes, b'' = jam kosong). Disimpan di cache."""
    f = os.path.join(CACHE, f"{t:%Y}", f"{t:%m}", f"{t:%d_%H}.bi5")
    if os.path.exists(f):
        return open(f, "rb").read()
    path = f"/datafeed/{SIMBOL}/{t.year}/{t.month-1:02d}/{t.day:02d}/{t.hour:02d}h_ticks.bi5"
    err, baru = None, False
    for coba in range(40):
        _tunggu_rehat()
        try:
            c = _koneksi(baru)
            c.request("GET", path, headers={"Host": HOST})
            r = c.getresponse()
            data = r.read()
            _statistik["req"] += 1
            if r.status in (429, 503):
                _statistik["429"] += 1
                jeda = min(300, 30 * (coba + 1))
                with _kunci:   # SEMUA jalur rehat bareng
                    _rehat_sampai[0] = max(_rehat_sampai[0], time.time() + jeda)
                err, baru = f"HTTP {r.status}", False
                continue
            if r.status == 404:
                data = b""
            elif r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            if data:
                lzma.decompress(data)   # pastiin gak korup sebelum disimpan
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f + ".tmp", "wb").write(data)
            os.replace(f + ".tmp", f)
            return data
        except Exception as e:
            _statistik["err"] += 1
            err, baru = e, True
            time.sleep(min(60, 3 * (coba + 1)))
    raise RuntimeError(f"jam {t} gagal 40x: {err}")

def urai(t, data):
    if not data:
        return []
    raw = lzma.decompress(data)
    out = []
    for i in range(0, len(raw), 20):
        ms, ask, bid, av, bv = struct.unpack(">IIIff", raw[i:i+20])
        out.append((t + dt.timedelta(milliseconds=ms), bid / FAKTOR, ask / FAKTOR))
    return out

def bulan(y, m, batas):
    akhir = min(dt.datetime(y + (m == 12), m % 12 + 1, 1), batas)
    jam, t = [], dt.datetime(y, m, 1)
    while t < akhir:
        jam.append(t); t += dt.timedelta(hours=1)
    return jam, akhir

def main():
    mulai = sys.argv[1] if len(sys.argv) > 1 else "2020-01"
    sampai = sys.argv[2] if len(sys.argv) > 2 else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    y, m = map(int, mulai.split("-"))
    batas = dt.datetime.fromisoformat(sampai) + dt.timedelta(days=1)  # inklusif s/d akhir hari itu
    os.makedirs(CACHE, exist_ok=True)
    log = open(os.path.join(FOLDER, "KEMAJUAN.txt"), "a", encoding="utf-8")
    ringkas_path = os.path.join(FOLDER, "RINGKASAN_BULAN.csv")
    if not os.path.exists(ringkas_path):
        open(ringkas_path, "w", encoding="utf-8").write(
            "bulan,tick,tick_awal_utc,tick_akhir_utc,bid_min,bid_max,spread_median,jam_senkam_kosong,sampai_utc\n")
    def tulis(s):
        print(s, flush=True); log.write(s + "\n"); log.flush()
    tulis(f"=== mulai {dt.datetime.now():%Y-%m-%d %H:%M} | IP {IPS} | {mulai} s/d {sampai} (UTC)")
    with ThreadPoolExecutor(UTAS) as ex:
        while dt.datetime(y, m, 1) < batas:
            nama = os.path.join(FOLDER, f"{SIMBOL}_{y}_{m:02d}.csv")
            jam, akhir = bulan(y, m, batas)
            lengkap = akhir == dt.datetime(y + (m == 12), m % 12 + 1, 1)
            if not lengkap:
                nama = nama.replace(".csv", "_SEBAGIAN.csv")
            if os.path.exists(nama) and lengkap:
                tulis(f"{y}-{m:02d} udah ada, lewat")
            else:
                t0 = time.time()
                mentah = dict(zip(jam, ex.map(ambil_mentah, jam)))   # error -> meledak, bulan gak ditulis
                ticks, kosong = [], 0
                for j in jam:
                    tk = urai(j, mentah[j])
                    if not tk and j.weekday() < 4:
                        kosong += 1   # Sen-Kam: wajar ~1 jam/hari (jeda harian emas) + hari libur
                    ticks += tk
                part = nama + ".part"
                with open(part, "w", encoding="utf-8", newline="\n") as f:
                    f.write("<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n")
                    for w, b, a in ticks:
                        f.write(f"{w:%Y.%m.%d}\t{w:%H:%M:%S}.{w.microsecond//1000:03d}\t{b:.3f}\t{a:.3f}\t\t\t6\n")
                os.replace(part, nama)
                if ticks:
                    bids = [x[1] for x in ticks]
                    sp = sorted(round(x[2] - x[1], 3) for x in ticks)
                    baris = f"{y}-{m:02d},{len(ticks)},{ticks[0][0]},{ticks[-1][0]},{min(bids):.3f},{max(bids):.3f},{sp[len(sp)//2]:.3f},{kosong},{akhir}"
                else:
                    baris = f"{y}-{m:02d},0,,,,,,{kosong},{akhir}"
                open(ringkas_path, "a", encoding="utf-8").write(baris + "\n")
                tulis(f"{y}-{m:02d} OK {len(ticks):,} tick, jam Sen-Kam kosong {kosong}, {time.time()-t0:.0f} dtk"
                      f" | req {_statistik['req']} kena-429 {_statistik['429']} error {_statistik['err']}"
                      + ("" if lengkap else "  (BULAN BELUM PENUH)"))
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    tulis("=== SELESAI")

if __name__ == "__main__":
    main()
