# Histórico

## Android 0.2.2-dev / pareamento QR — 2026-10-29

- QR local com seleção de interface/IP no receptor, sem salvar imagens.
- Leitor QR offline embarcado no Android; preenche os campos e exige confirmação.
- Validação de formato, versão, porta, IP e credenciais antes da conexão.
- Câmera de transmissão liberada antes de abrir o leitor.


## Android 0.2.1-dev — 2026-10-29

- Validação informa o campo incorreto e normaliza espaços/maiúsculas dos códigos sem afrouxar o pin TLS.
- Estado da conexão também junto ao botão, evitando que fique escondido acima da prévia.
- Erros exibidos como notificação breve e teclado recolhido ao conectar.
- Orientação junto ao botão quando a câmera ainda não está ativa.

## 0.2.0.dev1 — 2026-10-27

- Android Kotlin/Compose/CameraX: prévia, permissão, troca de câmera e JPEG orientado.
- Servidor WebSocket TLS com identidade privada, pinning e pareamento manual temporário.
- Recepção autenticada na UI Linux, saída virtual e neutralização de vídeo estagnado.
- Controle de fluxo com um quadro em voo, limites de mensagens/dimensões e heartbeat.
- Reconexão Android cancelável com backoff; câmera encerrada ao sair da tela.
- DataStore somente para endereço; nenhum segredo persistido no Android.
- Testes TLS reais em localhost, unitários Android, lint/formatação e CI Android.
- Debug APK e release sem assinatura gerados; execução em aparelho ainda pendente.
- USB automatizado, QR, descoberta e pareamento persistente ainda pendentes.

## 0.1.0.dev1 — 2026-10-27

- Fundação Linux com pacote instalável e launcher.
- Detecção por VIDIOC_QUERYCAP, diagnósticos sem privilégios.
- Padrão RGB, saída pyvirtualcam e prévia PySide6 em worker com mailbox limitada.
- Testes sem hardware, workflow CI e contrato inicial de protocolo.
