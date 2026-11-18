// Verifikasi cermin JS vs Python untuk editor Diagram (putaran 6).
// Ekstrak fungsi geometri murni dari app/templates/diagram_editor.html
// (bungkus..geserLabelBebas), jalankan hitungPenempatan (cermin
// gambarUlang tanpa DOM) untuk satu tata (kotak + panah) dari stdin,
// tulis hasil sebagai JSON. Dipakai /tmp/dg7/cek_editor.py.
const fs = require('fs');
const path = require('path');
const tplPath = process.argv[3] || path.join(
  __dirname, '..', 'app', 'templates', 'diagram_editor.html');
const tpl = fs.readFileSync(tplPath, 'utf8');
const awal = tpl.indexOf('function bungkus');
const akhir = tpl.indexOf('function gambarUlang');
if (awal < 0 || akhir < 0 || akhir <= awal) {
  console.error('fungsi JS tidak ditemukan di template');
  process.exit(1);
}
// TINGGI_KANVAS dan LEBAR_KANVAS dipakai ruteBengkok (jepit titik
// belok); di template = state.tinggi || 800 dan state.lebar ||
// 1400. Diisi dari tata masuk sebelum hitung.
var TINGGI_KANVAS = 800;
var LEBAR_KANVAS = 1400;
eval(tpl.slice(awal, akhir));

