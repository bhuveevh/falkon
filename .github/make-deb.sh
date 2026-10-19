#!/bin/sh
# Packages the staged Falkon install tree into an installable .deb.
# Usage: sh .github/make-deb.sh <version>
set -e

VERSION="${1:-1.0.0}"
PKGNAME="polecat-falkon"
STAGE="$PWD/stage"
PKG="$PWD/pkg"

if [ ! -d "$STAGE/usr" ]; then
    echo "ERROR: nothing staged in $STAGE" >&2
    exit 1
fi

rm -rf "$PKG"
mkdir -p "$PKG/DEBIAN"
cp -a "$STAGE/." "$PKG/"

# --- work out the shared-library dependencies properly --------------------
# The private Falkon library lives in the staged tree, so make it visible to the
# linker first. Without this dpkg-shlibdeps cannot follow the dependency chain
# and the generated Depends line comes out far too short.
if [ -d "$PKG/usr/lib/x86_64-linux-gnu" ]; then
    cp -a "$PKG/usr/lib/x86_64-linux-gnu/." /usr/lib/x86_64-linux-gnu/ || true
    ldconfig || true
fi

mkdir -p debian
cat > debian/control <<EOF
Source: $PKGNAME
Section: web
Priority: optional
Maintainer: Bhuvee Paswan <bhuveepaswan@gmail.com>
Standards-Version: 4.6.2
Build-Depends: debhelper-compat (= 13)

Package: $PKGNAME
Architecture: any
Depends: \${shlibs:Depends}, \${misc:Depends}
Description: Falkon-based web browser with a custom interface
EOF

BIN=""
for cand in "$PKG"/usr/bin/*; do
    [ -f "$cand" ] || continue
    BIN="$BIN -e $cand"
done
for cand in "$PKG"/usr/lib/x86_64-linux-gnu/libFalkon*.so*; do
    [ -f "$cand" ] || continue
    BIN="$BIN -e $cand"
done

DEPS=""
if command -v dpkg-shlibdeps >/dev/null 2>&1; then
    dpkg-shlibdeps -O $BIN > /tmp/shlibdeps.out 2> /tmp/shlibdeps.err || true
    sed -n '1,15p' /tmp/shlibdeps.err || true
    DEPS=$(sed -n 's/^shlibs:Depends=//p' /tmp/shlibdeps.out | tr '\n' ' ')
fi

if [ -z "$DEPS" ]; then
    echo "NOTE: dpkg-shlibdeps produced nothing, using the fallback list"
    DEPS="libc6, libstdc++6, libqt6core6, libqt6gui6, libqt6widgets6, libqt6network6, libqt6sql6, libqt6sql6-sqlite, libqt6printsupport6, libqt6webchannel6, libqt6webenginecore6, libqt6webenginewidgets6, libqt6quickwidgets6, libqt6svg6, libkf6archive6, libkf6i18n6, libkf6wallet6, libkf6kio6, libkf6crash6, libkf6coreaddons6, libkf6purpose6, libkf6jobwidgets6"
fi

cat > "$PKG/DEBIAN/control" <<EOF
Package: $PKGNAME
Version: $VERSION
Section: web
Priority: optional
Architecture: amd64
Maintainer: Bhuvee Paswan <bhuveepaswan@gmail.com>
Installed-Size: $(du -sk "$PKG" | cut -f1)
Depends: $DEPS
Description: Falkon-based web browser with a custom interface
 A Qt/QtWebEngine web browser derived from Falkon (KDE), with a custom
 user interface, Material icons and a personalised new tab page.
EOF

mkdir -p "$PKG/usr/share/doc/$PKGNAME"
if [ -f COPYING ]; then
    cp COPYING "$PKG/usr/share/doc/$PKGNAME/copyright"
fi

OUT="${PKGNAME}_${VERSION}_amd64.deb"
dpkg-deb --build --root-owner-group "$PKG" "$OUT"
echo "Built $OUT"
