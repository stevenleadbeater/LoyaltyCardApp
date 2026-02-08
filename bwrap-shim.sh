#!/bin/sh
# bwrap replacement for QEMU-emulated flatpak builds.
#
# Real bwrap needs user namespaces which don't work under QEMU.
# This shim processes bind-mount, env, chdir, and symlink arguments
# and applies them inside a new mount namespace (unshare -m) which
# only needs root — no user namespaces required.
#
# Requires: --privileged Docker container.

set -e

log() { echo "bwrap-shim: $*" >&2; }

log "invoked with $# args: $*"

# Collect mount operations in a temp file (one per line, tab-separated)
MOUNTS=$(mktemp)
trap "rm -f $MOUNTS" EXIT

CHDIR=""

while [ $# -gt 0 ] && [ "$1" != "--" ]; do
    case "$1" in
        --bind|--dev-bind)
            printf 'BIND\t%s\t%s\n' "$2" "$3" >> "$MOUNTS"
            shift 3 ;;
        --ro-bind)
            printf 'ROBIND\t%s\t%s\n' "$2" "$3" >> "$MOUNTS"
            shift 3 ;;
        --bind-try|--ro-bind-try)
            printf 'TRYBIND\t%s\t%s\n' "$2" "$3" >> "$MOUNTS"
            shift 3 ;;
        --symlink)
            printf 'SYMLINK\t%s\t%s\n' "$2" "$3" >> "$MOUNTS"
            shift 3 ;;
        --tmpfs)
            printf 'TMPFS\t%s\n' "$2" >> "$MOUNTS"
            shift 2 ;;
        --proc)
            printf 'PROC\t%s\n' "$2" >> "$MOUNTS"
            shift 2 ;;
        --dev)
            printf 'DEV\t%s\n' "$2" >> "$MOUNTS"
            shift 2 ;;
        --setenv)
            export "$2=$3"
            shift 3 ;;
        --unsetenv)
            unset "$2" 2>/dev/null || true
            shift 2 ;;
        --chdir)
            CHDIR="$2"
            shift 2 ;;
        # Two-argument options to skip
        --uid|--gid|--hostname|--lock-file|--sync-fd|--seccomp|--add-seccomp-fd|\
--info-fd|--json-status-fd|--block-fd|--userns-block-fd|--cap-add|--cap-drop|\
--perms|--size|--file|--bind-data|--ro-bind-data|--userns|--userns2|--pidns|\
--exec-label|--file-label|--remount-ro)
            shift 2 ;;
        # Single-flag options to skip
        --unshare-*|--share-net|--die-with-parent|--new-session|--as-pid-1|\
--clearenv)
            shift ;;
        # Unknown: skip one arg
        *)
            shift ;;
    esac
done
# Skip the -- separator
[ "$1" = "--" ] && shift

# If no mounts, just run directly
if [ ! -s "$MOUNTS" ]; then
    log "no mounts requested, running directly: $*"
    [ -n "$CHDIR" ] && cd "$CHDIR"
    exec "$@"
fi

log "$(wc -l < "$MOUNTS") mount ops queued, chdir=$CHDIR, cmd=$*"

# Apply mounts in a new mount namespace, then exec the command.
# We pass the mount file and chdir via env vars.
export _BWRAP_MOUNTS="$MOUNTS"
export _BWRAP_CHDIR="$CHDIR"

# Test whether unshare -m works at all under this kernel/QEMU combo
if unshare -m true 2>/dev/null; then
    log "unshare -m works, using mount namespace"
    exec unshare -m sh -c '
        while IFS="	" read -r OP A1 A2; do
            case "$OP" in
                BIND|ROBIND)
                    [ -e "$A1" ] || continue
                    if [ -d "$A1" ]; then
                        mkdir -p "$A2" 2>/dev/null || true
                    else
                        mkdir -p "$(dirname "$A2")" 2>/dev/null || true
                        touch "$A2" 2>/dev/null || true
                    fi
                    mount --bind "$A1" "$A2"
                    ;;
                TRYBIND)
                    [ -e "$A1" ] || continue
                    if [ -d "$A1" ]; then
                        mkdir -p "$A2" 2>/dev/null || true
                    else
                        mkdir -p "$(dirname "$A2")" 2>/dev/null || true
                        touch "$A2" 2>/dev/null || true
                    fi
                    mount --bind "$A1" "$A2" 2>/dev/null || true
                    ;;
                SYMLINK)
                    mkdir -p "$(dirname "$A2")" 2>/dev/null || true
                    ln -sf "$A1" "$A2" 2>/dev/null || true
                    ;;
                TMPFS)
                    mkdir -p "$A1" 2>/dev/null || true
                    mount -t tmpfs tmpfs "$A1"
                    ;;
                PROC)
                    mkdir -p "$A1" 2>/dev/null || true
                    mount -t proc proc "$A1"
                    ;;
                DEV)
                    mkdir -p "$A1" 2>/dev/null || true
                    mount --bind /dev "$A1"
                    ;;
            esac
        done < "$_BWRAP_MOUNTS"
        [ -n "$_BWRAP_CHDIR" ] && cd "$_BWRAP_CHDIR"
        exec "$@"
    ' _ "$@"
else
    log "WARNING: unshare -m FAILED (likely QEMU limitation), running without mount namespace"
    # Apply symlinks and env directly (skip bind mounts — they need a mount namespace)
    while IFS="	" read -r OP A1 A2; do
        case "$OP" in
            SYMLINK)
                mkdir -p "$(dirname "$A2")" 2>/dev/null || true
                ln -sf "$A1" "$A2" 2>/dev/null || true
                ;;
        esac
    done < "$MOUNTS"
    [ -n "$CHDIR" ] && cd "$CHDIR"
    log "falling back to direct exec: $*"
    exec "$@"
fi
