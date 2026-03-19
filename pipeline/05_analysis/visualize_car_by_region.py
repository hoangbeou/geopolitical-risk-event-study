"""
Visualize CAR by region (bar + box) using detected_events_with_region.csv

Input:
  - results/event_study/detected_events_with_region.csv
    columns: Region, CAR_BTC, CAR_GOLD, CAR_OIL

Output:
  - results/event_study/car_by_region_bar.png
  - results/event_study/car_by_region_box.png
  - results/event_study/top_events_by_region.csv (top 3 abs(CAR) per asset per region)
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

plt.style.use("seaborn-v0_8-darkgrid")


def parse_args():
    parser = argparse.ArgumentParser(description="Visualize CAR by region")
    parser.add_argument(
        "--input",
        type=str,
        default="results/event_study/detected_events_with_region.csv",
    )
    parser.add_argument(
        "--output-dir", type=str, default="results/event_study", help="Output directory"
    )
    return parser.parse_args()


def plot_bar(df, output_dir):
    car_cols = ["CAR_BTC", "CAR_GOLD", "CAR_OIL"]
    agg = df.groupby("Region")[car_cols].mean().reset_index()
    melted = agg.melt(id_vars="Region", var_name="Asset", value_name="CAR")

    plt.figure(figsize=(10, 5))
    sns.barplot(data=melted, x="Region", y="CAR", hue="Asset", palette="Set2")
    plt.axhline(0, color="red", linestyle="--", alpha=0.5)
    plt.title("Average CAR by Region")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out_path = Path(output_dir) / "car_by_region_bar.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved:", out_path)


def plot_box(df, output_dir):
    melted = df.melt(
        id_vars="Region", value_vars=["CAR_BTC", "CAR_GOLD", "CAR_OIL"], var_name="Asset", value_name="CAR"
    )
    plt.figure(figsize=(10, 5))
    sns.boxplot(data=melted, x="Region", y="CAR", hue="Asset", palette="Set3")
    plt.axhline(0, color="red", linestyle="--", alpha=0.5)
    plt.title("CAR Distribution by Region")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out_path = Path(output_dir) / "car_by_region_box.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved:", out_path)


def top_events(df, output_dir):
    records = []
    for region, sub in df.groupby("Region"):
        for asset in ["CAR_BTC", "CAR_GOLD", "CAR_OIL"]:
            sub_nonnull = sub.dropna(subset=[asset])
            top = sub_nonnull.reindex(
                sub_nonnull[asset].abs().sort_values(ascending=False).index
            ).head(3)
            for _, row in top.iterrows():
                records.append(
                    {
                        "Region": region,
                        "Asset": asset.replace("CAR_", ""),
                        "Event_Number": row.get("Event_Number"),
                        "Date": row.get("Date"),
                        "CAR": row[asset],
                        "Detected_Locations": row.get("Detected_Locations", ""),
                    }
                )
    out_df = pd.DataFrame(records)
    out_path = Path(output_dir) / "top_events_by_region.csv"
    out_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("Saved:", out_path)


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.input)
    if "Region" not in df.columns:
        raise SystemExit("Missing Region column in input.")

    plot_bar(df, output_dir)
    plot_box(df, output_dir)
    top_events(df, output_dir)


if __name__ == "__main__":
    main()

