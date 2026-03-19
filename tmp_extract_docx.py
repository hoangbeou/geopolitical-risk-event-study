from zipfile import ZipFile
from xml.etree import ElementTree as ET
from pathlib import Path

docx_path = Path(r'C:\Users\Admin\Desktop\khoa_luan_chinh_sua_final.docx')
out_path = Path('khoa_luan_chinh_sua_final.txt')

if not docx_path.exists():
    raise SystemExit(f"Docx not found: {docx_path}")

with ZipFile(docx_path) as docx:
    xml = docx.read('word/document.xml')

root = ET.fromstring(xml)
texts = []
for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    parts = []
    for t in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            parts.append(t.text)
    if parts:
        texts.append(''.join(parts))

out_path.write_text('\n'.join(texts), encoding='utf-8')
print(f"Written: {out_path.resolve()}")
