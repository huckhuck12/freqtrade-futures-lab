#!/bin/bash

# Freqtrade Futures Leveraged Strategy Launcher
# 适用于 OKX 交易所

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Freqtrade Futures Leveraged Strategy${NC}"
echo "============================================"

# 检查API密钥
if [ -z "$OKX_API_KEY" ] || [ -z "$OKX_API_SECRET" ] || [ -z "$OKX_API_PASSPHRASE" ]; then
    echo -e "${YELLOW}⚠️  请设置环境变量:${NC}"
    echo "export OKX_API_KEY=\"your_api_key\""
    echo "export OKX_API_SECRET=\"your_api_secret\""
    echo "export OKX_API_PASSPHRASE=\"your_passphrase\""
    echo ""
fi

# 命令选择
case "${1:-help}" in
    backtest)
        echo -e "${GREEN}📊 运行回测...${NC}"
        docker run --rm \
            -v $(pwd)/user_data:/freqtrade/user_data \
            freqtradeorg/freqtrade:develop backtesting \
            --config user_data/config/highfreq-config.json \
            --strategy-path user_data/strategies \
            --strategy FutureBuyHoldV2 \
            --timerange 20240101-20240301
        ;;
    download)
        echo -e "${GREEN}📥 下载数据...${NC}"
        docker run --rm \
            -v $(pwd)/user_data:/freqtrade/user_data \
            freqtradeorg/freqtrade:develop download-data \
            --config user_data/config/live-leveraged-config.json \
            --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT XRP/USDT:USDT DOGE/USDT:USDT \
            --timeframe 1m
        ;;
    trade)
        echo -e "${GREEN}🎯 启动实盘交易...${NC}"
        docker run -d \
            --name freqtrade-leveraged \
            -v $(pwd)/user_data:/freqtrade/user_data \
            -e OKX_API_KEY \
            -e OKX_API_SECRET \
            -e OKX_API_PASSPHRASE \
            freqtradeorg/freqtrade:develop trade \
            --config user_data/config/live-leveraged-config.json \
            --strategy-path user_data/strategies \
            --strategy FutureBuyHoldV2
        echo -e "${GREEN}✅ 实盘已启动${NC}"
        ;;
    stop)
        echo -e "${YELLOW}🛑 停止交易...${NC}"
        docker stop freqtrade-leveraged && docker rm freqtrade-leveraged
        echo -e "${GREEN}✅ 已停止${NC}"
        ;;
    logs)
        docker logs -f freqtrade-leveraged
        ;;
    status)
        docker exec freqtrade-leveraged curl -s http://localhost:8080/api/v1/status
        ;;
    profit)
        docker exec freqtrade-leveraged curl -s http://localhost:8080/api/v1/profit
        ;;
    help|*)
        echo -e "${GREEN}用法:${NC} ./run.sh [命令]"
        echo ""
        echo "命令:"
        echo "  backtest  - 运行回测"
        echo "  download  - 下载数据"
        echo "  trade     - 启动实盘交易"
        echo "  stop      - 停止交易"
        echo "  logs      - 查看日志"
        echo "  status    - 查看状态"
        echo "  profit    - 查看收益"
        echo "  help      - 显示帮助"
        ;;
esac
