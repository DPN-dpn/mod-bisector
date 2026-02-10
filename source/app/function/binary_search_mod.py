"""Interactive binary-search-style mod disabler.

Behavior summary:
- Detects mod folders by presence of any `.ini` file.
- Excludes folders already prefixed with `DISABLED ` from the bisection.
- During bisection, keeps only the current test group enabled and
  disables all other candidate mods (records those it disabled).
- On normal exit or signal, re-enables only the folders this program
  disabled during the run.

This file is a cleaned-up, more readable refactor of the original
implementation while preserving behavior.
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import signal
import sys
from typing import Dict, List, Optional, Set, Tuple


DISABLED_PREFIX = "DISABLED "

# Tracks folders this program disabled: list of disabled_on_disk_path strings
program_disabled: List[str] = []
# optional path where runtime-disabled entries are saved so recovery is possible
STATE_FILE: Optional[str] = None


def _is_disabled_name(name: str) -> bool:
    return name.startswith(DISABLED_PREFIX)


def _disabled_name_for(path: str) -> str:
    parent = os.path.dirname(path)
    name = os.path.basename(path)
    return os.path.join(parent, DISABLED_PREFIX + name)


def disable_folder(path: str) -> str:
    """Rename `path` to disabled name and return the new path.

    If `path` is already disabled, returns it unchanged.
    """
    name = os.path.basename(path)
    if _is_disabled_name(name):
        return path
    new_path = _disabled_name_for(path)
    os.rename(path, new_path)
    return new_path


def enable_folder(disabled_path: str) -> str:
    """Rename a disabled folder back to its original name and return it.

    If `disabled_path` is not a disabled name, returns it unchanged.
    """
    name = os.path.basename(disabled_path)
    if not _is_disabled_name(name):
        return disabled_path
    parent = os.path.dirname(disabled_path)
    orig_name = name[len(DISABLED_PREFIX) :]
    new_path = os.path.join(parent, orig_name)
    os.rename(disabled_path, new_path)
    return new_path


def find_mod_folders(start_path: Optional[str]) -> List[Dict[str, str]]:
    if not start_path:
        return []
    start_path = os.path.abspath(start_path)
    if not os.path.isdir(start_path):
        return []

    mods: List[Dict[str, str]] = []
    for dirpath, dirnames, files in os.walk(start_path, topdown=True):
        if any(f.lower().endswith(".ini") for f in files):
            mods.append(
                {"name": os.path.basename(dirpath), "path": os.path.abspath(dirpath)}
            )
            dirnames[:] = []
    return mods


def _save_state() -> None:
    """Write `program_disabled` to STATE_FILE (atomic replace)."""
    global STATE_FILE
    if not STATE_FILE:
        return
    # ensure target directory exists
    d = os.path.dirname(STATE_FILE)
    if d:
        os.makedirs(d, exist_ok=True)

    if not program_disabled:
        # remove state file if exists
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        return

    data = list(program_disabled)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)


def _load_state(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out: List[str] = []
    for item in data:
        if isinstance(item, str):
            out.append(item)
    return out


def recover_from_state(path: str) -> int:
    """Recover (enable) entries recorded in state file. Returns number restored.

    State file contains a JSON list of disabled-on-disk paths (strings).
    """
    restored = 0
    data = _load_state(path)
    for disabled in data:
        if os.path.exists(disabled) and _is_disabled_name(os.path.basename(disabled)):
            enable_folder(disabled)
            restored += 1
    # remove state file after attempting recovery
    if os.path.exists(path):
        os.remove(path)
    return restored


def run_bisection(start_path: str) -> None:
    mods = find_mod_folders(start_path)
    if not mods:
        print("모드를 찾지 못했습니다.")
        return

    # Print full mod list as JSON
    print(json.dumps(mods, ensure_ascii=False))

    # Build candidate list (original, unprefixed paths). Do not include
    # items already prefixed with DISABLED at program start.
    candidates: List[str] = []
    original_disabled_on_disk: Set[str] = set()
    for m in mods:
        name = m["name"]
        disk_path = os.path.abspath(m["path"])
        if _is_disabled_name(name):
            original_disabled_on_disk.add(disk_path)
        else:
            candidates.append(disk_path)

    if not candidates:
        print("활성화된(비활성화되지 않은) 모드가 없습니다.")
        return

    # Helpers to enable/disable only candidates we control
    def ensure_disabled(orig: str) -> None:
        if os.path.exists(orig):
            disabled = disable_folder(orig)
            program_disabled.append(disabled)
            # persist runtime-disabled list if requested
            if STATE_FILE:
                _save_state()

    def ensure_enabled_if_recorded(orig: str) -> None:
        # If we previously disabled this orig during this run, re-enable it.
        d = _disabled_name_for(orig)
        if (
            d in program_disabled
            and os.path.exists(d)
            and _is_disabled_name(os.path.basename(d))
        ):
            enable_folder(d)
            if d in program_disabled:
                program_disabled.remove(d)

    def set_active_group(group: List[str]) -> None:
        """Ensure only `group` (subset of `candidates`) is enabled.

        All other candidates will be disabled (if not already) and
        recorded so they can be restored later.
        """
        group_set = set(group)
        for orig in candidates:
            if orig in group_set:
                ensure_enabled_if_recorded(orig)
            else:
                ensure_disabled(orig)

    # Bisection loop: narrow `current` to a single candidate
    current = candidates.copy()
    try:
        while len(current) > 1:
            mid = len(current) // 2
            first = current[:mid]
            second = current[mid:]

            # Test first half: enable only `first` and keep others disabled
            set_active_group(first)

            # Output disabled and remaining lists (on-disk paths)
            disabled_list = [
                {"name": os.path.basename(p), "path": p}
                for p in candidates
                if p not in first
            ]
            remaining_list = [{"name": os.path.basename(p), "path": p} for p in first]
            print(json.dumps({"disabled": disabled_list}, ensure_ascii=False))
            print(json.dumps({"remaining": remaining_list}, ensure_ascii=False))

            resp = (
                input(
                    "이 상태에서 문제(또는 원하는 결과)가 발생합니까? (Y=예, N=아니오): "
                )
                .strip()
                .lower()
            )
            if resp == "y":
                # problem occurs when first half alone is enabled => culprit in first
                current = first
            else:
                # problem does not occur with first enabled => culprit in second
                # switch to second as active group
                set_active_group(second)
                current = second

        # Print result if single candidate remains
        if len(current) == 1:
            # print on-disk path (it may be disabled name or original depending on state)
            on_disk = _disabled_name_for(current[0])
            if os.path.exists(current[0]):
                print(current[0])
            elif os.path.exists(on_disk):
                print(on_disk)
            else:
                print(current[0])
        else:
            print("검색이 종료되었습니다.")

    finally:
        # If a state file was provided, use it to recover (enable) entries
        # we persisted during the run. If no state file is set, there is
        # nothing to recover here.
        if STATE_FILE:
            recover_from_state(STATE_FILE)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Binary search disable mods interactively"
    )
    sub = parser.add_subparsers(dest="cmd")

    runp = sub.add_parser("run", help="Run interactive bisection")
    runp.add_argument("path", nargs="?", help="Start path to search for mods")
    runp.add_argument(
        "--state",
        "-s",
        required=True,
        help="Path to save runtime-disabled list (JSON) (required)",
    )

    rec = sub.add_parser("recover", help="Recover from a saved state file")
    rec.add_argument("state_file", help="State file path to recover from")

    args = parser.parse_args()

    if args.cmd == "recover":
        n = recover_from_state(args.state_file)
        print(f"복구 시도 완료: {n} 항목 복구됨")
        return

    # default to run if no subcommand provided
    state = None
    path = None
    if args.cmd == "run":
        path = args.path
        state = args.state
    else:
        # legacy interactive prompt: require both path and state
        path = input("모드가 들어있는 폴더 경로를 입력하세요: ").strip()
        if not path:
            print("경로가 제공되지 않았습니다.")
            return
        state = input("상태 파일 경로를 입력하세요 (저장할 JSON 파일): ").strip()
        if not state:
            print("상태 파일 경로는 필수입니다.")
            return

    if not path:
        print("경로가 제공되지 않았습니다.")
        return

    if not state:
        print("--state 경로가 필요합니다.")
        return

    global STATE_FILE
    STATE_FILE = os.path.abspath(state)
    # ensure directory for state file exists
    d = os.path.dirname(STATE_FILE)
    if d:
        os.makedirs(d, exist_ok=True)
    try:
        run_bisection(path)
    except Exception as e:
        print(f"오류 발생: {e}")
        # non-zero exit to indicate failure
        sys.exit(1)


if __name__ == "__main__":
    main()
