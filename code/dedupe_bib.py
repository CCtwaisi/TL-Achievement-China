# dedupe_bib.py
# Deduplicate combined_raw.csv by DOI and (title similarity + year proximity)
# Outputs:
#   data_clean/master_bibliography.csv
#   data_clean/duplicates_report.csv
#   data_clean/excluded_duplicates.csv

import os, re, sys
from pathlib import Path
import pandas as pd

try:
    from rapidfuzz import fuzz
except Exception:
    # minimal fallback (lower accuracy)
    def _simple_ratio(a,b):
        a, b = str(a), str(b)
        from difflib import SequenceMatcher
        return int(100 * SequenceMatcher(None, a, b).ratio())
    class fuzz:
        ratio = staticmethod(_simple_ratio)

BASE = Path(__file__).resolve().parents[1]
OUT_DIR = BASE / "data_clean"
IN_CSV = OUT_DIR / "combined_raw.csv"
OUT_MASTER = OUT_DIR / "master_bibliography.csv"
OUT_DUPREP = OUT_DIR / "duplicates_report.csv"
OUT_EXCL = OUT_DIR / "excluded_duplicates.csv"

TITLE_SIM_THRESHOLD = float(os.getenv("TITLE_SIM_THRESHOLD", "0.92"))  # 0.92 ~ 92%

def norm_title(t):
    if pd.isna(t): return ""
    t = str(t).lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return t

def choose_primary(df_grp):
    # keep the record with DOI; if multiple, the longest abstract; else first
    with_doi = df_grp[df_grp["doi"].astype(str)!=""]
    if len(with_doi) >= 1:
        cand = with_doi.copy()
    else:
        cand = df_grp.copy()
    cand = cand.assign(_ablen=cand["abstract"].astype(str).str.len())
    return cand.sort_values(["_ablen"], ascending=[False]).iloc[0]

def main():
    if not IN_CSV.exists():
        print(f"[WARN] {IN_CSV} not found. Run merge_bib.py first.", file=sys.stderr)
        return
    df = pd.read_csv(IN_CSV)
    if df.empty:
        print("[WARN] combined_raw.csv is empty.")
        df.to_csv(OUT_MASTER, index=False); return

    df["rec_id"] = range(1, len(df)+1)
    df["doi"] = df["doi"].fillna("").astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["norm_title"] = df["title"].apply(norm_title)

    kept = []
    dup_rows = []
    excluded = []

    # 1) Exact DOI duplicates
    by_doi = df[df["doi"]!=""].groupby("doi", dropna=False)
    used_ids = set()
    for doi, grp in by_doi:
        if len(grp) == 1:
            kept.append(grp.iloc[0])
            used_ids.add(int(grp.iloc[0]["rec_id"]))
        else:
            winner = choose_primary(grp)
            kept.append(winner)
            used_ids.add(int(winner["rec_id"]))
            for _, r in grp.iterrows():
                if int(r["rec_id"]) == int(winner["rec_id"]): continue
                dup_rows.append({"dup_id": int(r["rec_id"]), "kept_id": int(winner["rec_id"]), "reason": "duplicate_doi", "score": 100, "doi": doi})
                excluded.append(r)

    # 2) Title-similarity duplicates for items without DOI
    remain = df[df["rec_id"].apply(lambda x: int(x) not in used_ids)].copy()
    # split by has_doi
    remain_no_doi = remain[remain["doi"]==""].copy()
    remain_yes_doi = remain[remain["doi"]!=""].copy()
    # add remaining DOI ones directly (unique)
    for _, r in remain_yes_doi.iterrows():
        kept.append(r); used_ids.add(int(r["rec_id"]))

    # O(n^2) compare for no DOI (ok for hundreds)
    visited = set()
    rows = remain_no_doi.to_dict("records")
    for i in range(len(rows)):
        if rows[i]["rec_id"] in visited: continue
        base = rows[i]
        winner = base
        group = [base]
        visited.add(base["rec_id"])
        for j in range(i+1, len(rows)):
            if rows[j]["rec_id"] in visited: continue
            cand = rows[j]
            if pd.notna(base["year"]) and pd.notna(cand["year"]):
                if abs(int(base["year"]) - int(cand["year"])) > 1:
                    continue
            score = fuzz.ratio(base["norm_title"], cand["norm_title"])
            if score >= int(TITLE_SIM_THRESHOLD*100):
                # mark as duplicate of winner
                visited.add(cand["rec_id"])
                dup_rows.append({"dup_id": int(cand["rec_id"]), "kept_id": int(winner["rec_id"]), "reason": "duplicate_title", "score": int(score), "doi": ""})
                excluded.append(cand)
        kept.append(winner)

    kept_df = pd.DataFrame(kept).drop(columns=["_ablen"], errors="ignore").sort_values("rec_id")
    excl_df = pd.DataFrame(excluded).drop(columns=["_ablen"], errors="ignore")
    dup_df = pd.DataFrame(dup_rows)

    # add user-screening placeholders
    for col in ["incl_titleabs", "exclusion_reason"]:
        if col not in kept_df.columns: kept_df[col] = ""

    kept_df.to_csv(OUT_MASTER, index=False)
    dup_df.to_csv(OUT_DUPREP, index=False)
    excl_df.to_csv(OUT_EXCL, index=False)

    print(f"[OK] Wrote {OUT_MASTER} ({len(kept_df)} kept).")
    print(f"[OK] Wrote {OUT_DUPREP} ({len(dup_df)} duplicates).")
    print(f"[OK] Wrote {OUT_EXCL} ({len(excl_df)} excluded).")

if __name__ == "__main__":
    main()
