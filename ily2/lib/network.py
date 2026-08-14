from __future__ import annotations

from ily2.lib.chroot import Chroot
from ily2.lib.output import info, success


def set_hostname(chroot: Chroot, hostname: str) -> None:
    info(f"Hostname ayarlanıyor: {hostname}")
    chroot.run(f"echo '{hostname}' > /etc/hostname")
    success("Hostname ayarlandı.")


def setup_networking(chroot: Chroot, init_system: str, method: str = "networkmanager") -> None:
    """
    method: "networkmanager" | "dhcpcd"
    init_system: "openrc" | "systemd"
    """
    if method == "networkmanager":
        info("NetworkManager kuruluyor...")
        chroot.run("emerge --noreplace net-misc/networkmanager")
        if init_system == "openrc":
            chroot.run("rc-update add NetworkManager default", check=False)
        else:
            chroot.run("systemctl enable NetworkManager", check=False)
    else:
        info("dhcpcd kuruluyor...")
        chroot.run("emerge --noreplace net-misc/dhcpcd")
        if init_system == "openrc":
            chroot.run("rc-update add dhcpcd default", check=False)
        else:
            chroot.run("systemctl enable dhcpcd", check=False)
    success("Ağ servisi etkinleştirildi.")
