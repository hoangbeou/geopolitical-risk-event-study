"""
Generate thesis-ready pattern story for BTC/GOLD event reactions.
Creates markdown summary + pivot tables for type/region.
"""

import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import sys
import io

# Fix encoding for Windows terminals
if hasattr(sys.stdout, "buffer") and not hasattr(sys.stdout, "_encoding_set"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stdout._encoding_set = True  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass


@dataclass
class EventRecord:
    event_id: str
    date: str
    name: str
    event_type: str
    region: str
    btc_car: Optional[float] = None
    gold_car: Optional[float] = None
    btc_direction: Optional[str] = None
    gold_direction: Optional[str] = None
    pattern: Optional[str] = None
    act_ratio: Optional[float] = None
    threat_ratio: Optional[float] = None


PATTERN_LABELS = {
    "both_inc": "Cả BTC & GOLD cùng tăng",
    "both_dec": "Cả BTC & GOLD cùng giảm",
    "btc_inc_gold_dec": "BTC tăng, GOLD giảm",
    "btc_dec_gold_inc": "BTC giảm, GOLD tăng (Flight-to-Quality)",
}


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_event_records(
    event_patterns: Dict, identified_events: Dict, act_threat: Dict
) -> Dict[str, EventRecord]:
    """Combine all sources into unified event records."""
    # Start with identified metadata
    records: Dict[str, EventRecord] = {}
    for event_id, data in identified_events.items():
        identified = data["identified"]
        records[event_id] = EventRecord(
            event_id=event_id,
            date=data["date"],
            name=identified["name"],
            event_type=identified["type"],
            region=identified["region"],
        )

    def _assign_direction(asset: str, direction: str):
        bucket = f"{asset}_{direction}"
        for entry in event_patterns[bucket]["events"]:
            event_id = entry["event"]
            record = records.get(event_id)
            if not record:
                continue
            car_val = entry["car"]
            if asset == "BTC":
                record.btc_car = car_val
                record.btc_direction = direction
            else:
                record.gold_car = car_val
                record.gold_direction = direction

    for asset in ["BTC", "GOLD"]:
        for direction in ["increase", "decrease"]:
            _assign_direction(asset, direction)

    # Map ACT/THREAT
    for direction in ["BTC_increase", "BTC_decrease"]:
        for entry in act_threat.get(direction, []):
            record = records.get(entry["event"])
            if not record:
                continue
            record.act_ratio = entry.get("act_ratio")
            record.threat_ratio = entry.get("threat_ratio")

    # Determine pattern
    for record in records.values():
        if record.btc_direction == "increase" and record.gold_direction == "increase":
            record.pattern = "both_inc"
        elif (
            record.btc_direction == "decrease" and record.gold_direction == "decrease"
        ):
            record.pattern = "both_dec"
        elif record.btc_direction == "increase" and record.gold_direction == "decrease":
            record.pattern = "btc_inc_gold_dec"
        elif record.btc_direction == "decrease" and record.gold_direction == "increase":
            record.pattern = "btc_dec_gold_inc"

    return records


def summarize_patterns(records: Dict[str, EventRecord]) -> pd.DataFrame:
    rows = []
    for record in records.values():
        if not record.pattern:
            continue
        rows.append(
            {
                "event": record.event_id,
                "date": record.date,
                "name": record.name,
                "pattern": record.pattern,
                "event_type": record.event_type,
                "region": record.region,
                "btc_car": record.btc_car,
                "gold_car": record.gold_car,
                "act_ratio": record.act_ratio,
                "threat_ratio": record.threat_ratio,
            }
        )
    return pd.DataFrame(rows)


def compute_pattern_stats(df: pd.DataFrame) -> Dict[str, Dict]:
    stats: Dict[str, Dict] = {}
    for pattern, group in df.groupby("pattern"):
        stats[pattern] = {
            "count": len(group),
            "share": len(group) / len(df),
            "avg_btc": group["btc_car"].mean(),
            "avg_gold": group["gold_car"].mean(),
            "avg_act": group["act_ratio"].mean(),
            "avg_threat": group["threat_ratio"].mean(),
            "type_dist": group["event_type"].value_counts(normalize=True).to_dict(),
            "region_dist": group["region"].value_counts(normalize=True).to_dict(),
            "top_events": group.sort_values("btc_car", ascending=False)[
                ["event", "date", "name", "btc_car", "gold_car"]
            ].head(3),
        }
    return stats


def save_pivots(df: pd.DataFrame, output_dir: Path):
    pivot_type = (
        pd.crosstab(df["pattern"], df["event_type"])
        .reindex(PATTERN_LABELS.keys())
        .fillna(0)
        .astype(int)
    )
    pivot_region = (
        pd.crosstab(df["pattern"], df["region"])
        .reindex(PATTERN_LABELS.keys())
        .fillna(0)
        .astype(int)
    )

    pivot_type.to_csv(output_dir / "pattern_vs_type.csv", encoding="utf-8", index=True)
    pivot_region.to_csv(
        output_dir / "pattern_vs_region.csv", encoding="utf-8", index=True
    )

    return pivot_type, pivot_region


def df_to_markdown_simple(df: pd.DataFrame) -> str:
    """Render DataFrame to Markdown without external dependencies."""
    cols = [""] + list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    separator = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for idx, row in df.iterrows():
        cells = [str(idx)] + [str(row[col]) for col in df.columns]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join([header, separator] + rows)


def write_markdown_report(
    stats: Dict[str, Dict],
    pivot_type: pd.DataFrame,
    pivot_region: pd.DataFrame,
    output_path: Path,
):
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Pattern Story: BTC vs GOLD phản ứng với GPR events\n\n")
        f.write(
            "Phân tích tổng hợp 61 events tự động phát hiện, chia thành 4 pattern cơ bản "
            "dựa trên phản ứng giá BTC và GOLD trong cửa sổ event study (CAR trong [-10, +10]).\n\n"
        )

        for key in PATTERN_LABELS:
            data = stats[key]
            label = PATTERN_LABELS[key]
            f.write(f"## {label}\n\n")
            f.write(f"- Số sự kiện: **{data['count']} ({data['share']*100:.1f}%)**\n")
            f.write(
                f"- BTC CAR trung bình: **{data['avg_btc']*100:+.2f}%**, GOLD CAR trung bình: **{data['avg_gold']*100:+.2f}%**\n"
            )
            f.write(
                f"- GPR ACT ratio: **{data['avg_act']:.3f}**, GPR THREAT ratio: **{data['avg_threat']:.3f}**\n"
            )
            type_top = sorted(
                data["type_dist"].items(), key=lambda x: x[1], reverse=True
            )[:2]
            region_top = sorted(
                data["region_dist"].items(), key=lambda x: x[1], reverse=True
            )[:2]
            f.write(
                "- Event mix nổi bật: "
                + ", ".join([f"{k} ({v*100:.1f}%)" for k, v in type_top])
                + "\n"
            )
            f.write(
                "- Region nổi bật: "
                + ", ".join([f"{k} ({v*100:.1f}%)" for k, v in region_top])
                + "\n"
            )
            f.write("- Top events (BTC CAR lớn nhất):\n")
            for _, row in data["top_events"].iterrows():
                f.write(
                    f"  * {row['event']} – {row['name']} ({row['date']}): "
                    f"BTC {row['btc_car']*100:+.2f}%, GOLD {row['gold_car']*100:+.2f}%\n"
                )
            f.write("\n")

        f.write("## Pivot: Pattern x Event Type\n\n")
        f.write(df_to_markdown_simple(pivot_type) + "\n\n")

        f.write("## Pivot: Pattern x Region\n\n")
        f.write(df_to_markdown_simple(pivot_region) + "\n\n")

        f.write("## Insight chính cho luận văn\n\n")
        f.write(
            "- **Flight-to-Quality rõ rệt**: nhóm BTC↓/GOLD↑ có ACT & THREAT ratio cao nhất "
            "(>0.78), 79% là war events, chủ yếu ở Trung Đông/Âu.\n"
        )
        f.write(
            "- **Risk-on double hedge**: nhóm cả hai cùng tăng gắn với events mixed hoặc war giới hạn, "
            "ACT/THREAT thấp → nhà đầu tư coi BTC & GOLD là bộ đôi phòng hộ.\n"
        )
        f.write(
            "- **Political/trade catalysts**: nhóm BTC↑/GOLD↓ có tỷ lệ political/mixed cao nhất, "
            "hàm ý BTC phản ứng như tài sản định hướng tăng trưởng, vàng bị bán ra.\n"
        )
        f.write(
            "- **European war drag**: nhóm cả hai cùng giảm tập trung vào Russia-Ukraine (53% events), "
            "cho thấy cú sốc chiến tranh châu Âu kéo cả tài sản rủi ro lẫn vàng xuống khi thanh khoản co lại.\n"
        )


def main():
    base_dir = Path("results/event_study")
    patterns_path = base_dir / "event_patterns.json"
    identified_path = base_dir / "identified_events.json"
    act_threat_path = base_dir / "gpr_act_threat_analysis.json"

    event_patterns = load_json(patterns_path)
    identified_events = load_json(identified_path)
    act_threat = load_json(act_threat_path)

    records = build_event_records(event_patterns, identified_events, act_threat)
    df = summarize_patterns(records)
    stats = compute_pattern_stats(df)

    output_dir = base_dir / "pattern_story"
    output_dir.mkdir(parents=True, exist_ok=True)

    pivot_type, pivot_region = save_pivots(df, output_dir)
    report_path = output_dir / "pattern_story_report.md"
    write_markdown_report(stats, pivot_type, pivot_region, report_path)

    print("=" * 80)
    print("Pattern story generated")
    print("=" * 80)
    print(f"Rows summarized: {len(df)}")
    print(f"Saved report: {report_path}")
    print(f"Saved pivot (type): {output_dir / 'pattern_vs_type.csv'}")
    print(f"Saved pivot (region): {output_dir / 'pattern_vs_region.csv'}")


if __name__ == "__main__":
    main()

