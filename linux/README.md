# NexoCam Linux — 0.2.0.dev1

Receptor gráfico Android: WebSocket TLS, pareamento manual temporário, JPEG
640×480 e saída pyvirtualcam para v4l2loopback. Inclui padrão sintético e diagnóstico.

Instale com `python -m pip install .` e execute `nexocam`. No modo Receber do Android,
Iniciar abre o servidor TLS na porta 8765. Copie os dados de pareamento da interface
para o Android e ative sua câmera. Interromper encerra conexões e libera o dispositivo.

`nexocam diagnostics` consulta o ambiente sem modificá-lo.
`nexocam synthetic --device /dev/videoN --seconds 10` testa a saída virtual.
O driver deve ser preparado pelo administrador; não execute o receptor como root.

Documentação completa em docs/ no monorepositório. Transmissão Android real ainda
não validada; testes TLS e JPEG em localhost são automatizados.
