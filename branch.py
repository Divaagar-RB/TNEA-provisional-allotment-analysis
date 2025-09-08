from flask import Blueprint, jsonify
import pandas as pd
import numpy as np

branch_bp = Blueprint("branch", __name__)

@branch_bp.route("/branch_data")
def branch_popularity():
    from cutoff import load_data
    df = load_data()

    # Pivot data: branches vs year
    branch_counts = df.groupby(['BRANCHCODE','YEAR'])['STUDENTID'].count().unstack(fill_value=0)

    branch_counts['new_branch'] = (branch_counts[2023] == 0) & (branch_counts[2025] > 0)
    new_branches = branch_counts[branch_counts['new_branch']].index.astype(str).tolist()



    # Ensure year columns are strings
    branch_counts.columns = branch_counts.columns.astype(str)

    # Filter out small branches (total < 100 across all years)
    branch_counts = branch_counts[branch_counts.sum(axis=1) >= 180]

    # --- Growth calculations ---
    # Absolute growth
    branch_counts['growth_23_24'] = branch_counts.get('2024',0) - branch_counts.get('2023',0)
    branch_counts['growth_24_25'] = branch_counts.get('2025',0) - branch_counts.get('2024',0)
    branch_counts['growth_23_25'] = branch_counts.get('2025',0) - branch_counts.get('2023',0)

    # Percent growth
    branch_counts['growth_percent_23_24'] = np.nan
    branch_counts['growth_percent_24_25'] = np.nan
    branch_counts['growth_percent_23_25'] = np.nan

    # Avoid divide by zero
    mask_23 = branch_counts.get('2023',0) > 0
    mask_24 = branch_counts.get('2024',0) > 0

    branch_counts.loc[mask_23, 'growth_percent_23_24'] = (
        branch_counts.loc[mask_23,'growth_23_24'] / branch_counts.loc[mask_23,'2023'] * 100
    ).round(1)

    branch_counts.loc[mask_24, 'growth_percent_24_25'] = (
        branch_counts.loc[mask_24,'growth_24_25'] / branch_counts.loc[mask_24,'2024'] * 100
    ).round(1)

    branch_counts.loc[mask_23, 'growth_percent_23_25'] = (
        branch_counts.loc[mask_23,'growth_23_25'] / branch_counts.loc[mask_23,'2023'] * 100
    ).round(1)

    # Mark new branches (no students in 2023 but students in 2025)

    # Categorize branches
    
    increasing_branches = branch_counts[branch_counts['growth_23_25'] > 0].index.astype(str).tolist()
    decreasing_branches = branch_counts[branch_counts['growth_23_25'] < 0].index.astype(str).tolist()

    # Top growing & declining based on 2023→2025 percent
    top_growing = (branch_counts.dropna(subset=['growth_percent_23_25'])
                   .sort_values('growth_percent_23_25', ascending=False)
                   .head(8).index.astype(str).tolist())

    top_declining = (branch_counts.dropna(subset=['growth_percent_23_25'])
                     .sort_values('growth_percent_23_25')
                     .head(8).index.astype(str).tolist())

    # Convert to dict for JSON
    records = branch_counts.reset_index().to_dict(orient='records')

    safe_df = branch_counts.replace([np.nan, np.inf, -np.inf], None)

    result = {
        "branches": safe_df.reset_index().to_dict(orient='records'),
        "new_branches": new_branches,
        "increasing_branches": increasing_branches,
        "decreasing_branches": decreasing_branches,
        "top_growing": top_growing,
        "top_declining": top_declining
    }

    return jsonify(result)
