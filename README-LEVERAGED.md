# Freqtrade Futures Leveraged Strategy

## 策略概述

**策略名称:** FutureBuyHoldV2  
**时间周期:** 1分钟  
**杠杆:** BTC/ETH/SOL 5x, XRP/DOGE 3x  
**目标:** 月收益 ~15% (不使用杠杆), ~75% (5x杠杆)

## 回测结果 (2024年1-2月)

| 指标 | 值 |
|------|-----|
| ROI | +14.53% |
| 胜率 | 87.9% |
| 交易次数 | 717 |
| 最大回撤 | 15.25% |
| 市场涨幅 | +28.91% |

**5x杠杆预期收益:** 14.53% × 5 = **~72.65% (2个月)**

## 文件结构

```
user_data/
├── config/
│   ├── live-leveraged-config.json  # 实盘配置
│   ├── highfreq-config.json        # 1m回测配置
│   └── bear-market-config.json     # 5m回测配置
└── strategies/
    ├── FutureBuyHoldV2.py          # 实盘策略
    ├── FutureBuyHold.py            # 回测策略
    └── FutureHighLeverage.py       # 高杠杆策略
```

## 快速开始

### 1. 设置API密钥

```bash
export OKX_API_KEY="your_api_key"
export OKX_API_SECRET="your_api_secret"
export OKX_API_PASSPHRASE="your_passphrase"
```

### 2. 运行回测

```bash
# 1分钟时间周期 (2024牛市)
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop backtesting \
  --config user_data/config/highfreq-config.json \
  --strategy-path user_data/strategies \
  --strategy FutureBuyHoldV2 \
  --timerange 20240101-20240301

# 5分钟时间周期 (2022熊市)
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop backtesting \
  --config user_data/config/bear-market-config.json \
  --strategy-path user_data/strategies \
  --strategy FutureBuyHoldV2 \
  --timerange 20220501-20221231
```

### 3. 下载数据

```bash
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop download-data \
  --config user_data/config/live-leveraged-config.json \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT XRP/USDT:USDT DOGE/USDT:USDT \
  --timeframe 1m
```

### 4. 实盘运行

```bash
docker run -d \
  --name freqtrade \
  -v $(pwd)/user_data:/freqtrade/user_data \
  -e OKX_API_KEY \
  -e OKX_API_SECRET \
  -e OKX_API_PASSPHRASE \
  freqtradeorg/freqtrade:develop trade \
  --config user_data/config/live-leveraged-config.json \
  --strategy-path user_data/strategies \
  --strategy FutureBuyHoldV2
```

### 5. 机器学习回测 (可选)

```bash
docker run --rm -v $(pwd)/user_data:/freqtrade/user_data \
  freqtradeorg/freqtrade:develop backtesting \
  --config user_data/config/bear-market-config.json \
  --strategy-path user_data/strategies \
  --strategy FutureMLV2 \
  --timerange 20220501-20221231
```

## 策略参数

| 参数 | 值 | 说明 |
|------|-----|------|
| timeframe | 1m | 1分钟K线 |
| max_open_trades | 3 | 最多同时3个交易 |
| stake_amount | 100 | 每次开仓100 USDT |
| stoploss | -5% | 止损5% |
| trailing_stop | True | 移动止损 |
| minimal_roi | 2.5% | 2.5%止盈 |

## 杠杆配置

| 交易对 | 杠杆 | 说明 |
|--------|------|------|
| BTC/USDT:USDT | 5x | 高流动性 |
| ETH/USDT:USDT | 5x | 高流动性 |
| SOL/USDT:USDT | 5x | 高波动性 |
| XRP/USDT:USDT | 3x | 中波动性 |
| DOGE/USDT:USDT | 3x | 中波动性 |

## 风险提示

⚠️ **高风险策略**

1. **杠杆风险:** 5x杠杆意味着5倍收益也5倍亏损
2. **市场风险:** 加密货币波动大，可能快速亏损
3. **回测偏差:** 历史表现不代表未来收益
4. **建议:**
   - 只投入你能承受亏损的资金
   - 从小仓位开始测试
   - 设置止损，不要抗单
   - 定期检查策略表现

## 预期收益计算

| 时间 | 无杠杆 | 5x杠杆 |
|------|--------|--------|
| 1个月 | ~7.5% | ~37.5% |
| 2个月 | ~15% | ~75% |
| 3个月 | ~22.5% | ~112.5% |

## 监控和调整

### 查看交易

```bash
# 查看实时交易
docker logs freqtrade --tail 100 | grep -i trade

# 查看利润
docker exec freqtrade curl http://localhost:8080/api/v1/status
```

### 停止机器人

```bash
docker stop freqtrade
docker rm freqtrade
```

## 策略对比

| 策略 | ROI | 胜率 | 交易次数 | 适合场景 |
|------|-----|------|----------|----------|
| FutureBuyHoldV2 | +14.53% | 87.9% | 717 | 趋势行情 |
| FutureHighLeverage | +12.14% | 86.1% | 1054 | 高波动 |
| FutureMLV2 | -67.41% | 63.5% | 7622 | 熊市 |

## 常见问题

Q: 为什么回测收益和实盘不一样?
A: 回测有滑点和手续费模拟，实盘可能有更大滑点

Q: 可以用其他交易所吗?
A: 可以，修改config中的exchange配置

Q: 如何调整杠杆?
A: 修改策略中的leverage_config字典

Q: 亏损了怎么办?
A: 检查市场是否在趋势中，如果是继续运行，否则暂停策略
