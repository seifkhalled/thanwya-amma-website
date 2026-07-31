import gzip
import struct
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
PARQUET = ROOT / "نتيجة ثانوية عامة نظام حديث.parquet"

MAGIC = b"TW26"


def varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def main():
    df = pd.read_parquet(
        PARQUET,
        columns=["arabic_name", "seating_no", "total_degree", "student_case_desc"],
    ).fillna("")
    df["student_case_desc"] = df["student_case_desc"].str.strip()
    df = df.sort_values("arabic_name", kind="mergesort").reset_index(drop=True)

    enc = [n.encode("utf-8") for n in df["arabic_name"].tolist()]
    lens = [len(n) for n in df["arabic_name"].tolist()]
    name_bytes = b"".join(enc)
    n = len(df)

    offsets = np.zeros(n + 1, dtype=np.int64)
    np.cumsum(lens, dtype=np.int64, out=offsets[1:])

    ids = df["seating_no"].to_numpy(dtype=np.int64)
    degrees = df["total_degree"].to_numpy(dtype=np.uint8)

    case_labels = df["student_case_desc"].unique().tolist()
    case_map = {c: i for i, c in enumerate(case_labels)}
    cases = df["student_case_desc"].map(case_map).to_numpy(dtype=np.uint8)

    header = MAGIC + struct.pack("<II", n, len(name_bytes))
    off_bytes = b"".join(varint(int(x)) for x in np.diff(offsets))
    id_bytes = b"".join(varint(int(x)) for x in ids)
    raw = header + off_bytes + id_bytes + degrees.tobytes() + cases.tobytes() + name_bytes

    OUT.mkdir(exist_ok=True)
    with gzip.open(OUT / "data.gz", "wb", compresslevel=9) as f:
        f.write(raw)

    meta = {"n": n, "cases": case_labels, "built": date.today().isoformat()}
    with open(OUT / "meta.js", "w", encoding="utf-8") as f:
        f.write(f"window.DATA_META = {meta!r};\n")

    print(f"rows: {n:,}")
    print(f"case labels: {case_labels}")
    print(f"raw binary: {len(raw)/1e6:.1f} MB, gzipped: {(OUT/'data.gz').stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
