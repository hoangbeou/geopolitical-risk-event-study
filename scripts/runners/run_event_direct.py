#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Chạy Event Study trực tiếp với error handling"""
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import sys
import traceback
import io
from pathlib import Path

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))

try:
    import sys
    sys.stdout.flush()
    
    print("=" * 80, flush=True)
    print("EVENT STUDY ANALYSIS", flush=True)
    print("=" * 80, flush=True)
    print("\nSU DUNG TU DONG PHAT HIEN EVENTS TU GPR\n", flush=True)
    print("Phuong phap:", flush=True)
    print("1. Phat hien GPR spikes (percentile 90)", flush=True)
    print("2. Phat hien high GPR periods (percentile 90)", flush=True)
    print("3. Window: 30 ngay, Combine: 7 ngay\n", flush=True)
    
    from scripts.run_qqr import GeopoliticalRiskAnalysis
    from scripts.run_event_study import EventStudy
    
    print("Loading data...", flush=True)
    analysis = GeopoliticalRiskAnalysis('data/data_optimized.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data_optimized.csv')
    print(f"Data loaded: {len(data)} rows", flush=True)
    
    print("Initializing Event Study...", flush=True)
    event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
    
    print("Analyzing all events...", flush=True)
    results = event_study.analyze_all_events(use_auto_detection=True)
    print(f"Analyzed {len(results)} events", flush=True)
    
    print("Plotting results...", flush=True)
    event_study.plot_event_study(results, output_dir='results')
    
    print("Generating summary...", flush=True)
    event_study.generate_summary(results, output_dir='results')
    
    print("\n" + "=" * 80, flush=True)
    print("HOAN THANH EVENT STUDY ANALYSIS", flush=True)
    print("=" * 80, flush=True)
    
except Exception as e:
    print(f"\nERROR: {e}", flush=True)
    traceback.print_exc()
    sys.stdout.flush()

