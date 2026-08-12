import base64
import json
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HTML = ROOT.parent / "Big Data Analytics.html"
CHARTS_DIR = ROOT / "assets" / "charts"
SITE_DATA_PATH = ROOT / "site-data.js"


CHART_METADATA = {
    99: {
        "title": "Flight Volume Trend",
        "section": "Visualizations",
        "description": "Yearly change in the number of flights processed in the analysis dataset.",
    },
    101: {
        "title": "Delay Comparison Over Years",
        "section": "Visualizations",
        "description": "Arrival and departure delay trends for the 2016-2018 flight data window.",
    },
    103: {
        "title": "Top Airports by Flight Volume",
        "section": "Visualizations",
        "description": "Horizontal comparison of the busiest origin airports in the dataset.",
    },
    105: {
        "title": "Delay Category Distribution",
        "section": "Visualizations",
        "description": "Share of flights grouped into low, moderate, and severe delay categories.",
    },
    107: {
        "title": "Flight Status Distribution",
        "section": "Visualizations",
        "description": "Operated versus cancelled flight share across the combined dataset.",
    },
    109: {
        "title": "Monthly Delay Trend",
        "section": "Visualizations",
        "description": "Average arrival delay by month to surface seasonal patterns.",
    },
    111: {
        "title": "Delay vs Departure Hour",
        "section": "Visualizations",
        "description": "Average arrival delay by scheduled departure hour.",
    },
    113: {
        "title": "Average Arrival Delay by Distance Range",
        "section": "Visualizations",
        "description": "How average arrival delay shifts across route distance buckets.",
    },
    115: {
        "title": "Delay Distribution Density Plot",
        "section": "Visualizations",
        "description": "Smoothed density view of arrival delay values after trimming extreme outliers.",
    },
    117: {
        "title": "Correlation Heatmap",
        "section": "Visualizations",
        "description": "Correlation matrix for core operational numeric variables used in the analysis.",
    },
    119: {
        "title": "Taxi Time Trend",
        "section": "Visualizations",
        "description": "Yearly taxi-in and taxi-out averages to reflect ground congestion patterns.",
    },
    121: {
        "title": "Top 10 Busiest Airports",
        "section": "Visualizations",
        "description": "Annotated version of the busiest airport comparison chart for presentation use.",
    },
}


TABLE_METADATA = {
    15: {"title": "Raw Dataset Preview", "section": "Notebook Outputs"},
    20: {"title": "Selected Raw Columns Preview", "section": "Notebook Outputs"},
    22: {"title": "Missing Value Percentages", "section": "Notebook Outputs"},
    24: {"title": "Standardized Flight Data Preview", "section": "Notebook Outputs"},
    28: {"title": "Cleaned Flight Data Preview", "section": "Notebook Outputs"},
    36: {"title": "Analysis Dataset Preview", "section": "Notebook Outputs"},
    38: {"title": "Overall Summary", "section": "Executive Summary"},
    40: {"title": "Flights by Year", "section": "Executive Summary"},
    42: {"title": "Delayed Flights Sample", "section": "Operational Filters"},
    44: {"title": "Cancelled Flights Sample", "section": "Operational Filters"},
    46: {"title": "Long Distance Flights Sample", "section": "Operational Filters"},
    48: {"title": "Busiest Origin Airports", "section": "Airport Analysis"},
    50: {"title": "Busiest Destination Airports", "section": "Airport Analysis"},
    52: {"title": "Origin Airport Delay Analysis", "section": "Airport Analysis"},
    54: {"title": "Destination Airport Delay Analysis", "section": "Airport Analysis"},
    56: {"title": "Busiest Departure Hours", "section": "Time Analysis"},
    58: {"title": "Hourly Delay Analysis", "section": "Time Analysis"},
    60: {"title": "Route Analysis", "section": "Route Analysis"},
    62: {"title": "Worst Routes by Arrival Delay", "section": "Route Analysis"},
    64: {"title": "Monthly Analysis", "section": "Time Analysis"},
    66: {"title": "Overall Monthly Pattern", "section": "Time Analysis"},
    68: {"title": "Day of Week Analysis", "section": "Time Analysis"},
    70: {"title": "Delay Category Distribution", "section": "Operational Outcomes"},
    72: {"title": "Flight Status Distribution", "section": "Operational Outcomes"},
    74: {"title": "Distance Delay Analysis", "section": "Distance and Taxi"},
    76: {"title": "Taxi Time Analysis", "section": "Distance and Taxi"},
    78: {"title": "Elapsed Time Analysis", "section": "Distance and Taxi"},
    80: {"title": "Origin Airport Year Analysis", "section": "Airport Rankings"},
    82: {"title": "Worst Origin Ranking by Year", "section": "Airport Rankings"},
    84: {"title": "Top 10 Worst Origins Each Year", "section": "Airport Rankings"},
    86: {"title": "Top 10 Best Origins Each Year", "section": "Airport Rankings"},
    88: {"title": "Delayed vs Non-Delayed Comparison", "section": "Operational Outcomes"},
    90: {"title": "Key Metrics Summary", "section": "Executive Summary"},
    123: {"title": "Machine Learning Dataset Preview", "section": "Machine Learning"},
}


