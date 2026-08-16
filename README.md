# AlcorLinux

**AlcorLinux**, [archiso](https://gitlab.archlinux.org/archlinux/archiso) altyapısı üzerine inşa edilmiş, Arch Linux tabanlı özel bir Live/Kurulum ISO profilidir.

## ✨ Hakkında

Bu depo, AlcorLinux'un ISO imajını oluşturmak için gereken tüm profil dosyalarını içerir: paket listeleri, önyükleme (boot) yapılandırmaları, sistem ayarları ve `airootfs` üzerinden özelleştirilmiş kök dosya sistemi şablonu.

## 📁 Proje Yapısı

```
.
├── airootfs/            # Canlı ortamın kök dosya sistemi şablonu (etc/, skel/, vb.)
├── efiboot/loader/       # UEFI önyükleme yapılandırması
├── grub/                 # GRUB önyükleyici yapılandırması
├── releng/               # Release engineering betikleri ve yardımcı dosyalar
├── syslinux/             # BIOS/Legacy önyükleme yapılandırması (isolinux/syslinux)
├── bootstrap_packages     # Bootstrap aşamasında kurulacak paket listesi
├── packages.x86_64       # Canlı ortama dahil edilecek paketlerin listesi
├── pacman.conf           # ISO derlemesi için pacman yapılandırması
└── profiledef.sh          # archiso profil tanım dosyası (ISO adı, sıkıştırma, vb.)
```

## 🛠️ Gereksinimler

ISO'yu derlemek için bir Arch Linux (veya türevi) sistemde aşağıdaki paketlerin kurulu olması gerekir:

```bash
sudo pacman -S archiso
```

## 🚀 Derleme (Build)

Depoyu klonladıktan sonra proje kök dizininde aşağıdaki komutu çalıştırın:

```bash
git clone https://github.com/laplace-daemon14/AlcorLinux-TRY.git
cd AlcorLinux-TRY
sudo mkarchiso -v -w work/ -o out/ .
```

- `-w` : Geçici derleme dizini (build çıktısı, gitignore'a dahildir)
- `-o` : Oluşturulan `.iso` dosyasının kaydedileceği çıktı dizini

Derleme tamamlandığında `out/` klasöründe önyüklenebilir bir `.iso` dosyası oluşur.

## 💿 ISO'yu Test Etme

Derlenen ISO'yu bir sanal makinede (QEMU örneği) hızlıca test edebilirsiniz:

```bash
qemu-system-x86_64 -m 4096 -enable-kvm -cdrom out/*.iso
```

## 🤝 Katkıda Bulunma

Katkılar memnuniyetle karşılanır! Bir özellik eklemeden veya hata düzeltmeden önce:

1. Bu depoyu fork'layın
2. Yeni bir dal (branch) oluşturun (`git checkout -b ozellik/yeni-ozellik`)
3. Değişikliklerinizi commit'leyin
4. Dalınızı push'layın ve bir Pull Request açın

## 📄 Lisans

Lisans bilgisi henüz belirtilmemiştir. Eklemek isterseniz bir `LICENSE` dosyası oluşturmanız önerilir.

## ⚠️ Not

Bu proje geliştirme aşamasındadır ("TRY" adından da anlaşılacağı gibi deneysel bir profildir). Üretim ortamında kullanmadan önce dikkatli test edilmesi tavsiye edilir.
