// Perbaiki daftar model vision 9router (ACC Bos 15Sep26).
//
// MASALAH: provider `ag` & `cb` tercabut (kredensial hilang), jadi
// `inferhub/cb/gpt-5.6-luna` (model vision lama) MATI. Daftar vision juga
// berisi model-model yang sudah mati (openrouter/nvidia free, AIH, gemini/*).
//
// SOLUSI: ganti daftar dengan urutan yang SUDAH DIBUKTIKAN HIDUP lewat tes
// gambar nyata: `inferhub/ag/gemini-3.8-flash-high` → HTTP 200 + jawab benar.
// Model lain dipertahankan sebagai cadangan berurutan.

const Database = require('better-sqlite3');
const db = new Database('/app/data/db/data.sqlite');
const row = db.prepare('SELECT id,data FROM settings WHERE id=1').get();
const s = JSON.parse(row.data);

const LAMA = s.capacityAdapter?.vision?.models || [];

// Urutan BARU: yang terbukti hidup DULU, cadangan sesudahnya.
const BARU = [
  'inferhub/ag/gemini-3.8-flash-high',   // ✅ teruji 15Sep26 (HTTP 200, jawab benar)
  'inferhub/ag/gemini-3.7-flash-high',
  'inferhub/ag/gemini-3.6-flash-high',
  'inferhub/gemini-3.8-flash',
  'inferhub/glm-4.6v',
  'inferhub/zai/glm-4.6v',
  'Infron/google/gemini-3.8-flash',
  'Xkiro/google/gemini-3.8-flash',
  'Infron/qwen/qwen3-vl-plus',
  'Xkiro/z-ai/glm-4.6v',
];

s.capacityAdapter = s.capacityAdapter || {};
s.capacityAdapter.vision = s.capacityAdapter.vision || {};
s.capacityAdapter.vision.enabled = true;
s.capacityAdapter.vision.models = BARU;

db.prepare('UPDATE settings SET data=? WHERE id=1').run(JSON.stringify(s));

console.log('=== LAMA (' + LAMA.length + ' model) ===');
LAMA.forEach(m => console.log('   -', m));
console.log('=== BARU (' + BARU.length + ' model) ===');
BARU.forEach(m => console.log('   +', m));
console.log('\nTersimpan:', db.prepare('SELECT data FROM settings WHERE id=1').get().data.includes('inferhub/ag/gemini-3.8-flash-high'));
db.close();
