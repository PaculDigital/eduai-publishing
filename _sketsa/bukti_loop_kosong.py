"""BUKTI: loop di `_revisi_kerja` KOSONG — `kepala` dihitung di luar loop.

Uji 2 arah (standar Bos):
  A. BUKTI KODE   : AST → pernyataan dalam loop `for idx, potongan in …`
  B. BUKTI JALAN  : jalankan tiruan loop dengan 2 bagian → berapa kali
                    panggilan AI terjadi?
"""
import ast

print('═' * 74)
print('A. AST — isi loop `for idx, potongan in enumerate(bagian_naskah…)`')
print('═' * 74)
src = open('/app/app/ai.py').read()
t = ast.parse(src)
found = False
for n in ast.walk(t):
    if isinstance(n, ast.FunctionDef) and n.name == '_revisi_kerja':
        print(f'fungsi _revisi_kerja: baris {n.lineno}-{n.end_lineno}')
        for b in n.body:
            if isinstance(b, ast.For) and 'bagian_naskah' in ast.unparse(b.iter):
                found = True
                print(f'  FOR baris {b.lineno}: {ast.unparse(b.iter)}')
                print(f'  → body berisi {len(b.body)} pernyataan:')
                for s in b.body:
                    print(f'       baris {s.lineno}: {ast.unparse(s)[:80]}')
                #  Apakah panggilan AI ada DI DALAM loop?
                dalam = ast.unparse(b)
                print(f'  → apakah loop memanggil AI? '
                      f'{"YA" if "_revisi_dengan_failover" in dalam else "TIDAK ❌"}')
                #  Apakah `kepala` dipakai di dalam loop?
                print(f'  → apakah `kepala` DIPAKAI di dalam loop? '
                      f'{"YA" if "user_msg" in dalam else "TIDAK ❌"}')
                print(f'  → baris sesudah loop: {b.end_lineno + 1}')
if not found:
    print('  (loop tidak ditemukan — periksa nama fungsi)')

print()
print('═' * 74)
print('B. PERILAKU — berapa kali panggilan AI untuk naskah 2 bagian?')
print('═' * 74)
panggil = 0


def tiru_loop(bagian):
    """Tiru PERSIS struktur kode sekarang."""
    global panggil
    for idx, potongan in enumerate(bagian, start=1):
        kepala = f'BAGIAN {idx}'
    #  ⚠️ DI SINI: panggilan AI ada DI LUAR loop (di-indentasi 4 spasi,
    #     sejajar `for`), sehingga hanya dijalankan SEKALI.
    panggil += 1
    return kepala


k = tiru_loop(['potongan-1', 'potongan-2'])
print(f'  bagian=2 → panggilan AI: {panggil}× (harusnya 2×) · kepala akhir={k!r}')
print(f'  → {"BUG TERBUKTI: cuma 1 bagian diproses" if panggil == 1 else "aman"}')
