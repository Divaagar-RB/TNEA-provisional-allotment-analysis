import pandas as pd
import numpy as np
from flask import Blueprint, jsonify
from cutoff import load_data  # your existing loader
import traceback

regional_bp = Blueprint("regional", __name__)

# Hardcoded mapping: district → zone
DISTRICT_ZONE = {
    "CHENNAI": "NORTH", "THIRUVALLUR": "NORTH", "KANCHEEPURAM": "NORTH",
    "VELLORE": "NORTH", "TIRUPATHUR": "NORTH", "RANIPET": "NORTH",
    "THIRUPPATTUR": "NORTH", # Corrected as per example data "TIRUPATHUR"
    "CHENGALPATTU": "NORTH", # Assuming Chengalpattu is North

    "MADURAI": "SOUTH", "THENI": "SOUTH", "THOOTHUKUDI": "SOUTH",
    "TIRUNELVELI": "SOUTH", "RAMANATHAPURAM": "SOUTH", "VIRUDHUNAGAR": "SOUTH",
    "KANYAKUMARI": "SOUTH", "SIVAGANGAI": "SOUTH", "DINDIGUL": "SOUTH", "TENKASI": "SOUTH",

    "TRICHY": "CENTRAL", "KARUR": "CENTRAL", "PUDUKKOTTAI": "CENTRAL",
    "PERAMBALUR": "CENTRAL", "ARIYALUR": "CENTRAL",
    "THANJAVUR": "CENTRAL", "THIRUVARUR": "CENTRAL", "NAGAPATTINAM": "CENTRAL",
    "NAGAPPATTINAM": "CENTRAL", # Handling both spellings
    "TIRUCHIRAPPALLI": "CENTRAL", # Handling Tiruchirappalli (Trichy)

    "COIMBATORE": "WEST", "ERODE": "WEST", "NILGIRIS": "WEST",
    "TIRUPPUR": "WEST", "TIRUPUR": "WEST", # Handling both spellings
    "THE NILGIRIS": "WEST", # Handling "THE NILGIRIS"

    "SALEM": "EAST", "NAMAKKAL": "EAST", "DHARMAPURI": "EAST",
    "KRISHNAGIRI": "EAST", "CUDDALORE": "EAST", "VILLUPURAM": "EAST",
    "MAYILADUTHURAI": "EAST", "TIRUVANNAMALAI": "EAST", "KALLAKKURICHI": "EAST",
}

