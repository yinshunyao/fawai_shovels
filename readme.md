# `fawai_shovels` 工具台账

English: [`readme.en.md`](readme.en.md)

本目录（`fawai_shovels/`）存放 **可分享的单文件铲子**（脚本/小工具；非宿主业务代码）。  
真源格式见 [`SHOVEL.md`](SHOVEL.md)；模板与校验在 `scaffold/`。

**硬性规定**：新增/改铲须（1）文首 `# --- shovel ---` 自述完整（2）同回合更新 **本文件与 `readme.en.md`**（3）`python3 fawai_shovels/scaffold/catalog.py --check` 通过。

## 铲子约定（相对旧 hipp-tools）

1. **平台适用性（强制）**：文首 `platforms` 必填；词表仅 `macOS` / `Linux` / `Windows`（或已核实的 `all`=`三者`）。`runtime: bash` 不得含 Windows、不得写 `all`。未列出的平台视为不支持。详见 `SHOVEL.md`；`--check` 不通过不得合入。
2. **一铲一文件**：逻辑自洽；`kind: library` 可被同仓 import；`launcher` 可薄封装另一铲。
3. **文首自述**：字段对齐 Skill（`id` / `title` / `when_to_use` + runtime/requires/side_effects/platforms/scores…），见 `SHOVEL.md`。
4. **无宿主业务依赖**：禁止 `import fawai_avatar`；禁止默认值写未公开路径/客户信息。
5. **隐私**：默认可标 `privacy: public`；含隐私不得进公共包。
6. **先查本文件 / `catalog.py --list`** 再动手；禁止对话里一次性脚本用完即弃。
7. **通用性 ≥3** 留本仓；≤2 与产品部署放 workspace `.cursor/tools/`。
8. **三维度评分**写入文首与台账（完备性 / 通用性 / 效率，1～5）。
9. **脱敏**：台账与源码只用占位符；口令仅 env。

新建铲子：复制 `scaffold/TEMPLATE.py` 或 `TEMPLATE.sh` → 放到 `shell/` / `python/` / `media/` → 填 meta → `--check` → 登记下表。

## 调用方式

在 workspace 根下直接跑脚本（本仓**不**发布到 PyPI）：

```bash
bash fawai_shovels/shell/rsync-ssh-deploy.sh
python3 fawai_shovels/python/check-knowledge-svg.py <路径>
```

在 Cursor **之外**做类似 Read / Grep / Glob（以及台账检索）：

```bash
bash fawai_shovels/shell/workspace-fs.sh read <文件> [--offset N] [--limit N]
bash fawai_shovels/shell/workspace-fs.sh grep '<正则>' [--path DIR] [--glob '*.py'] [-i]
bash fawai_shovels/shell/workspace-fs.sh glob '**/*.md' [--path DIR]
bash fawai_shovels/shell/workspace-fs.sh catalog rsync
```

`grep` 依赖本机 `rg`（ripgrep）。可选 `FAWAI_SHOVELS_ROOT`（兼容旧名 `HIPP_TOOLS_ROOT`）/ `WORKSPACE_FS_PYTHON`。

校验文首：

```bash
python3 fawai_shovels/scaffold/catalog.py --check
python3 fawai_shovels/scaffold/catalog.py --list
```

> 由 `hipp-tools` 更名；GitHub：https://github.com/yinshunyao/fawai_shovels

## 目录分类

| 分类目录 | 用途 |
|:---|:---|
| `shell/` | Bash 铲子 |
| `python/` | Python 铲子 / library |
| `media/` | 音视频、图片铲子 |
| `scaffold/` | 格式模板 + `catalog.py` 校验（非业务铲目录表） |
| `git/` | 仓库辅助（暂空） |
| `misc/` | 暂无法归类 |

新建类型分类时：先增上表一行，再建目录。**工程专用**脚本放在 `.cursor/tools/<工程名>/`。

---

## 评估维度（1～5，助手自动打分）

三列均须填写。**分流只看通用性**（≥3 留本仓）；完备性与效率是质量信号，用于选型与改进，不单独决定去向。

### 完备性

针对「台账用途」一句话，工具是否把该事做完、可安全复用。

