# 金融资讯智能分析系统 - 技术架构文档 (Architecture)

## 1. 系统总体架构图
```text
[ 前端 (Next.js/React) ]  <--- REST API --->  [ 后端服务 (Python FastAPI) ]
       (Dashboard)                                   |
                                                     |
                                          [ 智能代理层 (LangChain) ]
                                            /                  \
                                           /                    \
                         [ 爬虫 API (Jina Reader) ]      [ 大模型 API (通义千问) ]
                                 |
                         [ 目标财经网站 ]

[ 数据库 (MySQL) ] <----------------------- 后端服务存取数据
 (DataGrip 管理)
```

## 2. 技术栈详细选型

### 2.1 前端展示层 (Frontend)
- **框架**：Next.js
- **UI 组件库**：Tailwind CSS + Shadcn UI

### 2.2 后端服务层 (Backend)
- **框架**：FastAPI (Python)
- **核心职责**：提供 RESTful 接口，处理前端请求和业务逻辑，集成 `APScheduler` 执行定时任务。

### 2.3 智能代理层 (Agent Layer)
- **框架**：LangChain (Python)
- **爬虫模块**：Jina Reader API
- **LLM 模块**：通义千问 API (Zero-shot / Few-shot Prompting)

### 2.4 数据持久层 (Database)
- **数据库**：**MySQL**
- **ORM 框架**：SQLAlchemy (Python 生态标准)
- **管理工具**：DataGrip 2025.1.3

## 3. 部署方案 (Deployment)
- 采用 **Docker** 与 **Docker Compose** 进行全栈容器化部署。
- 后续将数据库、后端应用、前端应用全部打包，在云服务器一键拉起。