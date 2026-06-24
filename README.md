# 知乎评论整合

抓取知乎文章评论，分析评论内容，生成高质量文章。

## 功能

1. **评论抓取**：使用 Playwright 抓取指定知乎链接的评论
2. **评论分析**：情感分析、关键词提取、观点聚类
3. **文章生成**：基于分析结果生成结构化文章

## 技术栈

- **抓取**：Python + Playwright（处理反爬虫）
- **分析**：Pandas + NLP（jieba、snownlp）
- **生成**：模板化生成 / 可选接入 AI API

## 安装

```bash
pip install -r requirements.txt
playwright install
```

## 安全使用指南

**重要：为避免IP被封，请遵循以下原则：**

### 核心安全特性

1. **代理IP轮换**：支持自定义代理列表和免费代理API
2. **反检测机制**：隐藏浏览器指纹，模拟真实用户行为
3. **智能延迟**：随机请求间隔，避免固定模式
4. **请求限制**：每日请求上限，自动冷却机制
5. **验证码处理**：自动检测并等待人工处理
6. **重试机制**：失败自动重试，避免频繁请求

### 代理配置

编辑 `config/settings.json`：

```json
{
  "proxy": {
    "enabled": true,
    "proxy_list": [
      "http://proxy1:8080",
      "http://proxy2:8080"
    ],
    "use_free_api": true,
    "proxy_timeout": 10
  }
}
```

### 验证代理

```bash
python main.py --url "https://example.com" --validate-proxy
```

### 高级安全配置

```json
{
  "detection": {
    "enable_stealth": true,
    "enable_verification_check": true,
    "humanize_behavior": true
  },
  "limits": {
    "max_comments": 500,
    "daily_limit": 1000,
    "cooldown_minutes": 30,
    "max_retries": 3
  }
}
```

## 使用

### 图形界面（推荐）

```bash
# 启动配置页面
python start_config.py

# 或双击运行
启动配置页面.bat
```

访问 http://localhost:8501 进行可视化配置。

### 命令行

```bash
# 基本使用
python main.py --url "https://zhuanlan.zhihu.com/p/123456789"

# 检查配置
python main.py --url "https://example.com" --check-config

# 验证代理
python main.py --url "https://example.com" --validate-proxy

# 指定输出和评论数
python main.py --url "https://zhuanlan.zhihu.com/p/123456789" --output result.md --max-comments 200
```

## 项目结构

```
Zhihu-comments-integration/
├── src/                        # 源代码目录
│   ├── scraper/                # 抓取模块
│   │   ├── __init__.py
│   │   ├── zhihu_api.py        # 知乎API抓取器（推荐）
│   │   ├── zhihu_scraper.py    # 浏览器抓取器（备用）
│   │   ├── anti_detection.py   # 反检测模块
│   │   └── proxy_manager.py    # 代理管理器
│   ├── analyzer/               # 分析模块
│   │   ├── __init__.py
│   │   └── comment_analyzer.py # 评论分析器
│   └── generator/              # 生成模块
│       ├── __init__.py
│       └── article_generator.py # 文章生成器
├── config/                     # 配置文件
│   ├── settings.json           # 主配置
│   ├── cookie.txt              # 知乎Cookie（需自行获取）
│   ├── stopwords.txt           # 停用词表
│   └── proxy_sources.json      # 代理源配置
├── scripts/                    # 脚本文件
│   ├── app.py                  # Web配置界面
│   └── start_config.py         # 配置界面启动器
├── tests/                      # 测试目录
│   ├── __init__.py
│   └── test_core.py            # 核心功能测试
├── docs/                       # 文档目录
│   └── PRD.md                  # 产品需求文档
├── main.py                     # 主入口
├── pyproject.toml              # 项目配置
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明
```

## 配置页面功能

1. **代理配置**：可视化配置代理，支持免费API和自定义列表
2. **抓取设置**：调整延迟、超时、反检测等参数
3. **测试抓取**：在线测试抓取功能
4. **日志查看**：实时查看抓取日志

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. **启动配置页面**
   ```bash
   python start_config.py
   ```

3. **配置代理**
   - 访问 http://localhost:8501
   - 选择"代理配置"
   - 启用代理并保存

4. **测试抓取**
   - 选择"测试抓取"
   - 输入知乎链接
   - 点击"开始测试"

5. **正式使用**
   ```bash
   python main.py --url "https://zhuanlan.zhihu.com/p/123456789" --output result.md
   ```

## 风险提示

- 本工具仅供学习研究使用
- 请遵守知乎服务条款
- 高频抓取可能导致IP被封
- 建议使用代理并控制抓取频率
- 首次使用建议先测试少量评论