#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kiểm tra số lượng events được phát hiện"""
import sys
import io
from pathlib import Path
import pandas as pd

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent))

print("="*80)
print("KIỂM TRA SỐ LƯỢNG EVENTS")
print("="*80)

try:
    from scripts.run_qqr import GeopoliticalRiskAnalysis
    from scripts.detect_events import GPREventDetector
    
    # Load data
    print("\nLoading data...")
    analysis = GeopoliticalRiskAnalysis('data/data_optimized.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data_optimized.csv')
    print(f"Data loaded: {len(data)} rows")
    
    # Initialize detector
    print("Initializing detector...")
    detector = GPREventDetector(data)
    print("Detector initialized")
    
    # Test với các threshold khác nhau
    print("\n" + "="*80)
    print("KIỂM TRA SỐ LƯỢNG EVENTS VỚI CÁC THRESHOLD KHÁC NHAU")
    print("="*80)
    
    # Test spikes
    for percentile in [90, 95, 98]:
        spikes = detector.detect_spikes(threshold_percentile=percentile, window_days=7)
        print(f"\nSpikes (percentile {percentile}, window=7): {len(spikes)} events")
    
    # Test high periods
    for percentile in [85, 90, 95]:
        periods = detector.detect_high_periods(threshold_percentile=percentile, require_increase=True)
        print(f"\nHigh periods (percentile {percentile}): {len(periods)} events")
    
    # Test combined - mặc định
    print("\n" + "="*80)
    print("COMBINED EVENTS (MẶC ĐỊNH)")
    print("="*80)
    all_events_default = detector.detect_all_events(
        spike_percentile=95,
        high_period_percentile=90,
        combine=True,
        require_gpr_increase=True
    )
    print(f"\nCombined (default): {len(all_events_default)} events")
    
    # Test với threshold thấp hơn để có nhiều events hơn
    print("\n" + "="*80)
    print("TEST VỚI THRESHOLD THẤP HƠN (NHIỀU EVENTS HƠN)")
    print("="*80)
    
    for spike_pct in [90, 85, 80]:
        for period_pct in [85, 80, 75]:
            all_events = detector.detect_all_events(
                spike_percentile=spike_pct,
                high_period_percentile=period_pct,
                combine=True,
                require_gpr_increase=True
            )
            print(f"Spike {spike_pct}% + Period {period_pct}%: {len(all_events)} events")
    
    # Test không require_gpr_increase
    print("\n" + "="*80)
    print("TEST KHÔNG REQUIRE GPR INCREASE")
    print("="*80)
    all_events_no_req = detector.detect_all_events(
        spike_percentile=90,
        high_period_percentile=85,
        combine=True,
        require_gpr_increase=False
    )
    print(f"Without require_gpr_increase: {len(all_events_no_req)} events")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()

