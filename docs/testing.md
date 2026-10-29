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

## Correção de entrada Android — 29/10/2026

Android 0.2.1-dev: `ktlintCheck`, `testDebugUnitTest` (4 testes), `lintDebug` e
`assembleDebug` executados com sucesso. O novo teste verifica normalização de
espaços, separadores da fingerprint e maiúsculas, mantendo exigência de 64 hex,
e diferencia campo de IP inválido de fingerprint inválida. `git diff --check`
sem problemas. Não houve instalação automática nem validação visual no aparelho.
O APK debug foi atualizado no caminho habitual; o release unsigned anterior não
foi reconstruído nesta correção.

Diagnóstico da sessão: receptor escutando TCP8765 e teste TLS/hello em localhost
aprovado sem enviar credenciais. Usuário relatou a mensagem de formato inválido
no Android, indicando recusa antes da tentativa de conexão. Isso não identifica
qual campo estava errado e não comprova conectividade Wi-Fi entre os dispositivos.

## QR de pareamento — 29/10/2026

Receptor com qrcode 8.2: geração de matriz somente em memória. Teste decodifica a
imagem gerada com OpenCV e confere exatamente os dados de pareamento. Entradas
inválidas são recusadas. A suíte Linux passou com 26 testes (incluindo TLS local
e abertura/fechamento do diálogo na UI offscreen).

Android 0.2.2-dev: leitor ZXing embarcado, parser com limite de tamanho, versão,
porta, campos e credenciais. Testes cobrem leitura do formato válido e rejeição de
QR estrangeiro, versão/porta incompatível, tamanho excessivo e dados inválidos.
Build debug, 6 testes unitários Android, ktlintCheck e lintDebug aprovados;
leitura real pela câmera ainda pendente. Wheel e sdist Linux reconstruídos com QR.
O release unsigned anterior não foi atualizado com QR. Use o APK debug atual.

Validação manual: reinicie o receptor, escolha a interface do hotspot e escaneie
o QR com o novo APK. Confira preenchimento, cancelamento da leitura, retorno à
prévia, confirmação de conexão e segredo vencido. Teste também escanear enquanto
a prévia CameraX está ativa para confirmar liberação da câmera no aparelho.

## Interface e confirmação QR — 29/10/2026 (Android 0.2.3-dev)

26 testes Linux passaram após incluir confirmação autenticada sem sessão de
vídeo, ausência de confirmação para credencial inválida e fechamento/reabertura
do diálogo QR por sinal Qt. Ruff, formatação e git diff --check aprovados.
Android: ktlintCheck, 6 unitários, lintDebug e assembleDebug passaram. A nova tela
centraliza a prévia e coloca dados em popup; durante transmissão a representação
é decodificada do JPEG preparado para envio, no executor da câmera, com StateFlow.
O fechamento real após leitura, o popup no telefone e o custo da prévia JPEG
precisam de validação física. APK debug atualizado; release anterior não atualizado.

## Redesign desktop — 29/10/2026

27 testes Linux aprovados, incluindo geração/leitura de QR nos tamanhos de 4 e
5 pixels por módulo, prévia, início/encerramento e fechamento automático do QR.
Ruff e formatação aprovados; wheel e sdist gerados, incluindo tema e chevron SVG.
Revisão visual por capturas Qt offscreen em 1160×760 e 920×620, com imagem
sintética e estado vazio; diálogo QR revisado com endereço/credenciais fictícios.
Ainda requer avaliação visual na sessão KDE/Wayland real e teste do usuário com
vídeo do celular. O protocolo, resolução e limites de transmissão foram mantidos.

## Formato ao vivo e controles — 29/10/2026 (Android 0.2.4-dev)

28 testes Linux aprovados, com negociação explícita dos dois tamanhos, rejeição
de retrato sem capacidade negociada, proporção/barras na saída virtual e troca
Horizontal/Vertical dentro da mesma sessão TLS. Mudanças de formato durante a
negociação são aplicadas no estado inicial, sem enviar comandos prematuros.
Android: ktlintCheck, 6 testes unitários, lintDebug e assembleDebug aprovados.
APK instalado via ADB e versão 0.2.4-dev confirmada (versionCode6).
Ainda é necessário testar fisicamente a troca ao vivo no celular/OBS, rotação,
proporção e consumo de CPU; a automação não comprova esse comportamento no driver.

## Correção da orientação de pixels — Android 0.2.5-dev

10 testes Android aprovados (4 novos de rotação): modo horizontal com sensor
90/270, aparelho em paisagem, troca para retrato e todas as combinações dos
sensores 0/90/180/270 com buffers 640×480 e 480×640. Metadados inválidos recusados.
ktlintCheck, lintDebug e assembleDebug aprovados. A prévia local também processa
JPEG a até 15 FPS sem enviar antes de conectar. Avaliação física da orientação,
consumo de CPU e resposta ao seletor permanece necessária. Release não atualizado.
