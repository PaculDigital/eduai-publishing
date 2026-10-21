#!/usr/bin/env bash
#  Apakah OJS punya alat: (a) reset password user, (b) baca status submission?
docker run --rm alpine:3.20 sh -c "
apk add --no-cache openssh-client sshpass 2>/dev/null >/dev/null
sshpass -p 'duit@VPS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=25 -p 9027 ubuntu@103.186.30.230 'bash -s' <<'EOSSH'
echo '══ ① MCP: ada tool reset password / lihat status? ══'
grep -nE '@mcp.tool|async def ' /opt/data/services/ojs-mcp/main.py | sed -n '1,30p'
echo
echo '══ ② OJS: fungsi reset password resmi ══'
docker exec ojs-ojs_web-1 grep -rln 'sendPasswordReset\|PASSWORD_RESET' /var/www/html/lib/pkp/classes/ 2>/dev/null | head -5
echo
echo '══ ③ OJS: cara baca status submission (stage) ══'
docker exec ojs-ojs_web-1 sh -c \"grep -rn 'WORKFLOW_STAGE_ID\|getData(.stageId.)' /var/www/html/lib/pkp/classes/submission/Submission.php 2>/dev/null | head -6\"
EOSSH
" 2>&1 | tail -40