| 分 | 含义 |
|:---:|:---|
| 5 | 端到端覆盖声明用途；参数/env 文档齐全；缺参失败清晰；有合理默认或 dry-run |
| 4 | 主路径完整，常见选项基本齐；边角或产品默认值略绑 |
| 3 | 核心能跑，常见场景仍需人工补步或改代码 |
| 2 | 半成品，大量步骤仍在工具外 |
| 1 | 草稿 / 不可独立完成声明用途 |

### 通用性

| 分 | 含义 | 去向 |
|:---:|:---|:---|
| 5 | 任意仓库可复用，几乎无业务绑定 | 留 `fawai_shovels` |
| 4 | 通用运维/数据流，少量约定 | 留 |
| 3 | 领域通用（检测 VOC、远端排队、SVG 基建等） | 留 |
| 2 | 绑定本 workspace 某仓/某站/某版式 | `.cursor/tools` |
| 1 | 单次专栏/案例/论文图生成 | `.cursor/tools` |

### 效率

助手调用与执行的摩擦、依赖与资源代价（相对声明用途）。

| 分 | 含义 |
|:---:|:---|
| 5 | 一条命令 / 少量 env 即可；依赖轻；失败快；无交互 |
| 4 | 参数略多或有合理包装脚本；依赖可接受 |
| 3 | 须改 `__main__`、多步准备，或依赖偏重但与领域匹配 |
| 2 | 调用摩擦大、默认真慢、或每次重装重依赖 |
| 1 | 相对用途极慢/极重，几乎不适合助手反复调用 |

下表仅列留在本仓的工具（通用性 ≥3）。分数为助手按上表自动评估。

## shell/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `shell/rsync-ssh-deploy.sh` | 5 | 5 | 5 | 密码 SSH 下 rsync 目录到远端 | `DEPLOY_LOCAL=… DEPLOY_REMOTE=user@host:… bash fawai_shovels/shell/rsync-ssh-deploy.sh` | 口令仅 env |
| `shell/rsync-ssh-pull.sh` | 5 | 5 | 5 | 密码 SSH 下从远端 rsync 拉到本地 | `PULL_REMOTE=… PULL_LOCAL=… bash fawai_shovels/shell/rsync-ssh-pull.sh` | 口令仅 env |
| `shell/ssh-run-with-pass.sh` | 5 | 5 | 5 | 带可选密码跑本地命令（expect） | `SSH_PASS=… bash fawai_shovels/shell/ssh-run-with-pass.sh -- ssh …` | 无密码则直接 exec |
| `shell/publish-pypi-project.sh` | 4 | 5 | 4 | 任意其它项目的 `pyproject.toml` 目录 build + twine（**非**本仓自发布） | `PUBLISH_ROOT=… bash fawai_shovels/shell/publish-pypi-project.sh` | 凭据 `~/.pypirc` / `TWINE_*`；含 dry-run；本机解释器有硬编码偏好 |
| `shell/remote-pip-systemd-upgrade.sh` | 4 | 5 | 5 | 远端 pip 升级包并 systemctl restart | `REMOTE_SSH=… REMOTE_PIP_PACKAGE=… bash fawai_shovels/shell/remote-pip-systemd-upgrade.sh` | 依赖 `ssh-run-with-pass.sh`；默认 unit/校验偏某包名 |
| `shell/queue-remote-after.sh` | 5 | 4 | 4 | 远端等进程退出后再跑命令 | 见远端任务排队文档 | 依赖 `python/queue-remote-wait.py`；env 较多 |
| `shell/remote-job-status.sh` | 4 | 4 | 4 | 查远端近期任务状态 | `STATUS_SSH=… STATUS_REMOTE_CWD=… bash fawai_shovels/shell/remote-job-status.sh` | 依赖 `python/remote-job-status.py` |
| `shell/disable-systemd-osc-context.sh` | 4 | 4 | 4 | 关掉 Ubuntu systemd OSC 3008 刷屏 | 本机/远程见脚本头 | 密码走 env |
| `shell/download-coco2017.sh` | 5 | 4 | 3 | 下载 COCO 2017 检测常用包 | `DEST=… bash fawai_shovels/shell/download-coco2017.sh` | 官方 URL；体量大属用途本身 |
| `shell/download-voc-yolo.sh` | 4 | 4 | 4 | 下载 YOLO VOC.yaml 三包归档 | `DEST=… bash fawai_shovels/shell/download-voc-yolo.sh` | Ultralytics assets |
| `shell/workspace-fs.sh` | 5 | 5 | 5 | 启动 `python/workspace-fs.py`（Cursor 外 read/grep/glob/catalog） | `bash fawai_shovels/shell/workspace-fs.sh <子命令> …` | 见 python 行 |

