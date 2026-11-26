# RELEASE · GitHub Actions and publication
- Open **Actions → Compilar EMA Trader → Run workflow** and choose a branch. `publish_release` defaults to on. GitHub makes a `v0.1.<run number>` tag, notes and Release with all packages. Rerunning the same run updates its assets.
- Matrix: Windows x64 GUI/CLI (ZIP), macOS Apple Silicon and Intel GUI/CLI (TAR.GZ), Linux x64 and ARM64 CLI only (TAR.GZ). macOS packages are not notarized.
- The workflow tests before packaging and publishes only once all five packages exist. Turn publication off for artifacts retained for 14 days. Only the release job can write to the repository.
- File `.github/workflows/build.yml`. [Runs](https://github.com/ramonck/EMATrader/actions/workflows/build.yml) · [Releases](https://github.com/ramonck/EMATrader/releases)
