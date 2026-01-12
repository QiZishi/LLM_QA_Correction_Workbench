---
license: Apache License 2.0
---

# 🎯 大模型问答数据校正工作台

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Gradio](https://img.shields.io/badge/Gradio-5.49.1-orange.svg)](https://gradio.app/)

一个专业的大模型问答数据人工校正工具，提供直观的可视化界面，帮助数据标注人员高效完成大模型训练数据的质量提升工作。

## ✨ 核心特性

### 🎨 **双阶段校正工作流**
- **阶段1：首次校正** - 在编辑器中直接修改问题和回答内容
- **阶段2：差异确认** - 可视化对比原始内容与校正内容的差异
  - 🔴 红色删除线：标记需要删除的错误内容
  - 🟢 绿色高亮：标记新增或修正的内容

### 📊 **批量数据管理**
- 支持 CSV 格式数据导入（instruction、output、chunk 三列）
- 智能批次加载，默认每批 50 条数据，可自定义配置
- 自动预加载机制：处理到当前批次最后 1 个样本时自动加载下一批
- 实时统计：待处理、已校正、已丢弃样本数量

### 🔄 **灵活的样本导航**
- 支持上一条/下一条按钮快速切换
- 点击样本列表直接跳转到任意样本
- 当前处理样本始终显示在列表顶部
- 已丢弃样本可重新加载并恢复

### 💾 **多格式数据导出**
支持 4 种主流大模型训练数据格式：
- **Messages 格式**：OpenAI 风格的对话格式
- **ShareGPT 格式**：常见的对话共享格式
- **Query-Response 格式**：简洁的问答对格式
- **Alpaca 格式**：Stanford Alpaca 数据格式

### ⏮️ **回溯功能**
- 支持上传之前导出的校正数据 JSON 文件
- 自动匹配并加载已校正样本
- 从第一个未处理样本继续校正，无需重新开始

### 🧮 **LaTeX 公式渲染**
- 支持 LaTeX 数学公式渲染（使用 KaTeX）
- 多 CDN 备用策略，确保稳定加载
- 自动识别并渲染 `$...$` 和 `$$...$$` 格式的公式

### 🎯 **智能差异算法**
- 基于 difflib 的智能文本对比
- 语义级别的分词，减少噪音
- 自动合并连续的修改标记
- 支持中英文混合文本

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动应用

```bash
python app.py
```

访问本地地址：`http://127.0.0.1:7860`

### 克隆项目

```bash
git clone https://www.modelscope.cn/studios/MoonNight/LLM_QA_Correction_Workbench.git
cd LLM_QA_Correction_Workbench
```

## 📖 使用指南

### 1️⃣ 准备数据

准备包含以下三列的 CSV 文件：
- **instruction**：问题文本
- **output**：回答文本
- **chunk**：参考内容

示例：
```csv
instruction,output,chunk
什么是机器学习？,机器学习是一种人工智能技术...,机器学习是人工智能的一个分支...
深度学习的应用有哪些？,深度学习广泛应用于...,深度学习在计算机视觉、自然语言处理...
```

### 2️⃣ 上传文件

1. 点击"📁 上传CSV文件"按钮
2. 选择准备好的 CSV 文件
3. 系统自动加载前 50 条数据（可在设置中调整）

### 3️⃣ 校正样本

**阶段1：首次校正**
- 在编辑框中修改问题和回答内容
- 点击"🔍 生成校正预览"进入下一阶段

**阶段2：确认差异**
- 查看差异对比，确认修改正确
- 点击"✅ 提交最终样本"保存
- 或点击"❌ 丢弃此样本"跳过

### 4️⃣ 导出数据

1. 完成所有样本校正
2. 在"⚙️ 设置"中选择导出格式
3. 点击"💾 导出已校正数据"
4. 在"📥 导出文件下载"框中下载文件

### 5️⃣ 回溯功能（可选）

如需继续之前的校正工作：
1. 点击"⏮️ 回溯已校正数据"按钮
2. 上传之前导出的 JSON 文件
3. 系统自动跳转到第一个未处理样本

## 🏗️ 项目架构

```
LLM_QA_Correction_Workbench/
├── app.py                    # 主应用入口
├── requirements.txt          # 依赖列表
├── pytest.ini               # 测试配置
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── sample.py           # Sample 数据类
│   └── application_state.py # 应用状态管理
├── services/               # 核心服务
│   ├── __init__.py
│   ├── data_manager.py     # CSV 数据加载与批次管理
│   ├── diff_engine.py      # 文本差异计算引擎
│   ├── render_engine.py    # HTML/LaTeX 渲染引擎
│   └── export_manager.py   # 数据导出管理
├── ui/                     # UI 组件
│   ├── __init__.py
│   ├── layout.py          # Gradio 界面布局
│   └── event_handlers.py  # 事件处理逻辑
├── utils/                 # 工具函数
│   ├── __init__.py
│   ├── validation.py      # 数据验证
│   └── performance.py     # 性能监控
└── tests/                # 测试套件
    ├── test_data_manager.py
    ├── test_diff_engine.py
    ├── test_export_manager.py
    ├── test_render_engine.py
    └── ...
```

## 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_diff_engine.py

# 查看测试覆盖率
pytest --cov=. --cov-report=html
```

## ⚙️ 配置说明

### 批次加载设置
在"⚙️ 设置"中可调整：
- **每批加载数量**：10-200 条（默认 50）
- **导出格式**：Messages/ShareGPT/Query-Response/Alpaca
- **自定义文件名**：可自定义导出文件名

### 自动加载机制
- 当处理到当前批次的最后 1 个样本时自动触发
- 如果剩余样本少于批次大小，加载所有剩余样本
- 适用于：点击样本、上一条/下一条、提交/丢弃后跳转

## 📝 数据格式说明

### 导出格式示例

**Messages 格式**
```json
{
  "messages": [
    {"role": "user", "content": "问题"},
    {"role": "assistant", "content": "回答"}
  ]
}
```

**ShareGPT 格式**
```json
{
  "conversations": [
    {"from": "human", "value": "问题"},
    {"from": "gpt", "value": "回答"}
  ]
}
```

**Query-Response 格式**
```json
{
  "query": "问题",
  "response": "回答"
}
```

**Alpaca 格式**
```json
{
  "instruction": "问题",
  "input": "",
  "output": "回答"
}
```

## 🔧 技术栈

- **前端框架**：Gradio 5.49.1
- **数据处理**：Pandas
- **文本对比**：difflib (Python 标准库)
- **LaTeX 渲染**：KaTeX 0.16.9
- **测试框架**：pytest + hypothesis
- **样式**：自定义 CSS（Times New Roman 字体，85% 缩放）

## 📊 性能特性

- ✅ 支持大文件处理（10 万字符以内）
- ✅ 批次加载减少内存占用
- ✅ 智能缓存提升响应速度
- ✅ 性能监控装饰器追踪关键操作

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

## 🙏 致谢

- [Gradio](https://gradio.app/) - 优秀的机器学习 Web UI 框架
- [KaTeX](https://katex.org/) - 快速的 LaTeX 数学公式渲染库
- [ModelScope](https://modelscope.cn/) - 模型托管与部署平台

## 📮 联系方式

- 项目地址：https://www.modelscope.cn/studios/MoonNight/LLM_QA_Correction_Workbench
- Issue 反馈：https://www.modelscope.cn/studios/MoonNight/LLM_QA_Correction_Workbench/issues

---

⭐ 如果这个项目对你有帮助，欢迎 Star 支持！