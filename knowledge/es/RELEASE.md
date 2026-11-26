# RELEASE · GitHub Actions y publicación
- Abre **Actions → Compilar EMA Trader → Run workflow** y selecciona la rama. `publish_release` se activa por defecto. GitHub crea etiqueta `v0.1.<número de ejecución>`, notas y Release con todos los paquetes. Repetir la misma ejecución actualiza los adjuntos.
- Matriz: Windows x64 GUI/CLI (ZIP), macOS Apple Silicon e Intel GUI/CLI (TAR.GZ), Linux x64 y ARM64 solo CLI (TAR.GZ). Los paquetes macOS carecen de notarización.
- Se ejecutan pruebas antes de empaquetar y se publica cuando existen los cinco paquetes. Desactiva la publicación para artefactos disponibles 14 días. Solo el job de publicación puede escribir en el repositorio.
- Archivo `.github/workflows/build.yml`. [Ejecuciones](https://github.com/ramonck/EMATrader/actions/workflows/build.yml) · [Releases](https://github.com/ramonck/EMATrader/releases)
