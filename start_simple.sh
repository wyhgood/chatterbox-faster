#!/bin/bash

# === 配置 ===
TEMP_DIR="/tmp/voice_update_$(date +%s)"
TARGET_DIR="/root/chatterbox_fast/voices"
REPO="https://github.com/wyhgood/chatterbox-faster.git"

echo ">>> [Step 1] 下载最新音色..."
# --depth 1 表示只克隆最近一次提交，速度最快，不下载历史记录
git clone --depth 1 "$REPO" "$TEMP_DIR"

# 检查是否下载成功且存在 voices 目录
if [ -d "$TEMP_DIR/voices" ]; then
    echo ">>> [Step 2] 发现 voices 文件夹，正在覆盖更新..."
    
    # 确保目标文件夹存在
    mkdir -p "$TARGET_DIR"
    
    # 强制复制 (-f) 并递归 (-r)
    # 这会将临时目录下的 voices 里的所有文件扔到目标目录里
    cp -rf "$TEMP_DIR/voices/"* "$TARGET_DIR/"
    
    echo ">>> 更新完成。"
else
    echo ">>> 警告：下载失败或仓库中无 voices 目录，跳过更新。"
fi

# === 清理现场 ===
echo ">>> [Step 3] 清理临时文件..."
rm -rf "$TEMP_DIR"

# === 启动服务 ===
echo ">>> [Step 4] 启动 Uvicorn..."
# 必须用 exec，这样 Supervisor 才能接管 uvicorn 的进程ID
exec /root/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8004 --workers 2
