#!/bin/bash
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/Users/wayne./.npm-global/bin"

LOG_DIR="/Users/wayne./project/hh-online/v0.2.4/logs"
mkdir -p "$LOG_DIR"

# 持续运行，后端挂了自动重连
while true; do
    # 等待后端就绪（最多等 30s）
    echo "[$(date)] 等待 v0.2.4 后端就绪 (port 8003)..." >> "$LOG_DIR/tunnel.log"
    for i in $(seq 1 15); do
        if curl -s http://localhost:8003/api/status > /dev/null 2>&1; then
            echo "[$(date)] v0.2.4 服务已就绪" >> "$LOG_DIR/tunnel.log"
            break
        fi
        sleep 2
    done

    echo "[$(date)] 启动 tunnel → port 8003" >> "$LOG_DIR/tunnel.log"
    lt --port 8003 --subdomain hunterhub >> "$LOG_DIR/tunnel.log" 2>&1 &
    LT_PID=$!

    # 每 10 秒检查后端健康，挂了就重启 tunnel
    while kill -0 $LT_PID 2>/dev/null; do
        sleep 10
        if ! curl -s --max-time 5 http://localhost:8003/api/status > /dev/null 2>&1; then
            echo "[$(date)] ⚠️ 后端无响应，重启 tunnel..." >> "$LOG_DIR/tunnel.log"
            kill $LT_PID 2>/dev/null
            wait $LT_PID 2>/dev/null
            break
        fi
    done

    # lt 进程异常退出也重新来
    wait $LT_PID 2>/dev/null
    echo "[$(date)] tunnel 已退出，5s 后重试..." >> "$LOG_DIR/tunnel.log"
    sleep 5
done
