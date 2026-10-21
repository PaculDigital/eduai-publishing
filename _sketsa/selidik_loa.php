<?php
/**
 * SELIDIK LOA — apa yang BENAR-BENAR ada di jurnal JEMT untuk "letter".
 * Mode BACA saja. Menjawab: apakah user bisa mengunduh LOA dari OJS?
 */
chdir('/var/www/html');
if (!defined('INDEX_FILE_LOCATION')) define('INDEX_FILE_LOCATION', '/var/www/html/index.php');
require_once('/var/www/html/lib/pkp/includes/bootstrap.php');

$k = \Illuminate\Support\Facades\DB::connection();

echo "══ ① GENRE berkas di jurnal JEMT (context 1) ══\n";
foreach ($k->select("SELECT g.genre_id, g.key, g.category,
                            gs.setting_value AS nama
                     FROM genres g
                     LEFT JOIN genre_settings gs ON gs.genre_id = g.genre_id
                        AND gs.setting_name='name' AND gs.locale='en'
                     WHERE g.context_id = 1 ORDER BY g.genre_id") as $r) {
    echo "  id={$r->genre_id} key={$r->key} [{nama={$r->nama}] kat={$r->category}\n";
}

echo "\n══ ② APAKAH ada berkas jenis 'letter'/LOA terunggah? ══\n";
$ada = 0;
foreach ($k->select("SELECT fs.file_id, fs.submission_id, g.key AS genre_key, gs.setting_value AS nama
                     FROM submission_files sf
                     JOIN files fs ON fs.file_id = sf.file_id
                     JOIN genres g ON g.genre_id = sf.genre_id
                     LEFT JOIN genre_settings gs ON gs.genre_id = g.genre_id
                        AND gs.setting_name='name' AND gs.locale='en'
                     WHERE g.context_id = 1
                       AND (LOWER(g.key) LIKE '%letter%' OR LOWER(g.key) LIKE '%loa%'
                            OR LOWER(gs.setting_value) LIKE '%letter%'
                            OR LOWER(gs.setting_value) LIKE '%loa%'
                            OR LOWER(gs.setting_value) LIKE '%accept%')
                     LIMIT 10") as $r) {
    $ada++;
    echo "  file={$r->file_id} sub={$r->submission_id} genre={$r->genre_key} nama={$r->nama}\n";
}
echo '  jumlah=' . $ada . "\n";

echo "\n══ ③ berapa submission JEMT & statusnya? ══\n";
foreach ($k->select("SELECT submission_id, stage_id, status, date_submitted
                     FROM submissions WHERE context_id = 1 ORDER BY submission_id DESC LIMIT 10") as $r) {
    echo "  sub={$r->submission_id} stage={$r->stage_id} status={$r->status} tgl={$r->date_submitted}\n";
}

echo "\n══ ④ ARTEFAK 'letter' yang OJS sediakan di alur editorial ══\n";
echo "  (dari kelas Sender/email keputusan — cek yang DISIMPAN, bukan hanya dikirim)\n";
$f = '/var/www/html/lib/pkp/classes/mail/mailables/DecisionAcceptNotifyAuthor.php';
if (file_exists($f)) {
    echo "  ADA: " . basename($f) . "\n";
    echo (string) shell_exec("grep -nE 'class |template|getData|subject' $f | head -10") . "\n";
}

echo "\n══ ⑤ apakah kiriman email OJS disimpan ke DB (bisa dibaca ulang)? ══\n";
foreach ($k->select("SHOW TABLES LIKE '%email%'") as $r) {
    echo "  tabel: " . implode(' ', (array) $r) . "\n";
}
foreach ($k->select("SHOW TABLES LIKE '%log%'") as $r) {
    echo "  tabel: " . implode(' ', (array) $r) . "\n";
}
