from __future__ import annotations

from ily2.lib.chroot import Chroot
from ily2.lib.output import info, success, warn

KERNEL_METHODS = {
    "genkernel": "genkernel (otomatik derleme, en 'archinstall-vari' deneyim)",
    "gentoo-kernel-bin": "sys-kernel/gentoo-kernel-bin (önceden derlenmiş, en hızlı)",
    "gentoo-kernel": "sys-kernel/gentoo-kernel (dist-kernel, otomatik .config ile kaynaktan)",
    "manual": "Elle (make menuconfig) — kurulumdan sonra kendiniz yapacaksınız",
}


def install_kernel(chroot: Chroot, method: str) -> None:
    if method == "genkernel":
        _install_via_genkernel(chroot)
    elif method == "gentoo-kernel-bin":
        _install_binary(chroot, "sys-kernel/gentoo-kernel-bin")
    elif method == "gentoo-kernel":
        _install_binary(chroot, "sys-kernel/gentoo-kernel")
    elif method == "manual":
        _install_manual(chroot)
    else:
        raise ValueError(f"Bilinmeyen kernel metodu: {method}")


def _install_via_genkernel(chroot: Chroot) -> None:
    info("gentoo-sources ve genkernel kuruluyor...")
    chroot.run("emerge --noreplace sys-kernel/gentoo-sources sys-kernel/genkernel")
    info("Kernel + initramfs derleniyor (genkernel all). Bu uzun sürebilir, sabırlı olun...")
    chroot.run("genkernel --no-menuconfig all")
    success("genkernel ile kernel derlendi.")


def _install_binary(chroot: Chroot, package: str) -> None:
    info(f"{package} kuruluyor (önceden derlenmiş kernel + initramfs otomatik gelir)...")
    chroot.run(f"emerge --noreplace {package}")
    success(f"{package} kuruldu.")


def _install_manual(chroot: Chroot) -> None:
    warn("Manuel mod seçildi: gentoo-sources kuruldu, kernel yapılandırması/derlemesi size kaldı.")
    chroot.run("emerge --noreplace sys-kernel/gentoo-sources")
    info("Kurulumdan sonra chroot içinde şunları çalıştırabilirsiniz:")
    info("  cd /usr/src/linux && make menuconfig && make -j$(nproc) && make modules_install && make install")
