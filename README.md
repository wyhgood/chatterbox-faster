# Chatterbox Faster Service

这是一个基于 FastAPI 的语音合成/处理后端服务。
本项目使用 **Supervisor** 进行进程守护，并实现了一套 **基于 Git 的音色自动同步机制**。

## 📂 目录结构

* **项目根目录**: `/root/chatterbox_fast`
* **Python 虚拟环境**: `/root/venv`
* **音色存放目录**: `/root/chatterbox_fast/voices` (自动生成/更新)
* **Supervisor 配置**: `/etc/supervisor/conf.d/chatterbox.conf`

---

## 🚀 核心机制：音色自动更新

本项目**不**直接启动 uvicorn，而是通过脚本 `start_simple.sh` 启动。

**启动流程如下：**
1.  **自动下载**: 脚本在 `/tmp` 创建临时目录，从 GitHub 仓库 `wyhgood/chatterbox-faster` 拉取最新代码。
2.  **自动同步**: 将仓库内的 `voices` 文件夹内容强制覆盖到本项目的 `voices` 目录。
3.  **自动清理**: 删除临时下载文件。
4.  **启动服务**: 启动 uvicorn 服务 (Host: 0.0.0.0, Port: 8004, Workers: 4)。

**✨ 如何添加新音色：**
1.  在本地将音频文件放入 `voices` 文件夹。
2.  Push 到 GitHub 仓库 (`wyhgood/chatterbox-faster`)。
3.  在服务器执行 `supervisorctl restart chatterbox` 即可生效。

---

## 🛠 部署指南

如果你迁移服务器或重新部署，请按以下步骤操作。

### 1. 准备环境
确保 Python 3.x 已安装，并创建虚拟环境：
```bash
# 假设项目代码已在 /root/chatterbox_fast
cd /root
python3 -m venv venv
source venv/bin/activate
pip install -r /root/chatterbox_fast/requirements.txt  # 如果有的话
pip install uvicorn fastapi  # 确保安装核心依赖
