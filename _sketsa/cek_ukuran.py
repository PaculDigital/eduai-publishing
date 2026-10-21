import os

for fid, simpan in [(59, '94979bfacfa7a39b.docx'),
                    (58, '5dbe66b0e48ea0b1.docx'),
                    (57, '59e631ea7074d0dd.docx'),
                    (56, '0fdc31a831c258c9.docx')]:
    p = f'/app/uploads/3/{simpan}'
    print(fid, os.path.getsize(p) if os.path.exists(p) else 'HILANG', 'byte')
