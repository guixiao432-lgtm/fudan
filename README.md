# Fudan Grade Monitor (复旦成绩监控助手) 🎓

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

一个基于 Python + Selenium 的复旦大学教务系统成绩监控工具。支持 GUI 图形界面、后台静默运行、成绩自动对比以及微信推送通知。


## ✨ 功能特性

* **图形化界面 (GUI)**：基于 Tkinter 开发，操作简单直观。
* **双模式运行**：支持“可视化模式”（显示浏览器）和“后台静默模式”（无打扰）。
* **自动登录**：内置智能登录逻辑，支持 XPath 精准定位。
* **成绩推送**：集成 Pushplus，成绩更新时通过微信实时通知。
* **数据大屏**：直观展示总 GPA、专业排名以及单科成绩（含绩点）。
* **隐私安全**：所有账号密码仅保存在本地 `user_config.json`，不上传云端。

## 🛠️ 安装与运行 (源码方式)

如果你想直接运行源码，请确保已安装 [Google Chrome](https://www.google.com/chrome/) 浏览器。

1.  **克隆仓库**
    ```bash
    git clone [https://github.com/guixiao432-lgtm/fudan.git](https://github.com/guixiao432-lgtm/fudan.git)
    cd fudan-grade-monitor
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行程序**
    ```bash
    python gui_main.py
    ```

## 📦 下载可执行文件 (.exe)

不想安装 Python？可以直接下载打包好的程序：

1.  进入本仓库的 [**Releases**](https://github.com/你的用户名/fudan-grade-monitor/releases) 页面。
2.  下载最新的 `复旦查分神器.exe`。
3.  双击即可运行（首次运行会自动生成配置文件）。

## ⚙️ 配置说明

首次运行后，程序会在同目录下生成以下文件：
* `user_config.json`: 存储学号、密码、Pushplus Token。
* `grade_history.json`: 存储历史成绩数据，用于对比更新。

## ⚠️ 免责声明

本项目仅供学习交流使用。请勿用于高频恶意抓取，遵守学校教务系统使用规范。开发者不对使用本软件产生的任何后果负责。

---
Made with ❤️ by Liangliang