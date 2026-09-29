#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OK=0
FAIL=0

pass() {
    printf '[ OK ] %s\n' "$1"
    OK=$((OK + 1))
}

fail() {
    printf '[FAIL] %s\n' "$1"
    FAIL=$((FAIL + 1))
}

check_file() {
    if [[ -f "$1" ]]; then
        pass "$2"
    else
        fail "$2 ($1)"
    fi
}

check_exec() {
    if [[ -x "$1" ]]; then
        pass "$2"
    else
        fail "$2 ($1)"
    fi
}

check_contains() {
    if [[ -f "$1" ]] && grep -qF "$3" "$1"; then
        pass "$2"
    else
        fail "$2 ($1)"
    fi
}

printf '%s\n' 'Alcor deployment check'
printf '%s\n\n' "Source: $ROOT_DIR"

check_file "$ROOT_DIR/alcor_frontend.py" "Frontend"
check_file "$ROOT_DIR/alcor_backend.sh" "Backend"
check_file "$ROOT_DIR/algol-init" "Algol initializer"
check_file "$ROOT_DIR/alcor-firstboot" "Automatic first-boot initializer"
check_file "$ROOT_DIR/alcor-firstboot.service" "First-boot systemd service"
check_file "$ROOT_DIR/pacman" "Package router"
check_contains "$ROOT_DIR/install-alcor-calamares.sh" \
    "BlackArch setup avoids a full Live system upgrade prompt" \
    "printf 'n\\n' | script -q -e -c"
check_contains "$ROOT_DIR/install-alcor-calamares.sh" \
    "BlackArch keyring setup reports expected network delay" \
    "Keyserver access can take a few minutes."
check_contains "$ROOT_DIR/algol-init" \
    "First-boot packages use the host package router" \
    '"$PACMAN_ROUTER" -S --needed --noconfirm "$package"'
check_contains "$ROOT_DIR/pacman" \
    "First-boot host packages are queued" "ALCOR_HOST_PACKAGE_QUEUE"
check_contains "$ROOT_DIR/pacman" \
    "Exported command directories are added to Zsh PATH" \
    '# Alcor: add exported commands to PATH'
check_contains "$ROOT_DIR/pacman" \
    "Exported CLI tools receive desktop menu entries" \
    'create_cli_menu_entry "$command_name" "$REAL_HOME/.local/bin/$command_name"'
check_contains "$ROOT_DIR/pacman" \
    "CLI menu entries open the tool help in XFCE Terminal" \
    'xfce4-terminal --hold --execute "${escaped_binary}" -h'
check_contains "$ROOT_DIR/pacman" \
    "GUI apps export their actual desktop file path" \
    'algol_command distrobox-export --app "$desktop_file"'
check_contains "$ROOT_DIR/pacman" \
    "Every package executable in /usr/bin or /usr/sbin is exported to the host PATH" \
    "awk '\$NF ~ /^\\/usr\\/s?bin\\/[^/]+\$/ { print \$NF }'"
check_contains "$ROOT_DIR/pacman" \
    "Every exported CLI binary receives its own desktop menu entry" \
    'create_cli_menu_entry "$command_name" "$REAL_HOME/.local/bin/$command_name"'
check_contains "$ROOT_DIR/pacman" \
    "Router discovers desktop file paths from the installed package" \
    'awk '\''$NF ~ /\.desktop$/ { print $NF }'\'''
check_contains "$ROOT_DIR/pacman" \
    "Maltego's Java runtime library is installed inside Algol" \
    'algol_command sudo pacman -S --needed --noconfirm libxtst'
check_contains "$ROOT_DIR/alcor-firstboot" \
    "Host packages use the system pacman binary" \
    '/usr/bin/pacman -S --needed --noconfirm "${HOST_PACKAGES[@]}"'
check_contains "$ROOT_DIR/alcor-firstboot.service" \
    "First boot initializes Algol before the display manager" \
    "Before=display-manager.service"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "First-boot executable is installed for the user" \
    '"$TARGET_ROOT/usr/local/bin/algol-init"'
check_contains "$ROOT_DIR/alcor-firstboot" \
    "First boot selects graphical target" \
    "systemctl set-default graphical.target"
check_contains "$ROOT_DIR/alcor-firstboot" \
    "First boot enables LightDM after Algol setup" \
    "systemctl enable lightdm.service"
check_contains "$ROOT_DIR/alcor-firstboot" \
    "First boot chooses a user other than Live alcor" \
    '$1 != "alcor"'
check_contains "$ROOT_DIR/alcor-firstboot" \
    "Live alcor account is removed after setup" \
    "userdel alcor"
check_contains "$ROOT_DIR/alcor-firstboot" \
    "First boot runs algol-init without a manual command" \
    "/usr/local/bin/algol-init"
check_contains "$ROOT_DIR/alcor-firstboot" \
    "First boot verifies that algol was created" \
    "distrobox list | grep -qw algol"
