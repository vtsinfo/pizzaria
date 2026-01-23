import shutil
import os

source_dir = r"C:\Users\Tercio\.gemini\antigravity\brain\0342571e-17c9-4b83-9de5-060d3959b052"
dest_dir = r"c:\vts-site-python\pizzaria\static\uploads"

files = [
    "marmitex_frango_assado_1769136134136.png",
    "marmitex_parmegiana_1769136177408.png",
    "marmitex_picanha_assada_1769136227520.png",
    "coca_cola_2l_1769135764358.png",
    "guarana_2l_1769135778016.png",
    "suco_del_valle_uva_1769135790950.png",
    "cervejas_variadas_1769135805453.png"
]

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

log = []
for f in files:
    src = os.path.join(source_dir, f)
    dst = os.path.join(dest_dir, f)
    try:
        if os.path.exists(src):
            shutil.copy2(src, dst)
            log.append(f"Copied {f}")
        else:
            log.append(f"Source not found: {f}")
    except Exception as e:
        log.append(f"Error copying {f}: {e}")

with open("copy_log.txt", "w") as f:
    f.write("\n".join(log))
