from flask import Flask, render_template, jsonify
import pandas as pd
from cutoff import (
    cutoff_bp,               # the blueprint for the new cutoff page + API
    load_data,
    get_round_count,
    get_year_count,
    get_top10_colleges,
    get_community_count,
    get_college_type_count,
)

app = Flask(__name__)
app.register_blueprint(cutoff_bp, url_prefix="/cutoff")  # mounts /cutoff and /cutoff/data
from regional import regional_bp   # import blueprint

app.register_blueprint(regional_bp) 
from branch import branch_bp  # register it
app.register_blueprint(branch_bp)

# ---- Load and process data for MAIN PAGE ----
df = load_data()
round_count = get_round_count(df)
year_count = get_year_count(df)
top10_colleges = get_top10_colleges(df)
community_count = get_community_count(df)
college_type_count = get_college_type_count(df)

# ----- MAIN PAGE API (unchanged) -----
@app.route("/data")
def chart_data():
    return jsonify({
        "rounds": {
            "labels": round_count['ROUND'].tolist(),
            "data": round_count['count'].tolist()
        },
        "years": {
            "labels": year_count['YEAR'].tolist(),
            "data": year_count['count'].tolist()
        },
        "top10_colleges": {
            "labels": top10_colleges['COLLENAME'].tolist(),
            "data": top10_colleges['AGGRMARK'].tolist()
        },
        "community": {
            "labels": community_count['COMMUNITY'].tolist(),
            "data": community_count['count'].tolist()
        },
        "college_type": {
            "labels": college_type_count['COLLEGETYPE'].tolist(),
            "data": college_type_count['count'].tolist()
        }
    })

# ----- MAIN PAGE (unchanged) -----
@app.route("/")
def index():
    return render_template("index.html")

# ----- NEW PAGE: Cutoff Shifts Over Years -----
@app.route("/cutoff")
def cutoff_page():
    from cutoff import cutoff_insights   # import your function
    insights = cutoff_insights()         # get data
    return render_template("cutoff_shifts.html", insights=insights)
import numpy as np
from flask import jsonify



# Example endpoint (ensure you import np and jsonify)
@app.route("/cutoff-dashboard-data")
def cutoff_dashboard_data():
    # load and build insights
    from cutoff import build_insights
    df = load_data()
    insights = build_insights(df)

    # convert all DataFrames in insights to JSON-serializable lists (NaN -> None)
    safe_response = {}
    for k, v in insights.items():
        if isinstance(v, pd.DataFrame):
            safe_df = v.replace({np.nan: None})
            safe_response[k] = safe_df.to_dict(orient="records")
        else:
            # if some value isn't a DataFrame, attempt direct conversion
            safe_response[k] = v

    return jsonify(safe_response)


from flask import render_template
@app.route('/cutoff/regional')
def cutoff_regional_page():
    return render_template('cutoff_regional.html')


@app.route("/cutoff-dashboard")
def cutoff_dashboard():
    return render_template("cutoff_dashboard.html")

@app.route("/branch/dashhboard")
def branch_dashboard():
    return render_template("breanch.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

