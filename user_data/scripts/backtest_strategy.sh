#!/bin/bash

# Backtest a specific strategy
# Usage: ./backtest_strategy.sh <strategy_name> <timerange>

strategy_name=${1:-FutureTrendV1}
timerange=${2:-20240701-20250101}

echo "============================================"
echo "Strategy Backtest"
echo "============================================"
echo "Strategy: $strategy_name"
echo "Time Range: $timerange"
echo "============================================"

# Run backtest
freqtrade backtest \
    --config ../config/base-futures.json \
    --strategy-path ../strategies \
    --strategy-list "$strategy_name" \
    --datadir ../data \
    --timerange "$timerange" \
    --export trades \
    --export-filename "backtest_results/$strategy_name_$timerange.csv" 2>/dev/null

echo "============================================"
echo "Backtest completed for $strategy_name"
echo "============================================"

# Display results if backtest directory exists
if [ -d "backtest_results" ]; then
    echo "Results saved in backtest_results/"
    ls -la backtest_results/
fi