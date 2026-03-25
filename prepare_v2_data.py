"""
Convert sample_old_model_new_treatment.xlsx → comparison_data.csv
Uses v2 columns as defaults, computes change flags for region/function/industry/salary.
"""
import pandas as pd
import numpy as np
import os

EXCEL_PATH = os.path.expanduser(
    "~/Desktop/TwentySix Claude/claude portal march/sample_old_model_new_treatment.xlsx"
)
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "comparison_data.csv")


def clean(val):
    """Normalise a value: strip whitespace, convert None/NaN/'None' to empty string."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("none", "nan", "null", ""):
        return ""
    return s


def values_differ(a, b):
    """Return True if two cleaned values are meaningfully different."""
    ca, cb = clean(a), clean(b)
    if ca == "" and cb == "":
        return False
    return ca != cb


def salary_changed(v2, orig):
    """Compare salary values numerically (tolerance for float rounding)."""
    try:
        a = float(v2) if v2 is not None and not (isinstance(v2, float) and np.isnan(v2)) else None
        b = float(orig) if orig is not None and not (isinstance(orig, float) and np.isnan(orig)) else None
    except (ValueError, TypeError):
        return False
    if a is None and b is None:
        return False
    if a is None or b is None:
        return True
    return abs(a - b) > 0.01


def main():
    print(f"Reading {EXCEL_PATH} ...")
    df = pd.read_excel(EXCEL_PATH)
    print(f"  → {len(df)} rows, {len(df.columns)} columns")

    out = pd.DataFrame()

    # Core columns
    out["Id"] = df["id"]
    out["Date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    out["Job Title"] = df["job_title"].apply(clean)
    out["Company"] = df["company"].apply(clean)
    out["Location"] = df["location"].apply(clean)

    # Region (v2 default)
    out["Region"] = df["region_v2"].apply(clean)
    out["Region (Original)"] = df["region"].apply(clean)
    out["Region Changed"] = df.apply(lambda r: values_differ(r["region_v2"], r["region"]), axis=1)

    # Function (v2 default)
    out["Function"] = df["function_chatgpt_v2"].apply(clean)
    out["Function (Original)"] = df["function"].apply(clean)
    out["Function Changed"] = df.apply(lambda r: values_differ(r["function_chatgpt_v2"], r["function"]), axis=1)

    # Job Level (same in both models)
    out["Job Level"] = df["job_level"].apply(clean)

    # Industry (v2 default)
    out["Industry"] = df["industry_v2"].apply(clean)
    out["Industry (Original)"] = df["industry"].apply(clean)
    out["Industry Changed"] = df.apply(lambda r: values_differ(r["industry_v2"], r["industry"]), axis=1)

    # Salary (v2 default)
    out["Min Salary"] = pd.to_numeric(df["Low_Salary_v2"], errors="coerce")
    out["Max Salary"] = pd.to_numeric(df["High_Salary_v2"], errors="coerce")
    out["Min Salary (Original)"] = pd.to_numeric(df["min_salary"], errors="coerce")
    out["Max Salary (Original)"] = pd.to_numeric(df["max_salary"], errors="coerce")
    out["Salary Changed"] = df.apply(
        lambda r: salary_changed(r["Low_Salary_v2"], r["min_salary"])
        or salary_changed(r["High_Salary_v2"], r["max_salary"]),
        axis=1,
    )

    # Salary Period
    out["Salary Period"] = df["Metric"].apply(clean)

    # Job Description
    out["Job Description"] = df["description"].apply(clean)

    # Probabilities
    out["Function Probability"] = df["Function_probability"]
    out["Industry Probability"] = df["Industry_probability"]
    out["Job Level Probability"] = df["JobLevel_probability"]

    # Any Changed flag
    out["Any Changed"] = out["Region Changed"] | out["Function Changed"] | out["Industry Changed"] | out["Salary Changed"]

    # Print summary
    n = len(out)
    print(f"\nChange summary ({n} records):")
    print(f"  Region changed:   {out['Region Changed'].sum():>5} ({out['Region Changed'].mean()*100:.1f}%)")
    print(f"  Function changed: {out['Function Changed'].sum():>5} ({out['Function Changed'].mean()*100:.1f}%)")
    print(f"  Industry changed: {out['Industry Changed'].sum():>5} ({out['Industry Changed'].mean()*100:.1f}%)")
    print(f"  Salary changed:   {out['Salary Changed'].sum():>5} ({out['Salary Changed'].mean()*100:.1f}%)")
    print(f"  Any changed:      {out['Any Changed'].sum():>5} ({out['Any Changed'].mean()*100:.1f}%)")

    out.to_csv(OUTPUT_PATH, index=False)
    print(f"\nWrote {OUTPUT_PATH} ({len(out)} rows)")


if __name__ == "__main__":
    main()
