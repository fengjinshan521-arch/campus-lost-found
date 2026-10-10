# 变更记录

按时间倒序。每条记录包含：涉及文件、改动前后、改动原因、新增/删除。

---

## 2026-10-02 ⑩ 修复：提交认领 500（关联寻物启事 ID 不存在触发外键异常）

- 现象：认领表单手填了不存在的寻物启事 ID（如 1423），后端未校验直接 INSERT，触发 `t_claim` 外键约束 `IntegrityError` → 接口 500。
- 修复（三层防御）：
  - `services/claim_service.py` `submit_claim`：提交前校验 `lost_item_id` 在 `t_lost_item` 中存在，不存在抛业务错误「关联的寻物启事 #xxx 不存在，请核对编号或清空该栏后再提交」（HTTP 400，前端弹窗友好提示）。
  - `blueprints/claims.py` `create`：兜住非数字 ID（`abc`）与非法招领 ID 的 `ValueError`，返回 400 校验提示。
  - `web/src/views/claims/ClaimFormView.vue`：提交前客户端校验「关联寻物启事」必须为数字或留空。
- 回归测试：`test_claims.py` 新增 `test_submit_with_nonexistent_lost_item_id_rejected`。
- 验证：全量 pytest **82 passed**；诊断脚本复验三场景（不存在 ID→400 友好提示 / 非法字符串→400 / 正常提交→200 成功）。

---

## 2026-10-02 ⑨ 需求符合度核查（毕业设计初始需求 vs 实现）

- 产出 `docs/08-需求符合度核查.md`：逐条对照 `docs/01-需求与用例.md`。
- 结论：**初始需求 100% 覆盖，功能完善**。10 功能模块、12 用例(UC-01~UC-12)、6 项非功能性需求全部实现并可验证。
- 关键证据链：PBKDF2 120k+每用户盐、CSRF 全站、登录锁定10分、六因子可解释匹配、状态机强制校验、信用分驳回扣减、敏感信息脱敏、上传魔数校验、统计6维度、全链路操作日志。
- 质量引用：自动化测试 81 passed / 覆盖率 76%（见 ⑦）。

---

## 2026-10-02 ⑧ 技术债清理 + 忘记密码功能 + 认领驳回/撤回测试

### 1. 修复 D-01：`utcnow` 弃用（全仓）
- 7 个 app 文件 + `base.py` + `scripts/seed_demo.py`、`scripts/smoke_test.py`、`tests/conftest.py`、`tests/test_match.py` 全部 `datetime.utcnow()` → `datetime.now(UTC).replace(tzinfo=None)`（保持 naive UTC，避免与库字段时区比较报错）。
- 效果：pytest 弃用告警由 888 条降至 38 条，`utcnow` 调用清零。

### 2. 新增「忘记密码（找回密码）」功能
- 模型：`User` 增加 `reset_token` / `reset_token_expire` 列（dev 库已非破坏性 ALTER 同步）。
- 仓库：`UserRepository.by_reset_token`。
- 服务：`request_password_reset(username, student_no, real_name)`（身份校验签发一次性令牌）+ `reset_password_by_token(token, new_password)`。
- 路由：`POST /auth/forgot-password`、`POST /auth/reset-password`（均公开）。
- 前端：`api/auth.js` 增加接口；新增 `ForgotPasswordView.vue`（两步：身份校验→令牌→设新密码）；`LoginView` 加「忘记密码？」入口；`router` 加 `/forgot`。
- 修改密码（`/auth/change-password`）此前已存在且可用，本次仅核对保留。

### 3. 补认领驳回/撤回测试（D-02 部分关闭）
- `test_claims.py` 新增 6 条路由级用例：staff 驳回回退未认领、非职工驳回 403、驳回必填意见、本人撤回、第三方撤回拒绝、已通过后驳回非法流转。
- 新增 `test_password_reset.py`（3 条）：身份校验失败拒绝、正常重置+旧密码失效+令牌单次有效、非法令牌拒绝。

### 4. 验证
- 全量 pytest：**81 passed，0 failed**，语句覆盖率 **76%**（claims 蓝图 44%→64%、auth_service 76%→78%）。
- 前端 `npm run build` 通过。
- 文档：`docs/03-接口文档.md` 补 2 个接口；`docs/07-软件测试报告.md` 用例数 72→81、覆盖率 74%→76%、缺陷表 D-01 已修复/D-02 部分关闭/D-04 新增功能。

