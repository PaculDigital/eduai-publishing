<?php
/**
 * OJS 3.5 Article Status Bridge v1.0
 *
 * Endpoint: POST /mcp/article_status.php
 * Container: ojs-ojs_web-1
 *
 * Mengikuti pola PERSIS submit_article.php (bootstrap + respond + audit).
 * DIPANGGIL HANYA SAAT USER MENEKAN TOMBOL "Cek Status" — BUKAN otomatis.
 * (Putusan Bos 16 Okt 2026: hemat resource VPS.)
 *
 * Input JSON: {submission_id}  ATAU  {username}
 * Output JSON: {ok, status, kode, tahap, diperbarui, judul, url}
 *
 * Peta tahap OJS -> kata yang dimengerti user:
 *   stage_id 1 = Antrean          stage_id 4 = Perlu Revisi
 *   stage_id 2 = Diperiksa Editor stage_id 5 = Produksi
 *   stage_id 3 = Sedang Review
 *   status   3 = Diterima (published)   status 4 = Ditolak (declined)
 */

ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', '/tmp/php_status.log');
error_reporting(E_ERROR | E_PARSE);

if (!defined('SESSION_DISABLE')) define('SESSION_DISABLE', true);
if (!defined('NO_REDIRECT')) define('NO_REDIRECT', true);

header('Content-Type: application/json; charset=utf-8');

use APP\facades\Repo;
use PKP\db\DAORegistry;
use PKP\core\Core;

function respond($ok, $data = []) {
    $out = ['ok' => $ok] + $data;
    echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function fail($msg, $http = 400) {
    http_response_code($http);
    respond(false, ['error' => $msg]);
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    fail('Method not allowed', 405);
}

$raw = file_get_contents('php://input');
$input = json_decode($raw, true);
if (!is_array($input)) {
    fail('Invalid JSON payload', 400);
}

$sid      = isset($input['submission_id']) ? (int) $input['submission_id'] : 0;
$username = trim((string) ($input['username'] ?? ''));

if ($sid <= 0 && $username === '') {
    fail('Butuh submission_id atau username', 400);
}

// ── Bootstrap OJS (SAMA PERSIS dengan submit_article.php) ────────────────
//  ⚠️ Jangan disederhanakan: jembatan lama define `INDEX_FILE_LOCATION`
//  SEBELUM bootstrap. Tanpa itu → PHP Fatal "Undefined constant".
chdir('/var/www/html');
if (!defined('INDEX_FILE_LOCATION')) {
    define('INDEX_FILE_LOCATION', '/var/www/html/index.php');
}
require_once('/var/www/html/lib/pkp/includes/bootstrap.php');

try {
    $request = \Application::get()->getRequest();
} catch (\Throwable $e) {
    fail('OJS bootstrap gagal: ' . $e->getMessage(), 500);
}

// ── Cari submission ──────────────────────────────────────────────────────
try {
    if ($sid > 0) {
        $submission = Repo::submission()->get($sid);
        if (!$submission) fail('Submission tidak ditemukan', 404);
    } else {
        //  Cari lewat penulis: username OJS = email user.
        //  ⚠️ AKAR (baca OJS, 16 Okt): `submissions` TIDAK punya submitter_id;
        //  cara OJS SENDIRI mencari "artikel milik user X" =
        //      StageAssignment::withSubmissionIds(...)->withUserId($uid)
        //  (lib/pkp/classes/submission/Repository.php:187-193).
        //  Jadi penanda pemilik = tabel `stage_assignments`.
        $user = Repo::user()->getByUsername($username, true);
        if (!$user) fail('User tidak ditemukan', 404);
        $uid = (int) $user->getId();
        $punya = \PKP\stageAssignment\StageAssignment::withUserId($uid)->get();
        $ids = [];
        foreach ($punya as $sa) {
            $ids[] = (int) $sa->submissionId;
        }
        if (count($ids) === 0) {
            fail('Belum ada submission untuk user ini', 404);
        }
        sort($ids);
        $submission = Repo::submission()->get((int) end($ids));
        if (!$submission) fail('Submission tidak ditemukan', 404);
    }
} catch (\Throwable $e) {
    fail('Gagal membaca submission: ' . $e->getMessage(), 500);
}

// ── Baca status ──────────────────────────────────────────────────────────
$stageId  = (int) $submission->getData('stageId');
$statusId = (int) $submission->getData('status');

$PETA_TAHAP = [
    1 => ['Antrean',           'kuning'],
    2 => ['Diperiksa Editor',  'biru'],
    3 => ['Sedang Review',     'biru'],
    4 => ['Perlu Revisi',      'oranye'],
    5 => ['Produksi',          'hijau'],
];
$PETA_STATUS = [
    1 => ['Berjalan',  'biru'],
    3 => ['Diterima',  'hijau'],
    4 => ['Ditolak',   'merah'],
];

// status MENANG atas tahap kalau sudah final (diterima/ditolak)
if (isset($PETA_STATUS[$statusId]) && in_array($statusId, [3, 4], true)) {
    list($namaStatus, $warna) = $PETA_STATUS[$statusId];
} else if (isset($PETA_TAHAP[$stageId])) {
    list($namaStatus, $warna) = $PETA_TAHAP[$stageId];
} else {
    $namaStatus = 'Sedang Diproses';
    $warna = 'abu';
}

$diperbarui = (string) ($submission->getData('dateLastActivity')
    ?: $submission->getData('lastModified') ?: '');

//  Judul: JANGAN sampai menggagalkan pembacaan status.
//  ⚠️ `getLocalizedTitle()` butuh locale sesi web; di luar sesi galat
//  "Request not initialized" ⇒ dibungkus try/catch (pelajaran 16 Okt).
$judul = '';
try {
    $pub = $submission->getCurrentPublication();
    $judul = (string) $pub->getLocalizedTitle(null, 'id');
    if ($judul === '') {
        $judul = (string) $pub->getLocalizedTitle();
    }
} catch (\Throwable $e) {
    foreach ((array) $submission->getData('title') as $nilai) {
        if (is_string($nilai) && trim($nilai) !== '') {
            $judul = trim($nilai);
            break;
        }
    }
}

respond(true, [
    'submission_id' => (int) $submission->getId(),
    'status'        => $namaStatus,
    'warna'         => $warna,
    'tahap'         => $stageId,
    'kode_status'   => $statusId,
    'judul'         => $judul,
    'diperbarui'    => $diperbarui,
    'url'           => 'https://tridarma.id/index.php/jemt/workflow/index/'
                       . $submission->getId(),
]);