FEATURED_TABLE_IDS = [
    "cmd-38",
    "cmd-40",
    "cmd-48",
    "cmd-54",
    "cmd-58",
    "cmd-62",
    "cmd-64",
    "cmd-70",
    "cmd-72",
    "cmd-74",
    "cmd-80",
    "cmd-84",
    "cmd-86",
    "cmd-90",
]


SECTION_ORDER = [
    "Executive Summary",
    "Visualizations",
    "Airport Analysis",
    "Time Analysis",
    "Route Analysis",
    "Operational Outcomes",
    "Distance and Taxi",
    "Airport Rankings",
    "Machine Learning",
    "Operational Filters",
    "Notebook Outputs",
]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def read_model() -> dict:
    html = SOURCE_HTML.read_text(encoding="utf-8")
    match = re.search(r"var __DATABRICKS_NOTEBOOK_MODEL = '([^']+)';", html)
    if not match:
        raise RuntimeError("Unable to locate the Databricks notebook model in the exported HTML.")
    encoded = match.group(1)
    decoded = base64.b64decode(encoded).decode("utf-8")
    return json.loads(urllib.parse.unquote(decoded))


def infer_title(command_index: int, dataset_names: list[str]) -> str:
    metadata = TABLE_METADATA.get(command_index)
    if metadata:
        return metadata["title"]
    if dataset_names:
        return dataset_names[-1].replace("_", " ").title()
    return f"Notebook Output {command_index}"


def infer_section(command_index: int) -> str:
    metadata = TABLE_METADATA.get(command_index)
    if metadata:
        return metadata["section"]
    return "Notebook Outputs"


def schema_to_columns(schema: list[dict]) -> list[str]:
    return [field["name"] for field in schema]


def rows_to_records(columns: list[str], rows: list[list]) -> list[dict]:
    records = []
    for row in rows:
        record = {}
        for column, value in zip(columns, row):
            record[column] = value
        records.append(record)
    return records


def extract_tables(commands: list[dict]) -> list[dict]:
    tables = []
    for index, command in enumerate(commands):
        result = command.get("results") or {}
        items = result.get("data") or []
        table_items = [item for item in items if item.get("type") == "table"]
        if not table_items:
            continue

        ansi_notes = [item.get("data", "").strip() for item in items if item.get("type") == "ansi" and item.get("data", "").strip()]
        dataset_names = [info.get("name") for info in result.get("datasetInfos") or [] if info.get("name")]

        for position, item in enumerate(table_items):
            columns = schema_to_columns(item.get("schema") or [])
            rows = rows_to_records(columns, item.get("data") or [])
            dataset_name = dataset_names[min(position, len(dataset_names) - 1)] if dataset_names else None
            table_id = f"cmd-{index}" if position == 0 else f"cmd-{index}-{position + 1}"
            tables.append(
                {
                    "id": table_id,
                    "title": infer_title(index, dataset_names),
                    "datasetName": dataset_name,
                    "section": infer_section(index),
                    "commandIndex": index,
                    "columns": columns,
                    "rows": rows,
                    "displayedRowCount": len(rows),
                    "note": ansi_notes[0] if ansi_notes else "",
                    "commandSnippet": " ".join((command.get("command") or "").split())[:220],
                }
            )
    return tables


