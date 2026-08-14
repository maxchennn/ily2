from __future__ import annotations

import urllib.request

from ily2.lib.general import run
from ily2.lib.output import info, success, warn

MIRROR = "https://distfiles.gentoo.org"

# variant -> latest-*.txt pointer file on the mirror
VARIANTS = {
    "openrc": "releases/amd64/autobuilds/latest-stage3-amd64-openrc.txt",
    "systemd": "releases/amd64/autobuilds/latest-stage3-amd64-systemd.txt",
    "openrc-hardened": "releases/amd64/autobuilds/latest-stage3-amd64-hardened-openrc.txt",
    "systemd-hardened": "releases/amd64/autobuilds/latest-stage3-amd64-hardened-systemd.txt",
}


def resolve_latest_stage3_url(variant: str = "openrc") -> str:
    """
    Reads the `latest-stage3-*.txt` pointer file from the Gentoo mirrors and
    returns the full URL to the current stage3 tarball for that variant.
    """
    pointer_url = f"{MIRROR}/{VARIANTS[variant]}"
    with urllib.request.urlopen(pointer_url, timeout=30) as resp:
        text = resp.read().decode()

    tarball_path = None
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tarball_path = line.split()[0]
        break

    if not tarball_path:
        raise RuntimeError(f"Stage3 pointer dosyası ayrıştırılamadı: {pointer_url}")

    return f"{MIRROR}/releases/amd64/autobuilds/{tarball_path}"


def download_and_extract(variant: str, target: str = "/mnt/gentoo", dry_run: bool = False) -> None:
    url = resolve_latest_stage3_url(variant) if not dry_run else f"{MIRROR}/.../stage3-{variant}.tar.xz"
    info(f"Stage3 indiriliyor: {url}")

    tarball = "/tmp/stage3.tar.xz"
    run(f"curl -L --fail -o {tarball} {url}", dry_run=dry_run)
    success("Stage3 indirildi.")

    info("Stage3 arşivi çıkarılıyor (xattr/acl korunarak)...")
    run(
        f"tar xpf {tarball} --xattrs-include='*.*' --numeric-owner -C {target}",
        dry_run=dry_run,
    )
    success("Stage3 çıkarıldı.")
