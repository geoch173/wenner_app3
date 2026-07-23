[app]
title = Wenner Resistivity
package.name = wennerresistivity
package.domain = org.fieldtools

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0
requirements = python3==3.11.8,hostpython3==3.11.8,kivy

orientation = portrait
fullscreen = 0

android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Reasonable modern API level; adjust if Play Store requires higher at build time
android.api = 33
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
