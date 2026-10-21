"""Evaluasi JS di halaman ASLI — cari kenapa kb-log tidak tampil.

Pakai `Tab` dari potret_asli_sesi.py (sudah ada). Dipanggil berulang supaya
kalau CDP timeout, Wulan TAHU itu alat ukur, bukan aplikasi.
"""
import sys, subprocess, time, json
sys.path.insert(0, '/opt/data/services/eduai-publishing/_sketsa')
from potret_asli_sesi import Tab

kode = ("from app.auth import buat_token\nfrom app.config import SESSION_COOKIE\n"
        "print(SESSION_COOKIE + '|' + buat_token(3))\n")
r = subprocess.run(['docker', 'exec', '-w', '/app', 'eduai-app', 'python3', '-c',
                    kode], capture_output=True, text=True, timeout=90)
nama, token = r.stdout.strip().split('|', 1)

t = Tab('about:blank')
t.tanya('Page.enable')
t.tanya('Network.setCookie', name=nama, value=token, domain='eduai.bikinaja.id',
        path='/', secure=True, httpOnly=True)
t.tanya('Page.navigate', url='https://eduai.bikinaja.id/naskah')
time.sleep(10)


def nilai(e, tunggu=30):
    res = t.tanya('Runtime.evaluate', expression=e, returnByValue=True,
                  awaitPromise=True)
    v = res.get('result', {}).get('result', {})
    if 'value' in v:
        return v['value']
    return None


print('1. kbMuatLog jalan?')
print('  ', nilai("""(async () => {
  try { await kbMuatLog(); } catch (e) { return 'GALAT: ' + e.message; }
  var el = document.getElementById('kb-log');
  return 'display=' + (el ? getComputedStyle(el).display : 'ELEMEN HILANG') +
    ' | ikon=' + document.querySelectorAll('.kb-ik').length +
    ' | baris=' + (document.getElementById('kb-log-baris') || {innerHTML:''}).innerHTML.length;
})()"""))
print('2. isi ringkasan:', nilai("""(() => {
  var e=document.getElementById('kb-log-angka');
  return e ? (e.textContent||'').replace(/\\s+/g,' ').trim().slice(0,140) : 'kosong';})()"""))
print('3. data baris dari server:', nilai("""(async () => {
  var r = await fetch('/pembimbing/log/66'); var d = await r.json();
  return JSON.stringify((d.baris||[]).map(function(b){
    return {id:b.id, dilewati:b.dilewati, warna:b.warna, lencana:b.lencana};}));
})()"""))
print('4. _kbBaris terisi?', nilai("typeof _kbBaris !== 'undefined' ? _kbBaris.length : 'variabel tidak ada'"))
