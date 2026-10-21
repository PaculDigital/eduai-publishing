import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/templates/submit_jurnal.html')
s = f.read_text(encoding='utf-8')

# ══ HTML: tombol di tiap baris artikel (muncul hanya kalau DITERIMA) ══
lama_html = """        <td><span class="titik w-${a.warna || 'antre'}"></span>${a.status}
          ${a.tautan ? `<br><a href="${a.tautan}" target="_blank"
             rel="noopener" style="font-size:11.5px;color:var(--biru)">
             buka di Tridarma</a>` : ''}</td>"""
baru_html = """        <td><span class="titik w-${a.warna || 'antre'}"></span>${a.status}
          ${a.tautan ? `<br><a href="${a.tautan}" target="_blank"
             rel="noopener" style="font-size:11.5px;color:var(--biru)">
             buka di Tridarma</a>` : ''}
          ${sudahDiterima(a) ? `<br><button class="tombol putih btn-loa"
             data-berkas="${a.berkas_id}" style="margin-top:6px;font-size:12px">
             📄 Unduh LoA</button>` : ''}</td>"""
assert lama_html in s, 'HTML baris artikel tidak ketemu'
s = s.replace(lama_html, baru_html)
print('✓ tombol Unduh LoA ditambahkan di baris artikel')

# ══ Fungsi bantu: apakah status DITERIMA? ══
lama_fn = "  function gambarArtikel(daftar) {"
baru_fn = """  //  Putusan Bos 17 Okt 2026 — tombol LoA HANYA muncul kalau DITERIMA.
  const STATUS_DITERIMA = ['diterima', 'terbit', 'published', 'accepted'];
  function sudahDiterima(a) {
    return STATUS_DITERIMA.includes(String(a.status || '').trim().toLowerCase());
  }

  function gambarArtikel(daftar) {"""
assert lama_fn in s
s = s.replace(lama_fn, baru_fn, 1)
print('✓ fungsi sudahDiterima')

# ══ Penanganan klik tombol LoA (delegasi, karena baris dibuat dinamis) ══
lama_js = "  muatArtikel();"
baru_js = """  muatArtikel();

  //  ── TOMBOL \"Unduh LoA\" (delegasi: baris tabel dibuat dinamis) ────────
  document.addEventListener('click', async (ev) => {
    const b = ev.target.closest('.btn-loa');
    if (!b) return;
    const berkas = b.dataset.berkas;
    const asal = b.textContent;
    b.disabled = true; b.textContent = 'Menerbitkan LoA…';
    try {
      const r = await fetch('/api/ai/v1/loa/terbitkan', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'berkas_id=' + encodeURIComponent(berkas)
      });
      const j = await r.json();
      if (!j.ok) {
        alert(j.sebab || 'LoA belum bisa diterbitkan.');
        b.disabled = false; b.textContent = asal;
        return;
      }
      //  buka PDF di tab baru
      window.open('/api/ai/v1/loa/unduh?berkas_id=' + encodeURIComponent(berkas), '_blank');
      b.disabled = false;
      b.textContent = '📄 Unduh LoA (' + j.nomor + ')';
    } catch (e) {
      alert('Gagal menghubungi server.');
      b.disabled = false; b.textContent = asal;
    }
  });"""
assert lama_js in s
s = s.replace(lama_js, baru_js, 1)
print('✓ penanganan klik tombol LoA')

f.write_text(s, encoding='utf-8')
print('tersimpan')
