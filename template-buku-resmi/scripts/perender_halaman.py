#!/usr/bin/env python3
"""PERENDER HALAMAN GERBANG BUKU — WordCraft, dari akar.

Keputusan akar Boss, 26 Okt 2026 (bukan tambalan):
  * SATU-SATUNYA perender gerbang = WordCraft (`wordcraft-cli`).
  * Editor = OnlyOffice (tugasnya menyunting di browser, BUKAN
    perender gerbang — tidak dipanggil dari sini).
  * `soffice` (LibreOffice) TIDAK dipakai di gerbang sama sekali:
    bukan opsi, bukan fallback, bukan default. Di VPS Boss memang
    tidak ada `soffice`; yang ada hanya WordCraft dan OnlyOffice.
  * Mesin yang sudah ada saja: tanpa install, tanpa download baru.

Cara WordCraft ditemukan (urutan):
  1. Environment variable WORDCRAFT_CLI (path ke binary).
  2. `wordcraft-cli` di PATH.
  3. Lewat container hermes di host VPS (`docker exec hermes ...`),
     karena binary 0.7.0 yang sudah ada di VPS hanya terlihat dari
     dalam container itu (host: /root/.hermes/... -> /opt/data di
     dalam container). Mode ini menyalin DOCX ke dalam container,
     menjalankan `info`/`convert` di sana, lalu membersihkannya.

Fungsi di sini hanya memakai pustaka standar Python. `pdftotext`
(membaca PDF hasil render, BUKAN merender) tetap dipakai oleh
pemanggil yang butuh teks per halaman — pembaca, bukan perender.

  hitung_halaman(docx) -> int | None
      Jumlah halaman menurut WordCraft (`info`), atau None bila
      WordCraft tidak tersedia / gagal — pemanggil TIDAK BOLEH
      crash karenanya, melainkan melaporkan "tidak terukur".
  render_pdf(docx, pdf) -> bool
      True bila PDF berhasil ditulis WordCraft, False bila tidak.
"""
import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

CLI_DALAM_HERMES = '/opt/data/services/wordcraft-uji/bin/wordcraft-cli'


def _perintah_lokal():
    """[binary] bila WordCraft ada di mesin ini, else None."""
    env = os.environ.get('WORDCRAFT_CLI', '').strip()
    if env and Path(env).is_file() and os.access(env, os.X_OK):
        return [env]
    mana = shutil.which('wordcraft-cli')
    if mana:
        return [mana]
    return None


def _docker_tersedia():
    if not shutil.which('docker'):
        return False
    try:
        r = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'],
                           capture_output=True, text=True, timeout=30)
    except Exception:
        return False
    return 'hermes' in r.stdout.split()


def temukan_perender():
    """('cli', [binary]) | ('docker', None) | None."""
    lokal = _perintah_lokal()
    if lokal:
        return ('cli', lokal)
    if _docker_tersedia():
        return ('docker', None)
    return None


def _jalan_cli(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception:
        return None
    return r


def _info_cli(cmd, docx):
    r = _jalan_cli(cmd + ['info', str(docx)])
    if r is None or r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except Exception:
        return None
    pages = data.get('pages')
    return int(pages) if isinstance(pages, int) and pages > 0 else None


def _salin_ke_hermes(docx):
    nama = f'wc-{uuid.uuid4().hex[:12]}.docx'
    tujuan = f'/tmp/{nama}'
    r = subprocess.run(['docker', 'cp', str(docx), f'hermes:{tujuan}'],
                       capture_output=True, text=True, timeout=120)
    return tujuan if r.returncode == 0 else None


def _hapus_dari_hermes(path_dalam):
    subprocess.run(['docker', 'exec', 'hermes', 'rm', '-f', path_dalam],
                   capture_output=True, timeout=60)


def _info_docker(docx):
    dalam = _salin_ke_hermes(docx)
    if dalam is None:
        return None
    try:
        r = _jalan_cli(['docker', 'exec', '-e', 'HOME=/opt/data', 'hermes',
                        CLI_DALAM_HERMES, 'info', dalam])
        if r is None or r.returncode != 0:
            return None
        try:
            data = json.loads(r.stdout)
        except Exception:
            return None
        pages = data.get('pages')
        return int(pages) if isinstance(pages, int) and pages > 0 else None
    finally:
        _hapus_dari_hermes(dalam)


def hitung_halaman(docx):
    """Jumlah halaman WordCraft untuk DOCX, atau None bila tak terukur."""
    mode = temukan_perender()
    if mode is None:
        return None
    if mode[0] == 'cli':
        return _info_cli(mode[1], docx)
    return _info_docker(docx)


def _convert_cli(cmd, docx, pdf):
    r = _jalan_cli(cmd + ['convert', str(docx), str(pdf)])
    return bool(r is not None and r.returncode == 0 and Path(pdf).exists())


def _convert_docker(docx, pdf):
    dalam = _salin_ke_hermes(docx)
    if dalam is None:
        return False
    pdf_dalam = dalam.replace('.docx', '.pdf')
    try:
        r = _jalan_cli(['docker', 'exec', '-e', 'HOME=/opt/data', 'hermes',
                        CLI_DALAM_HERMES, 'convert', dalam, pdf_dalam])
        if r is None or r.returncode != 0:
            return False
        r2 = subprocess.run(['docker', 'cp', f'hermes:{pdf_dalam}', str(pdf)],
                            capture_output=True, text=True, timeout=120)
        return bool(r2.returncode == 0 and Path(pdf).exists())
    finally:
        _hapus_dari_hermes(dalam)
        _hapus_dari_hermes(pdf_dalam)


def render_pdf(docx, pdf):
    """Render DOCX ke PDF memakai WordCraft. True bila berhasil."""
    mode = temukan_perender()
    if mode is None:
        return False
    if mode[0] == 'cli':
        return _convert_cli(mode[1], docx, pdf)
    return _convert_docker(docx, pdf)
