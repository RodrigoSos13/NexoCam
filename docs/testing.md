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

## Fluidez no receptor — 07/11/2026

45 testes Linux aprovados. O novo teste TLS bloqueia deliberadamente a saída,
transmite três quadros aguardando ACK individual e confirma que a captura não
fica dependente do relógio de exibição. Ao liberar a saída, somente o quadro
mais recente aparece, sem fila acumulada. Repetições não aumentam a contagem;
FPS cai a zero e o quadro neutro aparece ao cessar o vídeo.

O ACK continua significando validação e decodificação, antes do consumo por UI/OBS.
A mailbox agora guarda um único quadro decodificado. A prévia Qt consulta essa
mailbox a cada 16 ms com temporizador preciso, sem aumentar o alvo de 15 FPS do
protocolo. Não exige atualizar o APK. A comparação física da fluidez/latência
continua pendente: não havia sessão TCP nem encaminhamento USB ativo durante a
investigação, então os testes não comprovam resolução das travadas no aparelho.

## Processamento Android — 0.2.6-dev, 07/11/2026

14 testes Android aprovados, ktlintCheck, lintDebug e assembleDebug concluídos.
Os quatro novos testes verificam ritmo médio de 15 FPS em uma câmera simulada
de 30 FPS com jitter, ausência de rajadas após uma pausa longa, preservação dos
prazos após atrasos e rejeição de intervalo inválido.

O processamento usa CameraX toBitmap, uma passagem de rotação/escala e uma
compressão JPEG. A prévia usa o bitmap preparado em vez de descomprimir o JPEG;
a captura não espera ACK de rede. A implementação de CameraX 1.4.2 foi conferida
no artefato local: YUV segue convertYUVToBitmap, sem JPEG intermediário.
Os testes de rotação anteriores continuam passando; a renderização no Canvas e
o ganho de FPS/latência ainda precisam de avaliação física. Medidas agregadas
estão disponíveis pelo log NexoCamPerf durante a câmera ativa.
APK debug instalado via ADB no SM-S918B, preservando dados e assinatura original;
versão 0.2.6-dev (versionCode 8) confirmada no aparelho. Em teste posterior, o
usuário relatou melhora na fluidez e atraso ainda perceptível na prévia local.
NexoCamPerf registrou aproximadamente 14,98–15,00 FPS após aquecimento inicial,
com processamento médio de 13,2–14,0 ms e máximo de 21,6 ms. Não havia sessão TCP
ou encaminhamento USB durante essa consulta; esses números são da captura local,
não da transmissão nem da latência absoluta.

## Prévia independente a 30 FPS — 0.2.7-dev

15 testes Android aprovados; ktlintCheck, lintDebug e assembleDebug concluídos.
O novo teste simula captura a 60 FPS por dez segundos e verifica aproximadamente
300 quadros de prévia para 150 quadros elegíveis à transmissão. JPEG é opcional
no quadro preparado; sem conexão apta ao envio, a prévia não comprime imagens.
O envio mantém o protocolo de 15 FPS e o controle de um quadro em voo.
APK instalado no SM-S918B e versão 0.2.7-dev (versionCode 9) confirmada.
Após aquecimento inicial, NexoCamPerf mediu 28,84–29,77 FPS, processamento médio
de 7,34–7,38 ms e máximo de 13,74 ms, contra cerca de 15 FPS e 13–14 ms na versão
0.2.6. O usuário confirmou que o atraso da prévia ficou menor. Essas medidas são
locais e não medem latência absoluta ou o percurso USB até o computador/OBS.

## Tela ligada — Android 0.2.8-dev

ktlintCheck, 15 testes unitários Android, lintDebug e assembleDebug aprovados.
A View Compose usa keepScreenOn enquanto câmera e sessão estão ativas, incluindo
conexão/reconexão. DisposableEffect restaura o valor anterior ao mudar de estado
ou sair da composição. Nenhuma permissão ou configuração global foi adicionada.
Ainda requer teste físico aguardando o tempo de desligamento durante a transmissão
para confirmar que permanece ligada, e após desconectar para confirmar a liberação.

## USB padrão e interface simplificada — Android 0.2.9-dev

46 testes Linux e 15 testes Android aprovados. Ruff, formatação, ktlintCheck,
lintDebug e assembleDebug aprovados. O teste de interface cobre USB selecionado
inicialmente, preparação automática, falha de autorização e nova tentativa,
QR com endereço local, troca para Wi-Fi e preservação da escolha ao reabrir o
pareamento. Confirma também que estatísticas/opções avançadas começam recolhidas,
que a ajuda de firewall fica oculta até ser solicitada e que o QR é desenhado.

Telas principal e de pareamento revisadas por capturas Qt offscreen com credenciais
fictícias. Corrigido fundo do conteúdo rolável para preservar contraste escuro.
APK 0.2.9-dev (versionCode 11) instalado no SM-S918B, preservando dados; versão
confirmada por ADB. A revisão visual Android e o fluxo completo de escanear e
transmitir nesta versão ainda precisam de validação no aparelho desbloqueado.

## Transmissão negociada a 30 FPS — Android 0.2.10-dev

