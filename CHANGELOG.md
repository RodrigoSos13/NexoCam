# Histórico

## Android 0.2.13-dev / instruções sob demanda — 2026-11-07

- Tela inicial com orientação curta e tipografia menor, em vez do parágrafo de configuração.
- Botão Como conectar abre instruções de USB, Wi-Fi e uso durante a transmissão.
- Conexão manual fica acessível dentro das instruções.

## Prévia orientada à chegada — 2026-11-07

- Acorda a prévia desktop quando chega um quadro, sem aguardar a próxima saída V4L2.
- Mantém o ritmo negociado da câmera virtual e a mailbox de última imagem.

## Android 0.2.12-dev / TCP de baixa latência — 2026-11-07

- Ativa TCP_NODELAY nos sockets do cliente antes do envio, evitando espera do algoritmo de Nagle.
- Mantém TLS, pinning, verificação de hostname, autenticação e janela limitada de dois quadros.
- Testa a opção no socket realmente criado pelo cliente de pareamento.

## Android 0.2.11-dev / janela de envio — 2026-11-07

- Até dois quadros em trânsito quando o receptor anuncia suporte, para reduzir espera por ACK.
- Mantém um único quadro com receptores antigos; valida sequência de cada confirmação.
- Diagnóstico agregado inclui taxa negociada, janela, FPS confirmado e tempo médio/máximo de ACK.

## Android 0.2.10-dev / transmissão a 30 FPS — 2026-11-07

- Negocia até 30 FPS entre Android e receptor atualizados; mantém 15 com versões antigas.
- Captura para envio, saída desktop e configuração da webcam virtual deixam de ficar limitadas a 15 FPS.
- Relógio de saída por prazos para evitar acumular atrasos de agendamento.
- Diagnóstico Android separa FPS da prévia e FPS de quadros comprimidos para envio.

## Fluxo USB padrão / Android 0.2.9-dev — 2026-11-07

- USB é a opção inicial; o receptor verifica o cabo automaticamente ao iniciar.
- Tela principal com uma ação de conexão, estatísticas e opções técnicas recolhidas.
- Wi-Fi continua selecionável, com ajuda de firewall sob demanda.
- Android começa pelo QR e mostra os controles conforme a etapa da conexão.
- Corrige o fundo do conteúdo rolável do pareamento para manter contraste no tema escuro.

## Android 0.2.8-dev — 2026-11-07

- Mantém automaticamente a tela ligada enquanto conecta, transmite ou tenta reconectar.
- Libera o desligamento normal ao desconectar, desativar a câmera ou sair do aplicativo.
- Não altera o tempo de desligamento nas configurações globais do Android.

## Android 0.2.7-dev — 2026-11-07

- Prévia local de até 30 FPS, independente do ritmo de envio de 15 FPS.
- Quadros usados somente pela prévia não passam por compressão JPEG.
- Teste separado dos ritmos de prévia e transmissão, preservando o protocolo atual.

## Android 0.2.6-dev — 2026-11-07

- Conversão CameraX direta para bitmap, rotação/escala em uma passagem e uma única compressão JPEG.
- Prévia reutiliza os pixels preparados, sem descomprimir o JPEG e sem aguardar ACK do computador.
- Ritmo de captura por prazos, evitando descartes extras por pequenas variações nos intervalos da câmera.
- Medidas agregadas de FPS e tempo de processamento no log NexoCamPerf, sem imagens ou credenciais.

## Receptor: fluidez e métricas — 2026-11-07

- Confirma o quadro após validar/decodificar, sem esperar o ciclo de exibição.
- Mantém somente o quadro mais recente para saída e reduz a espera da prévia Qt.
- FPS recebido conta imagens novas no último segundo; repetições não inflam a métrica.
- Correção compatível com o APK atual e os transportes Wi-Fi/USB; alvo permanece 15 FPS.

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
