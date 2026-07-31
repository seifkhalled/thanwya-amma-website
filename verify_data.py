import gzip
import struct
from pathlib import Path

import numpy as np
import pandas as pd

PARQUET = Path("نتيجة ثانوية عامة نظام حديث.parquet")
GZ = Path("docs/data.gz")


def read_varints(buf, pos, n):
    out = np.empty(n, dtype=np.int64)
    for i in range(n):
        v = 0
        s = 0
        while True:
            b = buf[pos]
            pos += 1
            v |= (b & 0x7F) << s
            if not (b & 0x80):
                break
            s += 7
        out[i] = v
    return out, pos


def parse():
    raw = gzip.decompress(GZ.read_bytes())
    assert raw[:4] == b"TW26", "bad magic"
    n, names_len = struct.unpack("<II", raw[4:12])
    pos = 12
    deltas, pos = read_varints(raw, pos, n)
    offsets = np.zeros(n + 1, dtype=np.int64)
    offsets[1:] = np.cumsum(deltas)
    ids, pos = read_varints(raw, pos, n)
    degrees = np.frombuffer(raw, dtype=np.uint8, count=n, offset=pos)
    pos += n
    cases = np.frombuffer(raw, dtype=np.uint8, count=n, offset=pos)
    pos += n
    names = raw[pos:pos + names_len].decode("utf-8")
    return n, offsets, ids, degrees, cases, names


def js_search(tokens, offsets, names):
    out = []
    for i in range(len(offsets) - 1):
        start, end = offsets[i], offsets[i + 1]
        ok = True
        for p in tokens:
            pos = names.find(p, start)
            if pos == -1 or pos + len(p) > end:
                ok = False
                break
        if ok:
            out.append(i)
        if len(out) >= 50:
            break
    return out


def main():
    n, offsets, ids, degrees, cases, names = parse()
    print(f"parsed rows: {n:,}")

    df = pd.read_parquet(PARQUET, columns=["arabic_name", "seating_no"]).fillna("")
    df["student_case_desc_strip"] = ""
    df = df.drop(columns="student_case_desc_strip")
    df = df.sort_values("arabic_name", kind="mergesort").reset_index(drop=True)

    queries = ["محمد أحمد", "عبد الرحمن", "أحمد", "مصطفى محمد"]
    for q in queries:
        tokens = [p.replace(" ", "") for p in q.split() if p.strip()]
        js_rows = js_search(tokens, offsets, names)
        js_names = [names[int(offsets[i]):int(offsets[i + 1])] for i in js_rows]
        mask = pd.Series(True, index=df.index)
        for p in tokens:
            mask &= df["arabic_name"].str.replace(" ", "", regex=False).str.contains(p, case=False, na=False)
        pd_names = df[mask]["arabic_name"].head(50).tolist()
        match = js_names == pd_names
        print(f"query {q!r}: JS top-50 == pandas top-50: {match}")

    sid = int(ids[12345])
    match = None
    for i in range(n):
        if ids[i] == sid:
            match = names[int(offsets[i]):int(offsets[i + 1])]
            break
    row = df[df["seating_no"] == sid]
    print(f"id search {sid}: found {match!r}, pandas row: {row['arabic_name'].tolist()}")
    assert match == row["arabic_name"].tolist()[0]

    print("format + algorithm verified OK")


if __name__ == "__main__":
    main()
