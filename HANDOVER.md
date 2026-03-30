# HANDOVER（第一次会话交接文档）

## 1. 项目背景与目标
- **项目目标**：构建金融资讯智能体，完成“网页抓取 -> AI分析 -> 数据入库 -> API输出 -> 前端展示”闭环。
- **当前阶段**：后端核心能力已完成并联调通过，处于“从可用到可扩展”阶段。
- **已完成里程碑**：
  - 完成 PRD 与架构文档（`docs/PRD.md`、`docs/Architecture.md`）。
  - 完成 FastAPI + MySQL 基础工程搭建。
  - 完成 Jina Reader 抓取服务与通义千问分析服务。
  - 完成核心业务链路 `POST /news/ingest`（抓取+分析+入库一体化）。
  - 完成端到端验证（HTTP 200 + MySQL 落库成功）。

## 2. 当前任务与进度
### 最近会话处理模块
- **核心业务编排模块**（`backend/services/pipeline.py`）
- **统一入口接口**（`backend/api/news.py` -> `POST /news/ingest`）
- **长文本入库修复**（`news.content_md` 改为 LONGTEXT）

### 已完成子任务
- [x] 接入 Jina Reader 并可返回 Markdown 正文
- [x] 接入通义千问（DashScope 兼容接口）并输出结构化 JSON
- [x] 统一编排抓取、分析、入库流程
- [x] 新增 `PipelineRequest/PipelineResponse` 数据模型
- [x] 修复 `content_md` 字段长度不足导致的入库失败
- [x] 本地接口调用验证与数据库结果核验

### 未完成部分
- [ ] 批量 URL 抓取与批量分析接口
- [ ] 定时调度（每日自动抓取）
- [ ] 失败重试、审计日志、可观测性
- [ ] 前端 Dashboard 联调

### 下一步最高优先级任务（P0）
- **实现批量任务接口**（一次提交多个 URL，支持并发抓取与逐条分析入库，返回任务结果汇总）。

## 3. 技术栈与架构
### 编程语言与框架
- Python 3.9（venv）
- FastAPI（后端 API）
- SQLAlchemy（ORM）
- LangChain（LLM 调用编排）

### 数据库
- MySQL（DataGrip 管理）

### 第三方服务
- Jina Reader（网页正文提取）
- 通义千问（DashScope OpenAI 兼容接口）

### 当前关键依赖版本（已安装环境）
- fastapi `0.128.8`
- uvicorn `0.39.0`
- sqlalchemy `2.0.48`
- requests `2.32.5`
- langchain `0.3.28`
- langchain-openai `0.3.35`
- dashscope `1.25.15`
- pymysql `1.1.2`

> 说明：`backend/requirements.txt` 当前是“未锁定版本”写法，建议后续补充锁定版本文件（如 `requirements-lock.txt`）。

## 4. 环境变量清单
| 变量名 | 用途 | 示例值 | 是否必需 | 当前状态 | 环境差异说明 |
|---|---|---|---|---|---|
| `DB_USER` | MySQL 用户名 | `root` | 是 | 已配置（`.env`） | 本地/测试/生产可能不同 |
| `DB_PASSWORD` | MySQL 密码 | `***` | 是 | 已配置（`.env`） | 强烈建议生产使用密钥管理 |
| `DB_HOST` | MySQL 主机 | `127.0.0.1` | 是 | 已配置（`.env`） | 生产通常为内网地址/服务名 |
| `DB_PORT` | MySQL 端口 | `3306` | 是 | 已配置（`.env`） | 一般一致 |
| `DB_NAME` | 业务数据库名 | `financial_agent_db` | 是 | 已配置（`.env`） | 各环境库名可区分 |
| `DASHSCOPE_API_KEY` | 通义千问 API Key | `sk-xxxx` | 是 | 已配置（系统环境变量） | 各环境必须独立 Key |

> 可选扩展：`JINA_API_KEY`（若使用 Jina 付费/鉴权模式，当前代码可扩展接入，匿名模式在部分域名会被风控）。

## 5. 本地开发指引
### 5.1 克隆与进入目录
```bash
git clone <repo-url>
cd 爬虫智能机器人
```

### 5.2 后端环境准备
```bash
cd backend
python -m venv venv
.\venv\Scripts\python -m pip install -r requirements.txt
.\venv\Scripts\python -m pip install langchain-openai dashscope
```

### 5.3 数据库准备
1. 确保本地 MySQL 已启动。
2. 在 `backend/.env` 配置 DB 参数。
3. 启动服务时会自动：
   - `Base.metadata.create_all(...)` 创建缺失表
   - 执行 `ALTER TABLE news MODIFY content_md LONGTEXT NULL` 修复字段类型

