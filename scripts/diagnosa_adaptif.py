"""Diagnosa dengan tunggu ADAPTIF — pantau sampai dokumen termuat.

Masalah: 25 detik belum cukup. Editor bilang "no logic document".
Kita pantau terus sampai logic document ADA (atau timeout).
"""
import json
import time

from cloakbrowser import launch

URL = 'https://eduai.bikinaja.id'
b = launch(headless=False, humanize=False)
page = b.new_page()
page.set_viewport_size({'width': 1500, 'height': 950})

console = []
page.on('console', lambda m: console.append((m.type, m.text[:160])))
page.on('pageerror', lambda e: console.append(('PAGEERROR', str(e)[:160])))

try:
    page.goto(f'{URL}/masuk', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector('#email', timeout=45000)
    page.fill('#email', 'oo.uji@eduai.local')
    page.fill('#password', 'rahasia123')
    page.click('button[type=submit]')
    page.wait_for_load_state('domcontentloaded', timeout=45000)
    time.sleep(3)

    page.goto(f'{URL}/edit/5', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_selector("iframe[src*='documenteditor']", timeout=100000)

    print('=' * 70)
    print('  PANTAU PEMUATAN DOKUMEN (adaptif, sampai 150 detik)')
    print('=' * 70)

    fr = None
    for f in page.frames:
        if 'documenteditor' in (f.url or ''):
            fr = f
            break

    for i in range(15):
        time.sleep(10)
        try:
            st = fr.evaluate('''() => {
                const e = window.editor;
                const out = {
                    canvas: document.querySelectorAll('canvas').length,
                    modified: e.isDocumentModified ? e.isDocumentModified() : null,
                };
                try { out.err = e.getEditorErrorInfo ? e.getEditorErrorInfo() : null; } catch(x){}
                try {
                    const ld = e.private_GetLogicDocument ? e.private_GetLogicDocument() : null;
                    out.adaLogicDoc = !!ld;
                } catch(x) { out.adaLogicDoc = 'err'; }
                try { out.bisaUndo = e.asc_getCanUndo ? e.asc_getCanUndo() : null; } catch(x){}
                try { out.hal = e.asc_getPageCount ? e.asc_getPageCount() : null; } catch(x){}
                return out;
            }''')
        except Exception as e:
            st = {'galat': str(e)[:60]}

        print(f'  t+{(i+1)*10:3d}s: canvas={st.get("canvas")} '
              f'logicDoc={st.get("adaLogicDoc")} err={str(st.get("err"))[:40]}')

        if st.get('adaLogicDoc') is True:
            print(f'\n  ✅ DOKUMEN TERMUAT setelah {(i+1)*10} detik!')
            print(f'     detail: {json.dumps(st, ensure_ascii=False)}')
            break

    # Coba tulis teks kalau logic document ada
    if st.get('adaLogicDoc') is True:
        print('\n=== Coba tulis teks + simpan ===')
        penanda = f'WULAN-{int(time.time())}'
        hasil = fr.evaluate('''(t) => {
            const e = window.editor;
            const out = {};
            try {
                const ld = e.private_GetLogicDocument();
                // Cari method tulis
                const proto = Object.getOwnPropertyNames(Object.getPrototypeOf(ld));
                out.methodTulis = proto.filter(m => /insert|add|text|paragraph|create/i.test(m)).slice(0,15);
                // Coba cara umum
                if (ld.InsertText) { ld.InsertText(t, true); out.cara = 'InsertText'; }
                else if (ld.GetContent && ld.GetContent()) {
                    const c = ld.GetContent();
                    if (c.InsertText) { c.InsertText(t, true); out.cara = 'Content.InsertText'; }
                }
            } catch (err) { out.err = String(err).slice(0,120); }
            return out;
        }''', penanda + '\n')
        print(f'  tulis: {json.dumps(hasil, ensure_ascii=False)[:500]}')

        time.sleep(5)
        cek = fr.evaluate('''() => {
            const e = window.editor;
            const out = {};
            try { out.modified = e.isDocumentModified(); } catch(x){}
            try { out.bisaUndo = e.asc_getCanUndo(); } catch(x){}
            return out;
        }''')
        print(f'  status: {json.dumps(cek, ensure_ascii=False)}')

    print('\n=== Konsol terakhir ===')
    for t, m in console[-10:]:
        print(f'  [{t}] {m[:130]}')

    page.screenshot(path='/opt/data/services/eduai-publishing/shots/muat-final.png')
    print('\n(screenshot: shots/muat-final.png)')

except Exception as e:
    print('galat:', str(e)[:200])
finally:
    try:
        b.close()
    except Exception:
        pass
