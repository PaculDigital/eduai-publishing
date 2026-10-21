#!/usr/bin/env python3
"""UJI LOGIN OJS — mengikuti CARA PERSIS yang dipakai jembatan yang sudah terbukti.

Jembatan submit_article.php pakai: use PKP\\db\\DAORegistry; + Repo::user()
Kita tiru supaya ujinya SAHIH.
"""
import base64
import subprocess
import textwrap

PHP = textwrap.dedent(r'''<?php
use APP\facades\Repo;
use PKP\db\DAORegistry;

$email = "uji-wulan-16okt2026@eduai.test";
$sandi = "Pass1EduAi";

$pdo = new PDO("mysql:host=ojs-ojs_db-1;dbname=ojs", "ojs", "OjsDb2026!Strong");
$st = $pdo->prepare("select user_id,username,email,length(password) len from users where username=?");
$st->execute([$email]);
$a = $st->fetch(PDO::FETCH_ASSOC);
echo "  1 user di DB: " . ($a ? json_encode($a) : "TIDAK ADA") . "\n";

define('SESSION_DISABLE', true);
define('NO_REDIRECT', true);
define('INDEX_FILE_LOCATION', '/var/www/html/index.php');
chdir('/var/www/html');
require_once('/var/www/html/lib/pkp/includes/bootstrap.php');

$user = Repo::user()->getByUsername($email, true);
if (!$user) { echo "  2 OJS kenal user: TIDAK KETEMU\n"; exit; }
echo "  2 OJS kenal user: id=" . $user->getId()
   . " username=" . $user->getUsername() . "\n";

$rehash = null;
$ok = \PKP\security\Validation::verifyPassword(
        $user->getUsername(), $sandi, $user->getPassword(), $rehash);
echo "  3 sandi '" . $sandi . "' COCOK? " . ($ok ? "YA ✅" : "TIDAK ❌") . "\n";
?>''')

b64 = base64.b64encode(PHP.encode()).decode()
inner = ("echo " + b64 + " | base64 -d > /tmp/ujilogin.php && "
         "docker cp /tmp/ujilogin.php ojs-ojs_web-1:/tmp/uji_login.php && "
         "docker exec ojs-ojs_web-1 php /tmp/uji_login.php")
cmd = ("docker run --rm alpine:3.20 sh -c \""
       "apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null; "
       "sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no "
       "-o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 '" + inner + "'\"")
out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(out.stdout[-3000:])
if out.stderr:
    print("STDERR:", out.stderr[-600:])
