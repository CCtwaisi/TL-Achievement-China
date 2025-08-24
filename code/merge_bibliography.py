# merge_bib.py
# Merge RIS (Scopus/ERIC/WoS/CNKI…) + CSV (Google Scholar) into one table
# Output: data_clean/combined_raw.csv

import os, re, csv, sys
from pathlib import Path
import pandas as pd

# optional: rispy for robust RIS parsing (workflow will install it)
try:
    import rispy  # type: ignore
except Exception:
    rispy = None

BASE = Path(__file__).resolve().parents[1]
RIS_DIR = BASE / "data_raw" / "ris"
CSV_DIR = BASE / "data_raw" / "csv"
OUT_DIR = BASE / "data_clean"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STD_COLS = ["source_file", "src_type", "title", "authors", "year", "journal", "doi", "url", "abstract"]

def _norm_str(x):
    if pd.isna(x): return ""
    return str(x).strip()

def _clean_doi(x):
    x = _norm_str(x)
    if not x: return ""
    x = x.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()
    x = x.replace("DOI:", "").replace("doi:", "").strip()
    return x.lower()

def _authors_to_str(auth_list):
    if not auth_list: return ""
    if isinstance(auth_list, str): return auth_list
    return "; ".join([str(a) for a in auth_list])

def parse_ris_fallback(text: str):
    # very small fallback parser (handles common RIS tags)
    recs, cur = [], {}
    for line in text.splitlines():
        if not line.strip():  # allow blank lines within a record
            continue
        if re.match(r"^[A-Z0-9]{2}\s+-\s+", line):
            tag, val = line.split(" - ", 1)
            tag, val = tag.strip(), val.strip()
            if tag == "TY":
                cur = {}
            elif tag == "ER":
                if cur: recs.append(cur); cur = {}
            elif tag in ("TI", "T1"): cur["title"] = val
            elif tag in ("JO", "JF", "T2"): cur["journal"] = val
            elif tag in ("PY", "Y1"):
                m = re.search(r"\d{4}", val); cur["year"] = int(m.group()) if m else None
            elif tag == "DO": cur["doi"] = val
            elif tag == "UR": cur["url"] = val
            elif tag == "AB": cur["abstract"] = val
            elif tag == "AU":
                cur.setdefault("authors", [])
                cur["authors"].append(val)
    return recs

def load_ris_files():
    rows = []
    if not RIS_DIR.exists(): return pd.DataFrame(columns=STD_COLS)
    for p in sorted(RIS_DIR.glob("*.ris")):
        try:
            if rispy is not None:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    entries = rispy.load(f)
                for e in entries:
                    rows.append({
                        "source_file": p.name, "src_type": "ris",
                        "title": _norm_str(e.get("title")),
                        "authors": _authors_to_str(e.get("authors")),
                        "year": e.get("year") or e.get("date"),
                        "journal": _norm_str(e.get("journal_name") or e.get("secondary_title")),
                        "doi": _clean_doi(e.get("doi")),
                        "url": _norm_str(e.get("url")),
                        "abstract": _norm_str(e.get("abstract")),
                    })
            else:
                text = p.read_text(encoding="utf-8", errors="ignore")
                for e in parse_ris_fallback(text):
                    rows.append({
                        "source_file": p.name, "src_type": "ris",
                        "title": _norm_str(e.get("title")),
                        "authors": _authors_to_str(e.get("authors")),
                        "year": e.get("year"),
                        "journal": _norm_str(e.get("journal")),
                        "doi": _clean_doi(e.get("doi")),
                        "url": _norm_str(e.get("url")),
                        "abstract": _norm_str(e.get("abstract")),
                    })
        except Exception as ex:
            print(f"[WARN] Failed to parse {p.name}: {ex}", file=sys.stderr)
    return pd.DataFrame(rows, columns=STD_COLS)

# map common CSV headers from Google Scholar/others to our standard names
CSV_HEADER_MAP = {
    "title": "title",
    "authors": "authors",
    "author": "authors",
    "year": "year",
    "publication year": "year",
    "journal": "journal",
    "source title": "journal",
    "doi": "doi",
    "url": "url",
    "link": "url",
    "abstract": "abstract",
    "description": "abstract",
}

def load_csv_files():
    frames = []
    if not CSV_DIR.exists(): return pd.DataFrame(columns=STD_COLS)
    for p in sorted(CSV_DIR.glob("*.csv")):
        df = None
        for enc in ("utf-8", "utf-8-sig", "latin-1", "gb18030"):
            try:
                df = pd.read_csv(p, encoding=enc)
                break
            except Exception:
                continue
        if df is None:
            print(f"[WARN] Failed to read {p.name} with common encodings.", file=sys.stderr)
            continue
        # normalize headers
        df_cols = [str(c).strip().lower() for c in df.columns]
        df.columns = df_cols
        out = {k: "" for k in STD_COLS}
        out_rows = []
        for _, row in df.iterrows():
            rec = {k: "" for k in STD_COLS}
            rec["source_file"] = p.name
            rec["src_type"] = "csv"
            for c in df.columns:
                key = CSV_HEADER_MAP.get(c)
                if not key: continue
                val = row[c]
                if key == "year":
                    try:
                        m = re.search(r"\d{4}", str(val))
                        rec["year"] = int(m.group()) if m else ""
                    except Exception:
                        rec["year"] = ""
                elif key == "doi":
                    rec["doi"] = _clean_doi(val)
                else:
                    rec[key] = _norm_str(val)
            out_rows.append(rec)
        frames.append(pd.DataFrame(out_rows, columns=STD_COLS))
    if frames:
        return pd.concat(frames, ignore_index=True)
    return pd.DataFrame(columns=STD_COLS)

def main():
    ris_df = load_ris_files()
    csv_df = load_csv_files()
    combined = pd.concat([ris_df, csv_df], ignore_index=True)
    # final cleaning
    combined["title"] = combined["title"].fillna("").str.strip()
    combined["authors"] = combined["authors"].fillna("").str.strip()
    combined["journal"] = combined["journal"].fillna("").str.strip()
    combined["doi"] = combined["doi"].apply(_clean_doi)
    combined["url"] = combined["url"].fillna("").str.strip()
    combined["abstract"] = combined["abstract"].fillna("").str.strip()
    combined.to_csv(OUT_DIR / "combined_raw.csv", index=False)
    print(f"[OK] Wrote {OUT_DIR / 'combined_raw.csv'} with {len(combined)} rows.")

if __name__ == "__main__":
    main()
