import pandas as pd

df = pd.read_parquet(r"C:\Users\DELL\Desktop\test\نتيجة ثانوية عامة نظام حديث.parquet").fillna("")

# Test 1: ID
r = df[df["seating_no"] == 2232886]
assert len(r) == 1
print("ID 2232886: OK -", r.iloc[0]["arabic_name"])

# Test 2: ID not found
r = df[df["seating_no"] == 9999999]
assert len(r) == 0
print("ID 9999999: OK - empty")

# Test 3: Name (all parts)
parts = "عبدالرحمن محمد نبيل السيد".split()
mask = pd.Series(True, index=df.index)
for p in parts:
    mask &= df["arabic_name"].str.replace(" ", "", regex=False).str.contains(p.replace(" ", ""), case=False, na=False)
r = df[mask]
print(f"Name all parts: {len(r)} results")
for _, row in r.iterrows():
    print(f"  {row['seating_no']} | {row['arabic_name']} | {row['total_degree']}")

# Test 4: Name with space (عبد الرحمن)
parts = "عبد الرحمن محمد نبيل السيد".split()
mask = pd.Series(True, index=df.index)
for p in parts:
    mask &= df["arabic_name"].str.replace(" ", "", regex=False).str.contains(p.replace(" ", ""), case=False, na=False)
r = df[mask]
print(f"Name with space: {len(r)} results")
for _, row in r.iterrows():
    print(f"  {row['seating_no']} | {row['arabic_name']} | {row['total_degree']}")

# Test 5: Common name
r = df[df["arabic_name"].str.replace(" ", "", regex=False).str.contains("أحمد", case=False, na=False)]
print(f"Search أحمد: {len(r)} results - OK")

print("\nAll tests passed!")
