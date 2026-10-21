import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/submit_jurnal.py')
s = f.read_text(encoding='utf-8')

# AKAR: alamat default 'http://ojs-ojs_web-1/mcp' = nama container INTERNAL VPS Tridarma
# -> DNS tidak ketemu dari container EduAi. Yang TERBUKTI jalan: lewat domain HTTPS.
lama = """OJS_BRIDGE = os.getenv(
    'EDUAI_OJS_BRIDGE',
    'http://ojs-ojs_web-1/mcp',
).rstrip('/')"""
baru = """#  ⚠️ 17 Okt 2026 (TERUKUR): default lama 'http://ojs-ojs_web-1/mcp' = nama
#  container INTERNAL VPS Tridarma => DNS tidak ketemu dari container EduAi
#  (Errno -3). Port 9027 di IP publik = SSH, BUKAN jembatan. Yang TERBUKTI
#  menjawab: lewat domain HTTPS `https://tridarma.id/mcp`.
OJS_BRIDGE = os.getenv(
    'EDUAI_OJS_BRIDGE',
    'https://tridarma.id/mcp',
).rstrip('/')"""
assert lama in s, 'pola OJS_BRIDGE tidak ketemu'
s = s.replace(lama, baru)
f.write_text(s, encoding='utf-8')
print('✓ OJS_BRIDGE: http://ojs-ojs_web-1/mcp  ->  https://tridarma.id/mcp')
print('cek:', "'https://tridarma.id/mcp'" in s)
