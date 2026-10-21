"""UKUR BIAYA AI NYATA untuk analisa harga Token Revisi.

Sumber angka WAJIB nyata:
  1. Tarif model di 9router (/v1/models atau catatan lama)
  2. Riwayat proses_ai di DB (token_in/token_out nyata)
  3. Uji terukur hari ini (PENUH vs POTONG)
"""
import sys, json, re
sys.path.insert(0, '/app')
from app.config import DATA_DIR
import sqlite3, os

db = os.path.join(DATA_DIR, 'eduai.db')
print('DB:', db, '| ada:', os.path.exists(db))

if os.path.exists(db):
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    print('\n=== RIWAYAT proses_ai (token nyata) ===')
    baris = c.execute("""SELECT id, token_in, token_out, token_revisi, model_ai,
                                panjang_naskah, dibuat
                         FROM proses_ai ORDER BY id DESC LIMIT 15""").fetchall()
    print(f'{"id":>4}{"tok_in":>10}{"tok_out":>10}{"rev":>5}{"naskah":>10}  model')
    tin = tout = 0
    for b in baris:
        print(f'{b["id"]:>4}{b["token_in"] or 0:>10,}{b["token_out"] or 0:>10,}'
              f'{b["token_revisi"] or 0:>5}{(b["panjang_naskah"] or 0):>10,}  {str(b["model_ai"])[:30]}')
        tin += b['token_in'] or 0; tout += b['token_out'] or 0
    n = len(baris)
    if n:
        print(f'\nRATA-RATA: tok_in={tin//n:,} · tok_out={tout//n:,} '
              f'· total={(tin+tout)//n:,} · Token Revisi rinci={max(1,-(-( (tin+tout)//n )//10000))}')
    c.close()
