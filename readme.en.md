# `fawai_shovels` catalog

中文台账: [`readme.md`](readme.md)

Shareable **single-file shovels** (scripts/helpers; not host product code).  
Format: [`SHOVEL.md`](SHOVEL.md); templates + validator: `scaffold/`.

**Required:** new/changed shovels must (1) have a full `# --- shovel ---` header (2) update **both** ledgers (3) pass `python3 fawai_shovels/scaffold/catalog.py --check`.

## Conventions

1. **Platforms (mandatory).** Header `platforms` required; tokens only `macOS` / `Linux` / `Windows` (or verified `all` = all three). `runtime: bash` must not list Windows or `all`. Omitted OS = unsupported. See `SHOVEL.md`; `--check` must pass.
2. **One shovel, one file.** `kind: library` may be imported in-repo; `launcher` may thin-wrap another shovel.
3. **Header meta** mirrors Skill fields (`id` / `title` / `when_to_use` + runtime/requires/platforms/scores…). See `SHOVEL.md`.
4. **No host business imports** (`fawai_avatar.*`); no unpublished paths/customer data in defaults.
5. **`privacy: public`** only when scrubbed; otherwise do not publish the pack entry.
6. Check this ledger / `catalog.py --list` before inventing tools; no one-off `/tmp` scripts.
7. **Generality ≥3** stays here; ≤2 → workspace `.cursor/tools/`.
8. Score **completeness / generality / efficiency** (1–5) in the header and both ledgers.
9. **Sanitize:** placeholders in docs; secrets only via env.

New shovel: copy `scaffold/TEMPLATE.py` or `TEMPLATE.sh` → `shell/`/`python/`/`media/` → fill meta → `--check` → register below.

## How to run

From the workspace root (this repo is **not** published to PyPI):

```bash
bash fawai_shovels/shell/rsync-ssh-deploy.sh
python3 fawai_shovels/python/check-knowledge-svg.py <path>
```

Cursor-like **read / grep / glob** (plus catalog search) outside Cursor:

```bash
bash fawai_shovels/shell/workspace-fs.sh read <file> [--offset N] [--limit N]
bash fawai_shovels/shell/workspace-fs.sh grep '<regex>' [--path DIR] [--glob '*.py']
bash fawai_shovels/shell/workspace-fs.sh glob '**/*.md' [--path DIR]
bash fawai_shovels/shell/workspace-fs.sh catalog rsync
```

`grep` needs `rg` (ripgrep). Optional: `FAWAI_SHOVELS_ROOT` (legacy `HIPP_TOOLS_ROOT`) / `WORKSPACE_FS_PYTHON`.

```bash
python3 fawai_shovels/scaffold/catalog.py --check
python3 fawai_shovels/scaffold/catalog.py --list
```

> Renamed from `hipp-tools`. GitHub: https://github.com/yinshunyao/fawai_shovels

## Categories

| Dir | Role |
|:---|:---|
| `shell/` | Bash shovels |
| `python/` | Python shovels / libraries |
| `media/` | Image/audio shovels |
| `scaffold/` | Templates + `catalog.py` |
| `git/` | Git helpers (empty) |
| `misc/` | Uncategorized |

**Project-only** tools: `.cursor/tools/<project>/`.

---

## Score dimensions (1–5, assistant auto-scores)

All three columns are required. **Placement uses generality only** (≥3 stay here). Completeness and efficiency are quality signals for picking/improving tools.

### Completeness

Relative to the one-line purpose: does the tool finish that job safely and reuseably?

| Score | Meaning |
|:---:|:---|
| 5 | End-to-end for stated purpose; params/env documented; clear fail-fast; sane defaults or dry-run |
| 4 | Main path complete; common options mostly covered; minor edge/product defaults |
| 3 | Core works; common cases still need manual follow-up or code edits |
| 2 | Partial; much of the job stays outside the tool |
| 1 | Sketch / cannot complete the stated purpose alone |

### Generality

| Score | Meaning | Where |
|:---:|:---|:---|
| 5 | Reusable in any repo, almost no business binding | keep in `fawai_shovels` |
| 4 | Generic ops/data flows, light conventions | keep |
| 3 | Domain-generic (VOC, remote queue, SVG helpers, …) | keep |
| 2 | Tied to this workspace / site / layout | `.cursor/tools` |
| 1 | One-off column / case / paper figure builders | `.cursor/tools` |

### Efficiency

Invocation friction and cost for assistants, relative to the stated purpose.

| Score | Meaning |
|:---:|:---|
| 5 | One command / few env vars; light deps; fail-fast; non-interactive |
| 4 | A few more knobs or a thin wrapper; acceptable deps |
| 3 | Must edit `__main__` or multi-step prep; heavier deps OK for the domain |
| 2 | High friction, very slow defaults, or reinstalls deps every run |
| 1 | Extremely slow/heavy for the job; poor fit for repeated assistant use |

Tables below list tools that stay in this repo (generality ≥3). Scores are assistant auto-evaluations.

