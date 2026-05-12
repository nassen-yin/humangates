# Human Gates v0.2.0 — 升级计划

基于真实公司注册流程重新设计 API。

## 1. 公司注册需要什么（真实流程）

| 材料 | 说明 | 类型 |
|------|------|------|
| 公司名称 | 备选 2-3 个，核名用 | 文本 |
| 经营范围 | 按工商局分类填 | 文本 |
| 注册资本 | 认缴制，无实缴要求 | 整数（万元） |
| 股东信息 | 每个股东: 姓名 + 身份证号 + 出资比例 + 职务 | 数组 |
| 注册地址 | 自有/租赁，需上传房产证 | 文本 + 文件 |
| 法人身份证 | 正反面照片 | 文件 |
| 监事身份证 | 正反面照片（一人公司也必须） | 文件 |
| 联系电话/邮箱 | 接收通知 | 文本 |

状态流转：
pending_review → needs_info → materials_ready → in_progress → completed/failed

## 2. 需要加的接口

POST /v1/tasks/{id}/files — 上传文件（身份证、房产证等）
GET /v1/tasks/{id}/files — 查看已上传文件
POST /v1/tasks/{id}/notes — 加备注（客服/服务商沟通）
GET /v1/tasks/{id}/timeline — 查看任务时间线

## 3. 改造内容

- models.py: 新增公司注册专用 schema，加入文件模型
- database.py: 新增 files + task_logs 两张表
- routers/tasks.py: 状态机细化，参数校验
- routers/files.py: 文件上传路由
- 本地存储（不用 S3，MVP 先存本地目录）

## 4. 不变

- FastAPI + SQLite + API Key 认证
- 项目结构
- CLI 工具（会新增子命令）
