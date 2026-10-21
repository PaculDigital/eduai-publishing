"""DIFF BAHAN — uji 12 (BENAR) vs uji 19 (AMBRUK): apa yang BEDA?
Mencetak jendela yang DIKIRIM oleh masing-masing cara, untuk kandidat yang SAMA.
"""
import sys
sys.path.insert(0, '/app')
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas

db = SessionLocal()
fb = db.get(FileBerkas, 81)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
b = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')


def _t(j):
    if 0 <= j < len(b):
        return 'L%06d| %s' % (j, ' '.join(b[j].split())[:58])
    return '(tepi)'


print('=' * 72)
print('CARA UJI 12 (BENAR 90%): jendela = baris j-1, j, j+1 APA ADANYA')
for j in (350, 417, 398, 344):
    print(' kandidat L%06d:' % j)
    print('   sebelum = %r' % _t(j - 1))
    print('   tengah  = %r' % _t(j))
    print('   sesudah = %r' % _t(j + 1))

print()
print('=' * 72)
print('CARA UJI 19 (AMBRUK): jendela = TETANGGA BERSIH (baris kosong dilewati)')
print('  L000350: sebelum = L000344 (ABSTRAK) ; sesudah = L000352 (PENDAHULUAN)')
print('  -> di uji 12: sebelum = L000349 ("") ; sesudah = L000351 ("")')
print()
print('  L000417: sebelum = L000415 ("Berdasarkan gap research...")')
print('           sesudah = L000419 ("Responden dalam penelitian ini...")')
print('  -> di uji 12: sebelum = L000416 ("") ; sesudah = L000418 ("")')
print()
print('  L000398: sebelum = L000396 ("Sebagian besar penelitian...")')
print('           sesudah = L000400 ("Penelitian terdahulu yang relevan...")')
print('  -> di uji 12: sebelum = L000397 ("") ; sesudah = L000399 ("")')
print()
print('=' * 72)
print('BARIS ASLI sekitar 344-355:')
for j in range(343, 356):
    print('   %s' % _t(j))
print()
print('BARIS ASLI sekitar 396-400:')
for j in range(395, 401):
    print('   %s' % _t(j))
db.close()
