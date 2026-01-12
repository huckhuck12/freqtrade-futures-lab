#!/bin/bash

# Hyperparameter optimization
# Usage: ./hyperopt.sh <strategy_name> <timerange> <epochs>

strategy_name=${1:-FutureTrendV1}
timerange=${2:-20240701-20250101}
epochs=${3:-100}

echo "============================================"
echo "Hyperparameter Optimization"
echo "============================================"
echo "Strategy: $strategy_name"
echo "Time Range: $timerange"
echo "Epochs: $epochs"
echo "============================================"

# Create hyperopt directory
mkdir -p hyperopt_results

# Run hyperopt
freqtrade hyperopt \
    --config ../config/base-futures.json \
    --strategy-path ../strategies \
    --strategy "$strategy_name" \
    --timerange "$timerange" \
    --epochs $epochs \
    --spaces all \
    --hyperopt-loss SharpeHyperOptLoss \
    --print-all \
    --json-save "hyperopt_results/$strategy_name_$timerange.json" \
    --csv-save "hyperopt_results/$strategy_name_$timerange.csv" 2>/dev/null

echo "============================================"
echo "Hyperparameter optimization completed"
echo "============================================"

# Display results
echo "Best hyperparameters:"
if [ -f "hyperopt_results/$strategy_name_$timerange.json" ]; then
    jq '.' "hyperopt_results/$strategy_name_$timerange.json"
fi