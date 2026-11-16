#!/usr/bin/env python3
"""
MONARCH Command Center (`monarch_ctl.py`)
Single-chat control plane for Adil Chandio's GitHub ecosystem (`adil-chandio/*`).
Runs directly via `gh` CLI from `Top1` so one Guru chat can inspect, trigger,
and debug workflows & states across all Monarch repositories.
"""

import argparse
import base64
import json
import subprocess
import sys
from typing import Any

OWNER = "adil-chandio"
CORE_REPOS = [
    "Monarch.Overall.Work",
    "Monarch-Studio",
    "portfolio",
    "Monarch.Stickman",
    "Monarch-Agent",
    "Monarch-Assistant-",
    "creatorreach-ai",
    "Top1",
]


def run_cmd(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def gh_api(path: str) -> Any:
    rc, out, err = run_cmd(["gh", "api", path])
    if rc != 0:
        raise RuntimeError(f"gh api {path} failed: {err.strip()}")
    return json.loads(out)


def cmd_overview(_args: argparse.Namespace) -> int:
    print(f"=== MONARCH ECOSYSTEM LIVE OVERVIEW ({OWNER}) ===\n")
    for repo in CORE_REPOS:
        full = f"{OWNER}/{repo}"
        try:
            commits = gh_api(f"repos/{full}/commits?per_page=1")
            c_msg = commits[0]["commit"]["message"].splitlines()[0][:65]
            c_dt = commits[0]["commit"]["author"]["date"]
        except Exception as exc:
            c_msg, c_dt = f"err: {exc}", "-"

        try:
            runs_data = gh_api(f"repos/{full}/actions/runs?per_page=3")
            runs = runs_data.get("workflow_runs", [])
            if runs:
                r0 = runs[0]
                run_line = f"{r0['name']} [{r0['status']}/{r0['conclusion']}] ({r0['created_at']})"
            else:
                run_line = "no workflow runs"
        except Exception:
            run_line = "actions unavailable"

        print(f"[{repo}]")
        print(f"  Last commit : {c_dt} | {c_msg}")
        print(f"  Last action : {run_line}\n")
    return 0


def cmd_workflows(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    rc, out, err = run_cmd(
        ["gh", "api", "--paginate", f"repos/{full}/actions/workflows?per_page=100",
         "--jq", '.workflows[] | "\\(.id)\\t\\(.state)\\t\\(.path)\\t\\(.name)"']
    )
    if rc != 0:
        print(err, file=sys.stderr)
        return rc
    needle = (args.filter or "").lower()
    lines = [ln for ln in out.splitlines() if needle in ln.lower()]
    print(f"=== {full} workflows (filter={args.filter or '*'}, count={len(lines)}) ===")
    for ln in lines:
        print(" ", ln)
    return 0


def cmd_runs(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    data = gh_api(f"repos/{full}/actions/runs?per_page={args.limit}")
    runs = data.get("workflow_runs", [])
    print(f"=== {full} latest {len(runs)} runs ===")
    for r in runs:
        print(
            f"  #{r['id']} | {r['created_at']} | {r['status']}/{r['conclusion']} "
            f"| branch={r['head_branch']} | {r['name']}"
        )
    return 0


def cmd_trigger(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    cmd = ["gh", "workflow", "run", args.workflow, "--repo", full]
    if args.ref:
        cmd.extend(["--ref", args.ref])
    for kv in args.field or []:
        cmd.extend(["-f", kv])
    rc, out, err = run_cmd(cmd)
    if rc != 0:
        print(err or out, file=sys.stderr)
        return rc
    print(f"Triggered {args.workflow} on {full} (ref={args.ref or 'default'}).")
    if out.strip():
        print(out.strip())
    return 0


def cmd_failed(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    rc, out, err = run_cmd(["gh", "run", "view", str(args.run_id), "--repo", full, "--log-failed"])
    if rc != 0:
        print(err or out, file=sys.stderr)
        return rc
    print(out[-4000:] if len(out) > 4000 else out)
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    cmd = ["gh", "run", "watch", str(args.run_id), "--repo", full, "--exit-status"]
    rc, out, err = run_cmd(cmd)
    if out.strip():
        print(out.strip())
    if err.strip():
        print(err.strip(), file=sys.stderr)
    return rc


def cmd_dispatchable(args: argparse.Namespace) -> int:
    full = f"{OWNER}/{args.repo}"
    tree = gh_api(f"repos/{full}/contents/.github/workflows")
    if not isinstance(tree, list):
        print("No .github/workflows found", file=sys.stderr)
        return 1
    needle = (args.filter or "").lower()
    hits = []
    for item in tree:
        name = item["name"]
        if not name.endswith((".yml", ".yaml")) or needle not in name.lower():
            continue
        data = gh_api(f"repos/{full}/contents/.github/workflows/{name}")
        if isinstance(data, dict) and "content" in data:
            txt = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            if "workflow_dispatch" in txt:
                hits.append(name)
    print(f"=== {full} workflow_dispatch workflows ({len(hits)}) ===")
    for h in sorted(hits):
        print(" ", h)
    return 0


def cmd_state(args: argparse.Namespace) -> int:
    repo = args.repo
    paths = (
        ["docs/continuity/STATE.md", "docs/continuity/channels/monarch-cam/NEXT_ACTION.md"]
        if repo == "Monarch.Overall.Work"
        else ["RESUME.md", "workflows/current/RESUME.md", "README.md"]
    )
    for p in paths:
        try:
            data = gh_api(f"repos/{OWNER}/{repo}/contents/{p}")
            if isinstance(data, dict) and "content" in data:
                txt = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
                print(f"=== {OWNER}/{repo}/{p} ===")
                print(txt[:2500])
                print()
        except Exception:
            pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="MONARCH Command Center CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ov = sub.add_parser("overview", help="Show latest commit & run across all Monarch repos")
    p_ov.set_defaults(func=cmd_overview)

    p_wf = sub.add_parser("workflows", help="List workflows in a repo")
    p_wf.add_argument("repo", help="Repo name (e.g. Monarch.Overall.Work)")
    p_wf.add_argument("filter", nargs="?", default="", help="Optional substring filter")
    p_wf.set_defaults(func=cmd_workflows)

    p_runs = sub.add_parser("runs", help="List latest workflow runs")
    p_runs.add_argument("repo", help="Repo name")
    p_runs.add_argument("--limit", type=int, default=10)
    p_runs.set_defaults(func=cmd_runs)

    p_trig = sub.add_parser("trigger", help="Trigger a GitHub Actions workflow via workflow_dispatch")
    p_trig.add_argument("repo", help="Repo name")
    p_trig.add_argument("workflow", help="Workflow filename or ID (e.g. yt-intel.yml)")
    p_trig.add_argument("--ref", default="", help="Branch ref")
    p_trig.add_argument("-f", "--field", action="append", help="Workflow input key=value")
    p_trig.set_defaults(func=cmd_trigger)

    p_fail = sub.add_parser("failed", help="Show failed step logs for a run")
    p_fail.add_argument("repo", help="Repo name")
    p_fail.add_argument("run_id", help="Workflow run ID")
    p_fail.set_defaults(func=cmd_failed)

    p_watch = sub.add_parser("watch", help="Watch a GitHub workflow run until completion")
    p_watch.add_argument("repo", help="Repo name")
    p_watch.add_argument("run_id", help="Workflow run ID")
    p_watch.set_defaults(func=cmd_watch)

    p_disp = sub.add_parser("dispatchable", help="List workflows with workflow_dispatch enabled")
    p_disp.add_argument("repo", nargs="?", default="Monarch.Overall.Work")
    p_disp.add_argument("filter", nargs="?", default="")
    p_disp.set_defaults(func=cmd_dispatchable)

    p_st = sub.add_parser("state", help="Read continuity state & next action from a repo")
    p_st.add_argument("repo", nargs="?", default="Monarch.Overall.Work")
    p_st.set_defaults(func=cmd_state)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
