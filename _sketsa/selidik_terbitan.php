<?php
/**
 * SELIDIK: apakah Tridarma menyimpan VOLUME + NOMOR TERBITAN untuk sebuah
 * artikel? (Untuk isian "Rencana Terbit: Volume X, Nomor Y" di LoA.)
 * Mode BACA saja.
 */
chdir('/var/www/html');
if (!defined('INDEX_FILE_LOCATION')) define('INDEX_FILE_LOCATION', '/var/www/html/index.php');
require_once('/var/www/html/lib/pkp/includes/bootstrap.php');

$k = \Illuminate\Support\Facades\DB::connection();

echo "══ ① tabel penerbitan (issues) ══\n";
foreach ($k->select("SHOW TABLES LIKE '%issue%'") as $r) {
    echo "  tabel: " . implode(' ', (array) $r) . "\n";
}

echo "\n══ ② isi tabel issues (kolom penting) ══\n";
foreach ($k->select("DESCRIBE issues") as $r) {
    echo "  {$r->Field}\n";
}

echo "\n══ ③ daftar terbitan jurnal JEMT ══\n";
foreach ($k->select("SELECT i.issue_id, i.volume, i.number, i.year, i.date_published, i.published
                     FROM issues i WHERE i.journal_id = 1 ORDER BY i.issue_id") as $r) {
    echo "  issue={$r->issue_id} Vol={$r->volume} No={$r->number} th={$r->year} terbit={$r->date_published} published={$r->published}\n";
}

echo "\n══ ④ artikel DITERBITKAN + terbitan mana? (publication_issues) ══\n";
foreach ($k->select("SELECT pi.publication_id, pi.issue_id, i.volume, i.number
                     FROM publication_issues pi
                     LEFT JOIN issues i ON i.issue_id = pi.issue_id
                     ORDER BY pi.publication_id DESC LIMIT 10") as $r) {
    echo "  pub={$r->publication_id} issue={$r->issue_id} Vol={$r->volume} No={$r->number}\n";
}

echo "\n══ ⑤ status artikel: mana yang DITERIMA / TERBIT? ══\n";
foreach ($k->select("SELECT submission_id, stage_id, status, date_submitted, date_published
                     FROM submissions WHERE context_id = 1 ORDER BY submission_id DESC LIMIT 8") as $r) {
    echo "  sub={$r->submission_id} stage={$r->stage_id} status={$r->status} tgl_terbit={$r->date_published}\n";
}

echo "\n══ ⑥ tanggal keputusan 'terima' tersimpan di mana? ══\n";
foreach ($k->select("SELECT DISTINCT setting_name FROM submission_settings
                     WHERE setting_name LIKE '%decision%' OR setting_name LIKE '%accept%'
                        OR setting_name LIKE '%date%' LIMIT 12") as $r) {
    echo "  setting: {$r->setting_name}\n";
}
