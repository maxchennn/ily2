from __future__ import annotations

import re

from ily2.lib.chroot import Chroot
from ily2.lib.general import run_argv
from ily2.lib.output import info, success, warn

USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")


def validate_username(name: str) -> bool | str:
    """questionary-style validator: return True if valid, else an error string."""
    if USERNAME_RE.match(name):
        return True
    return "Geçersiz kullanıcı adı (küçük harf/rakam/altçizgi/tire, harfle başlamalı)."


def _chpasswd(target: str, username: str, password: str, dry_run: bool) -> None:
    """
    Sets a password via chpasswd, piping "user:pass" over stdin as an argv
    list — never interpolated into a shell string — so passwords containing
    quotes, backslashes, `$`, etc. can never break out or be logged verbatim.
    """
    run_argv(
        ["chpasswd"],
        chroot_dir=target,
        dry_run=dry_run,
        input_data=f"{username}:{password}\n",
        redact_log=True,
    )


def set_root_password(chroot: Chroot, password: str) -> None:
    info("root parolası ayarlanıyor...")
    _chpasswd(chroot.target, "root", password, chroot.dry_run)
    success("root parolası ayarlandı.")


def create_user(chroot: Chroot, username: str, password: str, extra_groups: list[str] | None = None,
                 shell: str = "/bin/bash") -> None:
    if not USERNAME_RE.match(username):
        raise ValueError(f"Geçersiz kullanıcı adı: {username}")

    groups = extra_groups or ["wheel", "audio", "video", "usb", "plugdev"]
    info(f"Kullanıcı oluşturuluyor: {username}")

    chroot.run("emerge --noreplace app-shells/bash-completion", check=False)
    run_argv(
        ["useradd", "-m", "-G", ",".join(groups), "-s", shell, username],
        chroot_dir=chroot.target, dry_run=chroot.dry_run,
    )
    _chpasswd(chroot.target, username, password, chroot.dry_run)

    info("sudo kuruluyor ve wheel grubuna izin veriliyor...")
    chroot.run("emerge --noreplace app-admin/sudo", check=False)
    sudoers_line = "%wheel ALL=(ALL:ALL) ALL"
    chroot.run(
        f"grep -q '^{sudoers_line}$' /etc/sudoers || echo '{sudoers_line}' >> /etc/sudoers"
    )
    # Never leave a broken sudoers file behind — validate before we trust it.
    check = chroot.run("visudo -c", check=False)
    if not check:
        warn("visudo doğrulaması başarısız oldu! /etc/sudoers elle kontrol edilmeli.")
    success(f"Kullanıcı '{username}' oluşturuldu ve sudo yetkisi verildi.")
