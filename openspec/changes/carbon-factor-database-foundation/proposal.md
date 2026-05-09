## Why

CarbonRag 的 `calc-carbon` 已经具备 factor-driven baseline，但当前因子来源仍以本地种子文件和有限注册表为主，不能支撑可检索、可维护、可审计的企业级碳因子库。

V1.4.8 需要建设 CarbonRag 的运行时碳因子数据库：数据基准优先对齐 CarbonStop CCDB 中国碳数据库公开页面和公开网关展示的因子记录，前端提供同类搜索、分类、详情和来源展示体验；后端提供可维护的数据表、导入任务和查询 API；碳核算引擎可以优先从运行时因子库解析因子，并保留现有 seed fallback。

## What Changes

- 新增 CarbonRag 自有碳因子库数据模型，覆盖因子来源、因子记录、别名/关键词、导入任务和版本状态。
- SQLite / PostgreSQL 双运行时补齐因子库表结构。
- 新增用户可读的碳因子查询 API：关键词搜索、分类/行业/地区/年份/单位/来源筛选、详情读取。
- 新增管理员维护 API：导入 JSON/CSV、启停因子、重建索引、查看导入状态。
- 新增前端“碳因子库”页面，提供搜索框、热门关键词、分类入口、因子卡片、详情抽屉和来源引用。
- 碳核算 `FactorRegistry` 优先读取运行时因子库；无匹配时保留当前 seed JSON fallback。
- 新增 CarbonStop CCDB 公开数据适配器：按其公开页面加载的分类、公开接口响应字段和来源标注落库，保留 `CarbonStop CCDB` 与原始机构/文献来源双重溯源；不再手写、乱编或只用演示 seed 充当完成结果。
- 新增公开数据治理规则：只使用公开页面/公开接口可见内容，不绕过登录、付费墙或私有鉴权；导入时必须保留来源、年份、机构、规格、单位和原始字段快照。

## Capabilities

### Modified Capabilities

- `carbon-report-feedback`: 增加可维护碳因子库、查询 API、导入任务和碳核算解析接入。
- `frontend-shell-settings`: 增加碳因子库用户页面和工作台导航入口。
- `devops-release`: 增加因子库运行时表、导入数据治理和本地/云端验证要求。

## Impact

- Affected modules: M6 Carbon / Report / Feedback, M3 Frontend, M8 DevOps / Runtime DB.
- Affected backend areas: `backend/app/carbon/**`, runtime DB schema/bootstrap, API routes, admin routes, tests.
- Affected frontend areas: navigation, new carbon factor database page, carbon calculation factor selection affordances.
- Affected data: `data/factors/**` import contracts and curated seed metadata.
- External data boundary: CarbonStop CCDB is the V1.4.8 public benchmark and primary public seed source. CarbonRag stores a queryable copy of the public fields exposed by the CCDB page/gateway with attribution and raw-source snapshots; it must not fabricate factors, and it must not access non-public or authenticated CCDB data.
