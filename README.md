# Freqtrade Futures Strategy Backtesting Project

> 高频/中频期货策略回测项目，支持多策略对比

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/huckhuck12/freqtrade-futures-lab.git
cd freqtrade-futures-lab
```

### 2. 下载数据 (OKX)

```bash
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop download-data \
  --config user_data/config/base-futures.json \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT XRP/USDT:USDT \
  --timeframe 5m --timerange 20240101-20240131
```

### 3. 运行回测

```bash
# 基础回测 (5m, 1个交易对)
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop backtesting \
  --config user_data/config/base-futures.json \
  --strategy-path user_data/strategies --strategy FutureTrendV1

# 高频回测 (1m, 10个交易对)
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop backtesting \
  --config user_data/config/highfreq-config.json \
  --strategy-path user_data/strategies --strategy FutureHighFreqV1
```

---

## 配置文件

| 文件 | 用途 | Timeframe | 交易对数 |
|------|------|-----------|----------|
| `base-futures.json` | 基础配置 | 5m | 4 |
| `okx-futures.json` | OKX 5分钟 | 5m | 10 |
| `highfreq-config.json` | 高频1分钟 | 1m | 10 |

---

## 策略说明

### FutureTrendV1 - 趋势跟踪策略

| 参数 | 值 |
|------|-----|
| Timeframe | 5m |
| 指标 | EMA 12/26 + RSI 14 |
| 买入 | EMA金叉 + RSI < 70 |
| 卖出 | EMA死叉 或 RSI > 80 |
| 止损 | -3% |
| 止盈 | 5% |

### FutureMeanRevV1 - 均值回归策略

| 参数 | 值 |
|------|-----|
| Timeframe | 5m |
| 指标 | Bollinger Bands + RSI |
| 买入 | 触及下轨 + RSI < 35 |
| 卖出 | 触及上轨 或 RSI > 75 |
| 止损 | -3% |
| 止盈 | 5% |

### FutureHighFreqV1 - 高频趋势策略

| 参数 | 值 |
|------|-----|
| Timeframe | 1m |
| 指标 | EMA 9/21 |
| 买入 | EMA金叉 |
| 卖出 | EMA死叉 |
| 止损 | -2% |
| 止盈 | 1% → 0.5% → 0.2% → trailing |
| 追踪止盈 | 0.5%启动, 0.8%偏移 |

---

## 项目结构

```
freqtrade-futures-lab/
├── docker-compose.yml
├── README.md
└── user_data/
    ├── config/
    │   ├── base-futures.json       # 基础配置
    │   ├── okx-futures.json        # OKX 5分钟
    │   └── highfreq-config.json    # 高频1分钟
    ├── strategies/
    │   ├── _base.py                # 基础策略类
    │   ├── FutureTrendV1.py        # 趋势策略
    │   ├── FutureMeanRevV1.py      # 均值回归策略
    │   └── FutureHighFreqV1.py     # 高频策略
    ├── data/                       # K线数据
    └── backtest_results/           # 回测结果
```

---

## 回测结果 (2024年1月 OKX)

| 策略 | 交易次数 | 胜率 | ROI | 最大回撤 |
|------|----------|------|-----|----------|
| FutureTrendV1 | 17 | 35.3% | -2.84% | 19.23% |
| FutureMeanRevV1 | 21 | 28.6% | -13.64% | 20.88% |
| FutureHighFreqV1 | 204 | 51.5% | -0.89% | 1.34% |

---

## 常见问题

### 错误：SSL证书验证失败

```bash
# 使用 --pull always 强制拉取最新镜像
docker run --pull always ...
```

### 错误：No history found

```bash
# 确认下载数据时指定 --trading-mode futures
docker run ... download-data --trading-mode futures ...
```

### 错误：Market order requires price_side=other

修改配置文件：
```json
"entry_pricing": { "price_side": "other", "use_order_book": false },
"exit_pricing": { "price_side": "other", "use_order_book": false }
```
