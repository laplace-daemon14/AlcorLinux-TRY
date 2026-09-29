# Alcor GNU/Linux Alpha 3 Pre-release

Alcor Alpha 3 is an Arch-based installer focused on profile-driven deployment and an isolated Algol tool environment.

> Alpha 3 is a testing release. Use a virtual machine or a disposable test system and keep backups of important data.

## Alpha 3 Features

- Calamares-based installation
- PyQt6 profile-selection frontend
- Host kernel selection
- Host display-manager selection
- Pentest, Daily, Carma, and Expert profiles
- Expert package profiles: None, Pentest, Daily, and Carma
- Individual package checkbox selection
- Algol Distrobox environment on first boot
- Automatic BlackArch repository setup inside Algol
- Selected packages installed inside Algol
- Installed-system initramfs generation
- Alcor first-boot systemd service
- Alcor deployment validation script

## Installation Architecture

Alpha 3 uses three stages:

```text
1. Live preparation
2. Calamares target installation
3. Installed-system first boot
```

### Live preparation

The preparation script:

- Enables BlackArch in the Live environment when required.
- Initializes the BlackArch keyring without accepting a full Live system upgrade.
- Installs `python-pyqt6`.
- Installs Calamares if it is missing.
- Disables Live `os-prober`.
- Installs the Alcor frontend and backend.
- Installs the Calamares backend module.
- Installs the single supported desktop launcher.

### Calamares target installation

The backend:

- Installs the selected kernel into the target host.
- Installs and enables LightDM with its GTK greeter and XFCE session.
- Installs Zsh, sets it as the installed user's default login shell, and copies available Live shell and XFCE Terminal settings without overwriting existing target files.
- Copies Live GRUB defaults, additional GRUB scripts, and themes into the installed system while leaving the Live-generated `grub.cfg` behind for Calamares to regenerate.
- Removes inherited ArchISO mkinitcpio files.
- Generates a normal installed-system initramfs.
- Copies the Alcor selection and Expert configuration.
- Installs the first-boot service.

### First boot

`alcor-firstboot.service` checks the first-boot state automatically:

1. Installs/starts the rootless user's systemd runtime without requiring a typed username or command.
2. Runs `/usr/local/bin/algol-init` automatically to create the `algol` Distrobox container.
3. Adds the BlackArch repository inside Algol and refreshes its package databases.
4. Routes selected packages to the host system or Algol: daily applications go to the host, while security tools go to Algol.
5. Sets the graphical default target and enables LightDM after Algol setup.
6. Removes the leftover Live `alcor` account only after successful setup, preserving its home directory.
7. Creates `/var/lib/alcor/initialized`.

The firstboot script verifies the Algol container before trusting an existing completion marker, repairs a stale marker automatically, and has no systemd startup timeout during the initial container download. The display manager is ordered after firstboot so Algol initialization and selected package routing happen first. Kernel, Distrobox/Podman, and desktop prerequisites are installed into the host during Calamares because the firstboot initializer depends on them.

The host kernel is shared with Algol. A kernel is never installed inside the container.
The installed desktop user starts in Zsh. Existing `.zshrc`, `.zprofile`, `.zshenv`, Bash startup files, and XFCE Terminal settings are copied from the Live user's home when present. The installed user's `.zshenv` adds `~/.local/bin` to `PATH` so commands exported from Algol, such as `sqlmap`, can be run by name in new Zsh sessions.
When a security package is installed through the Alcor package router, every executable file it provides directly under `/usr/bin` or `/usr/sbin` is exported to `~/.local/bin` under its real command name and receives an application-menu launcher that opens its `-h` help output in XFCE Terminal. The directory is added to `.zshenv` so all exported tool names work in new terminals. Packages providing GUI applications also export each installed `.desktop` file through Distrobox.
The router also installs Maltego's `libxtst` Java/X11 runtime dependency in Algol before installing Maltego.

To refresh a launcher for a tool already installed on an existing system after updating the router:

```bash
sudo install -m 0755 /home/alcor/alcor-installer/pacman /usr/local/bin/pacman
sudo pacman -S --needed sqlmap
source ~/.zshenv
```
If initialization fails, inspect its journal and rerun it after resolving the reported error.

To update firstboot files on an already installed system from the installer project directory:

```bash
cd /home/alcor/alcor-installer
sudo /usr/bin/pacman -S --needed distrobox podman
sudo install -m 0755 algol-init /usr/local/bin/algol-init
sudo install -m 0755 pacman /usr/local/bin/pacman
sudo install -m 0755 alcor-firstboot /usr/local/sbin/alcor-firstboot
sudo install -m 0644 alcor-firstboot.service /etc/systemd/system/alcor-firstboot.service
sudo systemctl daemon-reload
sudo rm -f /var/lib/alcor/initialized
sudo systemctl reset-failed alcor-firstboot.service
sudo systemctl restart alcor-firstboot.service
```

## Profiles

### AlcorPentest

Security package groups:

