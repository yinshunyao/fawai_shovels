#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize remote training / queue jobs in one working directory.

Intended to run on the training machine (or via ``shell/remote-job-status.sh``).
Reads ``ps``, ``.queue-wait/*.env``, and recent ``queue-*.log`` / ``train-*.log``.
Does not kill processes and does not open a network connection itself.

Only keeps the newest N items and/or items touched within the last D days.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

_WAIT_RE = re.compile(r"queue-remote-wait\.py\s+(\S+)")
_LOG_TAIL = 40
_KNOWN_RUN = re.compile(
    r"(fill_[\w.-]+\.py|compare\.py|queue-remote-wait\.py|train_[\w.-]+\.py|"
    r"reeval_[\w.-]+\.py|dump_aug\.py|split_aug\.py)"
)


@dataclass
class JobRow:
    status: str  # running | queued | done | unknown
    name: str
    kind: str  # process | waiter | log
    pid: int | None = None
    mtime: float | None = None
    detail: str = ""
    paths: list[str] = field(default_factory=list)


def _load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value
    return data


def _ps_rows() -> list[tuple[int, str]]:
    out = subprocess.check_output(["ps", "-eo", "pid,lstart,args"], text=True, errors="replace")
    rows: list[tuple[int, str]] = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 6)
        if len(parts) < 7:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        # parts[1:6] = lstart fields (e.g. Wed Oct 28 12:43:01 2026), args = rest
        args = parts[6]
        rows.append((pid, args))
    return rows


def _tail(path: Path, n: int = _LOG_TAIL) -> str:
    try:
        data = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    lines = data.splitlines()
    return "\n".join(lines[-n:])


def _short(s: str, n: int = 120) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def _within(mtime: float, *, now: float, days: float | None) -> bool:
    if days is None or days <= 0:
        return True
    return (now - mtime) <= days * 86400.0


def _collect(cwd: Path, *, days: float | None, limit: int) -> list[JobRow]:
    now = time.time()
    ps = _ps_rows()
    wait_by_id: dict[str, list[int]] = {}
    run_procs: list[tuple[int, str, str]] = []

    for pid, args in ps:
        m = _WAIT_RE.search(args)
        if m:
            wait_by_id.setdefault(m.group(1), []).append(pid)
            continue
        hit = _KNOWN_RUN.search(args)
        if hit and "queue-remote-wait.py" not in args:
            run_procs.append((pid, hit.group(1), args))

    rows: list[JobRow] = []

    # Collapse DataLoader / spawn children: one row per script basename.
    by_name: dict[str, list[tuple[int, str]]] = {}
    for pid, name, args in run_procs:
        by_name.setdefault(name, []).append((pid, args))
    for name, group in by_name.items():
        # Prefer the /bin/sh -c launcher or the shortest python -u cmdline as "main".
        group_sorted = sorted(
            group,
            key=lambda t: (
                0 if "/bin/sh -c" in t[1] else 1,
                0 if " -u " in t[1] else 1,
                len(t[1]),
                t[0],
            ),
        )
        main_pid, main_args = group_sorted[0]
        n = len(group)
        detail = _short(main_args)
        if n > 1:
            detail = f"procs={n} main_pid={main_pid} | {detail}"
        rows.append(
            JobRow(
                status="running",
                name=name,
                kind="process",
                pid=main_pid,
                mtime=now,
                detail=detail,
            )
        )

    qdir = cwd / ".queue-wait"
    if qdir.is_dir():
        for env_path in sorted(qdir.glob("*.env")):
            wait_id = env_path.stem
            try:
                mtime = env_path.stat().st_mtime
            except OSError:
                continue
            if not _within(mtime, now=now, days=days):
                continue
            cfg = _load_env(env_path)
            run = cfg.get("QUEUE_RUN", "").strip()
            block = cfg.get("QUEUE_BLOCK", "").strip()
            pids = wait_by_id.get(wait_id, [])
            log_guess = cwd / f"queue-{wait_id}.log"
            tail = _tail(log_guess) if log_guess.is_file() else ""
            if pids:
                if "idle; starting" in tail and "finished" not in tail.splitlines()[-3:]:
                    status = "running"
                    detail = f"waiter launched run; block={_short(block, 80)}"
                elif any("waiting " in line for line in tail.splitlines()[-5:]):
                    status = "queued"
                    detail = f"waiting; block={_short(block, 80)}"
                else:
                    status = "queued"
                    detail = f"waiter alive pid={pids[0]}; block={_short(block, 80)}"
                rows.append(
                    JobRow(
                        status=status,
                        name=wait_id,
                        kind="waiter",
                        pid=pids[0],
                        mtime=mtime,
                        detail=detail + (f" | run={_short(run, 80)}" if run else ""),
                        paths=[str(env_path), str(log_guess) if log_guess.is_file() else ""],
                    )
                )
            else:
                # No live waiter: treat as done/unknown from log if recent enough
                if "queue " + wait_id + " finished" in tail or "finished" in tail[-200:]:
                    status = "done"
                    detail = f"waiter exited; run={_short(run, 80)}"
                elif log_guess.is_file() and _within(log_guess.stat().st_mtime, now=now, days=days):
                    status = "done"
                    detail = f"no waiter; last log={_short(tail.splitlines()[-1] if tail else '', 100)}"
                else:
                    continue
                rows.append(
                    JobRow(
                        status=status,
                        name=wait_id,
                        kind="waiter",
                        pid=None,
                        mtime=max(mtime, log_guess.stat().st_mtime if log_guess.is_file() else mtime),
                        detail=detail,
                        paths=[str(env_path)] + ([str(log_guess)] if log_guess.is_file() else []),
                    )
                )

    # Standalone recent logs (queue-*.log / train-*.log) not already covered
    seen_logs = {Path(p).name for row in rows for p in row.paths if p}
    log_files: list[Path] = []
    for pattern in ("queue-*.log", "train-*.log"):
        log_files.extend(cwd.glob(pattern))
    for path in log_files:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if not _within(mtime, now=now, days=days):
            continue
        if path.name in seen_logs:
            continue
        tail = _tail(path)
        last = tail.splitlines()[-1] if tail else ""
        # If a running process already owns this job name, skip as duplicate done
        base = path.stem  # queue-foo or train-foo
        if any(row.status == "running" and base.replace("queue-", "").replace("train-", "") in (row.name + row.detail) for row in rows):
            continue
        if "finished" in tail[-300:] or "=== " in last and "done" in last.lower():
            status = "done"
        elif any(row.status == "running" for row in rows) and any(
            Path(p).name == path.name for row in rows for p in row.paths
        ):
            continue
        else:
            # Heuristic: recent log with no live matching process → done/unknown
            status = "done" if (now - mtime) > 120 else "unknown"
        rows.append(
            JobRow(
                status=status,
                name=path.name,
                kind="log",
                pid=None,
                mtime=mtime,
                detail=_short(last, 100),
                paths=[str(path)],
            )
        )

    # Sort: running, queued, then by mtime desc
    rank = {"running": 0, "queued": 1, "unknown": 2, "done": 3}
    rows.sort(key=lambda r: (rank.get(r.status, 9), -(r.mtime or 0.0)))

    if limit > 0 and len(rows) > limit:
        # Keep all running/queued, then fill with newest done/unknown
        keep: list[JobRow] = [r for r in rows if r.status in ("running", "queued")]
        rest = [r for r in rows if r.status not in ("running", "queued")]
        need = max(0, limit - len(keep))
        rows = keep + rest[:need]
    return rows


def _fmt_time(mtime: float | None) -> str:
    if mtime is None:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))


def _print_table(rows: list[JobRow], cwd: Path) -> None:
    print(f"cwd={cwd}")
    print(f"count={len(rows)}  (running/queued always kept; done/unknown capped)")
    print()
    print(f"{'STATUS':<10} {'KIND':<8} {'PID':>8} {'MTIME':<19} NAME")
    print("-" * 88)
    for r in rows:
        pid = str(r.pid) if r.pid is not None else "-"
        print(f"{r.status:<10} {r.kind:<8} {pid:>8} {_fmt_time(r.mtime):<19} {r.name}")
        if r.detail:
            print(f"{'':10} {_short(r.detail, 100)}")
    print()
    by = {"running": 0, "queued": 0, "done": 0, "unknown": 0}
    for r in rows:
        by[r.status] = by.get(r.status, 0) + 1
    print(
        f"summary: running={by.get('running', 0)} queued={by.get('queued', 0)} "
        f"done={by.get('done', 0)} unknown={by.get('unknown', 0)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="List recent remote job status in a cwd")
    parser.add_argument("--cwd", default=os.environ.get("STATUS_CWD") or os.getcwd())
    parser.add_argument(
        "--days",
        type=float,
        default=float(os.environ["STATUS_DAYS"]) if os.environ.get("STATUS_DAYS") else 7.0,
        help="only include waiter/log items touched within this many days (default 7; 0=all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=int(os.environ["STATUS_LIMIT"]) if os.environ.get("STATUS_LIMIT") else 20,
        help="max rows after keeping all running/queued (default 20; 0=unlimited)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=os.environ.get("STATUS_JSON", "").strip() in ("1", "true", "yes"),
    )
    args = parser.parse_args()
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        raise SystemExit(f"missing cwd: {cwd}")
    days = None if args.days <= 0 else float(args.days)
    rows = _collect(cwd, days=days, limit=int(args.limit))
    if args.json:
        print(
            json.dumps(
                {
                    "cwd": str(cwd),
                    "days": days,
                    "limit": int(args.limit),
                    "jobs": [asdict(r) for r in rows],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print_table(rows, cwd)


if __name__ == "__main__":
    main()
