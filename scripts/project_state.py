#!/usr/bin/env python3
"""创建、推进和核验数学建模项目的可恢复状态。"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


STAGES = (
    "intake",
    "data",
    "parse",
    "research",
    "baseline",
    "model",
    "prototype",
    "solve",
    "validate",
    "evidence",
    "write",
    "format",
    "package",
    "complete",
)
GATE_STATUSES = ("PASS", "FAIL", "BLOCKED", "LIMITED")
SKILL_ROOT = Path(__file__).resolve().parents[1]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_paths(project_root: str) -> tuple[Path, Path]:
    project = Path(project_root).expanduser().resolve()
    if project == SKILL_ROOT or is_within(project, SKILL_ROOT):
        raise ValueError("PROJECT_ROOT 不能位于 SKILL_ROOT 内")
    state_path = project / ".work" / "run-state.json"
    return project, state_path


def load_state(state_path: Path) -> dict:
    if not state_path.is_file():
        raise FileNotFoundError(f"状态文件不存在: {state_path}")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("stage") not in STAGES:
        raise ValueError("状态文件中的 stage 无效")
    return state


def save_state(state_path: Path, state: dict) -> None:
    state["updated_at_utc"] = now_utc()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = state_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(state_path)


def cmd_init(args: argparse.Namespace) -> int:
    project, state_path = project_paths(args.project_root)
    project.mkdir(parents=True, exist_ok=True)
    if state_path.exists() and not args.force:
        print(f"状态已存在: {state_path}", file=sys.stderr)
        return 1
    timestamp = now_utc()
    state = {
        "schema_version": 1,
        "mode": args.mode,
        "stage": args.stage,
        "competition": args.competition,
        "year": args.year,
        "problem_id": args.problem_id,
        "created_at_utc": timestamp,
        "updated_at_utc": timestamp,
        "assumptions": [],
        "open_issues": [],
        "decisions": [],
        "artifacts": {},
        "gates": {},
        "history": [{"at_utc": timestamp, "event": "init", "stage": args.stage}],
        "next_action": args.next_action or "枚举题目、附件和模板",
    }
    save_state(state_path, state)
    print(state_path)
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    project, state_path = project_paths(args.project_root)
    state = load_state(state_path)
    current = state["stage"]
    target = args.to
    if STAGES.index(target) < STAGES.index(current) and not args.allow_regress:
        raise ValueError("默认禁止阶段回退；确认门禁失效时使用 --allow-regress")
    if current == "model" and target == "prototype" and not args.user_approval:
        raise ValueError(
            "从 model 进入 prototype 必须先取得用户确认，并通过 --user-approval 记录确认内容或回合"
        )

    evidence = []
    for item in args.evidence:
        path = (project / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        if not is_within(path, project):
            raise ValueError(f"证据必须位于 PROJECT_ROOT: {path}")
        if not path.exists():
            raise FileNotFoundError(f"证据不存在: {path}")
        evidence.append(str(path.relative_to(project)))

    timestamp = now_utc()
    if current == "model" and target == "prototype":
        state["decisions"].append({
            "at_utc": timestamp,
            "type": "model_user_approval",
            "detail": args.user_approval.strip(),
        })
    if args.gate:
        state["gates"][args.gate] = {
            "status": args.gate_status,
            "evidence": evidence,
            "at_utc": timestamp,
        }
    can_advance = not args.gate or args.gate_status in {"PASS", "LIMITED"}
    if can_advance:
        state["stage"] = target
    state["next_action"] = args.next_action or state.get("next_action", "")
    state["history"].append({
        "at_utc": timestamp,
        "event": "advance" if can_advance else "gate_blocked",
        "from": current,
        "to": target,
        "gate": args.gate,
        "gate_status": args.gate_status,
        "user_approval": args.user_approval if current == "model" and target == "prototype" else None,
    })
    save_state(state_path, state)
    print(json.dumps({"stage": state["stage"], "gate": args.gate, "status": args.gate_status}, ensure_ascii=False))
    return 0 if can_advance else 2


def cmd_artifact(args: argparse.Namespace) -> int:
    project, state_path = project_paths(args.project_root)
    state = load_state(state_path)
    artifact = Path(args.path)
    artifact = (project / artifact).resolve() if not artifact.is_absolute() else artifact.resolve()
    if not artifact.is_file() or not is_within(artifact, project):
        raise ValueError("产物必须是 PROJECT_ROOT 内的现有文件")
    relative = str(artifact.relative_to(project))
    state["artifacts"][args.name or relative] = {
        "path": relative,
        "sha256": sha256_file(artifact),
        "bytes": artifact.stat().st_size,
        "purpose": args.purpose,
        "recorded_at_utc": now_utc(),
    }
    save_state(state_path, state)
    print(relative)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    project, state_path = project_paths(args.project_root)
    state = load_state(state_path)
    drift = []
    for name, item in state.get("artifacts", {}).items():
        path = project / item["path"]
        if not path.is_file():
            drift.append({"artifact": name, "status": "missing"})
        elif sha256_file(path) != item["sha256"]:
            drift.append({"artifact": name, "status": "changed"})
    summary = {
        "stage": state["stage"],
        "mode": state["mode"],
        "next_action": state.get("next_action"),
        "gates": state.get("gates", {}),
        "artifact_drift": drift,
        "ok": not drift,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not drift else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="管理数学建模项目的可恢复运行状态")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="初始化状态")
    init.add_argument("--project-root", required=True)
    init.add_argument(
        "--mode",
        choices=("full", "data", "model", "code", "visualization", "paper"),
        default="full",
    )
    init.add_argument("--stage", choices=STAGES, default="intake")
    init.add_argument("--competition")
    init.add_argument("--year")
    init.add_argument("--problem-id")
    init.add_argument("--next-action")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    advance = commands.add_parser("advance", help="记录门禁并推进或回退阶段")
    advance.add_argument("--project-root", required=True)
    advance.add_argument("--to", choices=STAGES, required=True)
    advance.add_argument("--gate")
    advance.add_argument("--gate-status", choices=GATE_STATUSES)
    advance.add_argument("--evidence", action="append", default=[])
    advance.add_argument("--next-action")
    advance.add_argument(
        "--user-approval",
        help="从 model 进入 prototype 时必填：用户确认内容、回合标识或预先授权",
    )
    advance.add_argument("--allow-regress", action="store_true")
    advance.set_defaults(func=cmd_advance)

    artifact = commands.add_parser("artifact", help="记录产物哈希")
    artifact.add_argument("--project-root", required=True)
    artifact.add_argument("--path", required=True)
    artifact.add_argument("--name")
    artifact.add_argument("--purpose", default="")
    artifact.set_defaults(func=cmd_artifact)

    status = commands.add_parser("status", help="显示状态并检查产物漂移")
    status.add_argument("--project-root", required=True)
    status.set_defaults(func=cmd_status)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if bool(getattr(args, "gate", None)) != bool(getattr(args, "gate_status", None)):
        raise ValueError("--gate 与 --gate-status 必须同时提供")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
