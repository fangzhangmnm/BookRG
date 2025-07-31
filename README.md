# 🐉 小说大纲自动生成器（Book-RG）使用说明

> 📖 把你的网络小说 TXT 自动变成结构化大纲 + 网页预览！

---

## ✨ 我能拿它来干嘛？

* 你有一份长篇 TXT 小说？
* 想快速生成一份**自动分章的大纲摘要**？
* 想一键出结构图，不用人工标章节？

🎉 那你来对地方了！

---

## 🧩 第一步：准备文件和安装工具（只需要一次）

### ✅ 1. 下载本项目

1. 打开这个网站地址：[https://github.com/xxx/book-rg](https://github.com/xxx/book-rg)
2. 点击绿色的【Code】，选择【Download ZIP】
3. 解压到桌面（或任何你能找到的文件夹）

---

### ✅ 2. 安装 Python（翻译：帮你打开这个工具）

1. 打开这个网址：[https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
2. 点击【Download Python 3.xx】
3. 双击安装程序，一定要**勾选 Add Python to PATH**
4. 一路点击【Next】直到安装完成
5. 验证方法：

   * 点开始菜单 > 输入“cmd”回车
   * 输入：

     ```
     python --version
     ```
   * 如果看到类似 `Python 3.12.1` 就成功啦！

---

### ✅ 3. 安装支持库

1. 在开始菜单里打开命令行（cmd）
2. 输入以下两行（注意空格）：

   ```bat
   cd 桌面\book-rg
   pip install -r requirements.txt
   ```

---

## 🌐 第二步：准备访问模型（需要 API Key）

> 本工具使用智能大模型（像 ChatGPT）来自动分析你的小说，所以你需要一个**通行证（API Key）**

### ✅ 我们推荐使用 DeepSeek

#### 申请步骤：

1. 打开：[https://platform.deepseek.com/](https://platform.deepseek.com/)
2. 注册/登录账号
3. 点击右上角头像 → API Key → 生成新的 Key
4. 复制它（形如 `sk-xxxxx`）

#### 设置 Key（告诉程序你是谁）

1. 复制你的 API Key

   * 登录 [DeepSeek 平台](https://platform.deepseek.com)
   * 点击右上角头像 → API Key → 生成新的 key
   * 点击【复制】

2. 打开系统环境变量设置

   * 在【开始菜单】搜索 **环境变量** 或 **编辑系统环境变量**
   * 点击【环境变量...】按钮

3. 新增用户变量

   * 在“用户变量”区域点击【新建】
   * 变量名填：`DEEPSEEK_API_KEY`
   * 变量值粘贴你刚才复制的 key（形如 `sk-xxxxx`）
   * 点击【确定】

4. 关闭所有窗口并重新打开命令行窗口

> 💡 注意：你必须**重新打开命令行窗口**，才能让新设置生效！

---

## 🧙‍♂️ 第三步：运行小说分析

1. 把你的小说 TXT 文件放到 `book-rg` 文件夹中（例如 `修仙之路.txt`）**请保证你的小说是utf-8编码的！**

2. 在命令行输入：

   ```bat
   python book_rg.py 修仙之路.txt --model_1 deepseek-chat --model_2 deepseek-reasoner --base_url https://api.deepseek.com/v1 --api_key_environ DEEPSEEK_API_KEY
   ```

3. 等待几分钟……⏳

---

## 📂 第四步：查看大纲结果

分析完毕后，你会在原文件夹中看到这些文件：

| 文件         | 说明               |
| ---------- | ---------------- |
| 修仙之路.html  | 用浏览器打开即可，章节层级可折叠 |
| 修仙之路.json  | 高级用户可用于程序分析（可忽略） |
| 修仙之路\_data | 中间过程（可忽略或删掉）     |

---

## ❤️ 鸣谢

本工具基于：

* `batchfactory`（AI 批处理框架）
* `DeepSeek` 大模型平台