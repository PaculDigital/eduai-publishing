
import json, os, sqlite3, urllib.request, urllib.error, urllib.parse, http.cookiejar, secrets, shutil
BASE='http://127.0.0.1:8001'; DB='/tmp/ujiD_data/eduai.db'; UP='/tmp/ujiD_up'
OP=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0 Safari/537.36'}
def req(jalur, data=None):
    h=dict(H); body=None
    if data is not None:
        body=json.dumps(data).encode(); h['Content-Type']='application/json'
    r=urllib.request.Request(BASE+jalur, data=body, headers=h)   # data => POST otomatis
    try:
        with OP.open(r, timeout=60) as x: return x.status, x.read().decode()[:400]
    except urllib.error.HTTPError as e: return e.code, e.read().decode()[:400]
    except Exception as e: return 0, f'{type(e).__name__}: {e}'
c=sqlite3.connect(DB)
uid,email = c.execute("SELECT id,email FROM users WHERE email LIKE '%uji%' ORDER BY id DESC LIMIT 1").fetchone()
h=dict(H); h['Content-Type']='application/x-www-form-urlencoded'
r=urllib.request.Request(BASE+'/masuk', data=urllib.parse.urlencode({'email':email,'password':os.getenv('E2E_SANDI_BERAT','UjiBerat123!')}).encode(), headers=h)
try:
    with OP.open(r, timeout=60) as x: print('login', x.status)
except urllib.error.HTTPError as e: print('login', e.code, e.read().decode()[:200])
# salinan berkas baru utk uji
asli = c.execute("SELECT id,nama_simpan FROM files WHERE user_id=? AND nama LIKE '%.docx' AND terhapus_pada IS NULL ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
print('asli:', asli)
p_asli = f'{UP}/{uid}/{asli[1]}'
baru = 'diag404-%s.docx' % secrets.token_hex(5)
p_baru = f'{UP}/{uid}/{baru}'
shutil.copy2(p_asli, p_baru)
c.execute("INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,diubah,disunting_pada,terhapus_pada,folder_id) VALUES (?,?,?,?,?,datetime('now'),datetime('now'),NULL,NULL,NULL)",
          (uid,'diag404.docx',baru,os.path.getsize(p_baru),'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
c.commit()
fid = c.execute('SELECT id FROM files WHERE nama_simpan=?',(baru,)).fetchone()[0]
print('file BARU id=', fid, 'user_id=', c.execute('SELECT user_id FROM files WHERE id=?',(fid,)).fetchone()[0])
print('files BARU di COPY terlihat server?', c.execute('SELECT COUNT(*) FROM files').fetchone())
print('terapkan file BARU ->', req('/api/ai/v1/terapkan', {'file_id': fid}))
print('terapkan file LAMA (78) ->', req('/api/ai/v1/terapkan', {'file_id': 78}))
# rute naskah: apakah server melihat file BARU di daftar?
st, isi = req('/naskah')
print('naskah memuat nama baris?', baru[:14], baru in isi)
# bersih
c.execute('DELETE FROM files WHERE id=?',(fid,)); c.commit(); c.close()
try: os.remove(p_baru)
except OSError: pass
