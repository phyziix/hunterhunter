#!/bin/bash
set -e

# deploy.sh - hunterhunter 轻量级部署脚本
# 用法: bash deploy.sh <新版本号> <旧版本号>
# 示例: bash deploy.sh v0.4.1 v0.4.0
#
# 负责确定性操作（备份/验证/迁移/重启）。
# AI 仍负责：场景判断、目录创建、代码部署、配置修改、文档更新、隧道切换。
# 详见 docs/AI_WORKFLOW.md 部署规则。

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }

# ========== 参数检查 ==========
if [ $# -ne 2 ]; then
    echo "用法: bash deploy.sh <新版本号> <旧版本号>"
    echo "示例: bash deploy.sh v0.4.1 v0.4.0"
    exit 1
fi

NEW_VER="$1"
OLD_VER="$2"

# ========== 环境变量检查 ==========
if [ -z "$PRODUCTION" ]; then
    log_error "环境变量 PRODUCTION 未设置。"
    echo "请先设置: export PRODUCTION=/Users/xxx/project/hh-online"
    exit 1
fi

PROD_OLD="${PRODUCTION}/${OLD_VER}"
PROD_NEW="${PRODUCTION}/${NEW_VER}"
BACKUP_ROOT="$HOME/Documents/hunterhunter_backups"
BACKUP_PATH="${BACKUP_ROOT}/pre_deploy_$(date +%Y%m%d_%H%M%S)"
PLIST="com.phyziix.hunterhunter-${NEW_VER}.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VERIFY_SCRIPT="${SCRIPT_DIR}/verify_deployment.py"

echo "=========================================="
echo "  hunterhunter 部署脚本"
echo "  ${OLD_VER} → ${NEW_VER}"
echo "  生产目录: ${PRODUCTION}"
echo "=========================================="
echo ""

# ========== Step 1: 备份旧版本数据 ==========
log_info "Step 1/6: 备份旧版本数据..."
if [ ! -d "$PROD_OLD" ]; then
    log_error "旧版本目录不存在: ${PROD_OLD}"
    exit 1
fi
mkdir -p "$BACKUP_ROOT"
cp -r "${PROD_OLD}/data/" "$BACKUP_PATH"
log_info "备份完成: ${BACKUP_PATH}"

# ========== Step 2: 验证旧环境 ==========
log_info "Step 2/6: 验证旧环境数据完整性..."
python3 "$VERIFY_SCRIPT" --source "${PROD_OLD}/data/inspire"
log_info "旧环境验证通过"

# ========== Step 3: 迁移灵感文件 ==========
log_info "Step 3/6: 迁移灵感文件..."
if [ ! -d "$PROD_NEW" ]; then
    log_error "新版本目录不存在: ${PROD_NEW}"
    log_error "请先由 AI 完成目录创建和代码部署后，再运行本脚本。"
    exit 1
fi
mkdir -p "${PROD_NEW}/data/inspire/Inbox"
if ls "${PROD_OLD}/data/inspire/Inbox/"灵感-*.md 1>/dev/null 2>&1; then
    cp "${PROD_OLD}/data/inspire/Inbox/"灵感-*.md "${PROD_NEW}/data/inspire/Inbox/"
    count=$(ls "${PROD_NEW}/data/inspire/Inbox/"灵感-*.md 2>/dev/null | wc -l | tr -d ' ')
    log_info "已迁移 ${count} 个灵感文件"
else
    log_warn "无旧版本灵感文件，跳过"
fi

# ========== Step 4: 验证新环境 ==========
log_info "Step 4/6: 验证新环境数据完整性..."
python3 "$VERIFY_SCRIPT" --source "${PROD_NEW}/data/inspire"
log_info "新环境验证通过"

# ========== Step 5: 重启服务 ==========
log_info "Step 5/6: 重启服务..."

# 停止旧版本服务（如果存在）
OLD_PLIST="com.phyziix.hunterhunter-${OLD_VER}.plist"
OLD_PLIST_PATH="$HOME/Library/LaunchAgents/${OLD_PLIST}"
if [ -f "$OLD_PLIST_PATH" ]; then
    launchctl unload "$OLD_PLIST_PATH" 2>/dev/null || true
    log_info "已卸载旧服务: ${OLD_PLIST}"
fi

# 启动新版本服务
if [ -f "$PLIST_PATH" ]; then
    launchctl load "$PLIST_PATH"
    sleep 2
    if launchctl list | grep -q "hunterhunter-${NEW_VER}"; then
        log_info "新服务已启动: ${PLIST}"
    else
        log_error "服务启动失败，请检查 ${PLIST_PATH}"
        exit 1
    fi
else
    log_warn "plist 文件不存在: ${PLIST_PATH}（请由 AI 先创建 plist）"
fi

# ========== Step 6: 输出结果 ==========
echo ""
echo "=========================================="
log_info "部署脚本执行完毕"
echo "  备份位置: ${BACKUP_PATH}"
echo "  旧版本:   ${PROD_OLD}"
echo "  新版本:   ${PROD_NEW}"
echo "=========================================="
echo ""
log_info "后续步骤（由 AI 完成）："
echo "  - curl http://localhost:8003/api/version  确认版本"
echo "  - launchctl unload/load tunnel plist      重启隧道"
echo "  - 更新 docs/DEPLOYMENT.md 版本状态"
echo "  - 执行「同步文档」规则"
