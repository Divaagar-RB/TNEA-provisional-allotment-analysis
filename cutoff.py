from flask import Blueprint, jsonify,render_template
import pandas as pd
import numpy as np

cutoff_bp = Blueprint("cutoff", __name__)

DF_FILE = "data/Recent_Cleaned.csv"

def clean_column(col: str) -> str:
    return (col.replace("\n", "")
               .replace("\r", "")
               .replace("\t", "")
               .replace("  ", " ")
               .strip()
               .upper())
# Branch code to name mapping (extend as per your dataset)
BRANCH_CODE_MAP = {
    "CS": "Computer Science and Engineering",
    "IT": "Information Technology",
    "EC": "Electronics and Communication Engineering",
    "EE": "Electrical and Electronics Engineering",
    "ME": "Mechanical Engineering",
    "CE": "Civil Engineering",
    "IC": "Instrumentation and Control Engineering",
    "CH": "Chemical Engineering",
    "AE": "Aeronautical Engineering",
    "AU": "Automobile Engineering",
    "PH": "Pharmaceutical Technology",
    "BT": "Biotechnology",
    "PE": "Petroleum Engineering",
    "MT": "Mechatronics",
    "SB": "Software Engineering",
    "CZ": "Cyber Security",
    "MM": "Mining Engineering",
    "EV": "Environmental Engineering",
    "PP": "Production Engineering",
    "AP": "Applied Electronics",
    "CF": "Ceramic Technology",
    "LE": "Leather Technology",
    "FY": "Food Technology",
    "TS": "Textile Technology",
    "MZ": "Marine Engineering",
    "TT": "Telecommunication Engineering",
    "TX": "Textiles",
    "CN": "Construction Engineering",
    "EI": "Electronics and Instrumentation",
    "AL": "Artificial Intelligence",
    "MS": "Medical Electronics",
    "CO": "Computer Engineering",
    "SC": "Software and Computing",
    "PN": "Printing Technology",
    "AS": "Aerospace Engineering",
    "GI": "Geo Informatics",
    "PR": "Production Engineering",
    "RP": "Robotics",
    "PT": "Plastic Technology",
    "MU": "Music Technology",
    "MI": "Metallurgy",
    "MA": "Mathematics and Computing",
    "CJ": "Ceramics and Jewellery",
    "SF": "Safety and Fire Engineering",
    "CL": "Clothing and Fashion",
    "EY": "Energy Engineering",
    "PM": "Polymer Engineering",
    "CC": "Computer and Communication",
    "IE": "Industrial Engineering",
    "BS": "Biomedical Engineering",
    "RA": "Radiology",
    "BP": "Biophysics",
    "BY": "Bioinformatics",
    "IB": "Industrial Biotechnology",
    "AD": "Artificial Intelligence & Data Science",
    "IY": "Information Systems",
    "IS": "Instrumentation",
    "MG": "Management",
    "EM": "Embedded Systems",
    "IM": "Industrial Management",
    "CM": "Computer Engineering (Multimedia)",
    "AT": "Automation"
}

def add_branch_names(df):
    df["BranchName"] = df["BRANCHCODE"].map(BRANCH_CODE_MAP).fillna(df["BRANCHCODE"])
    return df

