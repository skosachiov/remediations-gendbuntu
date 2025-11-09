#!/bin/bash
set -e

# Build and Sign UKI for Debian with Secure Boot
# Usage: ./scripts/build-signed-uki.sh

echo "=== UKI Build and Sign Script ==="

# Configuration
OUTPUT_DIR="${OUTPUT_DIR:-./artifacts}"
UNSIGNED_UKI="linux.uki"
SIGNED_UKI="linux-signed.uki"
CMDLINE="root=/dev/mapper/crypt-root ro rd.auto rd.luks=1 rd.luks.options=tpm2-device=auto rootflags=subvol=@rootfs quiet"

# Validate environment
if [ -z "$SB_DB_KEY" ]; then
    echo "ERROR: SB_DB_KEY environment variable not set"
    echo "Please set the Secure Boot DB private key as SB_DB_KEY"
    exit 1
fi

if [ ! -f "assets/esl/DB.crt" ]; then
    echo "ERROR: DB.crt not found at assets/esl/DB.crt"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== Installing required packages ==="
apt-get update
apt-get install -y \
    sbsigntool \
    linux-image-amd64 \
    linux-headers-amd64 \
    systemd \
    systemd-ukify \
    systemd-boot-efi \
    cryptsetup \
    dracut \
    systemd-cryptsetup \
    tpm2-tools \
    tpm2-tss-engine-tools \
    tpm2-abrmd \
    cryptsetup-initramfs \
    efibootmgr \
    binutils \
    gnutls-bin \
    btrfs-progs

# Detect kernel version
KERNEL_VERSION=$(ls -1 /boot/vmlinuz-* | sort | tail -n1 | sed 's/\/boot\/vmlinuz-//')
if [ -z "$KERNEL_VERSION" ]; then
    echo "ERROR: Could not detect kernel version"
    exit 1
fi

echo "Detected kernel version: $KERNEL_VERSION"

# Build initrd
SCRIPT_DIR=$(dirname $0)
cp -f $SCRIPT_DIR/dracut.conf /etc/
dracut --no-hostonly --force --kver $KERNEL_VERSION

echo "=== Building UKI ==="
ukify build \
    --linux="/boot/vmlinuz-$KERNEL_VERSION" \
    --initrd="/boot/initrd.img-$KERNEL_VERSION" \
    --cmdline="$CMDLINE" \
    --output="/workspace/$UNSIGNED_UKI" \
    --uname="$KERNEL_VERSION"

echo "=== Setting up signing environment ==="
SIGNING_DIR=$(mktemp -d)
trap 'rm -rf "$SIGNING_DIR"' EXIT

echo "$SB_DB_KEY" > "$SIGNING_DIR/DB.key"
chmod 600 "$SIGNING_DIR/DB.key"
cp assets/esl/DB.crt "$SIGNING_DIR/"

echo "=== Signing UKI ==="
sbsign --key "$SIGNING_DIR/DB.key" \
       --cert "$SIGNING_DIR/DB.crt" \
       --output "/workspace/$SIGNED_UKI" \
       "/workspace/$UNSIGNED_UKI"

echo "=== Verifying signature ==="
sbverify --list "/workspace/$SIGNED_UKI"
sbverify --cert "$SIGNING_DIR/DB.crt" "/workspace/$SIGNED_UKI"

echo "=== Moving artifacts to output directory ==="
mv "/workspace/$UNSIGNED_UKI" "$OUTPUT_DIR/"
mv "/workspace/$SIGNED_UKI" "$OUTPUT_DIR/"

echo "=== Cleaning up ==="
rm -rf "$SIGNING_DIR"

echo "=== Build completed successfully ==="
echo "Kernel version: $KERNEL_VERSION"
echo "Unsigned UKI: $OUTPUT_DIR/$UNSIGNED_UKI"
echo "Signed UKI: $OUTPUT_DIR/$SIGNED_UKI"
ls -la "$OUTPUT_DIR/"
