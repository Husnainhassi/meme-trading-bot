#!/usr/bin/env python3
"""
Price Tracking Cron Job - Run every 5 minutes to track price progression
This helps determine optimal entry/exit timing patterns
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.price_tracker import PriceTracker

def main():
    """Main cron job function"""
    print(f"\n🔍 Price Tracking Cron - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        tracker = PriceTracker()
        tracker.record_price_snapshot()
        
        # Run analysis every hour (every 12th run of 5-minute cron)
        current_minute = datetime.now().minute
        if current_minute % 60 == 0:  # Run at the top of each hour
            tracker.analyze_timing_patterns()
        
    except Exception as e:
        print(f"❌ Price tracking error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
