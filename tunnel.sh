#!/bin/bash
export PATH="/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin:/Users/wayne./.npm-global/bin"

LOG_DIR="/Users/wayne./project/hh-online/v0.4.1/logs"
mkdir -p "$LOG_DIR"

# 持续运行，后端挂了自动重连
while true; do
    # 等待后端就绪（最多等 30s）
    echo "[$(date)] 等待 v0.4.1 后端就绪 (port 8003)..." >> "$LOG_DIR/tunnel.log"
    for i in $(seq 1 15); do
        if curl -s http://localhost:8003/api/status > /dev/null 2>&1; then
            echo "[$(date)] v0.4.1 服务已就绪" >> "$LOG_DIR/tunnel.log"
            break
        fi
        sleep 2
    done

    echo "[$(date)] 启动 tunnel → port 8003" >> "$LOG_DIR/tunnel.log"
    lt --port 8003 --subdomain hunterhub >> "$LOG_DIR/tunnel.log" 2>&1 &
    LT_PID=$!

    TUNNEL_FAIL_COUNT=0
    CHECK_COUNT=0

    # 每 10 秒检查健康
    while kill -0 $LT_PID 2>/dev/null; do
        sleep 10
        CHECK_COUNT=$((CHECK_COUNT + 1))

        # 1. 本地后端检查
        if ! curl -s --max-time 5 http://localhost:8003/api/status > /dev/null 2>&1; then
            echo "[$(date)] ⚠️ 后端无响应，重启 tunnel..." >> "$LOG_DIR/tunnel.log"
            kill $LT_PID 2>/dev/null
            wait $LT_PID 2>/dev/null
            break
        fi

        # 2. 公网可达性检查（每 60s 一次，连续 2 次失败才重启）
        if [ $((CHECK_COUNT % 6)) -eq 0 ]; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
                -H "Bypass-Tunnel-Reminder: 1" \
                https://hunterhub.loca.lt/api/status 2>/dev/null)
            if [ "$HTTP_CODE" != "200" ]; then
                TUNNEL_FAIL_COUNT=$((TUNNEL_FAIL_COUNT + 1))
                echo "[$(date)] ⚠️ 公网不可达 (HTTP $HTTP_CODE)，连续失败 $TUNNEL_FAIL_COUNT/2" >> "$LOG_DIR/tunnel.log"
                if [ $TUNNEL_FAIL_COUNT -ge 2 ]; then
                    echo "[$(date)] 🔄 公网连续2次不可达，重启 tunnel..." >> "$LOG_DIR/tunnel.log"
                    kill $LT_PID 2>/dev/null
                    wait $LT_PID 2>/dev/null
                    break
                fi
            else
                # 公网正常，重置计数器
                if [ $TUNNEL_FAIL_COUNT -gt 0 ]; then
                    echo "[$(date)] ✅ 公网已恢复" >> "$LOG_DIR/tunnel.log"
                fi
                TUNNEL_FAIL_COUNT=0
            fi
        fi
    done

    # lt 进程异常退出也重新来
    wait $LT_PID 2>/dev/null
    echo "[$(date)] tunnel 已退出，5s 后重试..." >> "$LOG_DIR/tunnel.log"
    sleep 5
done
