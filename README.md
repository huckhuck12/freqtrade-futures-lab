# Freqtrade Futures Strategy Backtesting Project

> 一个专为 **Futures 策略高效回测** 设计的项目结构
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
    │   ├── backtest_results/
    │   └── logs/

------------------------------------------------------------------------

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/huckhuck12/freqtrade-futures-lab.git
cd freqtrade-futures-lab
```

### 2. 下载数据

使用 Docker 容器下载数据：

```bash
docker run --rm --entrypoint sh \
  -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:stable \
  -c 'freqtrade download-data --exchange binance --pairs BTC/USDT:USDT ETH/USDT:USDT --timeframes 5m --timerange 20240101-20240201 --trading-mode futures'
```

### 3. 运行回测

```bash
docker run --rm --entrypoint sh \
  -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:stable \
  -c 'freqtrade backtesting --config /freqtrade/user_data/config/base-futures.json --strategy-path /freqtrade/user_data/strategies --strategy FutureTrendV1 --timerange 20240101-20240201'
```

### 4. 查看数据

```bash
docker run --rm --entrypoint sh \
  -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:stable \
  -c 'freqtrade list-data --exchange binance'
```

------------------------------------------------------------------------

## Docker Compose 部署

### 启动回测服务

```bash
docker compose --profile backtest up
```

### 启动交易服务

```bash
docker compose up
```

------------------------------------------------------------------------

## 服务器部署（2核2G）

```bash
sudo apt update
sudo apt install -y docker docker-compose-plugin
git clone https://github.com/huckhuck12/freqtrade-futures-lab.git
cd freqtrade-futures-lab
```

下载数据：

```bash
docker run --rm --entrypoint sh \
  -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:stable \
  -c 'freqtrade download-data --exchange binance --pairs BTC/USDT:USDT ETH/USDT:USDT --timeframes 5m --timerange 20240101-20240201 --trading-mode futures'
```

运行回测：

```bash
docker run --rm --entrypoint sh \
  -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:stable \
  -c 'freqtrade backtesting --config /freqtrade/user_data/config/base-futures.json --strategy-path /freqtrade/user_data/strategies --strategy FutureTrendV1 --timerange 20240101-20240201'
```

------------------------------------------------------------------------

## 故障排除

### 错误：StaticPairList requires pair_whitelist to be set

**原因**：配置文件中缺少 `pair_whitelist` 或 `pairlists` 配置

**解决**：确保 `base-futures.json` 包含正确的配置：

```json
{
  "pair_whitelist": ["BTC/USDT:USDT", "ETH/USDT:USDT"],
  "pairlists": [
    {
      "method": "StaticPairList",
      "config_pairs": ["BTC/USDT:USDT", "ETH/USDT:USDT"]
    }
  ]
}
```

### 错误：attempted relative import with no known parent package

**原因**：策略文件中使用了相对导入

**解决**：将相对导入改为绝对导入，例如：

```python
# 错误
from ._base import BaseFuturesStrategy

# 正确
from freqtrade.strategy import IStrategy
```

### 错误：No history for BTC/USDT:USDT, futures, 5m found

**原因**：数据未下载或下载位置不正确

**解决**：
1. 确保使用 `--trading-mode futures` 参数下载数据
2. 数据会自动保存到 `user_data/data/binance/` 目录
3. 检查数据文件是否存在：

```bash
ls -la user_data/data/binance/
```

------------------------------------------------------------------------

## 开发节奏建议

-   服务器 / 本地：高频回测 & 调参
-   CI：低频验证 & 回归对比

------------------------------------------------------------------------

## 策略说明

### FutureTrendV1

基于 EMA 交叉和 RSI 的趋势跟踪策略：

-   **买入信号**：快速 EMA 上穿慢速 EMA 且 RSI < 70
-   **卖出信号**：快速 EMA 下穿慢速 EMA 或 RSI > 80
-   **止损**：-3%
-   **止盈**：5%

------------------------------------------------------------------------

## 许可证

MIT License
