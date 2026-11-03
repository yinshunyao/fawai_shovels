# 铲子自述格式（Shovel header）

与 Skill JSON 同级的机读契约：每个可调用文件**文首**声明元数据；一铲一文件；除标准库 / 声明依赖 / 同仓 `kind: library` 外，**禁止**依赖宿主业务包（如 `fawai_avatar.*`）。

## 放置位置

- 有 shebang 时：紧跟 shebang（及可选 encoding 注释）之后。
- 无 shebang 时：文件最开头。
- 人类 docstring / 详细用法说明放在 meta 块**之后**。

## 块语法

统一用注释行（`#`），Python / Bash 相同：

```text
# --- shovel ---
# id: workspace_fs
# title: Cursor 外 read/grep/glob
# when_to_use: 无 Cursor 工具时查文件或检索台账
# runtime: python
# kind: shovel
# requires: stdlib; grep needs rg
# side_effects: fs_read
# platforms: macOS,Linux,Windows
# tags: fs, search, catalog
# privacy: public
# completeness: 5
# generality: 5
# efficiency: 5
# invoke: python3 fawai_shovels/python/workspace-fs.py --help
# depends_shovels:
# --- end-shovel ---
```

字段名小写；值为单行；多词直接写空格。空值可省略该行或留空。

## 字段（对齐 Skill）

| 字段 | 必填 | 说明 |
|:---|:---:|:---|
| `id` | 是 | `[a-z][a-z0-9_]{1,63}`，建议与文件名 stem 的蛇形一致 |
| `title` | 是 | ≤120 字短标题 |
| `when_to_use` | 是 | ≤500 字；何时选用（同 Skill） |
| `runtime` | 是 | `python` \| `bash` |
| `kind` | 是 | `shovel` 可直接跑；`launcher` 薄封装另一铲；`library` 仅被 import |
| `requires` | 是 | 依赖声明：`stdlib` / `rg` / `rsync` / pip 包名等；禁止写本机绝对路径 |
| `side_effects` | 是 | `none` \| `fs_read` \| `fs_write` \| `network` \| `remote` \| `process`（可逗号组合） |
| `platforms` | 是 | **强制**；见下方「平台适用性」 |
| `tags` | 否 | 逗号分隔 |
| `privacy` | 是 | `public` 可进公共包；含隐私则不得标 public |
| `completeness` | 是 | 1～5（台账完备性） |
| `generality` | 是 | 1～5；**≥3 才留本仓** |
| `efficiency` | 是 | 1～5 |
| `invoke` | 是 | 一条可复制调用示例（占位符用 `<…>`） |
| `depends_shovels` | 否 | 依赖的其它铲 `id`，逗号分隔 |

Skill 的 `steps` 在此对应**可执行正文**；不要把长步骤散文塞进 meta。

## 平台适用性（强制）

每把铲子**必须**声明适用平台；调用方 / 规划器只按此字段过滤，禁止靠猜。

1. **词表封闭**（大小写敏感）：仅允许 `macOS`、`Linux`、`Windows`。
2. **写法**：逗号分隔、至少一项，如 `macOS,Linux` 或 `Linux`。允许 `all` **仅**作为 `macOS,Linux,Windows` 的等价缩写（三端都已核实）。
3. **禁止**：留空、`*`、`unix`、`darwin`、`win`、`mac`、未核实就写 `all`。
4. **与 runtime 联动**（`catalog.py --check` 强制）：
   - `runtime: bash` → **不得**含 `Windows`，也**不得**写 `all`（Bash 铲默认只标 `macOS` 和/或 `Linux`；WSL 视作 Linux 时写 `Linux`，不要写 Windows）。
   - 仅 systemd / 远端 Linux 主机类 → 只写 `Linux`。
5. **未在列表中的平台视为不支持**：缺谁就不要标谁；补支持时同回合改 meta + 台账 + `--check`。

## 硬约束

1. **平台适用性**：上节全文；缺省或词法非法 → `--check` 失败，不得入库/发布。
2. **单文件**：逻辑在本文件内完成；`launcher` 可 `exec` 同仓另一铲；`library` 可被同仓 shovel import。
3. **无宿主业务依赖**：禁止 `import fawai_avatar` / 读未公开客户路径写进默认值。
4. **脱敏**：meta 与正文均不得写密钥、口令、内网主机、客户名、未公开绝对路径。
5. **台账同源**：`readme.md` / `readme.en.md` 的分数与用途须与文首 meta 一致；改铲同回合改台账，或用 `scaffold/catalog.py --check` 校验。

## 脚手架

| 路径 | 用途 |
|:---|:---|
| `scaffold/TEMPLATE.py` | Python 铲子模板 |
| `scaffold/TEMPLATE.sh` | Bash 铲子模板 |
| `scaffold/catalog.py` | 扫描 / 校验文首；打印机读表 |

```bash
python3 fawai_shovels/scaffold/catalog.py --check
python3 fawai_shovels/scaffold/catalog.py --list
```
