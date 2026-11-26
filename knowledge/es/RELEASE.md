# RELEASE · GitHub Actions y publicación
- Abre **Actions → Compilar EMA Trader → Run workflow** y selecciona la rama. `publish_release` se activa por defecto. GitHub crea etiqueta `v0.1.<número de ejecución>`, notas y Release con todos los paquetes. Repetir la misma ejecución actualiza los adjuntos.
- Matriz: Windows x64 GUI/CLI (ZIP), macOS Apple Silicon e Intel GUI/CLI (TAR.GZ), Linux x64 y ARM64 solo CLI (TAR.GZ). Los paquetes macOS carecen de notarización.
- Se ejecutan pruebas antes de empaquetar y se publica cuando existen los cinco paquetes. Desactiva la publicación para artefactos disponibles 14 días. El job de publicación valida los cinco paquetes, crea atestaciones de procedencia y publica SHA256SUMS. Las Actions están fijadas por SHA.
- Archivo `.github/workflows/build.yml`. [Ejecuciones](https://github.com/ramonck/EMATrader/actions/workflows/build.yml) · [Releases](https://github.com/ramonck/EMATrader/releases)

Verifica el paquete descargado antes de extraerlo.

```sh
gh attestation verify EMA-Trader-windows-x64.zip --repo ramonck/EMATrader --signer-workflow ramonck/EMATrader/.github/workflows/build.yml
```

La atestación acredita la procedencia en GitHub. SmartScreen evalúa por separado la firma Authenticode y la reputación del ejecutable. [GitHub](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) · [Microsoft](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)