---

## 2026-10-01 ⑦ 软件测试环节（pytest 自动化 + 黑盒用例 + 测试报告）

需求：此前仅有开发自测，未做正式「软件测试」。补齐课程交付所需的测试环节。

### 1. 测试执行
- 环境：venv 缺依赖，按 `server/requirements.txt` 用 `uv pip install` 补齐（Flask/SQLAlchemy/pymysql/pytest 等）；MySQL 8 测试库 `campus_lostfound_test` 由 conftest 自动建/清。
- 结果：**72 passed，0 failed**；语句覆盖率 **74%**（pytest-cov）；执行约 193s。
- 旧 58 用例（test_auth/admin_manage/items/claims/match/images/notify_stats/security）+ 新增 14 黑盒用例 = 72。

### 2. 新增文件
| 文件 | 说明 |
|---|---|
| `server/tests/test_blackbox.py` | 黑盒用例 14 条：等价类划分 + 边界值分析，覆盖口令强度(长度7/8、字符类、4连重复)、学号(5/6位)/姓名(1/2字)边界、登录锁定(累计5次后第6次锁定)、发布物品必填字段；全部通过 |
| `docs/07-软件测试报告.md` | 正式软件测试报告：概述/环境/策略(黑盒+白盒)/用例设计表/执行结果/覆盖率表/缺陷记录(D-01 utcnow 弃用 888 告警、D-02 覆盖薄弱 claims44%/admin54%、D-03 锁定阈值说明)/结论/复现命令 |

### 3. 发现的问题（均非阻塞）
- D-01：全仓 888 条 `datetime.utcnow()` 弃用告警，建议改 `datetime.now(datetime.UTC)`（未改，待用户确认是否动业务代码）。
- D-02：claims/admin/notify/stats 分支覆盖偏低，建议补用例。
- D-03：登录锁定为「第6次请求触发」，非缺陷，已用例验证。

---

## 2026-10-01 ⑥ 界面整体视觉优化（仅样式与结构，未改业务逻辑）

需求：梳理信息层级、统一设计规范、完善交互状态、保证响应式，不改动任何业务逻辑。

### 设计思路

以「设计令牌（Design Tokens）」为核心：在 `main.css` 中定义一套 `--lf-*` CSS 变量
（主色、语义色、文字层级、边框、背景、圆角、间距），所有页面样式改为引用变量，
替换散落各处的硬编码色值，保证全局一致性；后续换主题只需改变量定义即可全站生效。
主色采用校园蓝（`#2f54eb` 系），符合校园平台定位；信息层级遵循「品牌 → 核心行动 →
内容 → 辅助说明」的视觉权重递减。

### 修改的文件（7 个，均为样式/模板层）

| 文件 | 改动 |
|---|---|
| `web/src/styles/main.css` | 重写为设计令牌体系：新增 `--lf-primary/success/warning/danger`、`--lf-text-primary/regular/secondary/muted`、`--lf-border/bg`、`--lf-radius`、`--lf-space` 等变量；覆盖 Element Plus 主题变量统一组件观感；新增全局工具类 `.lf-container`/`.lf-card`/`.lf-muted` |
| `web/src/App.vue` | 顶栏加品牌图标与标识；移动端导航收纳进 `el-drawer` 抽屉菜单（原来小屏溢出）；修正路由菜单高亮匹配 |
| `web/src/views/HomeView.vue` | 重构 hero 区（大标题 + 副文案 + 搜索框一体）；统计卡片 4 列网格（移动端自适应降列）；「最新招领」「高频地点 TOP5」分区标题与留白统一 |
| `web/src/components/ItemCard.vue` | 封面空态显示「暂无图片」图标占位 + `@error` 加载失败兜底；悬停 `translateY(-4px)` + 阴影过渡；圆角、间距改用令牌 |
| `web/src/components/SearchBar.vue` | 输入框与筛选器间距、边框色改用令牌；筛选器 flex-wrap 换行防溢出 |
| `web/src/views/items/ItemDetailView.vue` | 硬编码灰 `#f1f3f7`/`#9ca3af`/`#374151` → `var(--lf-bg)`/`var(--lf-muted)`/`var(--lf-text-regular)` |
| `web/src/components/MatchReason.vue`、`web/src/views/NotifyView.vue`、`web/src/views/claims/ClaimDetailView.vue` | 同上，硬编码色值全部替换为令牌引用 |

