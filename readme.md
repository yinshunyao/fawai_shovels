# `hipp-tools` 工具台账

本目录（`hipp-tools/`）存放 **可复用的系统命令包装与辅助脚本**（非业务产品代码）；已从 `.cursor/tools` 迁出。  
规则见 workspace：`.cursor/rules/rules-cursor-tools.mdc`（真源目录为本仓）。

**硬性规定**：本目录下脚本或子目录有任何变动（新增、修改、删除、重命名），必须在同一回合更新本文件。只改工具、不改本台账，视为未完成。

## 使用约定

1. **先查本文件**再动手：已有工具 → 直接调用 / 原地小改，并在同一回合更新本表。
2. **没有合适工具** → 按分类新建到对应子目录，并在本文件对应分类下登记。
3. **禁止**每次对话新建一次性脚本后丢弃；同类能力应沉淀为工具。
4. 业务实现仍写在各子工程；本目录只收「助手侧可复用工具」。
5. **不必登记**：单次 `ls`/`cat`/`git status` 探查；应登记：会重复用的流程、新建的辅助脚本。
6. **按工程提炼**：只服务某一个工程、且会反复用的命令/脚本，放到 `<工程名>/`（与 workspace 子目录同名）。跨工程通用的仍按下面的类型目录放。
7. **脱敏**：源码、注释、本台账只写通用说明（用途、输入输出形态、依赖、调用方式）。禁止写入密钥、口令、令牌、内网地址、账号、客户名、合同报价、未公开数据路径、样本清单、训练机绝对路径。具体值调用时再用参数或环境变量传入；台账用 `<数据目录>` 这类占位符。


## 调用方式

在 workspace 根下直接跑脚本（本仓**不**发布到 PyPI）：

```bash
bash hipp-tools/shell/rsync-ssh-deploy.sh
python3 hipp-tools/python/check-knowledge-svg.py <路径>
```

在 Cursor **之外**做类似 Read / Grep / Glob（以及台账检索）：

```bash
bash hipp-tools/shell/workspace-fs.sh read <文件> [--offset N] [--limit N]
bash hipp-tools/shell/workspace-fs.sh grep '<正则>' [--path DIR] [--glob '*.py'] [-i]
bash hipp-tools/shell/workspace-fs.sh glob '**/*.md' [--path DIR]
bash hipp-tools/shell/workspace-fs.sh catalog rsync
```

`grep` 依赖本机 `rg`（ripgrep）。可选 `HIPP_TOOLS_ROOT` / `WORKSPACE_FS_PYTHON`。工程专用脚本见 `.cursor/tools/`。

## 目录分类

| 分类目录 | 用途 |
|:---|:---|
| `shell/` | 跨工程可复用 shell / 一键命令包装 |
| `python/` | 跨工程可复用 Python 辅助脚本 |
| `media/` | 跨工程音视频、图片等处理 |
| `git/` | 跨工程仓库检查、批量 git 辅助 |
| `misc/` | 暂无法归类 |

新建类型分类时：先增上表一行，再建目录。**工程专用**部署/评测脚本放在 workspace `.cursor/tools/<工程名>/`，台账见该处 `readme.md`；本仓只收**通用性 ≥3** 的跨工程工具（1～5 分）；≤2 分迁到 `.cursor/tools/`。

---

## 通用性评分（1～5）

| 分 | 含义 | 去向 |
|:---:|:---|:---|
| 5 | 任意仓库可复用，几乎无业务绑定 | 留 `hipp-tools` |
| 4 | 通用运维/数据流，少量约定 | 留 |
| 3 | 领域通用（检测 VOC、远端排队、SVG 基建等） | 留 |
| 2 | 绑定本 workspace 某仓/某站/某版式 | `.cursor/tools` |
| 1 | 单次专栏/案例/论文图生成 | `.cursor/tools` |

下表「通用性」列仅列留在本仓的工具。

## shell/

