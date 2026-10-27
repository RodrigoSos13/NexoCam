# NexoCam Protocol v1 — especificação inicial, servidor ainda não implementado

Transporte previsto: WebSocket sobre TLS 1.2+ tanto no Wi-Fi quanto no ADB Reverse.
Nenhum socket é aberto pela fase 1. O parser existente valida apenas o envelope;
validação dos campos e máquina de estados serão implementadas junto ao servidor.

Texto UTF-8, JSON objeto, até 4096 bytes. Envelope obrigatório:
`{"v":1,"type":"hello"}`. Tipos: hello, authenticate, configure, start, state,
stop, error. Versões diferentes são recusadas; mensagens desconhecidas são erros.

Sequência prevista: TLS com identidade verificada → hello → authenticate →
configure → start → quadros → stop. Não aceitar quadros antes da autenticação.
Um único emissor ativo por receptor. Heartbeat nativo WebSocket a cada 10 s,
timeout 20 s; timeout de autenticação 10 s. Backoff Android: 1, 2, 4, 8, 16, 30 s
com jitter e cancelamento explícito. Revogação deve invalidar reconexão.

Negociação inicial: JPEG 640×480, máximo 15 FPS, qualidade inicial 75.
Mensagens binárias previstas: cabeçalho network byte order `!4sBQQ` (21 bytes):
magic `NXCF`, versão 1, sequência uint64, timestamp monotônico do emissor em µs,
seguido de um JPEG. Limite total de 1 MiB. Validar dimensões antes de decodificar;
recusar dimensões diferentes das negociadas e JPEGs inválidos. Timestamp entre
máquinas não mede latência absoluta sem sincronização; serve para intervalos.
Fila de entrada e saída com capacidade 1, sobrescrita do quadro antigo. Frames
fora de ordem são descartados. Não usar compressão WebSocket para JPEG.

Pareamento planejado: identidade local persistente, certificado autoassinado;
QR ou entrada manual contém endereço, fingerprint SHA-256 e segredo temporário
aleatório. Validar o certificado pelo fingerprint antes de enviar o segredo,
sem trust-all. Confirmar pareamento localmente, trocar segredo por token
revogável por dispositivo; guardar credenciais no Keystore Android e arquivos
privados no Linux. Não implementar autenticação por PIN curto isolado.
Mudança de IP não muda a identidade. QR/códigos não devem aparecer em logs.

ADB Reverse: porta prevista 8765, Android acessa localhost; usar a mesma validação
TLS. Não remover encaminhamentos preexistentes ou pertencentes a outros apps.
