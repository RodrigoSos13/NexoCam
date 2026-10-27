# Evolução

1. Fundação: pacote, diagnóstico, detecção V4L2, padrão sintético, UI e testes.
   Bloqueio de validação real: falta dispositivo virtual carregado/acessível.
2. Transmissão: projeto Android compilável, CameraX, JPEG, servidor WebSocket TLS,
   identidade, autenticação e pareamento manual seguro; integração e teste Wi-Fi.
3. USB: ADB com timeout, dispositivos autorizados, reverse com propriedade e limpeza,
   usando o mesmo protocolo. Requer aparelho e depuração autorizada.
4. Produto: reconexão, métricas, configurações persistentes, QR, tradução, UX,
   diagnósticos acionáveis e distribuição. UI atual é ferramenta de fundação.
5. Medir desempenho, avaliar H.264, ampliar matriz e releases assinadas.

Critérios da primeira versão completa: build Android, captura, sessão autenticada,
recepção e decodificação, V4L2 contínuo, câmeras frontal/traseira, Wi-Fi/USB,
reconexão e encerramento estáveis, instalação reproduzível, testes aprovados.
Nenhum item dependente de Android ou transmissão está concluído na fase 1.
