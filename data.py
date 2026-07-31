import numpy as np
import pandas as pd
from functools import lru_cache
from pathlib import Path

PARQUET = Path(__file__).parent / "نتيجة ثانوية عامة نظام حديث.parquet"
df = pd.read_parquet(PARQUET).fillna("")
df["student_case_desc"] = df["student_case_desc"].str.strip()


@lru_cache(maxsize=1)
def dashboard_data():
    scores = df["total_degree"].to_numpy()
    n = len(scores)

    case_counts = df["student_case_desc"].value_counts()
    pass1 = int(case_counts.get("ناجح دور أول", 0))
    second = int(case_counts.get("دور ثان", 0))
    failed = int(case_counts.get("راسب دور أول", 0))
    absent = int(case_counts.get("غياب كلى دور أول", 0))

    return dict(
        scores=scores,
        n=n,
        pass1=pass1,
        second=second,
        failed=failed,
        absent=absent,
        pass1_rate=pass1 / n * 100,
        pass_all_rate=(pass1 + second) / n * 100,
        avg=float(np.mean(scores)),
        median=float(np.median(scores)),
        max_score=float(scores.max()),
    )