def load_data():
    df = pd.read_csv(DF_FILE)
    df = add_branch_names(df)
    df.columns = [clean_column(c) for c in df.columns]

    # rename for convenience
    df.rename(columns={
        'APPLN NO': 'STUDENTID',
        'COMMUNITY': 'COMMUNITY',
        'COLLEGE CODE': 'COLLEGECODE',
        'BRANCH CODE': 'BRANCHCODE',
        'ALLOTTED CATEGORY': 'ALLOTCATEGORY',
        'ROUND': 'ROUND',
        'YEAR': 'YEAR',
        '2023-2025 CLEANED.NAME OF THE COLLEGES': 'COLLENAME',
        '2023-2025 CLEANED.DISTRICT': 'DISTRICT',
        '2023-2025 CLEANED.TYPE OF COLLEGE': 'COLLEGETYPE'
    }, inplace=True)

    # Ensure numeric + limit to 2023–2025 if present
    if 'AGGRMARK' in df.columns:
        df['AGGRMARK'] = pd.to_numeric(df['AGGRMARK'], errors='coerce')
    df = df.dropna(subset=['AGGRMARK'])
    if 'YEAR' in df.columns:
        df['YEAR'] = pd.to_numeric(df['YEAR'], errors='coerce')
        df = df[df['YEAR'].isin([2023, 2024, 2025])]
    df["DISTRICT"] = df["DISTRICT"].str.strip().str.upper()


    return df

# ---- helpers used by MAIN PAGE (so imports in app.py keep working) ----
def get_round_count(df):
    return df.groupby('ROUND').size().reset_index(name='count')

def get_year_count(df):
    return df.groupby('YEAR').size().reset_index(name='count')

def get_top10_colleges(df):
    # by average AGGRMARK overall (for main page widget)
    college_avg = df.groupby(['COLLEGECODE', 'COLLENAME'])['AGGRMARK'].mean().reset_index()
    return college_avg.sort_values(by='AGGRMARK', ascending=False).head(10)

def get_community_count(df):
    return df.groupby('COMMUNITY').size().reset_index(name='count')

def get_college_type_count(df):
    return df.groupby('COLLEGETYPE').size().reset_index(name='count')

# ---- payload for /cutoff/data ----
def _safe_val(row, year):
    # return None if the year is missing
    return None if year not in row or pd.isna(row[year]) else float(row[year])

def _pct_change(v2023, v2025):
    if v2023 in (None, 0) or v2025 is None:
        return None
    return round(((v2025 - v2023) / v2023) * 100.0, 2)


# cutoff.py (or your backend module)
import numpy as np
import pandas as pd
from flask import jsonify

# assume load_data() and cutoff_bp defined earlier in this module

