from __future__ import annotations

import os

from ily2.lib import bootloader, disk, fstab, kernel, locale_tz, network, portage, stage3, users
from ily2.lib.chroot import Chroot
from ily2.lib.config import load_config, save_config
from ily2.lib.general import SysCallError
from ily2.lib.menu import checkbox, confirm, password_with_confirmation, select, text
from ily2.lib.output import banner, console, error, info, step, success, warn
from ily2.lib.users import validate_username

HOSTNAME_RE_MSG = "Geçersiz hostname (harf/rakam/tire, en fazla 63 karakter)."

TARGET = "/mnt/gentoo"


def _validate_hostname(name: str):
    import re
    if re.match(r"^[a-zA-Z0-9-]{1,63}$", name):
        return True
    return HOSTNAME_RE_MSG


def main(config_path: str | None = None, dry_run: bool = False) -> None:
    try:
        _run(config_path=config_path, dry_run=dry_run)
    except SysCallError as e:
        error(f"Bir komut başarısız oldu: {e}")
        _emergency_cleanup(dry_run)
        raise SystemExit(1)
    except KeyboardInterrupt:
        error("Kullanıcı tarafından durduruldu.")
        _emergency_cleanup(dry_run)
        raise SystemExit(1)


def _emergency_cleanup(dry_run: bool) -> None:
    """
    On failure, unmount whatever we mounted under TARGET instead of leaving
    the live environment in a half-mounted state (which would make a retry
    fail with "already mounted" errors, or risk data loss if the user
    reboots without noticing).
    """
    from ily2.lib.general import run
    warn(f"Temizlik yapılıyor: {TARGET} altındaki bağlamalar kaldırılıyor...")
    run(f"swapoff -a", dry_run=dry_run, check=False)
    run(f"umount -R -l {TARGET}", dry_run=dry_run, check=False)


def _run(config_path: str | None = None, dry_run: bool = False) -> None:
    banner()
    saved = load_config(config_path)
    answers: dict = {}

    # ---------------------------------------------------------------- disk
    step("1/9 — Disk Seçimi")
    disks = disk.list_disks(dry_run=dry_run)
    if not disks:
        error("Hiç disk bulunamadı.")
        return
    disk_choice = select(
        "Kurulum yapılacak diski seçin (TÜM VERİ SİLİNECEK):",
        choices=[f"{d['name']}  ({d['size']}, {d['model']})" for d in disks],
    )
    target_disk = disk_choice.split()[0]

    uefi = disk.is_uefi()
    info(f"Ürün bellenimi: {'UEFI' if uefi else 'BIOS/Legacy'} olarak algılandı.")

    root_fs = select("Kök (/) dosya sistemi:", choices=["ext4", "btrfs", "xfs"])
    want_swap = confirm("Swap bölümü oluşturulsun mu?", default=True)
    swap_size = text("Swap boyutu (ör. 4GiB):", default="4GiB") if want_swap else None

    if not confirm(f"{target_disk} diski silinip bölümlenecek. Onaylıyor musunuz?", default=False):
        error("Kullanıcı tarafından iptal edildi.")
        return

    plan = disk.PartitionPlan(
        disk=target_disk, swap_size=swap_size, root_fs=root_fs, uefi=uefi
    )
    partitions = disk.wipe_and_partition(plan, dry_run=dry_run)
    disk.format_partitions(partitions, plan, dry_run=dry_run)
    disk.mount_partitions(partitions, target=TARGET, dry_run=dry_run)

    # ------------------------------------------------------------- stage3
    step("2/9 — Stage3 İndirme")
    init_system = select("Init sistemi:", choices=["openrc", "systemd"])
    hardened = confirm("Hardened profil kullanılsın mı? (ileri seviye, güvenlik odaklı)", default=False)
    variant = f"{init_system}-hardened" if hardened else init_system
    stage3.download_and_extract(variant, target=TARGET, dry_run=dry_run)

    # ------------------------------------------------------------- portage
    step("3/9 — Portage Yapılandırması")
    jobs = max(os.cpu_count() or 4, 1)
    portage.write_make_conf(TARGET, jobs=jobs, uefi=uefi, dry_run=dry_run)

    with Chroot(target=TARGET, dry_run=dry_run) as chroot:
        portage.sync_portage(chroot)
        portage.select_profile(chroot, init_system=init_system, hardened=hardened)

        # --------------------------------------------------------- locale/tz
        step("4/9 — Zaman Dilimi ve Dil")
        timezone = text("Saat dilimi (ör. Europe/Istanbul):", default="Europe/Istanbul")
        locale_tz.set_timezone(chroot, timezone)

        default_locale_line = "en_US.UTF-8 UTF-8"
        locale_choices = checkbox(
            "Etkinleştirilecek locale'ler:",
            choices=[
                {"name": "en_US.UTF-8 UTF-8", "checked": True},
                {"name": "tr_TR.UTF-8 UTF-8", "checked": True},
            ],
        )
        default_locale = select(
            "Varsayılan sistem locale'i:",
            choices=["en_US.utf8", "tr_TR.utf8"],
        )
        locale_tz.set_locale(chroot, locale_choices or [default_locale_line], default_locale)

        # --------------------------------------------------------- network
        step("5/9 — Ağ Ayarları")
        hostname = text("Bilgisayar adı (hostname):", default="gentoo", validate=_validate_hostname)
        network.set_hostname(chroot, hostname)
        net_method = select("Ağ yönetimi:", choices=["networkmanager", "dhcpcd"])
        network.setup_networking(chroot, init_system=init_system, method=net_method)

        # --------------------------------------------------------- kernel
        step("6/9 — Kernel Kurulumu")
        kernel_method = select(
            "Kernel kurulum yöntemi:",
            choices=[f"{k}  —  {v}" for k, v in kernel.KERNEL_METHODS.items()],
        )
        kernel_method_key = kernel_method.split()[0]
        kernel.install_kernel(chroot, kernel_method_key)

        # --------------------------------------------------------- fstab
        step("7/9 — fstab")
        fstab.generate_fstab(partitions, root_fs, target=TARGET, dry_run=dry_run)

        # --------------------------------------------------------- bootloader
        step("8/9 — Bootloader (GRUB)")
        bootloader.install_grub(chroot, disk=target_disk, uefi=uefi)

        # --------------------------------------------------------- users
        step("9/9 — Kullanıcılar")
        root_pw = password_with_confirmation("root parolası")
        users.set_root_password(chroot, root_pw)

        if confirm("Yeni bir kullanıcı oluşturulsun mu?", default=True):
            username = text("Kullanıcı adı:", validate=validate_username)
            user_pw = password_with_confirmation(f"{username} parolası")
            users.create_user(chroot, username, user_pw)

        if init_system == "openrc":
            chroot.run("rc-update add sysklogd default", check=False)
            chroot.run("rc-update add cronie default", check=False)
        else:
            chroot.run("systemctl enable systemd-networkd", check=False)

    if config_path:
        save_config(config_path, {
            "disk": target_disk, "uefi": uefi, "root_fs": root_fs,
            "swap_size": swap_size, "variant": variant, "hostname": hostname,
            "kernel_method": kernel_method_key,
        })

    console.print()
    success("Kurulum tamamlandı! 🎉")
    info(f"Artık '{TARGET}' bağlamalarını kaldırıp yeniden başlatabilirsiniz:")
    info(f"  umount -R {TARGET} && reboot")
