# Arquitetura e decisões

Monorepositório Android/Linux, protocolo independente de UI. Estado: implementação
experimental da fase 2; build e testes sem aparelho executados, teste físico pendente.

## Linux

Python ≥3.11; PySide6 para UI; NumPy RGB; pyvirtualcam/v4l2loopback para saída;
OpenCV headless para JPEG (sem outro toolkit gráfico); websockets asyncio para
transporte; cryptography para certificado local. Dependências somente locais,
faixas no pyproject e snapshot de ambiente em requirements-tested-py314.txt.

UI no thread Qt principal. Um QThread possui geração sintética OU event loop
asyncio do receptor. Detecção de ambiente em outro worker com timeout de subprocess.
Saída V4L2 pertence ao worker e é fechada por context manager. Decodificação e
escrita ocorrem nesse worker; se o driver bloquear, investigar no hardware.
Mailbox UI com lock/capacidade 1, timer Qt e descarte de quadros antigos.
Não são emitidos sinais Qt por quadro. Métrica UI mede FPS de saída, não captura.

`devices/v4l2.py` usa VIDIOC_QUERYCAP e aceita apenas driver `v4l2 loopback`.
Não presume /dev/video10 e não confia no rótulo. Nunca carrega módulo ou altera
permissões silenciosamente. `video/stream.py` conserva o padrão sintético para
diagnóstico. `network/server.py` oferece fluxo autenticado e saída 640×480/15 alvo.
Saída neutra após desconexão ou um segundo sem vídeo; no fechamento também tenta
enviar neutro antes de liberar o dispositivo.

Servidor abre somente após Iniciar. Escuta IPv4 0.0.0.0:8765; não anuncia via mDNS
nem muda firewall. Aceita uma sessão, quatro negociações de aplicação pendentes,
mensagens limitadas, timeout e heartbeat. Não é destinado à exposição pública na
internet. JPEG tem cabeçalho/dimensões conferidos antes da decodificação e shape
conferido depois. A fila comprimida tem capacidade 1, com descarte e saída limitada.

## Segurança

Identidade EC P-256 persistente em $XDG_DATA_HOME/nexocam/identity (fallback
~/.local/share/nexocam/identity). Diretório 0700, arquivos 0600, escrita por replace.
Certificado autoassinado com SAN nexocam.local, validade de um ano. Identidade
incompleta/expirada produz erro e exige recuperação/renovação explícita.

Pareamento inicial manual: IPv4, fingerprint SHA-256 do DER e segredo 256-bit,
válido por cinco minutos para novas conexões. Segredo somente em memória, comparação
constante no servidor. Reiniciar muda segredo e revoga acessos anteriores.
Não há armazenamento de dispositivos pareados nem revogação individual ainda.

Android usa TrustManager restrito ao certificado exato fixado por SHA-256 e
verifica sua validade. Isso é uma política explícita de confiança local, não
trust-all. O verificador padrão de hostname do OkHttp é preservado: URL sempre
nexocam.local, Dns restrito resolve somente esse nome para o IPv4 informado. Não
há proxy, redirects ou modo de TLS desativado. Credenciais só saem após handshake.
O lint Android sinaliza CustomX509TrustManager; essa escolha requer revisão de
segurança continuada e tem testes de pin correto/incorreto e certificado ausente.
Certificado renovado exige nova confirmação da impressão digital pelo usuário.

## Android

Kotlin 2.1.20, AGP 8.9.2, Gradle 8.11.1, JDK17, API28 mínimo/API35 alvo.
Versões estáveis escolhidas por compatibilidade e build; não alegamos serem últimas.
Compose Material3; ViewModel/StateFlow; CameraX ligado ao lifecycle. Apenas CAMERA
e INTERNET. Ativação da câmera exige ação/consentimento e mostra prévia. Ao sair
da tela a câmera e conexão param; serviço foreground será uma fase posterior.

CameraManager configura KEEP_ONLY_LATEST e executor próprio. FrameProcessor converte
YUV_420_888 respeitando strides para NV21, JPEG/Bitmap, corrige rotação e ajusta em
canvas RGB 640×480 com barras sem deformar proporção, JPEG qualidade75. ImageProxy
é sempre fechado; bitmaps temporários são reciclados. A conversão é conservadora
e precisa de medição física antes de otimizações ou promessas de FPS.

ConnectionManager negocia sessão e mantém no máximo um JPEG em voo: espera ACK
de processamento do receptor; enquanto isso capturas são descartadas antes da
compressão. Heartbeat e backoff cancelável 1–30 s com jitter. Falhas TLS e rejeições
de autenticação não são repetidas automaticamente. Segredo expirado exige reinício
do receptor e nova entrada; não há reconexão ilimitada usando segredo vencido.
SettingsRepository usa DataStore somente para IP. Não persistimos tokens nem
fingerprints, então ainda não há material sensível a guardar no Keystore.
Recursos textuais Android permitem tradução; a UI Linux ainda usa textos inline.

## Evoluções

Testar câmera física e Wi-Fi antes de declarar fase2 validada; depois ADB com
timeouts, detecção/autorização e propriedade dos encaminhamentos. O protocolo já
permite teste ADB Reverse manual sem duplicar captura/decodificação. QR, descoberta,
pareamento persistente, métricas completas e distribuição assinada ainda pendentes.

Referências consultadas em 27/10/2026:
- https://letmaik.github.io/pyvirtualcam/
- https://github.com/v4l2loopback/v4l2loopback
- https://websockets.readthedocs.io/en/stable/reference/asyncio/server.html
- https://developer.android.com/media/camera/camerax/analyze
- https://developer.android.com/build/releases/agp-8-9-0-release-notes
- https://developer.android.com/jetpack/androidx/releases/camera
- https://android-developers.googleblog.com/2025/04/whats-new-in-jetpack-compose-april-25.html
