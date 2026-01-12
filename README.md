# Freqtrade Futures Strategy Backtesting Project

> 一个专为 **Futures 策略高效回测** 设计的项目结构\
> 适配 **2核2G 服务器 / 本地调试 / GitHub Actions**

------------------------------------------------------------------------

## 设计目标

-   快速策略试错（服务器 / 本地）
-   稳定可复现的回测环境（Docker）
-   多策略公平对比
-   避免配置散乱 & CI 低效失败

------------------------------------------------------------------------

## 项目结构

    freqtrade/
    ├── docker-compose.yml
    ├── README.md
    ├── user_data/
    │   ├── config/
    │   │   └── base-futures.json
    │   ├── strategy_configs/
    │   │   ├── FutureTrendV1.json
    │   │   └── FutureMeanRevV1.json
    │   ├── strategies/
    │   │   ├── _base.py
    │   │   ├── FutureTrendV1.py
    │   │   └── FutureMeanRevV1.py
    │   ├── data/
    │   ├── scripts/
    │   │   ├── download.sh
    │   │   ├── backtest_strategy.sh
    │   │   └── hyperopt.sh
    │   └── logs/

------------------------------------------------------------------------

## Base Futures 配置

``` json
{
  "dry_run": true,
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "exchange": {
    "name": "binance"
  },
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "fee": 0.0004,
  "timeframe": "5m",
  "startup_candle_count": 300,
  "max_open_trades": 1,
  "pair_whitelist": [
    "BTC/USDT:USDT",
    "ETH/USDT:USDT"
  ]
}
```

------------------------------------------------------------------------

## 回测使用方式

``` bash
./user_data/scripts/backtest_strategy.sh FutureTrendV1 20240701-20250101
```

------------------------------------------------------------------------

## 服务器部署（2核2G）

``` bash
sudo apt update
sudo apt install -y docker docker-compose-plugin
git clone <your-repo>
cd freqtrade
./user_data/scripts/download.sh
```

------------------------------------------------------------------------

## 开发节奏建议

-   服务器 / 本地：高频回测 & 调参
-   CI：低频验证 & 回归对比