## python/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `python/workspace-fs.py` | 5 | 5 | 5 | Cursor 外复刻：read / grep / glob / catalog | `python3 fawai_shovels/python/workspace-fs.py --help` | read/glob/catalog 仅标准库；grep 需 `rg`；非语义搜索 |
| `python/labelstudio-to-voc.py` | 4 | 4 | 3 | Label Studio 矩形框 → Pascal VOC | env 或 `__main__` | 仅标准库 |
| `python/coco-cvat-to-voc.py` | 4 | 4 | 3 | CVAT COCO → Pascal VOC | env 或 `__main__` | 仅标准库 |
| `python/merge-voc-dirs.py` | 4 | 4 | 3 | 合并两个 VOC 目录，按图 MD5 去重 | env | 仅标准库 |
| `python/stat-voc-annotations.py` | 5 | 4 | 3 | 统计 VOC 框类型与尺寸分布 | env | 仅标准库 |
| `python/md-to-docx.py` | 3 | 4 | 3 | 通用 Markdown → Word | 改 `__main__` 的 `SRC` | python-docx |
| `python/queue-remote-wait.py` | 5 | 4 | 4 | 远端轮询 ps 后执行命令 | 由 queue-remote-after 上传 | 仅标准库；轮询属设计 |
| `python/remote-job-status.py` | 4 | 4 | 4 | 汇总远端任务状态 | 本机或远程 | 仅标准库；已知进程名略偏训练仓 |
| `python/voc-onnx-diff-eval.py` | 3 | 3 | 2 | VOC + ONNX 检测 IoU 差异评测 | 改 `__main__` | onnxruntime+opencv |
| `python/check-knowledge-svg.py` | 4 | 3 | 5 | 检查 SVG UTF-8/可解析 | `python3 fawai_shovels/python/check-knowledge-svg.py <路径>` | 仅标准库 |
| `python/knowledge_svg.py` | 4 | 3 | 5 | 基础知识 SVG 共用样式/`write_svg` | 被其它脚本 import | 含中文 SVG 用本模块落盘 |
| `python/xhs-text-card.py` | 3 | 3 | 3 | 几行中文合成小红书竖版字图 | 改 `__main__` | Pillow；版式通用 |
| `python/gen-wechat-pay-api-v3-key.py` | 4 | 3 | 4 | 生成微信支付 APIv3 密钥 | 改 `__main__` | 仅标准库 secrets |

## media/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `media/photo-remove-watermark-deai.py` | 3 | 3 | 3 | 去右下角半透明水印 + 轻度实拍感 | 改 `__main__` | OpenCV+numpy；角区比例固定 |
| `media/redact-image-words.py` | 4 | 3 | 3 | OCR 涂盖图中敏感词 | `--input/--output/--word` | Pillow + tesseract |

## scaffold/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `scaffold/catalog.py` | 5 | 5 | 5 | 扫描/校验文首 shovel meta | `python3 fawai_shovels/scaffold/catalog.py --check` | 模板见同目录 `TEMPLATE.*` |

## git/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| （暂无；原 cursor/study 仓脚本 ≤2 已迁 `.cursor/tools/git/`） | — | — | — | — | — | — |

## misc/

| 路径 | 完备性 | 通用性 | 效率 | 用途 | 调用 | 备注 |
|:---|:---:|:---:|:---:|:---|:---|:---|
| （暂无） | — | — | — | — | — | — |

---

## 工程 / 低通用性工具

通用性 **≤2** 与产品部署脚本在：

`.cursor/tools/`（台账 `.cursor/tools/readme.md`）

查找顺序：先本文件（≥3），再 `.cursor/tools/readme.md`。