48 testes Linux e 18 Android aprovados; Ruff, formatação, ktlintCheck, lintDebug
 e assembleDebug aprovados. Os testes TLS simulam envio a 15 e 30 FPS, verificam
confirmação da taxa, ACK por quadro, saída real acima do antigo limite de 15 FPS
na simulação de 30 e abertura da webcam virtual em 30 FPS por backend simulado.
Os testes Android verificam seleção de 30 quando anunciado e retorno a 15 com
receptor antigo ou capacidades inválidas, além do intervalo de captura.

A saída usa prazos monotônicos, sem acumular arredondamentos de cada espera.
O protocolo mantém autenticação, dimensões limitadas e um quadro em voo. A taxa
real ainda exige teste físico de captura, codificação, USB, receptor e consumidor.
APK instalado no celular via atualização preservando os dados. Medidas anteriores
à atualização mostravam captura local de cerca de 29–30 FPS; isso não comprova
que o receptor recebia essa mesma taxa.

## Janela de envio — Android 0.2.11-dev

48 testes Linux e 23 Android aprovados, com lint, formatação e APK debug gerado.
O teste de janela simula ACK de 40 ms numa fonte de 30 FPS: um espaço permite
30 envios em dois segundos; dois espaços permitem 60. Outros testes cobrem
limite rígido de dois, envio rejeitado, limpeza, ACK fora de ordem/duplicado e
capacidade explícita do receptor. O teste TLS envia dois quadros antes de esperar
os ACKs, mantendo somente a última imagem na saída bloqueada.

Na versão 0.2.10, teste físico por USB com alvo 30 reportou somente 14–15 FPS no
desktop. O Android capturava cerca de 29 FPS mas codificava cerca de 14 FPS.
A janela de dois tenta remover a espera serial de ACK; seu efeito físico precisa
ser confirmado. NexoCamTransport mede taxa negociada, janela, FPS confirmado e
média/máximo de ACK para distinguir essa limitação de outros gargalos. APK 0.2.11
instalado no aparelho, preservando os dados.

### Medidas físicas da janela de dois

Na 0.2.11, USB ativo e alvo 30 confirmado: cerca de 24,9–25,8 FPS de ACK após
início da sessão, com ACK médio de 39,1–43,5 ms e máximo de 80,8 ms. O celular
capturava até 29,7 FPS e preparava cerca de 25 FPS para envio. O usuário relatou
pouca melhora na exibição. Isso não comprova que o desktop mostrava 25 FPS:
chegadas em rajada podem substituir quadros na mailbox antes da apresentação.

O artefato local e o código oficial do OkHttp 4.12.0 foram inspecionados: a criação
do socket no RealConnection não ativa TCP_NODELAY. A 0.2.12 configura a opção
explicitamente no SocketFactory, sem substituir a fábrica TLS. Referência:
[RealConnection 4.12.0](https://raw.githubusercontent.com/square/okhttp/parent-4.12.0/okhttp/src/main/kotlin/okhttp3/internal/connection/RealConnection.kt).

## TCP_NODELAY — Android 0.2.12-dev

24 testes Android aprovados, ktlintCheck, lintDebug e assembleDebug concluídos.
O teste cria um socket pelo próprio cliente de pareamento e verifica TCP_NODELAY
ativo antes de conectar, além de confirmar que redirecionamentos continuam
bloqueados. Os testes de identidade TLS e janela de quadros continuam passando.
APK instalado por atualização no celular. Comparação física do FPS exibido e do
ACK após essa mudança ainda pendente.

### Medidas físicas após TCP_NODELAY

Na 0.2.12, alvo 30 e janela dois: ACK médio caiu para aproximadamente 6,9–8,1 ms,
com amostras estabilizadas de 29,2–29,8 FPS confirmados. O usuário mediu 25–27 FPS
na prévia desktop. Isso confirma melhora no transporte, mas mostra que a taxa
confirmada ainda não era igual à taxa mostrada no desktop.

## Acordar a prévia na chegada

49 testes Linux aprovados. Um novo teste simula próximo tick virtual distante
 e confirma que a chegada de quadro acorda a prévia antes desse prazo. A câmera
virtual continua com relógio limitado à taxa negociada; a mailbox permanece de
uma imagem. O Android 0.2.12 não precisa ser substituído para esse ajuste.
Após reabrir o receptor e testar por USB, o usuário confirmou prévia mais próxima
de 29–30 FPS, especialmente com a câmera frontal. Logs da sessão registraram
amostra de aproximadamente 29,96 FPS confirmados, com ACK médio de 7,0 ms;
outras janelas variaram entre cerca de 24 e 29 FPS conforme a captura.
Isso valida a melhora de fluidez relatada, não uma garantia de 30 FPS constantes
nas duas câmeras nem uma medição de latência absoluta até o OBS.

## Texto curto e instruções — Android 0.2.13-dev

24 testes Android, ktlintCheck, lintDebug e assembleDebug aprovados. O parágrafo
inicial foi substituído por orientação curta em bodyMedium centralizada. Como
conectar abre um diálogo rolável com seções USB, Wi-Fi e uso durante transmissão;
a conexão manual fica acessível nesse diálogo. APK atualizado no celular sem
remover dados. Revisão visual e interação com a ajuda no aparelho ainda pendentes.
