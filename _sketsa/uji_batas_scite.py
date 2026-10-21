"""UJI BATAS Scite API (12Okt26) — apakah aman untuk skala besar?

Pertanyaan Bos: "aman untuk ribuan artikel atau tidak?"
Uji: 50 DOI nyata berturut-turut → catat HTTP + waktu + kapan mulai dibatasi.
"""
import json
import time
import urllib.error
import urllib.request

# 50 DOI nyata dari berbagai bidang (campuran besar/kecil)
DOIS = [
    '10.1038/nature12373', '10.1177/002224299405800302', '10.3389/fpsyg.2020.01234',
    '10.1016/j.jbusres.2019.07.017', '10.1016/j.jbusres.2016.04.024',
    '10.1108/02651339310025866', '10.5465/amr.2000.2791609',
    '10.1287/mnsc.1040.0257', '10.1016/j.ijresmar.2015.04.001',
    '10.1509/jmkg.73.3.52', '10.1002/smj.438', '10.1111/j.1467-6486.2006.00624.x',
    '10.1016/j.jretai.2012.10.001', '10.1177/002224299405800302',
    '10.1016/j.chb.2015.03.021', '10.1016/j.jbusres.2020.01.032',
    '10.1108/EJM-10-2017-0734', '10.1016/j.tourman.2018.02.012',
    '10.1016/j.ijhm.2019.102368', '10.1016/j.annals.2019.102795',
    '10.1002/mar.21341', '10.1016/j.techfore.2020.120234',
    '10.1108/IJCHM-04-2019-0377', '10.1080/02642069.2019.1613375',
    '10.1057/s41272-020-00241-7', '10.1016/j.jclepro.2020.121637',
    '10.1108/JSM-01-2019-0041', '10.1108/IJEBR-05-2019-0279',
    '10.1016/j.respol.2019.103833', '10.5465/amj.2017.0290',
    '10.1037/apl0000737', '10.1038/s41586-019-1234-5',
    '10.1126/science.1231143', '10.1073/pnas.1309969111',
    '10.1146/annurev-psych-010418-103348', '10.1016/j.cell.2017.09.024',
    '10.1038/nature11017', '10.1038/nature14539',
    '10.1016/j.jbusres.2011.02.001', '10.1108/09564231011083251',
    '10.1177/0047287517727578', '10.1016/j.chb.2019.106186',
    '10.1016/j.ijinfomgt.2020.102110', '10.1108/BPMJ-10-2019-0410',
    '10.1002/csr.1888', '10.1016/j.technovation.2018.06.005',
    '10.1108/MD-07-2018-0743', '10.1016/j.jom.2019.03.001',
    '10.1016/j.dss.2019.113185', '10.1109/TEM.2019.2911102',
]

print('UJI BATAS SCITE — %d DOI berturut-turut' % len(DOIS))
print('=' * 70)
a = time.time()
hitung, blokir, mulai_blokir = {}, 0, None
for i, d in enumerate(DOIS, 1):
    t0 = time.time()
    try:
        r = urllib.request.urlopen(
            'https://api.scite.ai/tallies/%s' % d, timeout=20)
        kode = r.status
        r.read()
    except urllib.error.HTTPError as e:
        kode = e.code
    except Exception as e:                                       # noqa: BLE001
        kode = 'ERR:%s' % type(e).__name__
    dt = time.time() - t0
    hitung[kode] = hitung.get(kode, 0) + 1
    if kode in (429, 403, 401, 503) and mulai_blokir is None:
        mulai_blokir = i
    tanda = '✅' if kode == 200 else ('🚫' if kode in (429, 403) else '⚠️')
    if i <= 12 or tanda != '✅':
        print('  %2d. %-40s %s %s  (%.2f dtk)' % (i, d, tanda, kode, dt))
    if i % 10 == 0:
        print('      ... %d selesai · %.1f dtk total' % (i, time.time() - a))
print('=' * 70)
print('RINGKASAN kode HTTP:', hitung)
print('TOTAL waktu: %.1f dtk untuk %d panggilan (rata %.2f dtk)' % (
    time.time() - a, len(DOIS), (time.time() - a) / len(DOIS)))
print('BLOKIR mulai pada panggilan ke-:', mulai_blokir or 'TIDAK ADA ✅')
