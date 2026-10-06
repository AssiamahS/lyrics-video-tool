#!/bin/zsh
# Build LyricLook.app with SwiftPM (no Xcode needed) and install it to ~/Applications.
set -euo pipefail
cd "$(dirname "$0")"
VERSION=$(cat ../VERSION)
swift build -c release
[[ -f AppIcon.icns ]] || python3 make_icon.py
APP=dist/LyricLook.app
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp .build/release/LyricLook "$APP/Contents/MacOS/LyricLook"
cp AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>LyricLook</string>
  <key>CFBundleDisplayName</key><string>LyricLook</string>
  <key>CFBundleIdentifier</key><string>com.djsly.lyriclook</string>
  <key>CFBundleExecutable</key><string>LyricLook</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>${VERSION}</string>
  <key>CFBundleVersion</key><string>${VERSION}</string>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - "$APP"
mkdir -p ~/Applications
rm -rf ~/Applications/LyricLook.app
cp -R "$APP" ~/Applications/
echo "Installed ~/Applications/LyricLook.app ($VERSION)"