## shell/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `shell/rsync-ssh-deploy.sh` | 5 | 5 | 5 | rsync local dir to remote over SSH (password optional) | `DEPLOY_LOCAL=… DEPLOY_REMOTE=user@host:… bash fawai_shovels/shell/rsync-ssh-deploy.sh` | password via env only |
| `shell/rsync-ssh-pull.sh` | 5 | 5 | 5 | rsync from remote to local | `PULL_REMOTE=… PULL_LOCAL=… bash fawai_shovels/shell/rsync-ssh-pull.sh` | password via env only |
| `shell/ssh-run-with-pass.sh` | 5 | 5 | 5 | run a local command that may prompt for SSH password | `SSH_PASS=… bash fawai_shovels/shell/ssh-run-with-pass.sh -- ssh …` | no password → exec as-is |
| `shell/publish-pypi-project.sh` | 4 | 5 | 4 | build+twine upload for **other** projects with `pyproject.toml` (not this repo) | `PUBLISH_ROOT=… bash fawai_shovels/shell/publish-pypi-project.sh` | `~/.pypirc` / `TWINE_*`; dry-run; local interpreter preference hardcoded |
| `shell/remote-pip-systemd-upgrade.sh` | 4 | 5 | 5 | remote `pip install -U` + `systemctl restart` | `REMOTE_SSH=… REMOTE_PIP_PACKAGE=… bash fawai_shovels/shell/remote-pip-systemd-upgrade.sh` | uses `ssh-run-with-pass.sh`; default unit/verify lean product-ish |
| `shell/queue-remote-after.sh` | 5 | 4 | 4 | wait for remote processes to exit, then run one command | see remote job queue notes | needs `python/queue-remote-wait.py`; many env vars |
| `shell/remote-job-status.sh` | 4 | 4 | 4 | list recent remote jobs (running/queued/done) | `STATUS_SSH=… STATUS_REMOTE_CWD=… bash fawai_shovels/shell/remote-job-status.sh` | needs `python/remote-job-status.py` |
| `shell/disable-systemd-osc-context.sh` | 4 | 4 | 4 | disable Ubuntu systemd OSC 3008 spam | local/remote; see script header | password via env |
| `shell/download-coco2017.sh` | 5 | 4 | 3 | download COCO 2017 detection packs | `DEST=… bash fawai_shovels/shell/download-coco2017.sh` | official URLs; large payload is inherent |
| `shell/download-voc-yolo.sh` | 4 | 4 | 4 | download YOLO `VOC.yaml` zip packs | `DEST=… bash fawai_shovels/shell/download-voc-yolo.sh` | Ultralytics assets |
| `shell/workspace-fs.sh` | 5 | 5 | 5 | launcher for `python/workspace-fs.py` | `bash fawai_shovels/shell/workspace-fs.sh <subcommand> …` | see python row |

## python/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `python/workspace-fs.py` | 5 | 5 | 5 | Outside-Cursor read / grep / glob / catalog | `python3 fawai_shovels/python/workspace-fs.py --help` | stdlib for read/glob/catalog; grep needs `rg`; not semantic search |
| `python/labelstudio-to-voc.py` | 4 | 4 | 3 | Label Studio boxes → Pascal VOC | env or `__main__` | stdlib only |
| `python/coco-cvat-to-voc.py` | 4 | 4 | 3 | CVAT COCO → Pascal VOC | env or `__main__` | stdlib only |
| `python/merge-voc-dirs.py` | 4 | 4 | 3 | merge two VOC trees, dedupe by image MD5 | env | stdlib only |
| `python/stat-voc-annotations.py` | 5 | 4 | 3 | VOC box class/size stats | env | stdlib only |
| `python/md-to-docx.py` | 3 | 4 | 3 | generic Markdown → Word | set `SRC` in `__main__` | python-docx |
| `python/queue-remote-wait.py` | 5 | 4 | 4 | poll `ps` then run a command | uploaded by queue-remote-after | stdlib only; polling by design |
| `python/remote-job-status.py` | 4 | 4 | 4 | summarize remote job status | local or remote | stdlib only; known process names lean training repos |
| `python/voc-onnx-diff-eval.py` | 3 | 3 | 2 | VOC + ONNX detect IoU diff eval | edit `__main__` | onnxruntime+opencv |
| `python/check-knowledge-svg.py` | 4 | 3 | 5 | check SVG UTF-8 / parseable | `python3 fawai_shovels/python/check-knowledge-svg.py <path>` | stdlib only |
| `python/knowledge_svg.py` | 4 | 3 | 5 | shared SVG style / `write_svg` | import from other scripts | write Chinese SVGs via this module |
| `python/xhs-text-card.py` | 3 | 3 | 3 | Xiaohongshu 3:4 text card from a few lines | edit `__main__` | Pillow |
| `python/gen-wechat-pay-api-v3-key.py` | 4 | 3 | 4 | generate WeChat Pay APIv3 key | edit `__main__` | stdlib `secrets` |

## media/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `media/photo-remove-watermark-deai.py` | 3 | 3 | 3 | remove corner watermark + light “real photo” look | edit `__main__` | OpenCV+numpy; fixed corner ratios |
| `media/redact-image-words.py` | 4 | 3 | 3 | OCR and redact sensitive words | `--input/--output/--word` | Pillow + tesseract |

## scaffold/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| `scaffold/catalog.py` | 5 | 5 | 5 | scan/validate shovel headers | `python3 fawai_shovels/scaffold/catalog.py --check` | see `TEMPLATE.*` |

## git/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| (none; cursor/study repo helpers scored ≤2 → `.cursor/tools/git/`) | — | — | — | — | — | — |

## misc/

| Path | Comp. | Gen. | Eff. | Purpose | Invoke | Notes |
|:---|:---:|:---:|:---:|:---|:---|:---|
| (none) | — | — | — | — | — | — |

---

## Project-specific / low-generality tools

Generality **≤2** and product deploy scripts live under:

`.cursor/tools/` (ledger `.cursor/tools/readme.md`)

Lookup order: this catalog (≥3) first, then `.cursor/tools/readme.md`.
