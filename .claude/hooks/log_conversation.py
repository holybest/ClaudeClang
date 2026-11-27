"""Append the user's prompts and Claude's replies to docs/conversation-log.md.

Runs as a Claude Code Stop hook (reads the hook JSON from stdin) or by hand:
    python log_conversation.py <transcript.jsonl>

Each turn is stored between `<!-- turn:<uuid> -->` and `<!-- /turn -->` markers.
On every run, turns already in the log are rewritten in place and new turns are
appended, so running it repeatedly never duplicates entries.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_REL = Path("docs") / "conversation-log.md"
HEADER = "# 대화 기록\n\n사용자 프롬프트와 Claude 답변 기록입니다. `.claude/hooks/log_conversation.py`가 자동으로 갱신합니다.\n"
REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
COMMAND_RE = re.compile(r"<command-name>(.*?)</command-name>", re.S)
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def prompt_text(entry):
    """Return the user's prompt text, or None if the entry is not a real prompt."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isSidechain"):
        return None
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, list):
        if any(b.get("type") == "tool_result" for b in content):
            return None
        content = "\n\n".join(b.get("text", "") for b in content if b.get("type") == "text")
    if not isinstance(content, str):
        return None
    cmd = COMMAND_RE.search(content)
    if cmd:
        args = ARGS_RE.search(content)
        return (cmd.group(1).strip() + " " + (args.group(1).strip() if args else "")).strip()
    if "<local-command-" in content:
        return None
    text = REMINDER_RE.sub("", content).strip()
    return text or None


def assistant_text(entry):
    if entry.get("type") != "assistant" or entry.get("isSidechain"):
        return None
    content = (entry.get("message") or {}).get("content")
    if not isinstance(content, list):
        return None
    parts = [b.get("text", "").strip() for b in content if b.get("type") == "text"]
    return "\n\n".join(p for p in parts if p) or None


def collect_turns(transcript):
    turns = []
    with open(transcript, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            prompt = prompt_text(entry)
            if prompt is not None:
                turns.append({"id": entry.get("uuid", ""), "ts": entry.get("timestamp", ""),
                              "prompt": prompt, "replies": []})
                continue
            reply = assistant_text(entry)
            if reply and turns:
                turns[-1]["replies"].append(reply)
    return [t for t in turns if t["id"] and t["replies"]]


def local_time(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts


def render(turn):
    quoted = "\n".join("> " + line if line else ">" for line in turn["prompt"].splitlines())
    reply = "\n\n".join(turn["replies"])
    return (f"<!-- turn:{turn['id']} -->\n"
            f"## {local_time(turn['ts'])}\n\n"
            f"**사용자**\n\n{quoted}\n\n"
            f"**Claude**\n\n{reply}\n\n"
            f"---\n<!-- /turn -->\n")


def main():
    if len(sys.argv) > 1:
        transcript, project = sys.argv[1], os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    else:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
        transcript = data.get("transcript_path")
        project = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    if not transcript or not os.path.exists(transcript):
        return

    log_path = Path(project) / LOG_REL
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.read_text(encoding="utf-8") if log_path.exists() else HEADER

    for turn in collect_turns(transcript):
        block = render(turn)
        pattern = re.compile(rf"<!-- turn:{re.escape(turn['id'])} -->\n.*?<!-- /turn -->\n", re.S)
        if pattern.search(log):
            log = pattern.sub(lambda _: block, log, count=1)
        else:
            log = log.rstrip("\n") + "\n\n" + block

    log_path.write_text(log, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
