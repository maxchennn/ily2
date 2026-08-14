from __future__ import annotations

from ily2.lib.chroot import Chroot
from ily2.lib.output import info, success


def install_grub(chroot: Chroot, disk: str, uefi: bool) -> None:
    info("GRUB kuruluyor...")
    chroot.run("emerge --noreplace sys-boot/grub")

    if uefi:
        chroot.run("emerge --noreplace sys-boot/efibootmgr", check=False)
        chroot.run(
            "grub-install --target=x86_64-efi --efi-directory=/boot/efi "
            "--bootloader-id=GENTOO"
        )
    else:
        chroot.run(f"grub-install --target=i386-pc {disk}")

    chroot.run("grub-mkconfig -o /boot/grub/grub.cfg")
    success("GRUB kuruldu ve yapılandırıldı.")
