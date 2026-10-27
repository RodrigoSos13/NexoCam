# Solução de problemas

- **Webcam virtual indisponível:** execute `nexocam diagnostics`; confira módulo
  disponível versus carregado e permissões. Veja installation-linux.md.
- **Câmera física recusada:** selecione apenas um dispositivo v4l2loopback. O nome
  NexoCam por si só não identifica um driver virtual.
- **Dispositivo ocupado:** interrompa outro produtor; não remova webcams em uso.
- **Navegador não encontra NexoCam:** inicie a saída virtual antes de abrir a lista
  de câmeras; confira permissões do site e sandbox do aplicativo.
- **Sem sessão gráfica:** execute diagnósticos ou synthetic pelo terminal. Testes
  Qt usam `QT_QPA_PLATFORM=offscreen`, que não valida Wayland real.
- **Erro de pip:** confirme versão Python e disponibilidade de wheels; use o venv.
- **Padrão aparece parado:** o marcador branco inferior deve se mover. Compare a
  prévia e o consumidor. Barras são sintéticas, não a câmera do celular.

Não envie logs contendo imagens, tokens, fingerprints de pareamento com segredo
ou chaves. Não há gravação de vídeo ou logs de quadros na implementação atual.
