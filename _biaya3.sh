#!/bin/bash
# UKUR BIAYA NYATA 1 REVISI — dari 9router via EDUAI_ROUTER_KEY.
# Metode: DELTA SALDO sebelum/sesudah (usage.cost tidak reliabel).
K=$(docker exec eduai-app printenv EDUAI_ROUTER_KEY 2>/dev/null)
BASE=http://172.17.0.1:20128

echo "═══ Cari endpoint saldo 9router ═══"
for u in /v1/me/usage /v1/me /v1/usage /api/v1/me/usage /api/v1/user/self; do
  printf "  %-22s " "$u"
  code=$(curl -s -o /tmp/_r.json -w "%{http_code}" --max-time 12 "$BASE$u" -H "Authorization: Bearer $K")
  isi=$(head -c 200 /tmp/_r.json 2>/dev/null | tr -d '\n' | sed 's/^[[:space:]]*//')
  echo "HTTP $code | ${isi:0:150}"
done