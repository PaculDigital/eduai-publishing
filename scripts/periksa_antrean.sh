#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  periksa_antrean.sh — DIAGNOSA ANTREAN AI EDUAI (bottle neck / hantu)
# ═══════════════════════════════════════════════════════════════════════════
#  Dipakai saat: revisi mahasiswa lama sekali / "Menunggu antrean" tak maju /
#                status gagal dengan token_in=0.
#
#  AKAR YANG DICARI (terukur 25Sep26):
#    PROSES HANTU = baris DB status 'jalan' TANPA utas hidup yang menjalankan
#    → menahan slot → 8 hantu = slot habis (EDUAI_AI_KONKUREN=8)
#    → SEMUA permintaan 'Menunggu antrean' dan TIDAK PERNAH dilayani
#    → tunggu 180 dtk (jalur 1) + 240 dtk (jalur 2) = 420-460 dtk GAGAL.
#
#  PEMAKAIAN:
#     bash scripts/periksa_antrean.sh              # periksa saja
#     bash scripts/periksa_antrean.sh --bersihkan  # periksa + bersihkan hantu
#     bash scripts/periksa_antrean.sh --proses 20  # periksa 20 proses terakhir
#
#  CONTAINER: default `eduai-app` (ubah lewat argumen ke-2 variabel CONTAINER).
# ═══════════════════════════════════════════════════════════════════════════
set -uo pipefail

CONTAINER="${CONTAINER:-eduai-app}"
BERSIHKAN=0
N_PROSES=12

while [ $# -gt 0 ]; do
  case "$1" in
    --bersihkan) BERSIHKAN=1 ;;
    --proses)    shift; N_PROSES="${1:-12}" ;;
    *) echo "argumen tidak dikenal: $1"; exit 2 ;;
  esac
  shift
done

printf '\n%s\n' "$(printf '═%.0s' {1..72})" 
echo "  DIAGNOSA ANTREAN AI — container: $CONTAINER"
echo "$(printf '═%.0s' {1..72})" 

#  ── 1. container hidup? ─────────────────────────────────────────────────
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "  ❌ Container '$CONTAINER' TIDAK JALAN."
  echo "     Jalan:  bash jalankan.sh"
  exit 1
fi
echo "  ✅ Container jalan"

#  ── 2. slot & antrean saat ini ──────────────────────────────────────────
echo
echo "── [1/4] SLOT & ANTREAN ──────────────────────────────────────────"
docker exec "$CONTAINER" python3 -c "
import sys; sys.path.insert(0,'/app')
from app import proses as P
import threading
hidup=[t.name for t in threading.enumerate() if t.name.startswith('proses-ai-')]
print(f'  EDUAI_AI_KONKUREN : {P.KONKUREN_MAKS}')
print(f'  _sedang_jalan     : {P._sedang_jalan}')
print(f'  _antrean          : {list(P._antrean) or \"(kosong)\"}')
print(f'  utas proses-ai    : {hidup or \"(tidak ada)\"}')
print(f'  statistik         : {P.statistik_antrean()}')
if P._sedang_jalan != len(hidup):
    print()
    print('  🚨 SLOT BOCOR! _sedang_jalan != jumlah utas hidup')
    print(f'     selisih = {P._sedang_jalan - len(hidup)} slot TERTAHAN')
    print('     → jalankan: bash scripts/periksa_antrean.sh --bersihkan')
if P._sedang_jalan >= P.KONKUREN_MAKS:
    print()
    print('  🚨 SLOT HABIS — permintaan baru MENGANTRE dan TIDAK dilayani')
    print('     sampai ada slot bebas. Cek hantu di langkah [2/4].')
"

#  ── 3. hantu di DB ──────────────────────────────────────────────────────
echo
echo "── [2/4] PROSES 'jalan'/'menunggu' DI DB (kandidat hantu) ─────────"
docker exec "$CONTAINER" python3 -c "
import sys; sys.path.insert(0,'/app')
import sqlite3, threading
from datetime import datetime, timezone
c=sqlite3.connect('/app/data/eduai.db')
hidup={t.name for t in threading.enumerate() if t.name.startswith('proses-ai-')}
rows=list(c.execute(\"\"\"SELECT id,kode,status,tahap,dibuat,bagian_ke,jumlah_bagian
                       FROM proses_ai WHERE status IN ('jalan','menunggu')
                       ORDER BY id DESC\"\"\"))
if not rows:
    print('  ✅ TIDAK ADA proses menggantung — antrean bersih.')
for r in rows:
    pid,kode,status,tahap,dibuat,bk,jb=r
    hantu = f'proses-ai-{kode}' not in hidup
    tanda = '🚨 HANTU' if hantu else '⏳ JALAN'
    print(f'  {tanda} id={pid} kode={kode} status={status} tahap={tahap!r}')
    print(f'           dibuat={dibuat} · bagian={bk}/{jb} · utas_hidup={not hantu}')
"

#  ── 4. proses terakhir (pola gagal) ─────────────────────────────────────
echo
echo "── [3/4] PROSES TERAKHIR (cari token_in=0 & durasi ~420 dtk) ───────"
docker exec "$CONTAINER" python3 -c "
import sqlite3
c=sqlite3.connect('/app/data/eduai.db')
q='''SELECT id,status,model_ai,token_in,substr(dibuat,12,8),substr(selesai,12,8),
            cast((julianday(selesai)-julianday(dibuat))*86400 as int) AS dtk
     FROM proses_ai ORDER BY id DESC LIMIT $N_PROSES'''
for r in c.execute(q):
    pid,status,model,tin,dibuat,selesai,dtk=r
    tanda=''
    if dtk is not None and dtk>=400 and status=='gagal':
        tanda='  ← 🚨 420-460 dtk GAGAL (pola ANTREAN macet)'
    if tin==0 and status=='gagal':
        tanda+='  ← 🚨 token_in=0 = AI TAK PERNAH DIPANGGIL'
    print(f'  id={pid:4d} {status:<8} in={tin or 0:<7} {dibuat}→{selesai} '
          f'{dtk if dtk is not None else \"?\":>5}s · {model or \"-\"}{tanda}')
"

#  ── 5. bersihkan (opsional) ─────────────────────────────────────────────
echo
if [ "$BERSIHKAN" -eq 1 ]; then
  echo "── [4/4] BERSIHKAN HANTU ─────────────────────────────────────────"
  docker exec "$CONTAINER" python3 -c "
import sys; sys.path.insert(0,'/app')
from app.proses import bersihkan_hantu, statistik_antrean
n=bersihkan_hantu()
print(f'  ✅ {n} proses menggantung DITUTUP + kuota dikembalikan')
print(f'  statistik sesudah: {statistik_antrean()}')
"
else
  echo "── [4/4] BERSIHKAN (opsional) ────────────────────────────────────"
  echo "  Untuk membersihkan hantu (kuota otomatis dikembalikan):"
  echo "     bash scripts/periksa_antrean.sh --bersihkan"
fi

printf '\n%s\n' "$(printf '═%.0s' {1..72})" 
echo "  RINGKASAN ARTI:"
echo "    token_in=0 + gagal + ~420 dtk  ⇒  ANTREAN MACET, BUKAN AI"
echo "    status='jalan' tanpa utas      ⇒  HANTU (obat: --bersihkan)"
echo "    'Menunggu antrean'             ⇒  BUKAN error, perilaku normal"
echo "    HTTP 402                       ⇒  kuota user habis, bukan bug"
echo "$(printf '═%.0s' {1..72})" 
