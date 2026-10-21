<?php
/**
 * LENGKAPI submit_article.php — langkah yang KURANG (bukan tambalan).
 *
 * ═══ BACAAN AKAR (bukan tebakan) ═══════════════════════════════════════
 * Jembatan `submit_article.php` sekarang melakukan:
 *    ① Repo::submission()->add()          → artikel dibuat
 *    ② Repo::author()->add()              → penulis dibuat (metadata)
 *    ③ primaryContactId = $primaryAuthorId
 *
 * Yang OJS SENDIRI lakukan tapi JEMBATAN LEWATKAN:
 *    ④ Repo::stageAssignment()->build()   → TAUTKAN AKUN ke artikel
 *       Dasar: OJS bertanya "artikel milik siapa?" lewat
 *       `StageAssignment::withSubmissionIds(...)->withUserId($uid)`
 *       (lib/pkp/classes/submission/Repository.php:187-193) dan
 *       `Repo::submission()->getCollector()->assignedTo([$uid])`.
 *       Tanpa langkah ini artikel masuk Tridarma TANPA pemilik ⇒ user
 *       tidak melihatnya di dashboard-nya, dan EduAi tak bisa menemukannya.
 *
 * ⚠️ primaryContactId = AUTHOR id itu SUDAH BENAR (alamat korespondensi,
 *    bukan penanda pemilik). JANGAN diubah.
 *
 * ⚠️ Bentuk resmi OJS (lib/pkp/classes/stageAssignment/Repository.php:39):
 *        StageAssignment::create([
 *            'submissionId' => …, 'userGroupId' => …,
 *            'userId' => …, 'recommendOnly' => …,
 *            'canChangeMetadata' => …, 'dateAssigned' => …,
 *        ]);
 *    → dibungkus resmi oleh `Repo::stageAssignment()->build(...)` + `save()`.
 *    JANGAN tambah `setData()` — Model ini TIDAK punya setData().
 *
 * Pemakaian:
 *     php lengkapi_jembatan.php            # periksa saja
 *     php lengkapi_jembatan.php --tulis    # tulis (buat cadangan dulu)
 */
$TULIS = in_array('--tulis', $argv ?? []);

$tujuan = '/var/www/html/mcp/submit_article.php';
$kerja = '/tmp/submit_article.kerja.php';

//  ── Selalu kerjakan dari CADANGAN ASLI, bukan dari berkas yang mungkin
//     sudah pernah tersentuh (mencegah tambalan menumpuk).
$asli = '/var/www/html/mcp/backup_register/submit_article.php.20261016-161746.bak';
$sumber = file_exists($asli) ? $asli : $tujuan;
$isi = file_get_contents($sumber);
if ($isi === false) {
    exit("⛔ Tidak bisa membaca sumber: $sumber\n");
}

//  ── Sudah lengkap? ──────────────────────────────────────────────────────
if (strpos($isi, 'stageAssignment()->build') !== false) {
    exit("✓ Langkah penautan akun SUDAH ADA.\n");
}

//  ── Titik sisip: tepat SESUDAH primaryContactId diset di akhir blok
//     penulis — di situ $submissionId, $userId, $primaryAuthorId tersedia.
$penanda = "    if (\$primaryAuthorId) {\n"
    . "        Repo::publication()->edit(\$publication, "
    . "['primaryContactId' => \$primaryAuthorId]);\n"
    . "    }";

if (strpos($isi, $penanda) === false) {
    exit("⛔ Penanda tidak ditemukan — BERHENTI (jangan ubah manual).\n");
}

$tambahan = $penanda . "\n\n"
    . "    //  === Tautkan akun pengirim ke artikel (langkah OJS yang kurang) ===\n"
    . "    //  OJS bertanya \"artikel ini milik siapa?\" lewat stage_assignments\n"
    . "    //  (StageAssignment::withSubmissionIds()->withUserId()). Tanpa ini\n"
    . "    //  artikel tidak punya pemilik: user tak melihatnya di dashboard\n"
    . "    //  dan EduAi tak bisa menemukannya.\n"
    . "    //  Bentuk resmi: lib/pkp/classes/stageAssignment/Repository.php:39\n"
    . "    try {\n"
    . "        \$grupIds = Repo::userGroup()->getArrayIdByRoleId(\n"
    . "            \\PKP\\security\\Role::ROLE_ID_AUTHOR, (int) \$contextId);\n"
    . "        if (!empty(\$grupIds)) {\n"
    . "            //  daftarkan user ke grup Author jurnal ini (sekali saja)\n"
    . "            Repo::userGroup()->assignUserToGroup((int) \$userId,\n"
    . "                                                (int) \$grupIds[0]);\n"
    . "            //  tautkan penulis ke ARTIKEL (penanda pemilik)\n"
    . "            Repo::stageAssignment()->build(\n"
    . "                (int) \$submissionId, (int) \$grupIds[0],\n"
    . "                (int) \$userId)->save();\n"
    . "        }\n"
    . "    } catch (\\Throwable \$e) {\n"
    . "        error_log('taut akun gagal: ' . \$e->getMessage());\n"
    . "    }";

$baru = str_replace($penanda, $tambahan, $isi);

echo "── PERIKSA ──\n";
echo '  sumber        : ' . $sumber . "\n";
echo '  ukuran lama   : ' . strlen($isi) . " byte\n";
echo '  ukuran baru   : ' . strlen($baru) . " byte\n";
echo '  tambahan      : ' . (strlen($baru) - strlen($isi)) . " byte\n";

if (!$TULIS) {
    echo "\n⏸️  BELUM ditulis (mode periksa).\n";
    file_put_contents($kerja, $baru);
    echo '   Hasil periksa disimpan ke: ' . $kerja . "\n";
    exit(0);
}

file_put_contents($kerja, $baru);
//  cadangan dulu, baru tulis
$cad = '/var/www/html/mcp/backup_register/submit_article.php.'
    . date('Ymd-His') . '.bak';
copy($tujuan, $cad);
if (!copy($kerja, $tujuan)) {
    exit("⛔ Gagal menulis $tujuan\n");
}
echo "\n✅ DITULIS. Cadangan: $cad\n";
