#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-screen Title/Abstract with heuristic rules and write suggestions.
Input: data_clean/TitleAbs_Screening.xlsx (preferred) or data_clean/master_refs_raw.csv
Output: data_clean/TitleAbs_Screening_AUTO.xlsx  (incl_titleabs_yesno / exclusion_reason prefilled where high-confidence)
"""
import os, re, hashlib, pandas as pd

DATA_DIR = "data_clean"
SRC_XLSX = os.path.join(DATA_DIR, "TitleAbs_Screening.xlsx")
SRC_RAW  = os.path.join(DATA_DIR, "master_refs_raw.csv")
OUT_XLSX = os.path.join(DATA_DIR, "TitleAbs_Screening_AUTO.xlsx")

def read_any_csv(path):
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return pd.read_csv(path, dtype=str, encoding=enc).fillna("")
        except Exception:
            pass
    return pd.read_csv(path, dtype=str).fillna("")

def norm(s):  # lower + remove non-alnum
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

def first_nonempty(*vals):
    for v in vals:
        if isinstance(v,str) and v.strip():
            return v
    return ""

def build_from_raw(df):
    cols = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
    col_title   = pick("title","ti")
    col_abs     = pick("abstract","ab")
    col_authors = pick("authors","au","author")
    col_year    = pick("year","py","yr")
    col_journal = pick("journal","source","so")
    col_doi     = pick("doi")
    col_url     = pick("url","link")

    work = pd.DataFrame()
    work["title"]   = df[col_title]   if col_title else ""
    work["authors"] = df[col_authors] if col_authors else ""
    work["year"]    = df[col_year]    if col_year else ""
    work["journal"] = df[col_journal] if col_journal else ""
    work["abstract"]= df[col_abs]     if col_abs else ""
    if col_doi: work["doi"] = df[col_doi]
    if col_url: work["url"] = df[col_url]

    # study_id
    sid = []
    for _, r in work.iterrows():
        t = first_nonempty(r.get("title",""))
        y = first_nonempty(r.get("year",""))
        sid.append(hashlib.md5((t+"|"+y).encode("utf-8","ignore")).hexdigest()[:12])
    work.insert(0,"study_id",sid)
    work.insert(1,"incl_titleabs_yesno","")
    work.insert(2,"exclusion_reason","")
    return work

def load_screening():
    if os.path.exists(SRC_XLSX):
        return pd.read_excel(SRC_XLSX, sheet_name="Screening").fillna("")
    elif os.path.exists(SRC_RAW):
        return build_from_raw(read_any_csv(SRC_RAW))
    else:
        raise SystemExit("Missing input: TitleAbs_Screening.xlsx or master_refs_raw.csv")

# ----- rules -----
KW_NOT_MS = {"university","college","higher education","undergraduate",
             "senior high","upper secondary","high school",
             "primary","elementary","kindergarten","preschool",
             "vocational","tvet"}
KW_MS_POS = {"middle school","junior high","lower secondary","初中","初级中学"}

CHINA_POS = {"china","chinese","prc","mainland","beijing","shanghai","guangdong","zhejiang",
             "jiangsu","shandong","sichuan","hubei","hunan","henan","shenzhen","tianjin","chongqing",
             "hong kong","macau","guangxi","heilongjiang","liaoning","shanxi","shaanxi"}
NON_CHINA = {"united states","usa","uk","england","australia","canada","singapore","malaysia",
             "japan","korea","vietnam","thailand","india","pakistan","iran","turkey","brazil","mexico",
             "nigeria","ethiopia","spain","france","germany","italy"}

KW_NOT_QUANT = {"qualitative","interview","focus group","ethnograph","phenomenolog","narrative",
                "grounded theory","discourse analysis","thematic analysis","case study"}
KW_THEORY = {"conceptual","theoretical","framework","model proposal","literature review","scoping review",
             "bibliometric","meta-analysis","protocol","editorial","commentary","viewpoint"}
KW_ACH = {"achievement","test score","exam","gpa","performance","grades","academic"}
KW_TL  = {"transformational leadership","transformational","mlq","tlq","tfl"}

def any_in(text, vocab): return any(k in text for k in vocab)
def none_in(text, vocab): return not any_in(text, vocab)

# ----- main -----
df = load_screening()
text = (df.get("title","") + " " + df.get("abstract","")).fillna("").map(norm)

# duplicate by DOI or normalized title
if "doi" in df.columns:
    dup_mask = df["doi"].str.lower().duplicated(keep="first") & df["doi"].ne("")
else:
    dup_mask = df["title"].fillna("").map(norm).duplicated(keep="first")

auto_reason = []
auto_yesno  = []
for i, t in enumerate(text):
    reason = ""
    # duplicates
    if dup_mask.iloc[i]:
        reason = "DUPLICATE_DATASET"
    # not middle-school (if negative terms exist and no positive ms terms)
    elif any_in(t, KW_NOT_MS) and none_in(t, KW_MS_POS):
        reason = "NOT_MIDDLE_SCHOOL"
    # NOT_CHINA (mentions other countries and no China tokens)
    elif any_in(t, NON_CHINA) and none_in(t, CHINA_POS):
        reason = "NOT_CHINA"
    # purely non-quant
    elif any_in(t, KW_NOT_QUANT) and none_in(t, {"regression","anova","correlation","structural equation","sem","survey","quantitat"}):
        reason = "NOT_QUANT"
    # theory/review etc.
    elif any_in(t, KW_THEORY):
        reason = "THEORY_ONLY"

    if reason:
        auto_reason.append(reason); auto_yesno.append("no"); continue

    # high-confidence include
    if any_in(t, KW_TL) and any_in(t, KW_ACH) and any_in(t, CHINA_POS|KW_MS_POS):
        auto_reason.append(""); auto_yesno.append("yes")
    else:
        auto_reason.append(""); auto_yesno.append("")  # leave for human review

# write suggestions
out = df.copy()
if "incl_titleabs_yesno" not in out.columns: out.insert(1,"incl_titleabs_yesno","")
if "exclusion_reason" not in out.columns: out.insert(2,"exclusion_reason","")
# 仅在空白处填入建议，不覆盖人工决定
out["incl_titleabs_yesno"] = out["incl_titleabs_yesno"].mask(out["incl_titleabs_yesno"].eq(""), auto_yesno)
out["exclusion_reason"]    = out["exclusion_reason"].mask(out["exclusion_reason"].eq(""), auto_reason)
# 打标签辅助
out["auto_flag"] = ["AUTO" if y or r else "" for y,r in zip(auto_yesno,auto_reason)]

# 输出
with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
    out.to_excel(w, index=False, sheet_name="Screening")
    pd.DataFrame({"YesNo":["yes","no"]}).to_excel(w, index=False, sheet_name="YesNo")
    pd.DataFrame({"Allowed_Values":["NOT_MIDDLE_SCHOOL","NOT_CHINA","NOT_QUANT","NO_EFFECT_SIZE",
                                     "DUPLICATE_DATASET","THEORY_ONLY","OTHER"]}).to_excel(w, index=False, sheet_name="Dictionary")

# 简报
print("Autoscreen done.")
print("Suggested NO:", sum([x=='no' for x in auto_yesno]))
print("Suggested YES:", sum([x=='yes' for x in auto_yesno]))
print("Total blank (needs human):", sum([x=='' for x in auto_yesno]))
