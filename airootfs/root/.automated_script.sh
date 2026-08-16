#!/usr/bin/env bash
#
# AlcorLinux automated startup script handler
# Reads "script=" from /proc/cmdline, fetches it (local or remote), and executes it on tty1.

set -u

script_cmdline() {
    local param
    for param in $(</proc/cmdline); do
        case "${param}" in
            script=*)
                echo "${param#*=}"
                return 0
                ;;
        esac
    done
}

log() {
    printf '%s: %s\n' "$0" "$1"
}

automated_script() {
    local script rt
    script="$(script_cmdline)"

    if [[ -z "${script}" ]]; then
        return 0
    fi

    if [[ -x /tmp/startup_script ]]; then
        log "startup script already present, skipping fetch"
        return 0
    fi

    if [[ "${script}" =~ ^((http|https|ftp|tftp)://) ]]; then
        log "downloading ${script}"
        # There's no synchronization for network availability before executing this script; to ensure the
        # network is online, we use a transient systemd service that depends on network-online.target to
        # download the script rather than manually polling the target.
        systemd-run --pty --quiet \
            -p Wants=network-online.target \
            -p After=network-online.target \
            curl "${script}" \
                --location \
                --retry-connrefused \
                --retry 10 \
                --fail \
                --silent \
                --show-error \
                -o /tmp/startup_script
        rt=$?
    else
        if [[ ! -f "${script}" ]]; then
            log "local script '${script}' not found"
            return 1
        fi
        cp "${script}" /tmp/startup_script
        rt=$?
    fi

    if [[ ${rt} -ne 0 ]]; then
        log "failed to fetch script (exit code ${rt})"
        return "${rt}"
    fi

    if [[ ! -s /tmp/startup_script ]]; then
        log "fetched script is empty, aborting"
        return 1
    fi

    chmod +x /tmp/startup_script

    log "executing automated script"
    # Note: this script runs while other services (e.g. pacman-init) may still be in progress. If your
    # script depends on other services, synchronize with "systemctl is-system-running --wait" first.
    /tmp/startup_script
}

if [[ "$(tty)" == "/dev/tty1" ]]; then
    automated_script
fi