function hitungPenempatan(kotak, panah, indikator) {
  var peta = {}, tinggi = {};
  kotak.forEach(function (k) {
    peta[k.id] = k;
    tinggi[k.id] = tinggiTampil(k);
  });
  var daftar = panah;
  var kelompok = {};
  daftar.forEach(function (p, idx) {
    var a = peta[p.dari], b = peta[p.ke];
    if (!a || !b) return;
    var kunci = p.dari + '>' + p.ke;
    if (!kelompok[kunci]) kelompok[kunci] = [];
    kelompok[kunci].push(idx);
  });
  var JARAK_JALUR = 40;
  var geserLabel = {};
  var garis = {};
  Object.keys(kelompok).forEach(function (kunci) {
    var idxs = susunanKelompok(kelompok[kunci], daftar);
    var n = idxs.length;
    idxs.forEach(function (idx, i) {
      var p = daftar[idx];
      var a = peta[p.dari], b = peta[p.ke];
      var aT = {x: a.x, y: a.y, w: a.w, h: tinggi[a.id]};
      var bT = {x: b.x, y: b.y, w: b.w, h: tinggi[b.id]};
      var vertikal = tumpukVertikal(aT, bT);
      var rMin = vertikal ? Math.min(a.w, b.w) / 2
                          : Math.min(tinggi[a.id], tinggi[b.id]) / 2;
      var langkahJalur = n <= 1 ? JARAK_JALUR
        : Math.min(JARAK_JALUR, 2 * (rMin - 6) / (n - 1));
      var dy = (i - (n - 1) / 2) * langkahJalur;
      geserLabel[idx] = dy;
      var ujung;
      if (vertikal) {
        var s, e;
        if (a.y + tinggi[a.id] / 2 <= b.y + tinggi[b.id] / 2) {
          s = titikElips(a, tinggi[a.id], dy, 'bawah');
          e = titikElips(b, tinggi[b.id], dy, 'atas');
        } else {
          s = titikElips(a, tinggi[a.id], dy, 'atas');
          e = titikElips(b, tinggi[b.id], dy, 'bawah');
        }
        ujung = [s[0], s[1], e[0], e[1]];
      } else {
        var s2 = titikElips(a, tinggi[a.id], dy, 'kanan'),
            e2 = titikElips(b, tinggi[b.id], dy, 'kiri');
        ujung = [s2[0], s2[1], e2[0], e2[1]];
      }
      garis[idx] = {x1: ujung[0], y1: ujung[1], x2: ujung[2],
                    y2: ujung[3],
                    lx: (ujung[0] + ujung[2]) / 2,
                    ly: (ujung[1] + ujung[3]) / 2};
    });
  });
  var kotakGambar = kotak.map(function (k) {
    return {id: k.id, x: k.x, y: k.y, w: k.w, h: tinggi[k.id]};
  });
  // Indikator (Bagian 20): posisi kotak + panah + teks dari
  // hitungPosisiIndikator (template), sama dengan tambah_indikator
  // + panah_indikator + pilihFontIndikator di Python. Label juga
  // menghindari kotak indikator (kotakLabel, cermin penempatan_label).
  var posInd = hitungPosisiIndikator(kotak, indikator || [], tinggi);
  var kotakLabel = kotakGambar.concat(posInd.map(function (i) {
    return {x: i.x, y: i.y, w: i.w, h: i.h};
  }));
  var labelSudah = [];
  var hasil = [];
  // Urutan penempatan label sama dengan penempatan_label di
  // app/gambar.py: per kelompok (dari, ke) + susunan, bukan urutan
  // daftar panah (daftar mencampur segmen langsung dan lewat).
  var urutanLabel = [];
  Object.keys(kelompok).forEach(function (kunci) {
    susunanKelompok(kelompok[kunci], daftar).forEach(function (idx) {
      urutanLabel.push(idx);
    });
  });
  urutanLabel.forEach(function (idx) {
    var p = daftar[idx];
    var a = peta[p.dari], b = peta[p.ke];
    if (!a || !b || !garis[idx]) return;
    var u = garis[idx];
    var mx = u.lx, my = u.ly;
    var titik = [[u.x1, u.y1], [u.x2, u.y2]];
    var rute = [];
    var aT2 = {x: a.x, y: a.y, w: a.w, h: tinggi[a.id]};
    var bT2 = {x: b.x, y: b.y, w: b.w, h: tinggi[b.id]};
    var lurus = ruteLurus(aT2, bT2, geserLabel[idx], kotakGambar,
                          p.dari, p.ke, tumpukVertikal(aT2, bT2));
    if (lurus) {
      u = {x1: lurus[0], y1: lurus[1], x2: lurus[2], y2: lurus[3],
           lx: (lurus[0] + lurus[2]) / 2,
           ly: (lurus[1] + lurus[3]) / 2};
      mx = u.lx; my = u.ly;
      titik = [[u.x1, u.y1], [u.x2, u.y2]];
    }
    var rb = ruteBengkok(u.x1, u.y1, u.x2, u.y2, geserLabel[idx],
                         kotakGambar, p.dari, p.ke);
    if (rb.length) {
      rute = rb;
      titik = [[u.x1, u.y1]].concat(rb, [[u.x2, u.y2]]);
      var tengah = titikPolilinia(titik, panjangPolilinia(titik) / 2);
      mx = tengah[0]; my = tengah[1];
    }
    // Python menggeser dan mencatat SEMUA panah, termasuk segmen
    // kedua tanpa label (kotak 12x8). Label menghindari kotak
    // indikator juga (kotakLabel).
    var pos = geserLabelBebas(titik, mx, my, p.label || '', kotakLabel,
                              labelSudah);
    var cx = pos[0], cy = pos[1];
    labelSudah.push({
      kiri: pos[0] - lebarLabel(p.label || '') / 2 - 6,
      atas: pos[1] - tinggiLabel(p.label || '') / 2 - 4,
      kanan: pos[0] + lebarLabel(p.label || '') / 2 + 6,
      bawah: pos[1] + tinggiLabel(p.label || '') / 2 + 4});
    hasil.push({label: p.label || '', gaya: p.gaya || '',
                dari: p.dari, ke: p.ke,
                x1: u.x1, y1: u.y1, x2: u.x2, y2: u.y2,
                rute: rute, cx: cx, cy: cy});
  });
  return {label: hasil, indikator: posInd};
}

const masuk = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
TINGGI_KANVAS = masuk.tinggi || 800;
LEBAR_KANVAS = masuk.lebar || 1400;
const keluar = hitungPenempatan(masuk.kotak, masuk.panah,
                                masuk.indikator);
process.stdout.write(JSON.stringify(keluar));
