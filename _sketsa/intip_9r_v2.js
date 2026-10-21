// Intip 9router (baca saja, tidak mengubah apa pun)
const Database = require('better-sqlite3');
const db = new Database('/app/data/db/data.sqlite', { readonly: true });

const tabel = db.prepare(
  "SELECT name FROM sqlite_master WHERE type='table'").all()
  .map(r => r.name);
console.log('TABEL:', tabel.join(', '));

for (const t of ['providerConnections']) {
  if (!tabel.includes(t)) continue;
  const kol = db.prepare(`PRAGMA table_info(${t})`).all().map(r => r.name);
  console.log(`\nKOLom ${t}:`, kol.join(', '));
  const rows = db.prepare(`SELECT * FROM ${t}`).all();
  for (const r of rows) {
    const aman = {};
    for (const [k, v] of Object.entries(r)) {
      // Jangan pernah cetak kunci/token
      if (/key|token|secret|password|credential/i.test(k)) {
        aman[k] = v ? `<ADA len=${String(v).length}>` : '<KOSONG>';
      } else {
        aman[k] = v;
      }
    }
    console.log(JSON.stringify(aman));
  }
}

// kombinasi model (kalau tabelnya ada)
for (const t of tabel.filter(x => /combo|model|preset/i.test(x))) {
  console.log('\n== TABEL', t, '==');
  const kol = db.prepare(`PRAGMA table_info(${t})`).all().map(r => r.name);
  console.log('kolom:', kol.join(', '));
  const rows = db.prepare(`SELECT * FROM ${t} LIMIT 30`).all();
  for (const r of rows) {
    const aman = {};
    for (const [k, v] of Object.entries(r)) {
      if (/key|token|secret|password/i.test(k)) {
        aman[k] = v ? `<ADA len=${String(v).length}>` : '<KOSONG>';
      } else {
        aman[k] = typeof v === 'string' && v.length > 200 ? v.slice(0, 200) + '…' : v;
      }
    }
    console.log(JSON.stringify(aman));
  }
}
