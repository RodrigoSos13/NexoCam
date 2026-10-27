# Evolução

1. Fundação Linux implementada: pacote, diagnóstico, V4L2, padrão sintético, UI e
   testes. Usuário mostrou barras sintéticas recebidas por fonte de vídeo no OBS;
   estabilidade/movimento/FPS não foram confirmados.
2. Captura/transmissão implementadas: Android compilável, CameraX, JPEG,
   WebSocket TLS, pinning, segredo temporário manual, receptor integrado à UI,
   controle de fluxo, reconexão e testes TLS sem aparelho. Falta validar instalação,
   câmera física, câmeras frontal/traseira e Android → Wi-Fi → Linux → OBS.
3. USB: protocolo compartilhado permite ADB Reverse manual; automação de detecção,
   autorização, propriedade e limpeza dos encaminhamentos ainda não implementada.
4. Produto: QR, descoberta, pareamento persistente/revogação por aparelho,
   configurações completas, métricas, acessibilidade, tradução e instaladores.
5. Medir latência/desempenho, otimizar conversão, avaliar H.264, ampliar matriz,
   assinatura e processo de releases. Nada disso está declarado pronto.

A primeira versão funcional completa exige validação física Wi-Fi/USB, reconexão,
encerramento e consumidores, além dos builds e testes automatizados já existentes.
