# Histórico

## Android 0.2.5-dev — 2026-10-29

- Corrige formato: Horizontal/Vertical agora aplica rotação real dos pixels, em vez de só alterar o canvas.
- Prévia local usa o mesmo processamento JPEG mesmo antes de conectar; Horizontal é o padrão inicial.
- Testes de rotação do sensor e troca de proporção.


## Android 0.2.4-dev / formato ao vivo — 2026-10-29

- Formato Horizontal (padrão) ou Vertical selecionável no desktop durante a transmissão.
- Prévia e JPEG em 640×480 ou 480×640, conforme o formato escolhido.
- Webcam virtual mantém 640×480 e acomoda retrato com barras para preservar a sessão do consumidor.
- Painel lateral simplificado e botão Android de alternar câmera por ícone acessível.


## Interface desktop — 2026-10-29

- Tema grafite com destaque verde, identidade visual e painel lateral de conexão.
- Prévia expansível sem recorte e métricas de saída separadas.
- Estado da sessão, saída escolhida e ações principais organizadas em áreas próprias.
- Diálogo QR revisado, com rolagem e preenchimento manual recolhido.
- Seleção de webcam preservada ao atualizar diagnósticos; câmera física continua recusada.


## Android 0.2.3-dev / interface — 2026-10-29

- Prévia como área principal; dados de conexão em popup editável quando desconectado.
- Durante a transmissão, exibe o JPEG preparado para envio, com rotação e proporção.
- Confirmação autenticada da leitura do QR fecha seu diálogo no computador sem iniciar vídeo.
- Controles de escanear, alternar câmera, conectar/desconectar e desativar próximos à prévia.


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