# Optional mapping: urban vs rural classification
URBAN_RURAL = {
    "CHENNAI": "URBAN", "COIMBATORE": "URBAN", "MADURAI": "URBAN",
    "TRICHY": "URBAN", "SALEM": "URBAN", "TIRUCHIRAPPALLI": "URBAN", # Ensure consistency
    "ERODE": "URBAN", "TIRUPPUR": "URBAN", "VELLORE": "URBAN",
    "KANCHEEPURAM": "URBAN", "THIRUVALLUR": "URBAN", "CHENGALPATTU": "URBAN",
    "THOOTHUKUDI": "URBAN", "TIRUNELVELI": "URBAN", "NAGAPATTINAM": "URBAN",
    "MAYILADUTHURAI": "URBAN", "DINDIGUL": "URBAN", "KARUR": "URBAN",
    # All other districts will implicitly be considered RURAL if not listed here.
}
@regional_bp.route("/cutoff/regional-data")
def regional_data():
    try:
        df = load_data()

        if "DISTRICT" not in df.columns or "YEAR" not in df.columns or "AGGRMARK" not in df.columns:
            return jsonify({"error": "Essential columns (DISTRICT, YEAR, AGGRMARK) missing"}), 400

        all_years = [2023, 2024, 2025]

        # --- District-level analysis ---
        district_avg = (
            df.groupby(["DISTRICT", "YEAR"])["AGGRMARK"]
              .mean()
              .reset_index(name="avg_cutoff")
              .pivot(index="DISTRICT", columns="YEAR", values="avg_cutoff")
              .reset_index()
        )
        for year in all_years:
            if year not in district_avg.columns:
                district_avg[year] = np.nan
        district_avg = district_avg[['DISTRICT'] + all_years]
        district_avg = district_avg.rename(columns=lambda x: f"avg_{x}" if isinstance(x, int) else x)

        # --- Change & percentage change metrics ---
        district_avg["avg_change_23_24"] = district_avg["avg_2024"] - district_avg["avg_2023"]
        district_avg["avg_change_24_25"] = district_avg["avg_2025"] - district_avg["avg_2024"]
        district_avg["avg_change_23_25"] = district_avg["avg_2025"] - district_avg["avg_2023"]

        for col_name, start_year, end_year in [
            ("pct_change_23_24", "avg_2023", "avg_2024"),
            ("pct_change_24_25", "avg_2024", "avg_2025"),
            ("pct_change_23_25", "avg_2023", "avg_2025")
        ]:
            district_avg[col_name] = np.where(
                district_avg[start_year] != 0,
                ((district_avg[end_year] - district_avg[start_year]) / district_avg[start_year]) * 100,
                0
            )
            district_avg.loc[(district_avg[start_year] == 0) & (district_avg[end_year] != 0), col_name] = 1000.0

        # --- Volatility & Trend ---
        district_avg["volatility"] = district_avg[[f"avg_{y}" for y in all_years]].std(axis=1)
        def trend(row):
            if row["avg_2023"] < row["avg_2024"] < row["avg_2025"]:
                return "increasing"
            elif row["avg_2023"] > row["avg_2024"] > row["avg_2025"]:
                return "decreasing"
            else:
                return "stable"
        district_avg["trend"] = district_avg.apply(trend, axis=1)

        # Add Zone and Urban/Rural info
        district_avg["ZONE"] = district_avg["DISTRICT"].map(DISTRICT_ZONE).fillna("UNKNOWN")
        district_avg["AREA_TYPE"] = district_avg["DISTRICT"].map(URBAN_RURAL).fillna("RURAL")

        # --- Zone-level analysis ---
        df["ZONE"] = df["DISTRICT"].map(DISTRICT_ZONE).fillna("UNKNOWN")
        zone_avg = (
            df.groupby(["ZONE", "YEAR"])["AGGRMARK"]
              .mean()
              .reset_index(name="avg_cutoff")
              .pivot(index="ZONE", columns="YEAR", values="avg_cutoff")
              .reset_index()
        )
        for year in all_years:
            if year not in zone_avg.columns:
                zone_avg[year] = np.nan
        zone_avg = zone_avg[['ZONE'] + all_years]
        zone_avg = zone_avg.rename(columns=lambda x: f"avg_{x}" if isinstance(x, int) else x)
        zone_avg["avg_change_23_25"] = zone_avg["avg_2025"] - zone_avg["avg_2023"]
        zone_avg["volatility"] = zone_avg[[f"avg_{y}" for y in all_years]].std(axis=1)
        def zone_trend(row):
            if row["avg_2023"] < row["avg_2024"] < row["avg_2025"]:
                return "increasing"
            elif row["avg_2023"] > row["avg_2024"] > row["avg_2025"]:
                return "decreasing"
            else:
                return "stable"
        zone_avg["trend"] = zone_avg.apply(zone_trend, axis=1)

        # --- Area Type analysis ---
        df["AREA_TYPE"] = df["DISTRICT"].map(URBAN_RURAL).fillna("RURAL")
        area_type_avg = (
            df.groupby(["AREA_TYPE", "YEAR"])["AGGRMARK"]
              .mean()
              .reset_index(name="avg_cutoff")
              .pivot(index="AREA_TYPE", columns="YEAR", values="avg_cutoff")
              .reset_index()
        )
        for year in all_years:
            if year not in area_type_avg.columns:
                area_type_avg[year] = np.nan
        area_type_avg = area_type_avg[['AREA_TYPE'] + all_years]
        area_type_avg = area_type_avg.rename(columns=lambda x: f"avg_{x}" if isinstance(x, int) else x)
        area_type_avg["avg_change_23_25"] = area_type_avg["avg_2025"] - area_type_avg["avg_2023"]
        area_type_avg["volatility"] = area_type_avg[[f"avg_{y}" for y in all_years]].std(axis=1)
        def area_trend(row):
            if row["avg_2023"] < row["avg_2024"] < row["avg_2025"]:
                return "increasing"
            elif row["avg_2023"] > row["avg_2024"] > row["avg_2025"]:
                return "decreasing"
            else:
                return "stable"
        area_type_avg["trend"] = area_type_avg.apply(area_trend, axis=1)

        # --- Top districts by allotment ---
        district_counts = (
            df.groupby("DISTRICT")
              .size()
              .reset_index(name="allotment_count")
              .sort_values("allotment_count", ascending=False)
              .head(10)
        )

        # Fill NaN with 0 for consistency
        district_avg = district_avg.fillna(0)
        zone_avg = zone_avg.fillna(0)
        area_type_avg = area_type_avg.fillna(0)

        # --- Return everything with NEW trend & volatility fields ---
        return jsonify({
            "district_data": district_avg.to_dict(orient="records"),
            "zone_data": zone_avg.to_dict(orient="records"),
            "area_type_data": area_type_avg.to_dict(orient="records"),
            "top_district_counts": district_counts.to_dict(orient="records")
        })

    except Exception as e:
        print("ERROR in /cutoff/regional-data:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
