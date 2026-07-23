# Wenner Soil Resistivity Calculator (Android)

A small Kivy app that replaces the manual Excel workflow for Wenner four-electrode
soil resistivity testing.

## What it does
- Input per electrode spacing `a` (m): two measurement pairs `V1/I1`, `V2/I2` (mV, mA)
- Computes, per spacing:
  - `R = V / I`
  - `rho = 2 * pi * a * R`  (apparent resistivity, Ohm-meter)
  - `rho_avg` = average of the two measurement positions
- Plots `rho_avg` vs. spacing `a` (spacing approximates test depth) as a
  resistivity-depth chart, drawn directly on a Kivy Canvas (no matplotlib
  dependency, keeps the APK small)
- Exports all rows to a CSV file in the app's private storage folder

This matches the calculation used in `Template_Wenner_Soil_Resistivity_r2.xls`
(verified: a=0.5, V=1mV, I=2mA -> rho = 1.5708 Ohm.m in both the spreadsheet
and this app).

## Files
- `main.py` — the app
- `buildozer.spec` — Android packaging configuration
- `.github/workflows/build.yml` — GitHub Actions workflow that builds the
  `.apk` for you automatically (no local Android SDK/NDK setup needed)

## Building the APK — recommended: GitHub Actions
Building an Android APK requires the Android SDK, NDK, and a full Linux
build toolchain (several GB of downloads) — not something that can be done
in a small sandbox. The easiest path:

1. Create a new GitHub repository and push this folder to it.
2. Go to the repo's **Actions** tab -> select **Build APK** -> **Run workflow**
   (or just push to `main`, it runs automatically).
3. Wait for the build (first build takes ~20–30 minutes; it downloads and
   caches the Android SDK/NDK). When it finishes, download the `.apk` from
   the workflow run's **Artifacts** section.
4. Transfer the `.apk` to your Android phone and install it (you'll need to
   allow "install from unknown sources" once, since it isn't from the Play
   Store).

## Building locally (alternative)
If you have a Linux machine (or WSL) and want to build locally instead:
```bash
pip install buildozer cython==0.29.33
sudo apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool \
    pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
    cmake libffi-dev libssl-dev
buildozer android debug
```
The first run downloads the Android SDK/NDK automatically (large, slow).
The resulting APK appears in `bin/`.

## Testing on desktop first
You can run the app on a regular PC before building the APK, to check the
UI and math:
```bash
pip install kivy
python main.py
```

## Notes / possible next steps
- Electrode spacing defaults follow a common IEEE 81 Wenner test sequence
  (0.5, 1, 2, 4, 8, 12, 16, 20 m) — edit freely, rows can be added/removed.
- CSV export currently writes to the app's private data directory
  (`app.user_data_dir`). If you want it saved to a shared/Downloads folder
  instead, that needs Android's scoped-storage APIs (via `plyer` or
  `androidstorage4kivy`) — happy to add this if useful.
- If you'd rather not deal with APK builds at all, this same calculator
  could be delivered as a simple web page (HTML/JS) that works in any
  Android browser and can be "Added to Home Screen" to behave like an app,
  with no build toolchain required. Let me know if you'd prefer that route.