### 5.4 启动服务
```bash
cd backend
.\venv\Scripts\uvicorn main:app --reload --port 8000
```

### 5.5 访问地址
- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`GET /ping`
- 核心接口：`POST /news/ingest`

### 5.6 常见问题排查
- **Unknown database**：确认数据库已创建且 `DB_NAME` 正确。
- **Data too long for column content_md**：确认 `news.content_md` 为 `LONGTEXT`（服务启动会自动修复）。
- **Jina 451/风控**：目标站点可能限制匿名抓取，改用可访问来源或接入 Jina Key。
- **LLM 调用失败**：检查 `DASHSCOPE_API_KEY` 是否在系统环境变量中生效。

## 6. 分支与版本策略
- **当前工作分支**：`master`
- **最近一次已提交 commit**：`a4877e6a54b7cac365ca9de93b483a2f83326394`
- **最近一次提交信息**：`feat: 增加MySQL数据库连接配置，定义News与Analysis数据模型并创建测试API`
- **建议分支规范（后续执行）**：
  - 功能分支：`feature/<module>-<short-desc>`
  - 修复分支：`fix/<issue>-<short-desc>`
  - 提交信息：继续使用中文，格式建议 `feat|fix|refactor: 描述`
- **合并流程建议**：
  1. `master` 拉最新
  2. 新建功能分支开发
  3. 本地自测通过后发起 PR
  4. 通过后 Squash Merge 到 `master`

## 7. 测试与验收标准
### 当前可用测试命令（手动）
```bash
cd backend
.\venv\Scripts\python test_scraper.py
.\venv\Scripts\python test_ai.py
```

### 集成验收命令（示例）
```bash
cd backend
.\venv\Scripts\python -c "import requests; payload={'url':'https://en.wikipedia.org/wiki/Stock_market','source':'wikipedia'}; r=requests.post('http://127.0.0.1:8000/news/ingest', json=payload, timeout=120); print(r.status_code); print(r.text)"
```

### 覆盖率要求
- 当前阶段：**未建立自动化单元测试与覆盖率门槛**（待建设）。
- 建议目标：核心服务层（`services/`）覆盖率不低于 70%。

### 功能验收 Checklist
- [ ] `/ping` 返回 200
- [ ] `/news/ingest` 对可访问 URL 返回 200
- [ ] 返回体包含 `summary/impact_assessment/affected_sectors/logical_reasoning`
- [ ] `news` 表有对应记录
- [ ] `analysis` 表有对应记录且 `news_id` 正确关联

## 8. 风险与待决策事项
| 项目 | 描述 | 优先级 | 截止日期 | 责任建议 |
|---|---|---|---|---|
| Jina 匿名风控 | Yahoo/Reuters 等域名可能 451，影响抓取稳定性 | P0 | 2026-03-31 | 接入 Jina Key + 备用源策略 |
| 缺少批处理能力 | 仅支持单 URL，无法满足每日批量资讯处理 | P0 | 2026-04-01 | 新增批量任务接口 |
| 缺少定时调度 | 尚未自动执行每日抓取与分析 | P1 | 2026-04-02 | 接入 APScheduler |
| 缺少自动化测试 | 回归风险高，交付质量难量化 | P1 | 2026-04-03 | 增加 pytest + 集成测试 |
| 依赖未锁版本 | 环境复现存在漂移风险 | P2 | 2026-04-03 | 生成锁定依赖文件 |

## 9. 新会话快速上手检查单（必须按顺序）
1. **环境验证**
   - 检查 Python / MySQL / venv 可用
   - 校验 `DASHSCOPE_API_KEY` 是否生效
2. **拉取最新代码**
   - `git pull origin master`
   - 查看是否有未提交本地改动
3. **更新依赖**
   - `pip install -r backend/requirements.txt`
   - 补装 `langchain-openai`、`dashscope`（若缺失）
4. **运行测试**
   - 运行 `test_scraper.py`、`test_ai.py`
   - 启动 FastAPI 并调用 `POST /news/ingest`
5. **功能验证后再继续编码**
   - 确认 HTTP 200 与 MySQL 落库
   - 再进入下一功能开发（优先：批量任务接口）

---

## 附：关键代码入口
- 后端入口：`backend/main.py`
- 统一接口：`backend/api/news.py`
- 核心编排：`backend/services/pipeline.py`
- 爬虫服务：`backend/services/scraper.py`
- AI 服务：`backend/services/ai_agent.py`
- 数据模型：`backend/models/news.py`、`backend/models/analysis.py`
