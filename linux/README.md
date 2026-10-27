# NexoCam para Linux — 0.1.0.dev1

Fundação: interface PySide6, diagnóstico, padrão RGB e saída real pyvirtualcam
para v4l2loopback. Android e rede ainda não estão implementados.

Instale com `python -m pip install .` e execute `nexocam`.
`nexocam diagnostics` verifica o ambiente sem alterá-lo.
`nexocam synthetic --device /dev/videoN --seconds 10` testa a saída virtual.
O driver deve estar preparado pelo administrador; não execute o receptor como root.

Na raiz do monorepositório, veja docs/installation-linux.md, docs/testing.md e
protocol/README.md. Nenhuma compatibilidade de consumidor foi comprovada.
