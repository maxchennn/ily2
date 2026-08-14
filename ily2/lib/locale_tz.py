from __future__ import annotations

from ily2.lib.chroot import Chroot
from ily2.lib.output import info, success


def set_timezone(chroot: Chroot, timezone: str) -> None:
    info(f"Zaman dilimi ayarlanıyor: {timezone}")
    chroot.run(f"echo '{timezone}' > /etc/timezone")
    chroot.run("emerge --config sys-libs/timezone-data", check=False)
    success("Zaman dilimi ayarlandı.")


def set_locale(chroot: Chroot, locales: list[str], default_locale: str) -> None:
    """
    locales: e.g. ["en_US.UTF-8 UTF-8", "tr_TR.UTF-8 UTF-8"]
    default_locale: e.g. "en_US.utf8"
    """
    info("locale.gen düzenleniyor...")
    content = "\n".join(locales) + "\n"
    path = f"{chroot.target}/etc/locale.gen"
    if chroot.dry_run:
        info(f"[dry-run] {path} içeriği:\n{content}")
    else:
        with open(path, "w") as f:
            f.write(content)

    chroot.run("locale-gen")
    chroot.run(f"eselect locale set {default_locale}", check=False)
    success("Locale ayarlandı.")