def build_insights(df: pd.DataFrame):
    insights = {}

    # --- 1) Yearly average trend (safe)
    yearly_avg = (
        df.groupby("YEAR")["AGGRMARK"]
          .mean()
          .reset_index(name="AVG")
          .sort_values("YEAR")
    )
    yearly_avg["YoY_Change"] = yearly_avg["AVG"].diff()
    insights["yearly_avg_trend"] = yearly_avg

    # --- 2) College average per year pivot (one row per college, cols for each year)
    college_year = (
        df.groupby(["COLLENAME", "YEAR"])["AGGRMARK"]
          .mean()
          .reset_index()
    )
    # pivot -> index COLLENAME, columns are years (as integers). Convert columns to strings for JSON safety.
    college_pivot = college_year.pivot(index="COLLENAME", columns="YEAR", values="AGGRMARK")
    # ensure 2023/2024/2025 exist and convert year columns to strings
    for yr in [2023, 2024, 2025]:
        if yr not in college_pivot.columns:
            college_pivot[yr] = np.nan
    # convert numeric-year columns to string names "2023", "2024", "2025" (makes JSON keys predictable)
    college_pivot.columns = college_pivot.columns.map(lambda c: str(c))

    # overall average across available years (skipna)
    college_pivot["AVG_OVERALL"] = college_pivot[["2023", "2024", "2025"]].mean(axis=1, skipna=True)

    # get first & last year available per college (for informational display)
    first_last = college_year.groupby("COLLENAME")["YEAR"].agg(["min", "max"]).rename(columns={"min":"First_Year", "max":"Last_Year"})

    # select top-10 by AVG_OVERALL
    top10 = college_pivot.sort_values("AVG_OVERALL", ascending=False).head(10).copy()
    # join first/last
    top10 = top10.merge(first_last, left_index=True, right_index=True)

    # compute start/end/net/pct/trend
    top10["Start_Cutoff"] = top10["2023"]
    top10["End_Cutoff"] = top10["2025"]
    top10["Net_Increase_Cutoff"] = top10["End_Cutoff"] - top10["Start_Cutoff"]
    top10["Pct_Change"] = np.where(
        top10["Start_Cutoff"].notna() & top10["End_Cutoff"].notna() & (top10["Start_Cutoff"] != 0),
        (top10["Net_Increase_Cutoff"] / top10["Start_Cutoff"]) * 100.0,
        np.nan
    )

    def compute_trend(row):
        # strictly monotonic across all three years -> labeled increasing/decreasing
        if pd.notna(row["2023"]) and pd.notna(row["2024"]) and pd.notna(row["2025"]):
            if (row["2023"] < row["2024"]) and (row["2024"] < row["2025"]):
                return "increasing"
            if (row["2023"] > row["2024"]) and (row["2024"] > row["2025"]):
                return "decreasing"
        # fallback to sign of net increase
        ni = row["Net_Increase_Cutoff"]
        if pd.notna(ni):
            return "up" if ni > 0 else ("down" if ni < 0 else "flat")
        return "flat"

    top10["Trend"] = top10.apply(compute_trend, axis=1)

    # prepare DataFrame to return
    top10_out = top10.reset_index().rename_axis(None)  # COLLENAME becomes column
    insights["top_10_colleges_by_average_overall_cutoff"] = top10_out

    # --- 3) Branch-level averages (across all colleges) and trends (no college names)
    branch_year = (
        df.groupby(["BRANCHCODE", "YEAR"])["AGGRMARK"]
          .mean()
          .reset_index()
    )
    branch_pivot = branch_year.pivot(index="BRANCHCODE", columns="YEAR", values="AGGRMARK")
    for yr in [2023, 2024, 2025]:
        if yr not in branch_pivot.columns:
            branch_pivot[yr] = np.nan
    branch_pivot.columns = branch_pivot.columns.map(lambda c: str(c))

    # metrics
    branch_pivot["Net_Increase"] = branch_pivot["2025"] - branch_pivot["2023"]
    branch_pivot["Pct_Change"] = np.where(
        branch_pivot["2023"].notna() & branch_pivot["2025"].notna() & (branch_pivot["2023"] != 0),
        (branch_pivot["Net_Increase"] / branch_pivot["2023"]) * 100.0,
        np.nan
    )
    # strict monotonic increasing/decreasing flags
    branch_pivot["Increasing"] = (
        branch_pivot["2023"].notna() & branch_pivot["2024"].notna() & branch_pivot["2025"].notna() &
        (branch_pivot["2023"] < branch_pivot["2024"]) & (branch_pivot["2024"] < branch_pivot["2025"])
    )
    branch_pivot["Decreasing"] = (
        branch_pivot["2023"].notna() & branch_pivot["2024"].notna() & branch_pivot["2025"].notna() &
        (branch_pivot["2023"] > branch_pivot["2024"]) & (branch_pivot["2024"] > branch_pivot["2025"])
    )

    # only branch-level results (no college names)
    inc_branches = branch_pivot[branch_pivot["Increasing"]].copy()
    dec_branches = branch_pivot[branch_pivot["Decreasing"]].copy()

    # sort for convenience
    inc_branches = inc_branches.sort_values("Net_Increase", ascending=False).reset_index()
    dec_branches = dec_branches.sort_values("Net_Increase", ascending=True).reset_index()

    insights["increasing_branches"] = inc_branches
    insights["decreasing_branches"] = dec_branches

    # --- 4) Keep the community trend existing output (if you want it)
    community_trends = (
        df.groupby(["YEAR", "COMMUNITY"])["AGGRMARK"]
          .mean()
          .reset_index(name="CUTOFF")
          .sort_values(["YEAR", "COMMUNITY"])
    )
    insights["community_avg_mark_trends"] = community_trends
    print(insights)

    return insights
