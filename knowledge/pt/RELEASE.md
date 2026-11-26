# RELEASE · GitHub Actions e publicação
- Em **Actions → Compilar EMA Trader → Run workflow**, selecione o branch desejado. `publish_release` vem ativado. O GitHub cria a tag `v0.1.<número da execução>`, notas e Release com todos os pacotes. Um rerun da mesma execução atualiza os anexos.
- Matriz: Windows x64 GUI/CLI (ZIP), macOS Apple Silicon e Intel GUI/CLI (TAR.GZ), Linux x64 e ARM64 apenas CLI (TAR.GZ). Os pacotes macOS não são notarizados.
- O workflow testa antes de empacotar. Só publica com os cinco pacotes presentes. Desmarque a publicação para Artifacts com 14 dias de retenção. A escrita no repositório pertence somente ao job de publicação.
- Arquivo `.github/workflows/build.yml`. [Execuções](https://github.com/ramonck/EMATrader/actions/workflows/build.yml) · [Releases](https://github.com/ramonck/EMATrader/releases)
