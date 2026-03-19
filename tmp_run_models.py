import pandas as pd
from pathlib import Path
from scripts.run_event_study import EventStudy
from src.preprocessing import DataPreprocessor

models = ["market", "factor"]

data_path = Path('data/raw/data.csv')
if not data_path.exists():
    raise SystemExit("data/raw/data.csv not found")

preprocessor = DataPreprocessor()
data = preprocessor.load_data(str(data_path))

for model in models:
    print(f"\n=== Running Event Study with model={model} ===")
    es = EventStudy(data, assets=['BTC','GOLD','OIL'], model=model)
    results = es.analyze_all_events(use_auto_detection=True)
    out_dir = Path('results') / f'event_study_{model}'
    es.plot_event_study(results, output_dir=str(out_dir), use_tight_layout=False)
    # plot aggregate AAR/CAAR and CAR
    try:
        es.plot_average_aar(str(out_dir))
    except Exception as e:
        print(f"plot_average_aar failed: {e}")
    try:
        es.plot_aggregate_car(results, str(out_dir))
    except Exception as e:
        print(f"plot_aggregate_car failed: {e}")
    es.generate_summary(results, output_dir=str(out_dir))
    print(f"Completed model={model}. Output: {out_dir}")

print("All models done.")
