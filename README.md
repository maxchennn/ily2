# ILY2

**ILY2**, [archinstall](https://github.com/archlinux/archinstall)'dan ilham alan, Gentoo Linux için
kılavuzlu (guided) bir kurulum aracıdır. Python ile yazılmıştır, menü tabanlı bir arayüzle
(soru-cevap şeklinde) sizi disk bölümlemeden bootloader'a kadar tüm kurulum sürecinde yönlendirir.

> ⚠️ **Önemli:** Bu proje bir taslak/scaffold olarak hazırlanmıştır. Gerçek bir kurulumdan önce
> mutlaka bir sanal makinede (QEMU/VirtualBox) test edin. Disk üzerinde **geri dönüşü olmayan**
> işlemler (bölümleme, formatlama) yapar.

## Özellikler

- Disk bölümleme (GPT, UEFI/BIOS otomatik algılama, ext4/btrfs/xfs, opsiyonel swap)
- En güncel stage3 tarball'ının otomatik bulunup indirilmesi (openrc/systemd, hardened varyantları dahil)
- `make.conf` oluşturma, Portage senkronizasyonu (`emerge-webrsync`), profil seçimi
- Zaman dilimi / locale ayarları
- Ağ yapılandırması (hostname + NetworkManager veya dhcpcd)
- Kernel kurulumu için 4 seçenek:
  - `genkernel` (otomatik derleme — archinstall'a en yakın deneyim)
  - `sys-kernel/gentoo-kernel-bin` (önceden derlenmiş, en hızlı)
  - `sys-kernel/gentoo-kernel` (dist-kernel, otomatik `.config` ile kaynaktan)
  - Manuel (`gentoo-sources` kurulur, `make menuconfig` size kalır)
- Otomatik `/etc/fstab` oluşturma (UUID tabanlı)
- GRUB kurulumu (UEFI ve BIOS için)
- Kullanıcı/parola/`sudo` yapılandırması

## Kullanım

Bir Gentoo (veya SystemRescue gibi) canlı ortamında, root olarak:

```bash
git clone <bu-repo>
cd ILY2
pip install --break-system-packages -e .
ily2
```

Komutlar boyunca sadece ekrana ne yapacağını yazdırıp hiçbir şeyi gerçekten çalıştırmayan
güvenli test modu:

```bash
ily2 --dry-run
```

## Proje Yapısı

```
ily2/
  __main__.py          # CLI giriş noktası
  lib/
    disk.py            # bölümleme / mkfs / mount
    stage3.py           # stage3 indirme + çıkarma
    portage.py          # make.conf, sync, profil
    chroot.py           # proc/sys/dev bağlama, chroot context manager
    kernel.py            # kernel kurulum stratejileri
    network.py           # hostname, NetworkManager/dhcpcd
    locale_tz.py         # saat dilimi + locale
    users.py             # root/kullanıcı parolaları, sudo
    bootloader.py        # GRUB
    fstab.py             # /etc/fstab üretimi
    menu.py              # questionary tabanlı TUI yardımcıları
    general.py            # SysCommand: subprocess sarmalayıcı (+ chroot + dry-run desteği)
    config.py             # JSON config kaydet/yükle
    output.py             # rich tabanlı konsol çıktıları
  scripts/
    guided.py            # ana kılavuzlu kurulum akışı
examples/
  config-sample.json      # örnek yapılandırma dosyası
```

## Yol Haritası / Eksikler

- [ ] Btrfs alt birim (subvolume) düzeni desteği
- [ ] LUKS disk şifreleme
- [ ] Masaüstü ortamı profilleri (GNOME/KDE/vb.) için hazır paket setleri
- [ ] GPG doğrulamalı stage3 indirme (şu an sadece HTTPS + tar)
- [ ] `--config` ile tam non-interactive (sessiz) kurulum modu
- [ ] Çoklu disk / RAID desteği

## Lisans

MIT.
