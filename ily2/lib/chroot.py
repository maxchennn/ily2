from __future__ import annotations

from contextlib import contextmanager

from ily2.lib.general import run
from ily2.lib.output import info, success, warn

PSEUDO_MOUNTS = [
    ("--types proc /proc", "proc"),
    ("--rbind /sys sys", "sys"),
    ("--make-rslave sys", None),
    ("--rbind /dev dev", "dev"),
    ("--make-rslave dev", None),
    ("--bind /run run", "run") ,
]


class Chroot:
    """
    Context manager that prepares `target` for a chroot install:
      - copies /etc/resolv.conf (for DNS inside the chroot)
      - bind-mounts /proc, /sys, /dev, /run
    and tears everything down on exit (reverse order).
    """

    def __init__(self, target: str = "/mnt/gentoo", dry_run: bool = False):
        self.target = target
        self.dry_run = dry_run
        self._mounted: list[str] = []

    def __enter__(self) -> "Chroot":
        info("Chroot ortamı hazırlanıyor (proc/sys/dev/run bağlanıyor)...")
        run(f"cp --dereference /etc/resolv.conf {self.target}/etc/resolv.conf", dry_run=self.dry_run, check=False)

        run(f"mount --types proc /proc {self.target}/proc", dry_run=self.dry_run)
        self._mounted.append(f"{self.target}/proc")

        run(f"mount --rbind /sys {self.target}/sys", dry_run=self.dry_run)
        run(f"mount --make-rslave {self.target}/sys", dry_run=self.dry_run)
        self._mounted.append(f"{self.target}/sys")

        run(f"mount --rbind /dev {self.target}/dev", dry_run=self.dry_run)
        run(f"mount --make-rslave {self.target}/dev", dry_run=self.dry_run)
        self._mounted.append(f"{self.target}/dev")

        run(f"mount --bind /run {self.target}/run", dry_run=self.dry_run, check=False)
        self._mounted.append(f"{self.target}/run")

        success("Chroot ortamı hazır.")
        return self

    def run(self, cmd: str, check: bool = True):
        return run(cmd, chroot_dir=self.target, dry_run=self.dry_run, check=check)

    def __exit__(self, exc_type, exc, tb) -> None:
        info("Chroot bağlamaları kaldırılıyor...")
        for mountpoint in reversed(self._mounted):
            run(f"umount -R -l {mountpoint}", dry_run=self.dry_run, check=False)
        success("Chroot temizlendi.")
