#!/bin/bash

# Download historical data for futures trading
echo "Downloading historical data for futures pairs..."

# Set timeframe
timeframe="5m"
pairs=("BTC/USDT:USDT" "ETH/USDT:USDT")

# Create data directory if it doesn't exist
mkdir -p ../data

# Download data for each pair
for pair in "${pairs[@]}"; do
    echo "Downloading data for $pair..."
    freqtrade download-data \
        --exchange binance \
        --pairs "$pair" \
        --timeframes "$timeframe" \
        --datadir ../data \
        --days 365
done

echo "Data download completed!"
ls -la ../data/