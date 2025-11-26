# To use this, put the script in the same directory as your image00.tpf file

import os
import re
import struct

INPUT_FILE = "image00.tpf"
OUT_DIR = "result"
MAX_BMP_SIZE = 100_000_000  # Safety

os.makedirs(OUT_DIR, exist_ok=True)

with open(INPUT_FILE, "rb") as f:
    data = f.read()

# Extract filenames in order

filename_regex = re.compile(
    rb"([A-Za-z0-9_\-]+(?:[A-Za-z0-9_\-])*\.bmp)",
    re.IGNORECASE
)

filenames_raw = filename_regex.findall(data)

# Decode filenames
filenames = []
for raw in filenames_raw:
    try:
        decoded = raw.decode("shift_jis")
    except:
        decoded = raw.decode("latin1")
    filenames.append(decoded)

print(f"[+] Found {len(filenames)} possible filenames")

# Find valid BMPs in order

bmps = []
i = 0
N = len(data)

while i < N - 6:
    if data[i:i+2] == b'BM':
        size = struct.unpack_from("<I", data, i+2)[0]
        if 0 < size < MAX_BMP_SIZE and i+size <= N:
            bmps.append((i, size))
            i += size  # Jump ahead so we don't re-detect inside image data
        else:
            i += 1
    else:
        i += 1

print(f"[+] Found {len(bmps)} valid BMPs")

# Pair BMPs by order

count = min(len(filenames), len(bmps))
print(f"[+] Pairing {count} filenames with {count} BMPs (ordered)")

used = set()

for index in range(count):
    name = filenames[index]
    bmp_offset, bmp_size = bmps[index]

    # Sanitize file name
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)

    # Avoid duplicates
    original = safe_name
    n = 1
    while safe_name.lower() in used:
        base, ext = os.path.splitext(original)
        safe_name = f"{base}_{n}{ext}"
        n += 1

    used.add(safe_name.lower())

    out_path = os.path.join(OUT_DIR, safe_name)

    with open(out_path, "wb") as out:
        out.write(data[bmp_offset:bmp_offset + bmp_size])

    print(f"    {safe_name}  <-  BMP @ 0x{bmp_offset:X} ({bmp_size} bytes)")

# Extract leftover BMPs with fallback names

if len(bmps) > count:
    print(f"[+] {len(bmps) - count} extra BMPs → fallback names")
    for idx in range(count, len(bmps)):
        bmp_offset, bmp_size = bmps[idx]
        fallback = f"image_extra_{idx:03d}.bmp"
        with open(os.path.join(OUT_DIR, fallback), "wb") as out:
            out.write(data[bmp_offset:bmp_offset + bmp_size])

print("[✓] Finished extracting")