### 未改动

- 所有 `<script>` 业务逻辑、接口调用、路由守卫、状态管理零改动；
- 仅动了 `<style>` 与纯展示性模板结构（如空态占位、抽屉菜单容器）。

### 验证

- `npm run build` 通过（vite ✓ built）；
- Edge 无头截图核对：桌面端首页/招领列表/登录页、移动端（375px）首页/招领列表均
  无横向溢出、层级清晰、菜单正常收纳进抽屉。
  截图存于 `C:/Users/29551/WorkBuddy/2026-10-01-14-13-35/ui-*.png`。

---

## 2026-10-01 ⑤ 修复「认领管理」页面白屏

**涉及文件**：`web/src/views/claims/ClaimListView.vue`（重写）

**现象**：登录后点击菜单「认领管理」整页白屏，浏览器控制台报
`TypeError: Cannot destructure property 'row' of 'undefined'`（ClaimListView.vue:38-39）。

**原因**：页面用渲染函数 `h('el-table', …, { default: ({ row }) => … })` 内联表格组件。
渲染函数中的字符串标签不会被解析为 Element Plus 组件（只有模板编译才会解析），
`el-table` 被当成原生未知元素，其 children 被当作元素子节点处理，
作用域插槽函数以无参调用执行，解构 `{ row }` 时抛错，整个组件树渲染崩溃。

**改动前后**：
- 改动前：`<script setup>` 里用 `h()` 手写 el-table/el-table-column 内联组件，模板只有两个 tab 包裹；
- 改动后：表格改为标准模板写法 `<el-table>` + `<template #default="{ row }">`（与其他列表页风格一致）；
  两个列表请求各加 `.catch` 兜底（单接口失败不再拖垮整页）；空列表显示 `el-empty` 占位。

**验证**：npm run build 通过；真实浏览器（Chromium）登录 zhangsan 后访问 /claims，
表格 6 列正常渲染、空状态显示「暂无认领申请」，浏览器控制台无任何报错。

---

## 2026-10-01 ④ 配图改为网络真实照片（Pexels），弃用生成示意图

需求：配图不要自己生成，要按发布名称从网络找真实对应图片。

### 1. 修改的已有文件（2 个）

| 文件 | 改动前 | 改动后 | 原因 |
|---|---|---|---|
| `server/scripts/seed_demo.py` | 配图固定调 `demo_images.ensure_item_image()`（本地绘制示意图） | 新增 `attach_image()`：优先调 `fetch_real_images.fetch_for_item()` 抓网络真实照片，网络失败时才回退示意图；提示文案同步更新 | 用户要求真实图片，示意图仅作断网兜底 |
| `docs/06-图片来源.md` | 不存在 → 由脚本自动生成 | 每张图的单号/标题/本地路径/Pexels 来源页与许可说明 | 满足论文与答辩的素材出处追溯 |

### 2. 新增文件（2 个）

| 文件 | 内容 |
|---|---|
| `server/scripts/fetch_real_images.py` | 真实照片抓取器：①`REAL_PHOTOS` 关键词→Pexels 照片 ID 映射（手机/卡片/保温杯/钥匙/双肩包/围巾/U 盘 7 类，同类 2 张轮换避免重复）；②`images.pexels.com` 下载 800px JPEG（UA 伪装 + JPEG/PNG 魔数校验）；③回填 `item.images` 并更新 `t_attachment`（`original_name` 记 `Pexels:<id>` 来源）；④CLI `--only/--force`；⑤下载失败自动回退本地示意图，保证有图 |
| `docs/06-图片来源.md` | 12 张配图的完整来源清单（类型/单号/标题/本地路径/图片内容/Pexels 页面） |

### 3. 选定的真实照片（Pexels ID 均经人工确认内容对应）

