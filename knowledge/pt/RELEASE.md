# RELEASE · GitHub Actions e publicação
- Em **Actions → Compilar EMA Trader → Run workflow**, selecione o branch desejado. `publish_release` vem ativado. O GitHub cria a tag `v0.1.<número da execução>`, notas e Release com todos os pacotes. Um rerun da mesma execução atualiza os anexos.
- Matriz: Windows x64 GUI/CLI (ZIP), macOS Apple Silicon e Intel GUI/CLI (TAR.GZ), Linux x64 e ARM64 apenas CLI (TAR.GZ). Os pacotes macOS não são notarizados.
- O workflow testa antes de empacotar. Só publica com os cinco pacotes presentes. Desmarque a publicação para Artifacts com 14 dias de retenção. O job de publicação valida os cinco pacotes, cria as atestações de procedência e publica o arquivo SHA256SUMS. As Actions estão fixadas por SHA.
- Arquivo `.github/workflows/build.yml`. [Execuções](https://github.com/ramonck/EMATrader/actions/workflows/build.yml) · [Releases](https://github.com/ramonck/EMATrader/releases)

Verifique o pacote baixado antes de extrair.

```sh
gh attestation verify EMA-Trader-windows-x64.zip --repo ramonck/EMATrader --signer-workflow ramonck/EMATrader/.github/workflows/build.yml
```

A atestação comprova a procedência no GitHub. O SmartScreen avalia a assinatura Authenticode e a reputação do executável por conta própria. [GitHub](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations) · [Microsoft](https://learn.microsoft.com/windows/apps/package-and-deploy/smartscreen-reputation)