- Reconnaissance
- Web testing
- Wireless and network analysis
- Passwords and exploits
- OSINT and traffic tools
- Cloud and container security
- Forensics and reverse engineering
- Privacy and social testing

Default kernel: `linux`

### AlcorDaily

Daily-use package groups:

- Gaming
- Workspace and media
- Development
- Communication and files
- Terminal utilities
- Virtualization
- Monitoring and hardware

Default kernel: `linux-zen`

### AlcorCarma

Combines the Pentest and Daily package groups and installs both host kernels:

- Daily/Game (Zen): `linux-zen`
- CyberSEC (Linux): `linux`

### AlcorExpert

Expert mode provides independent controls for:

- Kernel
- Container engine
- Firewall
- Desktop
- Filesystem
- Security profile
- Bootloader
- Network profile
- Display manager

The Expert package profile controls the available package groups:

| Package profile | Result |
|---|---|
| None | No Algol packages |
| Pentest | Pentest groups |
| Daily | Daily groups |
| Carma | Pentest and Daily groups |

Packages remain individually selectable after choosing a package profile.

Default kernel: `linux-hardened`

## Display Manager

LightDM with XFCE is currently supported. KDE/SDDM, GNOME/GDM, and Hyprland are marked as coming soon in the installer.

LightDM is installed with its greeter and XFCE session, enabled at boot, and configured as the graphical login target.

## Live Setup

Copy the project:

```bash
sudo mkdir -p /home/alcor
sudo cp -a ./alcor-installer /home/alcor/alcor-installer
sudo chown -R alcor:alcor /home/alcor/alcor-installer
```

Make launchers executable:

```bash
chmod +x /home/alcor/alcor-installer/*.sh
chmod +x /home/alcor/alcor-installer/alcor-install
```

Install the desktop launcher:

```bash
mkdir -p /home/alcor/Desktop
cp /home/alcor/alcor-installer/alcor-install.desktop \
   /home/alcor/Desktop/alcor-install.desktop
chmod +x /home/alcor/Desktop/alcor-install.desktop
```

Run the preparation flow:

```bash
/home/alcor/alcor-installer/alcor-install
```

The launcher opens a terminal, runs `install-alcor-calamares.sh`, and starts the frontend after successful preparation.

To run the preparation script directly:

```bash
cd /home/alcor/alcor-installer
sudo bash install-alcor-calamares.sh
```

## Algol Verification

Check the first-boot service:

```bash
systemctl status alcor-firstboot.service
```

Successful completion:

```text
status=0/SUCCESS
Active: active (exited)
```

Check the completion marker:

```bash
test -f /var/lib/alcor/initialized && echo "Alcor firstboot completed"
```

Check the container:

```bash
distrobox list
```

Check BlackArch:

```bash
distrobox enter algol -- \
    grep -n -A3 -B1 blackarch /etc/pacman.conf
```

Check selected packages:

```bash
distrobox enter algol -- pacman -Q nikto
distrobox enter algol -- pacman -Q gobuster
pacman -Q vlc
pacman -Q firefox
```

## Alpha 3 Test Requirements

For reliable testing:

- Use an x86_64 Arch-based Live system.
- Use UEFI when possible.
- Provide at least 4 GB RAM.
- Provide at least 30 GB of disk space.
- Provide network access during preparation and first boot.
- Use a clean VM snapshot for each installation test.

Large Carma and Expert installations can require additional disk space and download time.

## Troubleshooting

### Frontend does not start

```bash
sudo pacman -S --needed --noconfirm python-pyqt6
python3 /home/alcor/alcor-installer/alcor_frontend.py
```

### First boot fails

```bash
systemctl status alcor-firstboot.service --no-pager
sudo journalctl -u alcor-firstboot.service -b --no-pager
test -e /var/lib/alcor/initialized && echo "First boot completed" || echo "First boot incomplete"
df -h
distrobox list
```

The first-boot setup does not block LightDM. If the display stays on a TTY, check:

```bash
systemctl get-default
systemctl status lightdm.service --no-pager
sudo journalctl -b -u lightdm.service --no-pager
```

### BlackArch is not visible

```bash
distrobox enter algol -- \
    grep -n -A3 -B1 blackarch /etc/pacman.conf
```

The package installation must not be considered successful unless the `[blackarch]` repository is present and the service exits with status `0`.

### Display manager is wrong

```bash
cat /etc/alcor/selection.txt
systemctl get-default
systemctl status display-manager.service
sudo journalctl -b -u lightdm.service --no-pager
sudo journalctl -b -u alcor-firstboot.service --no-pager
```

## Alpha 3 Limitations

- Alpha 3 is not a production release.
- Package availability depends on current Arch and BlackArch repositories.
- AUR packages are not built automatically; packages unavailable in configured repositories can fail during first boot.
- First boot requires network access.
- Large package profiles take time to download.
- Expert infrastructure settings are stored for deployment configuration, but some settings may require additional desktop-specific integration.
- The current workflow targets x86_64 Arch-based systems.
