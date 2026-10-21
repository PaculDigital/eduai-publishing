#!/bin/bash
# UKUR BIAYA NYATA: berapa biaya 1 revisi (naskah 55.000 kar)?
# Cara: DELTA SALDO 9router sebelum/sesudah.
echo "═══ SALDO 9router SEBELUM ═══"
curl -s --max-time 20 "http://172.17.0.1:20128/v1/me/usage" \
  -H "Authorization: Bearer $(docker exec eduai-app printenv EDUAI_ROUTER_KEY 2>/dev/null)" 2>/dev/null | head -c 600
echo
echo
echo "═══ Kunci router dipakai? ═══"
docker exec eduai-app printenv EDUAI_ROUTER_KEY 2>/dev/null | head -c 20 && echo "...(ada)"
docker exec eduai-app printenv EDUAI_AI_MODEL 2>/dev/null
docker exec eduai-app printenv EDUAI_ROUTER_BASE 2>/dev/null