from __future__ import annotations

import re
from dataclasses import dataclass

from ily2.lib.general import run
from ily2.lib.output import info, success, warn


def list_disks(dry_run: bool = False) -> list[dict]:
    """Return a list of block devices (disks only, no partitions) via lsblk."""
    out = run(
        "lsblk -dn -o NAME,SIZE,MODEL,TYPE -e7,11",
        dry_run=dry_run,
        check=False,
    ).output
    disks = []
    for line in out.strip().splitlines():
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        name, size = parts[0], parts[1]
        typ = parts[-1]
        model = parts[2] if len(parts) == 4 else ""
        if typ != "disk":
            continue
        disks.append({"name": f"/dev/{name}", "size": size, "model": model})

    if not disks and dry_run:
        # No real block devices visible (e.g. running --dry-run inside a
        # container for testing) — surface a fake disk so the rest of the
        # flow can still be exercised end-to-end.
        disks.append({"name": "/dev/sda", "size": "(dry-run, örnek)", "model": "TEST-DISK"})

    return disks


def is_uefi() -> bool:
    import os

    return os.path.isdir("/sys/firmware/efi")


@dataclass
class PartitionPlan:
    disk: str
    efi_size: str = "512MiB"
    swap_size: str | None = "4GiB"     # None => no swap partition
    root_fs: str = "ext4"              # ext4 | btrfs | xfs
    uefi: bool = True


def wipe_and_partition(plan: PartitionPlan, dry_run: bool = False) -> dict:
    """
    Wipes `plan.disk` and creates a fresh partition table:
      - (UEFI) ESP (fat32)  - plan.efi_size
      - (BIOS) bios_grub (1MiB) if not uefi
      - swap (optional)     - plan.swap_size
      - root (rest)         - plan.root_fs

    Returns a dict mapping role -> partition device path.
    """
    disk = plan.disk
    info(f"{disk} sıfırlanıp yeniden bölümlenecek. TÜM VERİ SİLİNECEK.")

    run(f"wipefs -af {disk}", dry_run=dry_run, check=False)
    run(f"sgdisk --zap-all {disk}", dry_run=dry_run, check=False)

    label = "gpt"
    run(f"parted -s {disk} mklabel {label}", dry_run=dry_run)

    cursor_mib = 1
    partitions: dict[str, str] = {}
    part_index = 1

    if plan.uefi:
        end = cursor_mib + _size_to_mib(plan.efi_size)
        run(f"parted -s {disk} mkpart ESP fat32 {cursor_mib}MiB {end}MiB", dry_run=dry_run)
        run(f"parted -s {disk} set {part_index} esp on", dry_run=dry_run)
        partitions["efi"] = _partition_path(disk, part_index)
        cursor_mib = end
        part_index += 1
    else:
        end = cursor_mib + 1
        run(f"parted -s {disk} mkpart biosgrub {cursor_mib}MiB {end}MiB", dry_run=dry_run)
        run(f"parted -s {disk} set {part_index} bios_grub on", dry_run=dry_run)
        partitions["biosgrub"] = _partition_path(disk, part_index)
        cursor_mib = end
        part_index += 1

    if plan.swap_size:
        end = cursor_mib + _size_to_mib(plan.swap_size)
        run(f"parted -s {disk} mkpart swap linux-swap {cursor_mib}MiB {end}MiB", dry_run=dry_run)
        partitions["swap"] = _partition_path(disk, part_index)
        cursor_mib = end
        part_index += 1

    run(f"parted -s {disk} mkpart root {cursor_mib}MiB 100%", dry_run=dry_run)
    partitions["root"] = _partition_path(disk, part_index)

    # Not every live environment ships both tools (some minimal/rescue images
    # lack udevadm); try both so partition nodes are guaranteed to exist
    # before we try to mkfs/mount them.
    run(f"partprobe {disk}", dry_run=dry_run, check=False)
    run("udevadm settle", dry_run=dry_run, check=False)
    success("Bölümleme tamamlandı.")
    return partitions


def format_partitions(partitions: dict, plan: PartitionPlan, dry_run: bool = False) -> None:
    if "efi" in partitions:
        run(f"mkfs.vfat -F32 {partitions['efi']}", dry_run=dry_run)
    if "swap" in partitions:
        run(f"mkswap {partitions['swap']}", dry_run=dry_run)

    root_fs = plan.root_fs
    root_dev = partitions["root"]
    if root_fs == "ext4":
        run(f"mkfs.ext4 -F {root_dev}", dry_run=dry_run)
    elif root_fs == "btrfs":
        run(f"mkfs.btrfs -f {root_dev}", dry_run=dry_run)
    elif root_fs == "xfs":
        run(f"mkfs.xfs -f {root_dev}", dry_run=dry_run)
    else:
        raise ValueError(f"Desteklenmeyen dosya sistemi: {root_fs}")
    success("Dosya sistemleri oluşturuldu.")


def mount_partitions(partitions: dict, target: str = "/mnt/gentoo", dry_run: bool = False) -> None:
    run(f"mkdir -p {target}", dry_run=dry_run)
    run(f"mount {partitions['root']} {target}", dry_run=dry_run)
    if "efi" in partitions:
        run(f"mkdir -p {target}/boot/efi", dry_run=dry_run)
        run(f"mount {partitions['efi']} {target}/boot/efi", dry_run=dry_run)
    if "swap" in partitions:
        run(f"swapon {partitions['swap']}", dry_run=dry_run)
    success(f"Bölümler {target} altına bağlandı.")


def _size_to_mib(size: str) -> int:
    match = re.match(r"(\d+(?:\.\d+)?)\s*([A-Za-z]*)", size.strip())
    if not match:
        raise ValueError(f"Geçersiz boyut: {size}")
    value, unit = float(match.group(1)), match.group(2).lower()
    unit = unit or "mib"
    factor = {
        "mib": 1,
        "gib": 1024,
        "tib": 1024 * 1024,
        "mb": 1,
        "gb": 1024,
    }.get(unit, 1)
    return int(value * factor)


def _partition_path(disk: str, index: int) -> str:
    # nvme/mmcblk devices need a "p" before the partition number
    if re.search(r"(nvme\d+n\d+|mmcblk\d+)$", disk):
        return f"{disk}p{index}"
    return f"{disk}{index}"
