from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field

from ily2.lib.output import console


class SysCallError(Exception):
    def __init__(self, cmd: str, returncode: int, output: str):
        self.cmd = cmd
        self.returncode = returncode
        self.output = output
        super().__init__(f"Command failed ({returncode}): {cmd}\n{output}")


def run_argv(
    argv: list[str],
    *,
    chroot_dir: str | None = None,
    dry_run: bool = False,
    check: bool = True,
    input_data: str | None = None,
    redact_log: bool = False,
) -> subprocess.CompletedProcess:
    """
    Runs a command as an argv list (NO shell involved) — the safe way to pass
    secrets (passwords) or user-controlled strings, since there is no shell
    quoting/escaping step where injection could occur.

    `input_data` is piped to stdin (e.g. "user:password\\n" for chpasswd).
    `redact_log` hides the argv/input from dry-run and error output (use for
    anything containing a password).
    """
    full_argv = (["chroot", chroot_dir] + argv) if chroot_dir else list(argv)

    if dry_run:
        shown = "[REDACTED - hassas veri]" if redact_log else " ".join(shlex.quote(a) for a in full_argv)
        console.print(f"[dim][dry-run][/dim] {shown}")
        return subprocess.CompletedProcess(full_argv, 0, stdout="", stderr="")

    proc = subprocess.run(
        full_argv,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if check and proc.returncode != 0:
        shown = "[REDACTED]" if redact_log else " ".join(full_argv)
        raise SysCallError(shown, proc.returncode, "" if redact_log else (proc.stdout or ""))
    return proc


@dataclass
class SysCommand:
    """
    A thin wrapper around subprocess that:
      - optionally runs inside a chroot (via `chroot_dir`)
      - supports a global dry-run mode where commands are only printed
      - raises SysCallError on non-zero exit unless `check=False`
    """

    cmd: str
    chroot_dir: str | None = None
    dry_run: bool = False
    check: bool = True
    capture: bool = True
    output: str = field(default="", init=False)
    returncode: int = field(default=0, init=False)

    def __post_init__(self):
        full_cmd = self.cmd
        if self.chroot_dir:
            full_cmd = f"chroot {shlex.quote(self.chroot_dir)} /bin/bash -c {shlex.quote(self.cmd)}"

        if self.dry_run:
            console.print(f"[dim][dry-run][/dim] {full_cmd}")
            self.returncode = 0
            self.output = ""
            return

        proc = subprocess.run(
            full_cmd,
            shell=True,
            executable="/bin/bash",
            stdout=subprocess.PIPE if self.capture else None,
            stderr=subprocess.STDOUT if self.capture else None,
            text=True,
        )
        self.returncode = proc.returncode
        self.output = proc.stdout or "" if self.capture else ""

        if self.check and self.returncode != 0:
            raise SysCallError(full_cmd, self.returncode, self.output)

    def __bool__(self):
        return self.returncode == 0

    def __str__(self):
        return self.output


def run(cmd: str, *, chroot_dir: str | None = None, dry_run: bool = False,
        check: bool = True, capture: bool = True) -> SysCommand:
    return SysCommand(cmd, chroot_dir=chroot_dir, dry_run=dry_run, check=check, capture=capture)