| 物品 | 照片内容 | Pexels ID |
|---|---|---|
| iPhone13 手机 | 黑色智能手机放深色木桌 | 226638 / 358627 |
| 校园卡 | 银行卡/借记卡微距特写 | 11363562 / 7821687 |
| 保温杯 | 不锈钢保温瓶 | 30469934 / 34515259 |
| 钥匙串 | 一串钥匙 | 17026019 / 27522902 |
| 黑色双肩包 | 黑色背包 | 16359291 / 16359252 |
| 灰色围巾 | 灰色针织织物 | 14840511 / 6630873 |
| 银色 U 盘 | 手持 U 盘 | 5474288 / 7442204 |

### 4. 自主决策与影响

1. **图源选 Pexels**：环境网络实测——Wikimedia/Wikipedia/Openverse/Unsplash 页面均被阻断或有反爬（Anubis PoW），仅 `images.pexels.com` 与 `cdn.pixabay.com` 可直连；Pexels License 为 CC0 级（免费商用、可修改、无需署名），合规成本最低。校园卡暂以银行卡特写近似替代（Pexels 无"校园卡"类照片）。
2. **照片 ID 人工检索固定写死**而非运行时搜索：Unsplash/Pexels 搜索接口均需 API Key 或有反爬，运行时搜索不可行；固定 ID 让配图结果可复现（论文截图稳定）。代价：新增物品类型需人工补 ID（脚本保留示意图兜底，不会无图）。
3. **旧示意图文件保留在 uploads**：只是切换引用不删文件；如需清理可手动删除 `instance/uploads/*/demo_*.png`。
4. **`t_attachment.original_name` 复用为来源留痕**（`Pexels:<id>`）：不新增字段、不迁移表结构；完整来源页在 `docs/06-图片来源.md`。

### 5. 验证

```
抓取：12/12 张真实 JPEG（ffd8ffe1 魔数），0 失败
seed --reset：自动配图输出「Pexels 真实照片」；7 招领 + 5 寻物 image_list 全部 real_*.jpg
HTTP：GET /api/v1/items/found → image_list 正常；GET /uploads/found_item/real_LF-2026-0004.jpg → 200（34KB）
回归：冒烟 18/18；pytest 58 passed
```

---

## 2026-10-01 ③ 招领/寻物信息添加相关图片（演示配图 + 上传链路修复）

需求：发布的招领里要有相关图片。排查发现后端图片链路（模型 `images` JSON 字段、`_save_attachments`、`/upload` 接口、前端 `UploadImages` 组件、卡片封面与详情画廊）均已存在，真正缺三件事：①库里的数据没有图，页面全是空占位；②`/upload` 参数不匹配导致目录归类失效；③没有针对图片的测试。本次补齐。

### 1. 修改的已有文件（7 个）

| 文件 | 改动前 | 改动后 | 原因 |
|---|---|---|---|
| `server/app/blueprints/main.py` `upload()` | 只读 `request.form.get("subdir")` | 改为 `subdir or entity_type or "misc"`，兼容两种字段名 | 前端 `UploadImages.vue` 传的是 `entity_type`，导致所有图片都落进 `misc/`，附件目录语义失效（真实 bug） |
| `server/scripts/seed_demo.py` | 只建数据不配图；参数仅 `--reset` | 新增 `--no-images`；创建每条招领/寻物后自动调 `ensure_item_image()`；文件头 try-import `demo_images`，缺 Pillow 时优雅降级 | 演示库必须"有图"才能支撑检索/认领演示 |
| `server/requirements.txt` | 无 Pillow | 追加 `Pillow==12.3.0` | 配图绘制依赖 |
| `web/src/components/ItemCard.vue` | 无图时只显示一个灰色图标；图片 404 时显示破损 | 空封面加"暂无图片"文字；`el-image` 增加 `#error` 插槽显示"图片加载失败"；空态样式改为纵向布局 | 空态与失败态可读性 |
| `web/src/views/items/ItemDetailView.vue` | 画廊图片加载失败无兜底 | `el-image` 增加 `#error` 插槽（`.img-error` 样式） | 同上 |
| `README.md`（后补） | 演示账号/验证说明 | 补充配图说明与 `demo_images.py` 用法（见下方文档同步） | 文档一致性 |
| `docs/03-接口文档.md`（后补） | `/upload` 只写 `subdir` | 说明 `entity_type/subdir` 均可 | 同上 |

### 2. 新增文件（2 个）

