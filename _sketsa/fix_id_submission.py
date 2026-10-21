import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/loa/verifikasi-loa.html')
s = f.read_text(encoding='utf-8')

# AKAR: halaman minta d.submission_id, tapi catat_terbit menyimpan 'id_ojs'
lama = '<tr><td>ID Submission</td><td>${esc(d.submission_id)}</td></tr>'
baru = '<tr><td>ID Submission</td><td>${esc(d.id_ojs || d.submission_id || "-")}</td></tr>'
assert lama in s
s = s.replace(lama, baru)
f.write_text(s, encoding='utf-8')
print('✓ ID Submission: pakai id_ojs (dengan cadangan submission_id)')
print('cek:', 'd.id_ojs || d.submission_id' in s)
