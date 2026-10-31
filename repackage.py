import zipfile, os

src_dir = r'C:\Users\kchan\.gemini\antigravity\scratch\techfusion_combined'
out_zip = r'C:\Users\kchan\Downloads\New folder\techfusion_combined.zip'

EXCLUDE_DIRS = {'__pycache__', '.git'}
EXCLUDE_EXTS = {'.pyc', '.pyo'}

with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    file_count = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in files:
            if any(fname.endswith(e) for e in EXCLUDE_EXTS):
                continue
            full = os.path.join(root, fname)
            arcname = os.path.join('techfusion_combined', os.path.relpath(full, src_dir))
            arcname = arcname.replace(os.sep, '/')
            zf.write(full, arcname)
            file_count += 1

size_mb = os.path.getsize(out_zip) / 1024 / 1024
print("Packaged", file_count, "files ->", out_zip)
print("Zip size:", round(size_mb, 1), "MB")

names = set(zipfile.ZipFile(out_zip).namelist())
checks = [
    'techfusion_combined/app/inkloom_engine.py',
    'techfusion_combined/app/test_suite.py',
    'techfusion_combined/requirements.txt',
    'techfusion_combined/models/inkloom/metadata.json',
    'techfusion_combined/models/inkloom/encoder/model.onnx',
    'techfusion_combined/models/inkloom/encoder/model.onnx.data',
    'techfusion_combined/scripts/export_onnx.py',
    'techfusion_combined/data/test_labeled.csv',
    'techfusion_combined/README.md',
]
print()
for c in checks:
    tag = "OK     " if c in names else "MISSING"
    print(tag, c)
