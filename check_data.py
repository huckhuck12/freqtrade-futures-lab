#!/usr/bin/env python3
import pandas as pd
import os

data_dir = 'user_data/data/okx/futures'
files = [f for f in os.listdir(data_dir) if '5m' in f and 'feather' in f]
print(f'Found {len(files)} 5m data files')

for f in files[:3]:
    filepath = os.path.join(data_dir, f)
    df = pd.read_feather(filepath)
    print(f'{f}: {df["date"].min()} to {df["date"].max()}, {len(df)} rows')
