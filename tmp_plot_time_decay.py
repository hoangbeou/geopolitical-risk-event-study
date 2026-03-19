import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

df = pd.read_csv("results/time_decay_analysis/aar_by_day.csv")
assets = ["BTC","GOLD","OIL"]
colors = {"BTC":"#1f77b4","GOLD":"#d4a017","OIL":"#2ca02c"}

out_dir = Path("results/time_decay_analysis")
out_dir.mkdir(parents=True, exist_ok=True)

for asset in assets:
    fig, ax = plt.subplots(figsize=(8,5))
    ax.axhline(0, color="gray", linestyle="--", linewidth=1)
    ax.plot(df["Day"], df[asset], color=colors.get(asset,"black"), linewidth=2)
    ax.set_title(f"Time Decay - AAR by Day ({asset})", fontsize=13, fontweight="bold")
    ax.set_xlabel("Day (event window)")
    ax.set_ylabel("AAR")
    ax.grid(True, alpha=0.3)
    ax.axvline(0, color="red", linestyle="-", linewidth=1)
    plt.tight_layout()
    out_path = out_dir / f"time_decay_{asset.lower()}.png"
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Saved", out_path)

print("Done.")