def extract_charts(commands: list[dict]) -> list[dict]:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    charts = []
    for index, command in enumerate(commands):
        result = command.get("results") or {}
        items = result.get("data") or []
        for item in items:
            if item.get("type") != "mimeBundle":
                continue
            data = item.get("data") or {}
            image_png = data.get("image/png")
            if not image_png:
                continue

            metadata = CHART_METADATA.get(index, {})
            title = metadata.get("title", f"Visualization {index}")
            file_name = f"{index:03d}-{slugify(title)}.png"
            output_path = CHARTS_DIR / file_name
            output_path.write_bytes(base64.b64decode(image_png))

            charts.append(
                {
                    "id": f"chart-{index}",
                    "title": title,
                    "section": metadata.get("section", "Visualizations"),
                    "description": metadata.get("description", ""),
                    "commandIndex": index,
                    "image": f"assets/charts/{file_name}",
                }
            )
    return charts


def extract_ml_summary(commands: list[dict]) -> dict:
    ansi_by_index = {}
    for index, command in enumerate(commands):
        texts = []
        for item in (command.get("results") or {}).get("data", []):
            if item.get("type") == "ansi" and item.get("data", "").strip():
                texts.append(item["data"].strip())
        if texts:
            ansi_by_index[index] = "\n".join(texts)

    balance_text = ansi_by_index.get(128, "")
    dt_text = ansi_by_index.get(131, "")
    importance_text = ansi_by_index.get(133, "")
    rf_text = ansi_by_index.get(135, "")
    gbt_text = ansi_by_index.get(138, "")

    balance_match = re.search(
        r"Delayed \(1\):\s*(\d+), On-Time \(0\):\s*(\d+).*?\|\s*1\|(\d+)\|.*?\|\s*0\|(\d+)\|",
        balance_text,
        re.S,
    )
    balance = {}
    if balance_match:
        balance = {
            "originalDelayed": int(balance_match.group(1)),
            "originalOnTime": int(balance_match.group(2)),
            "balancedDelayed": int(balance_match.group(3)),
            "balancedOnTime": int(balance_match.group(4)),
        }

    dt_trials = []
    for match in re.finditer(
        r"maxDepth=(\d+), minInstances=(\d+) -> Acc=(\d+\.\d+), Precision=(\d+\.\d+), Recall=(\d+\.\d+), AUC=(\d+\.\d+)",
        dt_text,
    ):
        dt_trials.append(
            {
                "maxDepth": int(match.group(1)),
                "minInstances": int(match.group(2)),
                "accuracy": float(match.group(3)),
                "precision": float(match.group(4)),
                "recall": float(match.group(5)),
                "auc": float(match.group(6)),
            }
        )

    dt_best = {}
    best_match = re.search(r"Best params -> maxDepth=(\d+), minInstancesPerNode=(\d+)", dt_text)
    if best_match:
        dt_best = {
            "maxDepth": int(best_match.group(1)),
            "minInstancesPerNode": int(best_match.group(2)),
        }

    feature_importances = []
    for line in importance_text.splitlines():
        if ":" not in line or line.startswith("Feature Importances"):
            continue
        feature, value = line.split(":", 1)
        feature_importances.append({"feature": feature.strip(), "importance": float(value.strip())})

    rf_trials = []
    for match in re.finditer(
        r"RF \(maxDepth=(\d+), minInstances=(\d+)\) -> Acc=(\d+\.\d+), Precision=(\d+\.\d+), Recall=(\d+\.\d+), AUC=(\d+\.\d+)",
        rf_text,
    ):
        rf_trials.append(
            {
                "maxDepth": int(match.group(1)),
                "minInstances": int(match.group(2)),
                "accuracy": float(match.group(3)),
                "precision": float(match.group(4)),
                "recall": float(match.group(5)),
                "auc": float(match.group(6)),
            }
        )

    rf_best = {}
    rf_best_match = re.search(
        r"Best RF params -> maxDepth=(\d+), minInstancesPerNode=(\d+).*?Best RF -> Accuracy=(\d+\.\d+), AUC=(\d+\.\d+)",
        rf_text,
        re.S,
    )
    if rf_best_match:
        rf_best = {
            "maxDepth": int(rf_best_match.group(1)),
            "minInstancesPerNode": int(rf_best_match.group(2)),
            "accuracy": float(rf_best_match.group(3)),
            "auc": float(rf_best_match.group(4)),
        }

    gbt_metrics = {}
    gbt_match = re.search(
        r"Accuracy\s*=\s*(\d+\.\d+).*?Precision\s*=\s*(\d+\.\d+).*?Recall\s*=\s*(\d+\.\d+).*?AUC\s*=\s*(\d+\.\d+)",
        gbt_text,
        re.S,
    )
    if gbt_match:
        gbt_metrics = {
            "accuracy": float(gbt_match.group(1)),
            "precision": float(gbt_match.group(2)),
            "recall": float(gbt_match.group(3)),
            "auc": float(gbt_match.group(4)),
        }

    return {
        "balance": balance,
        "decisionTree": {
            "trials": dt_trials,
            "bestParams": dt_best,
        },
        "randomForest": {
            "trials": rf_trials,
            "best": rf_best,
        },
        "gradientBoostedTree": gbt_metrics,
        "featureImportances": feature_importances,
    }


