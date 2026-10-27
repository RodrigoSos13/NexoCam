# Testes e evidências — 27/10/2026

## Linux

CachyOS, kernel 7.3.0-4-cachyos, Python 3.14.8. Dependências em .venv e snapshot
em linux/requirements-tested-py314.txt (não é lock multiplataforma).

- `pytest linux/tests -q`: **21 testes aprovados**, exit 0.
- `ruff check linux scripts`, `ruff format --check linux scripts`: aprovados.
- `pip check`: sem inconsistências; `compileall linux/src`: aprovado.
- Build wheel/sdist 0.2.0.dev1 em linux/dist/. Wheel instalado em diretório
  temporário separado e importado fora dos fontes.
- TLS real em localhost: certificado desconhecido e nome TLS incorreto recusados.
- Autenticação correta, segredo incorreto/expirado, binário antes de autenticação,
  mensagens grandes, timeout de negociação e segundo emissor recusados.
- JPEG recebido/decodificado, ordem de sequência, dimensões, tamanho e RGB conferidos.
  Falhas do OpenCV são convertidas em rejeição de protocolo.
- ACK de quadro, desconexão, nova conexão, quadro neutro ao desconectar ou estagnar.
- Captura sintética, ioctl simulado, recusa de câmera física e fechamento em erro.
- Qt offscreen: prévia sintética, receptor TLS em porta efêmera, pareamento na UI,
  cancelamento e fechamento de threads. Não comprova KDE/Wayland real.

Sockets são bloqueados no sandbox desta sessão; os testes de integração passaram
fora dele com autorização. Não foram substituídos por mocks nem marcados skip.
As chamadas V4L2 nos testes continuam simuladas; não comprovam driver real.
O usuário mostrou a imagem sintética no OBS por fonte de vídeo em screenshot;
movimento, FPS e estabilidade não foram confirmados. Essa evidência não é teste
Android ou de Wi-Fi.

Emissor opcional sem celular, com receptor gráfico iniciado:

```sh
.venv/bin/python scripts/send_synthetic.py --certificate ~/.local/share/nexocam/identity/identity.pem
```

O segredo é solicitado sem eco no terminal, nunca passado por argumento. Esse
emissor implementa autenticação, JPEG e espera ACK; a suíte testa o mesmo caminho
no servidor. O comando interativo acima não foi executado contra uma sessão do
usuário. Não use certificado baixado de fonte desconhecida.

## Android

Ferramentas locais: JDK17, Gradle8.11.1, AGP8.9.2, Kotlin2.1.20, API35/build-tools35.

- `ktlintFormat` executado; `ktlintCheck` aprovado.
- `testDebugUnitTest`: **3 testes aprovados**, nenhum ignorado. Entrada de pareamento,
  segredo oculto no toString, certificado fixado correto, pin incorreto e ausência
  de certificado. Fixture server.crt é pública e não contém chave privada.
- `assembleDebug`: APK instalável de desenvolvimento gerado.
- `assembleRelease`: APK release **sem assinatura** gerado.
- `lintDebug`: zero erros e 10 avisos no relatório local: atualizações de
  bibliotecas, TrustManager próprio e configuração de backup por versão Android.
  Backup está explicitamente desabilitado no manifesto e nas regras de extração.
  Veja relatório em android/app/build/reports/.
- SDK reporta diferença de versão XML com AGP, sem impedir os builds.
- Alguns binários nativos de dependências foram empacotados sem remoção de símbolos;
  isso não foi tratado como falha de build.
- ADB local executado: lista vazia. Nenhum APK foi instalado em aparelho nesta sessão.

Workflows Linux/Android preparados; não executados no GitHub nesta sessão.

## Teste físico necessário

1. Instale o APK debug conforme installation-android.md. Abra o receptor atualizado
   e feche a instância antiga para liberar V4L2/porta8765.
2. Selecione Receber do Android, selecione NexoCam V4L2 e Iniciar. Copie o IPv4
   correto, fingerprint e segredo da tela local para o Android em até cinco minutos.
3. Ative a câmera e conecte. Confirme movimento no Android, Linux e OBS, distinguindo
   prévia de captura da janela. Faça testes separados com Meet/Discord.
4. Teste câmeras frontal/traseira, rotação, retrato/paisagem, perda de Wi-Fi,
   reconexão com segredo ainda válido, expiração e novo pareamento.
5. Desligue a câmera/bloqueie o Android: confira desconexão e quadro neutro no
   receptor. Reinicie e feche receptor ativo; confira liberação do dispositivo.
6. Registre modelo/Android/kernel/ambiente/consumidor, FPS real e resultado na matriz.
7. ADB Reverse manual é opcional, exige depuração autorizada e ainda não foi testado.

Medição física de FPS capturado/recebido/entregue, taxa de dados e latência completa
permanece pendente. A UI Linux atual mede FPS de saída do worker, inclusive quadros
neutros/repetidos, não FPS da câmera Android.
