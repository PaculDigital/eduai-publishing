"""Cari berkas yang punya NASKAH ASLI (sumber='unggah'/'naskah') untuk uji C7."""
import sqlite3

c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row

print("=== sumber versi yang ADA di DB (per berkas) ===")
for r in c.execute('''
        select file_id, sumber, count(*) n, max(length(isi)) maks
        from versi_dokumen
        where length(trim(coalesce(isi,''))) > 500
        group by file_id, sumber order by file_id'''):
    print(f"  file {r['file_id']:3d} | sumber={str(r['sumber']):8s} | "
          f"{r['n']} versi | maks {r['maks']} kar")

print()
print("=== versi sumber BUKAN 'ai' (kandidat naskah asli) ===")
n = 0
for r in c.execute('''select file_id,nomor,sumber,length(isi) n,
                      substr(isi,1,100) kp from versi_dokumen
                      where coalesce(sumber,'') <> 'ai'
                      and length(trim(coalesce(isi,'')))>500
                      order by file_id,nomor'''):
    n += 1
    print(f"  file {r['file_id']:3d} v{r['nomor']} [{r['sumber']}] {r['n']} kar")
    print(f"      {str(r['kp'])[:95]!r}")
print(f'  total = {n}')

print()
print("=== section_state (naskah asli tiap bab disimpan di sini!) ===")
for r in c.execute('''select file_id, count(*) n,
                      sum(case when length(trim(coalesce(isi_teks,'')))>200
                          then 1 else 0 end) berisi,
                      max(char_count) maks
                      from section_state group by file_id having n>0'''):
    print(f"  file {r['file_id']:3d} | {r['n']} bagian | "
          f"berisi {r['berisi']} | maks {r['maks']} kar")
