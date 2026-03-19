"""
Map extracted locations to regions and aggregate CAR by region.

Input:
  - events_with_locations: results/event_study/detected_events_with_locations.csv
    (must contain columns: Event_Number, Date, CAR_BTC, CAR_GOLD, CAR_OIL, Detected_Locations)
  - simple country-to-region mapping defined in this script (can be extended).

Output:
  - results/event_study/detected_events_with_region.csv (adds Region column)
  - results/event_study/car_by_region.csv (avg CAR by region)
"""

import argparse
import pandas as pd
from pathlib import Path

# Simple country to region mapping (extend as needed)
COUNTRY_REGION_MAP = {
    # Middle East
    "Israel": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
    "Syria": "Middle East", "Lebanon": "Middle East", "Yemen": "Middle East",
    "Qatar": "Middle East", "UAE": "Middle East", "Saudi Arabia": "Middle East",
    "Jordan": "Middle East", "Kuwait": "Middle East",
    # Europe
    "Ukraine": "Europe", "Russia": "Europe", "United Kingdom": "Europe",
    "France": "Europe", "Germany": "Europe", "Spain": "Europe", "Italy": "Europe",
    "Poland": "Europe", "Belarus": "Europe",
    # Asia
    "China": "Asia", "India": "Asia", "Pakistan": "Asia", "Japan": "Asia",
    "South Korea": "Asia", "North Korea": "Asia", "Philippines": "Asia",
    # Africa
    "Somalia": "Africa", "Nigeria": "Africa", "Ethiopia": "Africa", "Libya": "Africa",
    "Egypt": "Africa", "Sudan": "Africa", "South Sudan": "Africa",
    # Americas
    "United States": "Americas", "USA": "Americas", "Canada": "Americas",
    "Mexico": "Americas", "Brazil": "Americas", "Argentina": "Americas",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Map locations to region and aggregate CAR by region")
    parser.add_argument("--input", type=str, default="results/event_study/detected_events_with_locations.csv")
    parser.add_argument("--output", type=str, default="results/event_study/detected_events_with_region.csv")
    parser.add_argument("--agg-output", type=str, default="results/event_study/car_by_region.csv")
    return parser.parse_args()


def detect_region(detected_locs: str) -> str:
    if not isinstance(detected_locs, str) or detected_locs.strip() == "":
        return "Unknown"
    countries = [c.strip() for c in detected_locs.split(",") if c.strip()]
    regions = []
    for c in countries:
        # exact match first
        if c in COUNTRY_REGION_MAP:
            regions.append(COUNTRY_REGION_MAP[c])
        else:
            # simple contains match (e.g., "Russian Federation" -> "Russia")
            for k, v in COUNTRY_REGION_MAP.items():
                if k.lower() in c.lower():
                    regions.append(v)
                    break
    if not regions:
        return "Unknown"
    # pick the most common region in the list
    return pd.Series(regions).mode().iloc[0]


def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    agg_path = Path(args.agg_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    agg_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)
    if "Detected_Locations" not in df.columns:
        raise SystemExit("Missing Detected_Locations in input CSV.")

    df["Region"] = df["Detected_Locations"].apply(detect_region)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    # Aggregate CAR by region
    car_cols = ["CAR_BTC", "CAR_GOLD", "CAR_OIL"]
    agg = df.groupby("Region")[car_cols].mean().reset_index()
    agg.to_csv(agg_path, index=False, encoding="utf-8-sig")

    print("Saved:", output_path)
    print("Saved:", agg_path)
    print("\nCAR by Region:\n", agg)


if __name__ == "__main__":
    main()