def build_highlights(tables: list[dict]) -> dict:
    table_map = {table["id"]: table for table in tables}
    overall = table_map.get("cmd-38", {}).get("rows", [{}])[0]
    yearly = table_map.get("cmd-90", {}).get("rows", [])
    delay_categories = table_map.get("cmd-70", {}).get("rows", [])
    flight_status = table_map.get("cmd-72", {}).get("rows", [])

    total_flights = overall.get("total_flights") or 0
    total_cancelled = overall.get("total_cancelled_flights") or 0
    if total_flights:
        overall["cancellation_rate"] = round((total_cancelled / total_flights) * 100, 2)

        weighted_delay_numerator = 0.0
        weighted_delay_denominator = 0
        for row in yearly:
            flights = row.get("total_flights") or 0
            delay_rate = row.get("delay_rate")
            if flights and delay_rate is not None:
                weighted_delay_numerator += flights * delay_rate
                weighted_delay_denominator += flights

        if weighted_delay_denominator:
            overall["delay_rate"] = round(weighted_delay_numerator / weighted_delay_denominator, 2)

    return {
        "overallSummary": overall,
        "yearlySummary": yearly,
        "delayCategories": delay_categories,
        "flightStatus": flight_status,
    }


def build_site_data() -> dict:
    model = read_model()
    commands = model.get("commands") or []
    tables = extract_tables(commands)
    charts = extract_charts(commands)
    return {
        "meta": {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sourceHtml": SOURCE_HTML.name,
            "totalTables": len(tables),
            "totalCharts": len(charts),
            "sectionOrder": SECTION_ORDER,
            "featuredTableIds": FEATURED_TABLE_IDS,
        },
        "project": {
            "title": "Flight Delay Analytics",
            "subtitle": "Sanitized web presentation of the PySpark and Databricks notebook outputs for the 2016-2018 U.S. airline delay study.",
            "dataset": "Kaggle airline-delay-and-cancellation-data-2009-2018",
            "years": [2016, 2017, 2018],
            "stack": ["PySpark", "Databricks", "Pandas", "Matplotlib", "Seaborn", "MongoDB"],
        },
        "highlights": build_highlights(tables),
        "ml": extract_ml_summary(commands),
        "charts": charts,
        "tables": tables,
    }


def main() -> None:
    data = build_site_data()
    SITE_DATA_PATH.write_text(
        "window.SITE_DATA = " + json.dumps(data, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {SITE_DATA_PATH}")
    print(f"Extracted {data['meta']['totalTables']} tables and {data['meta']['totalCharts']} charts")


if __name__ == "__main__":
    main()