check_contains "$ROOT_DIR/alcor-firstboot.service" \
    "First boot is not cut off while downloading the container" \
    "TimeoutStartSec=infinity"
algol_init_line="$(grep -nF '/usr/local/bin/algol-init' "$ROOT_DIR/alcor-firstboot" | head -n 1 | cut -d: -f1)"
host_packages_line="$(grep -nF '/usr/bin/pacman -S --needed --noconfirm "${HOST_PACKAGES[@]}"' "$ROOT_DIR/alcor-firstboot" | cut -d: -f1)"
if [[ -n "$algol_init_line" && -n "$host_packages_line" && "$algol_init_line" -lt "$host_packages_line" ]]; then
    pass "Algol initializes before queued host packages are installed"
else
    fail "Algol initializes before queued host packages are installed"
fi
if grep -qF 'ConditionPathExists=!/var/lib/alcor/initialized' \
    "$ROOT_DIR/alcor-firstboot.service"; then
    fail "First boot can recover a stale initialized marker"
else
    pass "First boot can recover a stale initialized marker"
fi
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Installed system boots into graphical.target" \
    "ln -sfn /usr/lib/systemd/system/graphical.target"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Display manager is explicitly pulled into graphical.target" \
    'graphical.target.wants/$DISPLAY_MANAGER.service'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Display manager service alias is explicitly installed" \
    'systemd/system/display-manager.service'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "LightDM host includes Xorg" "xorg-server"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Target installation includes Zsh" "    zsh"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Target installation includes Distrobox" "    distrobox"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Target installation includes Podman" "    podman"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Installed user gets Zsh as default shell" \
    'usermod --shell /usr/bin/zsh "$username"'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Live Zsh configuration is copied without overwriting" \
    'for config_file in .zshrc .zprofile .zshenv .bashrc .bash_profile .profile'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Exported Distrobox commands are added to the installed user's Zsh PATH" \
    '# Alcor: add exported commands to PATH'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Zsh PATH setup preserves existing PATH entries" \
    'export PATH="$HOME/.local/bin:$PATH"'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Live GRUB defaults are copied" 'cp -a "$live_default" "$target_default"'
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "GRUB customization directories are merged" \
    "usr/share/grub/themes"
check_contains "$ROOT_DIR/alcor_backend.sh" \
    "Live grub.cfg is not copied into the installed system" \
    "Calamares will generate a target-specific configuration."
check_contains "$ROOT_DIR/alcor_frontend.py" \
    "Long package groups can be collapsed" "Show packages"
check_contains "$ROOT_DIR/alcor_frontend.py" \
    "Unimplemented desktop options are marked" "Coming Soon"
check_file "$ROOT_DIR/install-alcor-calamares.sh" "Calamares preparation script"
check_file "$ROOT_DIR/alcor-install" "Installer launcher"
check_file "$ROOT_DIR/alcor-install.desktop" "Installer desktop entry"

for image in red_alcor.png blue_alcor.png purple_alcor.png expert_alcor.png; do
    check_file "$ROOT_DIR/$image" "Branding asset: $image"
done

check_file "$ROOT_DIR/calamares/modules/alcor_backend.conf" \
    "Alcor Calamares module configuration"
check_contains "$ROOT_DIR/calamares/modules/alcor_backend.conf" \
    "Backend command is connected" "/usr/local/lib/alcor/alcor_backend.sh"

if [[ -x "$ROOT_DIR/alcor_backend.sh" ]]; then
    pass "Backend is executable"
else
    fail "Backend is executable ($ROOT_DIR/alcor_backend.sh)"
fi

if [[ -x "$ROOT_DIR/algol-init" ]]; then
    pass "Algol initializer is executable"
else
    fail "Algol initializer is executable ($ROOT_DIR/algol-init)"
fi

if [[ -e "$ROOT_DIR/alcor-installer.desktop" ]]; then
    fail "Obsolete alcor-installer.desktop is absent"
else
    pass "Obsolete alcor-installer.desktop is absent"
fi

if [[ -f /etc/calamares/settings.conf ]]; then
    pass "Calamares settings are installed"
else
    printf '[INFO] Calamares settings are not installed in the current environment.\n'
fi

if [[ -f /etc/alcor/selection.txt ]]; then
    check_contains "/etc/alcor/selection.txt" \
        "Display manager selection exists" "DISPLAY_MANAGER:"
else
    printf '[INFO] No installed Alcor selection file; run this on the installed system to check it.\n'
fi

printf '\n%s\n' 'Summary'
printf 'Passed: %d\nFailed: %d\n' "$OK" "$FAIL"

if [[ "$FAIL" -eq 0 ]]; then
    printf '%s\n' 'Alcor deployment check passed.'
    exit 0
fi

printf '%s\n' 'Alcor deployment check found problems.'
exit 1
