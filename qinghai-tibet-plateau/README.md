# 青藏高原生态保护科普资源数据管理系统

基于 **Flask + MySQL + Bootstrap + ECharts** 的科普资源查阅系统，面向数据库课程设计。

系统数据：从科普中国网采集的 64 篇青藏高原生态保护科普文章，含 30 家来源机构、75 个关键词、8 个生态专题。

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 文章浏览 | 首页卡片式浏览，按生态专题分类导航，分页展示 |
| 智能检索 | 标题模糊查询，关键词 / 来源机构 / 专题 / 发布时间范围组合检索 |
| 统计可视化 | 年度发文量、来源发文量 TOP10、专题分布、关键词云与热度 TOP20 |
| 来源机构管理 | 机构列表与发文量统计，登录后可增删改 |
| 用户与收藏 | 注册登录（密码哈希存储）、收藏 / 取消收藏、我的收藏列表 |

## 数据库设计

7 张表：`source`（来源机构）、`article`（科普文章）、`topic`（生态专题）、`keyword`（关键词）、`article_keyword`（文章-关键词关联，M:N）、`user`（用户）、`favorite`（收藏，M:N，含收藏时间属性）。

表结构与约束详见课程设计文档《数据库设计.docx》。

## 运行方式

### 1. 准备数据库

确保 MySQL 中已建好名为 `qinghai_tibet_eco` 的数据库并导入数据。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置连接

复制 `.env.example` 为 `.env`，填写 MySQL 用户名和密码：

```bash
copy .env.example .env
```

### 4. 启动

```bash
python app.py
```

浏览器访问 http://127.0.0.1:5000

## 目录结构

```
qinghai-tibet-plateau/
├── app.py              # Flask 应用入口（应用工厂）
├── config.py           # 配置（读取 .env）
├── db.py               # PyMySQL 连接管理
├── requirements.txt
├── .env.example        # 配置示例
├── routes/
│   ├── article.py      # 文章浏览 / 智能检索 / 详情
│   ├── auth.py         # 注册 / 登录 / 收藏
│   ├── source.py       # 来源机构管理
│   └── stats.py        # 统计可视化
├── templates/          # Jinja2 模板（Bootstrap 5）
└── static/
    ├── css/            # 自定义样式
    └── lib/            # 本地依赖库（Bootstrap、ECharts，避免 CDN 被墙）
```

## 技术说明

- 数据库访问使用 PyMySQL 原生 SQL，组合检索动态拼接 WHERE 条件，全部参数化防注入。
- 文章配图仅存 URL 不入库，前端 `<img>` 直接引用并带 `onerror` 兜底。
- 密码使用 Werkzeug `pbkdf2:sha256` 哈希存储，适配 `password_hash VARCHAR(128)` 字段长度。
- Bootstrap 与 ECharts 已下载到 `static/lib/`，无需联网即可使用。

## 小组成员

| 学号 | 姓名 | 分工 |
| --- | --- | --- |
| 202430809278 | 吴森灵（组长） | 总体协调与系统功能设计 |
| 202430809234 | 覃欣怡 | 数据采集与清洗 |
| 202430809341 | 王克芸 | ER 图绘制与元数据设计 |
| 202430809167 | 汪紫涵 | 数据库搭建 |
| 202430809247 | 莫樱樱 | 数据导入 |
| 202430809444 | 陈燕溪 | 数据验证与测试 |
