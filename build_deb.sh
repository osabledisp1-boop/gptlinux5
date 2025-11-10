#!/usr/bin/env bash
set -euo pipefail
PKGNAME="gptlinux5"
VERSION="1.0-1"
OUT="${PKGNAME}_${VERSION}_all.deb"

rm -rf build
mkdir -p build/usr/bin
cp -a src/gptlinux5.py build/usr/bin/gptlinux5
cp -a src/gptlinux5d.py build/usr/bin/gptlinux5d
chmod +x build/usr/bin/gptlinux5 build/usr/bin/gptlinux5d

mkdir -p build/DEBIAN
cp -a debian/control build/DEBIAN/control
chmod 755 build/DEBIAN
chmod 644 build/DEBIAN/control

dpkg-deb --build build "$OUT"
echo "Package built: $OUT"