| 文件 | 内容 |
|---|---|
| `server/scripts/demo_images.py` | 演示配图生成器（约 430 行）：①关键词→形状映射（手机/充电宝/耳机/笔记本/水杯/雨伞/眼镜/钥匙/证件/书/箱包 等 13 类，命中标题关键词即按物品画形，否则按分类回退）；②800×600 渐变底 + 主体图形 + 底部信息条（标题/分类/单号）+ 左上角类型标签；③`ensure_item_image()` 回填 `item.images` 并写 `t_attachment` 留痕（sha256/size/mime），已有图不重复生成；④CLI：`--force` 覆盖重绘、`--only found\|lost`；缺 Pillow 时退出码 1 并提示 |
| `server/tests/test_images.py` | 5 条用例：先传图拿 URL 再建招领绑定并回显 / multipart 直传一次完成建档+存图+落盘可访问 / 伪装 png 的非图片被魔数校验拦截 400 / 未登录上传 401 / `ensure_item_image` 回填与留痕及幂等 |

### 3. 自主决策与影响

1. **用代码绘示意图而非下载网图**：真实照片有版权与网络依赖；按物品类型绘制的示意图与内容"相关"且可离线复现。影响：图是扁平风格示意图，答辩演示如需实拍图，直接在「编辑」页用上传组件替换即可（存储路径结构完全相同）。
2. **中文渲染依赖系统字体**（微软雅黑 msyh.ttc，缺失时回退 simhei/DejaVu/default）：Windows/常见 Linux 均可渲染；极端精简环境可能退化为默认字体，不影响功能。
3. **配图走 `t_attachment` 留痕**：与用户真实上传同一条数据链路，日志/审计口径一致。
4. **seed 默认配图、`--no-images` 可关**：保证"开箱即有图"，同时给论文截图场景留纯净开关。
5. **`_to_datetime` 不新增格式**：测试中 datetime 经 Flask 序列化为 RFC-822 字符串导致 400，属测试构造问题（真实前端传 `YYYY-MM-DDTHH:mm`），改测试而非放宽服务端校验。

### 4. 验证

```
配图：招领 7 + 寻物 5 共 12 张 PNG 落盘 instance/uploads/{found_item,lost_item}/，
     t_attachment 22 条（含此前批量补图的留痕）
接口：GET /api/v1/items/found → items[].image_list 非空；
     GET /uploads/found_item/demo_LF-2026-0004.png → 200 PNG；
     GET /api/v1/items/found/<id> → image_list 回显
pytest：test_images.py 5 passed；全量 58 条见下方回归结果
前端：npm run build ✓
```

---

## 2026-10-01 ② 新增「管理员管理」模块（系统管理员可管理后台账号）

需求：需要一个管理系统的管理员——后台要能创建、编辑、停用管理账号，并保留至少一个可用管理员。

### 1. 修改的已有文件（6 个）

| 文件 | 改动前 | 改动后 | 原因 |
|---|---|---|---|
| `server/app/repositories/__init__.py` | `UserRepository` 仅有 `search()`（面向全部用户）与 `staff_and_admins()`（不分页） | 新增 `search_managers(keyword, role, status, page)`（限定 `role in (staff, admin)` 的分页检索）与 `count_active_admins()` | 管理账号列表需要与学生列表分离且分页；"最后一个管理员"保护需要启用管理员计数 |
| `server/app/services/auth_service.py` | 只有面向学生注册的 `register_user`、自助 `change_password`、以及无自我保护校验的 `set_user_role` | ①导入 `ROLE_ADMIN/ROLE_STAFF` 并定义 `MANAGER_ROLES`；②新增 `create_manager/update_manager/reset_password`；③新增内部保护 `_assert_not_self`、`_assert_not_last_admin`；④`set_user_role` 增加"禁止改自己角色"与"最后一个管理员不可降级" | 原来后台无法新建管理账号；且管理员可在「用户管理」页把自己降级导致后台失联（真实漏洞） |
| `server/app/blueprints/admin.py` | 只有统计、用户、分类、日志、运维 5 组 | 新增"管理员管理"5 个路由（`/admins` 的 GET/POST、PUT、重置密码、启停），并导入 `ROLES/ROLE_ADMIN/ROLE_STAFF` | 暴露管理账号维护入口，全部 `@admin_required` |
| `web/src/api/admin.js` | 无管理员管理相关方法 | 新增 `fetchAdmins/createAdmin/updateAdmin/resetAdminPassword/setAdminStatus` | 前端调用封装 |
| `web/src/router/index.js` | 后台仅 4 个路由 | 新增 `/admin/admins`（`meta.requiresAdmin`） | 页面可达 |
| `web/src/App.vue` | "后台管理"是单个菜单项，无子入口 | 改为 `el-sub-menu`，含统计看板/用户管理/分类管理/系统日志/管理员管理；`activeMenu` 对 `/admin` 前缀返回完整路径以正确高亮 | 后台页面此前无统一导航，新页面无法进入 |

