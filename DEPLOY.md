# 部署指南 - 老年陪伴 Agent

本项目是一个基于 Streamlit 的 Web 应用。为了让互联网上的用户能够访问，最推荐的部署方案是使用 **Streamlit Community Cloud**。

## 方案优势
1.  **免费托管**：Streamlit 官方提供免费的社区云服务。
2.  **自动 HTTPS**：浏览器录音功能（麦克风权限）强制要求 HTTPS 环境，Streamlit Cloud 自动提供 HTTPS 证书，无需自行配置。
3.  **一键部署**：直接连接 GitHub 仓库即可部署。

## 部署步骤

### 0. 先决条件
由于你的本地环境似乎没有安装 Git，你需要先安装它：
*   **下载 Git**: 访问 [git-scm.com](https://git-scm.com/download/win) 下载并安装 Windows 版本。
*   安装时一路默认点击 "Next" 即可。
*   安装完成后，**重启**你的终端或编辑器，输入 `git --version` 确认安装成功。

### 1. 准备 GitHub 仓库
你需要将当前项目上传到 GitHub。
1.  登录 [GitHub](https://github.com/) 并创建一个新的仓库（Repository），例如命名为 `oldperson-agent`。
2.  在项目根目录（`C:\Users\Administrator\Documents\trae_projects\oldpersonAgents`）打开终端，执行以下命令：

    ```bash
    # 初始化 Git 仓库
    git init

    # 添加所有文件
    git add .

    # 提交代码
    git commit -m "Initial commit"

    # 将分支重命名为 main
    git branch -M main

    # 关联远程仓库 (请将 URL 替换为你刚才创建的仓库地址)
    git remote add origin https://github.com/你的用户名/oldperson-agent.git

    # 推送到 GitHub
    git push -u origin main
    ```
    *(注意：我已经为你创建了 `.gitignore` 文件，它会自动忽略 `memories.db`, `.env` 等敏感文件，请放心提交)*

### 2. 在 Streamlit Cloud 上部署
1.  访问 [share.streamlit.io](https://share.streamlit.io/) 并使用 GitHub 账号登录。
2.  点击右上角的 **"New app"** 按钮。
3.  选择刚才创建的 GitHub 仓库 (`oldperson-agent`)。
4.  配置部署信息：
    *   **Repository**: `你的用户名/oldperson-agent`
    *   **Branch**: `main`
    *   **Main file path**: `web_app.py`
5.  点击 **"Deploy!"**。

### 3. 配置环境变量 (Secrets)
项目运行需要阿里云和 DashScope 的 API Key，这些不能直接写在代码里，需要在 Streamlit Cloud 的后台配置。

1.  在部署好的应用页面，点击右下角的 **"Manage app"** 按钮（或右上角的三个点 -> Settings -> Secrets）。
2.  在 **"Secrets"** 文本框中，粘贴 `.env` 文件中的内容（格式如下）：
    ```toml
    # 注意：Streamlit Secrets 使用 TOML 格式
    DASHSCOPE_API_KEY = "sk-..."
    ALIYUN_TOKEN = "..."
    ALIYUN_APPKEY = "..."
    # 其他在 .env 中的变量
    ```
3.  点击 **"Save"**。

### 4. 等待构建完成
Streamlit Cloud 会自动读取 `requirements.txt` 安装依赖。由于我们使用了本地的 `nls` SDK，`requirements.txt` 已经配置了从 `./libs/...` 安装，这应该能自动处理。

构建完成后，你将获得一个 `https://oldperson-agent-xxx.streamlit.app` 的访问链接，可以直接分享给其他人使用。

## 常见问题
*   **录音无法启动**：请确保通过 `https` 协议访问（Streamlit Cloud 默认支持）。
*   **数据持久化**：Streamlit Cloud 的文件系统是临时的，重启后 `memories.db` 会被重置。如果需要长期保存对话历史，需要对接云数据库（如 Supabase 或 AWS RDS）。目前演示版本使用本地 SQLite，数据不会在重启后保留。
