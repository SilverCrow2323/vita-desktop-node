#!/bin/sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)"
VERSION="$(PYTHONPATH="$ROOT/server" python3 -c 'import version; print(version.APP_VERSION)' | sed 's/[^A-Za-z0-9.+~:-]/-/g')"
PKG="$ROOT/dist/deb-root"
OUT="$ROOT/dist/vitamon_${VERSION}_all.deb"

rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN" "$PKG/usr/lib/vitamon" "$PKG/usr/bin" \
         "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/128x128/apps"

cp "$ROOT/packaging/debian/control" "$PKG/DEBIAN/control"
sed -i "s/^Version:.*/Version: $VERSION/" "$PKG/DEBIAN/control"
cp -R "$ROOT/server/." "$PKG/usr/lib/vitamon/"
if [ -f "$ROOT/vita/sce_sys/icon0.png" ]; then
    cp "$ROOT/vita/sce_sys/icon0.png" "$PKG/usr/lib/vitamon/icon0.png"
fi
cp "$ROOT/packaging/linux/vitamon" "$PKG/usr/bin/vitamon"
chmod 0755 "$PKG/usr/bin/vitamon"
cp "$ROOT/packaging/debian/vitamon.desktop" "$PKG/usr/share/applications/vitamon.desktop"
if [ -f "$ROOT/vita/sce_sys/icon0.png" ]; then
    cp "$ROOT/vita/sce_sys/icon0.png" "$PKG/usr/share/icons/hicolor/128x128/apps/vitamon.png"
fi

mkdir -p "$ROOT/dist"
dpkg-deb --build --root-owner-group "$PKG" "$OUT"
printf 'Built package: %s\n' "$OUT"