| 路径 | 通用性 | 用途 | 调用 | 备注 |
|:---|:---:|:---|:---|:---|
| `shell/rsync-ssh-deploy.sh` | 5 | 密码 SSH 下 rsync 目录到远端 | `DEPLOY_LOCAL=… DEPLOY_REMOTE=user@host:… bash hipp-tools/shell/rsync-ssh-deploy.sh` | 口令仅 env |
| `shell/rsync-ssh-pull.sh` | 5 | 密码 SSH 下从远端 rsync 拉到本地 | `PULL_REMOTE=… PULL_LOCAL=… bash hipp-tools/shell/rsync-ssh-pull.sh` | 口令仅 env |
| `shell/ssh-run-with-pass.sh` | 5 | 带可选密码跑本地命令（expect） | `SSH_PASS=… bash hipp-tools/shell/ssh-run-with-pass.sh -- ssh …` | 无密码则直接 exec |
| `shell/publish-pypi-project.sh` | 5 | 任意其它项目的 `pyproject.toml` 目录 build + twine（**非**本仓自发布） | `PUBLISH_ROOT=… bash hipp-tools/shell/publish-pypi-project.sh` | 凭据 `~/.pypirc` / `TWINE_*`；如 `hipp-https-agent` |
| `shell/remote-pip-systemd-upgrade.sh` | 5 | 远端 pip 升级包并 systemctl restart | `REMOTE_SSH=… REMOTE_PIP_PACKAGE=… bash hipp-tools/shell/remote-pip-systemd-upgrade.sh` | 依赖 `ssh-run-with-pass.sh` |
| `shell/queue-remote-after.sh` | 4 | 远端等进程退出后再跑命令 | 见台账原调用 / 远端任务排队文档 | 依赖 `python/queue-remote-wait.py` |
| `shell/remote-job-status.sh` | 4 | 查远端近期任务状态 | `STATUS_SSH=… STATUS_REMOTE_CWD=… bash hipp-tools/shell/remote-job-status.sh` | 依赖 `python/remote-job-status.py` |
| `shell/disable-systemd-osc-context.sh` | 4 | 关掉 Ubuntu systemd OSC 3008 刷屏 | 本机/远程见脚本头 | 密码走 env |
| `shell/download-coco2017.sh` | 4 | 下载 COCO 2017 检测常用包 | `DEST=… bash hipp-tools/shell/download-coco2017.sh` | 官方 URL |
| `shell/download-voc-yolo.sh` | 4 | 下载 YOLO VOC.yaml 三包归档 | `DEST=… bash hipp-tools/shell/download-voc-yolo.sh` | Ultralytics assets |
| `shell/workspace-fs.sh` | 5 | 启动 `python/workspace-fs.py`（Cursor 外 read/grep/glob/catalog） | `bash hipp-tools/shell/workspace-fs.sh <子命令> …` | 见 python 行 |

## python/

| 路径 | 通用性 | 用途 | 调用 | 备注 |
|:---|:---:|:---|:---|:---|
| `python/workspace-fs.py` | 5 | Cursor 外复刻：read / grep / glob / catalog | `python3 hipp-tools/python/workspace-fs.py --help` | read/glob/catalog 仅标准库；grep 需 `rg`；非语义搜索 |
| `python/labelstudio-to-voc.py` | 4 | Label Studio 矩形框 → Pascal VOC | env 或 `__main__` | 仅标准库 |
| `python/coco-cvat-to-voc.py` | 4 | CVAT COCO → Pascal VOC | env 或 `__main__` | 仅标准库 |
| `python/merge-voc-dirs.py` | 4 | 合并两个 VOC 目录，按图 MD5 去重 | env | 仅标准库 |
| `python/stat-voc-annotations.py` | 4 | 统计 VOC 框类型与尺寸分布 | env | 仅标准库 |
| `python/md-to-docx.py` | 4 | 通用 Markdown → Word | 改 `__main__` 的 `SRC` | python-docx |
| `python/queue-remote-wait.py` | 4 | 远端轮询 ps 后执行命令 | 由 queue-remote-after 上传 | 仅标准库 |
| `python/remote-job-status.py` | 4 | 汇总远端任务状态 | 本机或远程 | 仅标准库 |
| `python/voc-onnx-diff-eval.py` | 3 | VOC + ONNX 检测 IoU 差异评测 | 改 `__main__` | onnxruntime+opencv |
| `python/check-knowledge-svg.py` | 3 | 检查 SVG UTF-8/可解析 | `python3 hipp-tools/python/check-knowledge-svg.py <路径>` | 仅标准库 |
| `python/knowledge_svg.py` | 3 | 基础知识 SVG 共用样式/`write_svg` | 被其它脚本 import | 含中文 SVG 用本模块落盘 |
| `python/xhs-text-card.py` | 3 | 几行中文合成小红书竖版字图 | 改 `__main__` | Pillow；版式通用 |
| `python/gen-wechat-pay-api-v3-key.py` | 3 | 生成微信支付 APIv3 密钥 | 改 `__main__` | 仅标准库 secrets |

## media/

| 路径 | 通用性 | 用途 | 调用 | 备注 |
|:---|:---:|:---|:---|:---|
| `media/photo-remove-watermark-deai.py` | 3 | 去右下角半透明水印 + 轻度实拍感 | 改 `__main__` | OpenCV+numpy |
| `media/redact-image-words.py` | 3 | OCR 涂盖图中敏感词 | `--input/--output/--word` | Pillow + tesseract |

## git/

| 路径 | 通用性 | 用途 | 调用 | 备注 |
|:---|:---:|:---|:---|:---|
| （暂无；原 cursor/study 仓脚本 ≤2 已迁 `.cursor/tools/git/`） | — | — | — | — |

## misc/

| 路径 | 通用性 | 用途 | 调用 | 备注 |
|:---|:---:|:---|:---|:---|
| （暂无） | — | — | — | — |

---

## 工程 / 低通用性工具

通用性 **≤2** 与产品部署脚本在：

`.cursor/tools/`（台账 `.cursor/tools/readme.md`）

查找顺序：先本文件（≥3），再 `.cursor/tools/readme.md`。

