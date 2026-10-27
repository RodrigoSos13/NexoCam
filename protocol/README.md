# NexoCam Protocol v1 — implementação inicial

WebSocket sobre TLS 1.2+, porta TCP 8765. Mesmo protocolo para Wi-Fi e eventual
ADB Reverse. Sem compressão WebSocket. Um emissor ativo; até quatro handshakes
de aplicação pendentes. Origem de navegador recusada (`origins=[None]`).

## Identidade e autenticação

Receptor possui certificado EC P-256 autoassinado (validade de um ano), SAN
`nexocam.local`, e chave persistente em diretório privado. O cliente verifica
SHA-256 do certificado DER antes de autenticar e verifica validade. No Android,
OkHttp verifica normalmente o hostname `nexocam.local`; um Dns restrito resolve
esse nome para o IPv4 manual. Não há hostnameVerifier permissivo ou trust-all.

Interface do receptor exibe fingerprint e segredo aleatório de 256 bits. O segredo
fica em memória e aceita novas conexões por cinco minutos. Sessões autenticadas
continuam depois disso. Parar o servidor desconecta todos; cada reinício gera
outro segredo. Trata-se de autorização efêmera de sessão, sem cadastro permanente
de aparelhos. QR, confirmação adicional e tokens persistentes/revogação individual
são evoluções pendentes. Não coloque material de pareamento em logs ou URLs.

## Controle e ordem

Texto JSON UTF-8 objeto, máximo 4096 bytes. Envelope: `{"v":1,"type":"hello"}`.
Campos inteiros devem ser inteiros JSON, não booleanos. Versões desconhecidas
são recusadas. Tipos reconhecidos: hello, authenticate, configure, start, state,
stop, error. Tipos fora da ordem da sessão são recusados.

1. Cliente `hello`, campo `device` string imprimível de 1 a 80 caracteres.
2. Servidor `hello`.
3. Cliente `authenticate`, `token` hex minúsculo de 64 caracteres.
4. Servidor `state`, `state="authenticated"`.
5. Cliente `configure`, `width=640,height=480,fps=15,codec="jpeg"`.
6. Servidor confirma com `configure` e os mesmos campos.
7. Cliente `start`; servidor `state`, `state="streaming"`.
8. Cliente envia mensagens binárias JPEG. Servidor confirma processamento com
   `state`, `state="frame",sequence=N`. Android mantém no máximo um quadro em voo;
   capturas enquanto aguarda confirmação são descartadas, sem fila crescente.
9. Cliente `stop` ou fechamento WebSocket encerra a sessão.

Autenticação/configuração: timeout 10 s por mensagem. Durante vídeo: sem quadros
por 20 s encerra. Heartbeat WebSocket 10 s, timeout 20 s. Fechamento 1008 indica
protocolo/autenticação inválidos; 1013 indica receptor ocupado; excesso de tamanho
é fechado pelo WebSocket com 1009. Android não repete falha TLS ou fechamento
1008/1009; erros de transporte usam backoff de 1 a 30 s com jitter e cancelamento.

## Vídeo

Cabeçalho binário big-endian `!4sBQQ` de 21 bytes: magic `NXCF`, versão 1,
sequência uint64 crescente por sessão, timestamp monotônico do emissor em µs;
seguido de JPEG 8-bit. Limite total 1 MiB. Dimensões 640×480 verificadas no SOF
antes da decodificação e novamente depois; JPEG malformado é recusado. Timestamp
entre máquinas não mede latência absoluta sem sincronização.

Saída alvo 15 FPS; fila comprimida de capacidade 1 e mailbox UI de capacidade 1.
ACK indica processamento do quadro pelo receptor, não que OBS o tenha consumido.
O receptor envia quadro neutro quando desconecta ou fica 1 s sem vídeo. Android
corrige rotação e ajusta para 640×480 com barras, sem deformar proporção. A captura
nativa e FPS real dependem do aparelho e ainda não foram medidos.
