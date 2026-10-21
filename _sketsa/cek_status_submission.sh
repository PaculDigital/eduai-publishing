#!/usr/bin/env bash
#  Bisakah kita baca STATUS submission? Cari kolom nyata di DB OJS.
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① kolom tabel submissions (status/stage) ══'
docker exec ojs-ojs_db-1 mysql -uroot -p'TridarmaOJS2026!Secure' -N -e \"select column_name from information_schema.columns where table_schema='ojs' and table_name='submissions' order by ordinal_position;\" 2>/dev/null | tr '\n' ' '
echo
echo
echo '══ ② isi submissions (5 terakhir) ══'
docker exec ojs-ojs_db-1 mysql -uroot -p'TridarmaOJS2026!Secure' -e \"select submission_id, context_id, stage_id, status, date_submitted from ojs.submissions order by submission_id desc limit 5;\" 2>/dev/null
echo '══ ③ tabel stage_assignment ada? (riwayat tahap) ══'
docker exec ojs-ojs_db-1 mysql -uroot -p'TridarmaOJS2026!Secure' -N -e \"show tables from ojs like '%stage%';\" 2>/dev/null | tr '\n' ' '
EOSSH
" 2>&1 | tail -30