### 2. 新增文件（3 个）

| 文件 | 内容 |
|---|---|
| `server/scripts/create_admin.py` | 命令行创建/提升管理账号：`--list`、`-u/-p/-n/-r/--phone/--college`、`--promote`；已存在账号默认跳过 |
| `server/tests/test_admin_manage.py` | 14 条用例：新建/重名/弱密码/学生与楼管越权 403/列表不含学生/重置密码后可登录且旧密码失效/禁改自己角色/禁停用自己/最后一个管理员保护/停用后不可登录再启用恢复/编辑资料与提权/拒绝操作学生账号/操作写日志 |
| `web/src/views/admin/AdminsView.vue` | 管理账号列表（筛选/分页）、新增与编辑对话框、重置密码、启停；顶部展示启用管理员数量与规则提示 |

### 3. 自主决策与影响

1. **角色体系不新增"超级管理员"**：沿用既有 `student / staff / admin` 三角色，管理员管理入口限定 `admin`。影响：所有 `admin` 平级，可互相停用（但不可停用自己，且系统至少保留一个）。如需分级，后续加 `super_admin` 只需扩展 `ROLES` 与 `admin_required`。
2. **自我保护规则**：禁止改自己角色/停用自己（原先 `set_user_role` 无此限制，属可导致后台失联的缺陷）。影响：管理员无法自行降权，需另一名管理员操作——因此默认演示库提供了两个管理员账号 `admin` 与 `sysadmin`。
3. **管理账号 `verified=True`**：后台创建的账号视为已完成身份核对，与学生注册需实名认证的流程区分。
4. **新建管理账号不复用 `register_user`**：后者强制 `role=student`，故另设 `create_manager` 并限制 `role ∈ {staff, admin}`。
5. **`_assert_not_last_admin` 目前不可从 UI 触发**（操作者自身必是启用管理员，故计数≥1），按防御性代码保留，覆盖并发与后续引入超级管理员的场景；测试用 `MonkeyPatch` 覆盖该分支。
6. **演示库新增两个账号**：`staff02 / Staff@2026`（楼管）、`sysadmin / SysAdmin@2026`（系统管理员），用于演示多管理员互相管理；均为弱默认密码，部署前必须修改。

### 4. 验证

```
新增路由：GET/POST /api/v1/admin/admins、PUT /admins/<id>、POST /admins/<id>/password、/admins/<id>/status
端到端：未登录 401 → 学生 403 → 管理员 200（3 条管理账号）
       新建 sysadmin 成功；弱密码 400「密码长度至少 8 位」；停用自己 400
       重置 staff02 密码 → 新密码登录 200 / 旧密码 400
       日志追溯：manager_create → manager_reset_password → user_login
pytest：test_admin_manage.py 14 passed
前端：npm run build ✓（AdminsView 已产出独立 chunk）
```

---

## 2026-10-01 ① 项目落地（后端补全 + 前端 + 文档）

- 修复 `scripts/init_db.py`、`run.py` 中 `if __name__ == "__main__"` 混入零宽空格（`__&#8203;main__`）导致脚本静默退出。
- 数据库连接密码统一配置于 server/.env（该文件不入库），代码与示例中仅保留占位符。
- 新增 7 个蓝图文件（`server/app/blueprints/`），路由达 58 条。
- 新增 `seed_demo.py`、`smoke_test.py`、`export_init_sql.py`；测试 39 条；SQL 脚本 `schema.sql` / `init_data.sql`。
- 新建 Vue3 前端工程（`web/`）28 个文件；文档 5 篇与部署配置 3 份。
