# NexoCam

Software livre em desenvolvimento para transformar Android em webcam Linux,
localmente por Wi-Fi ou USB. Licença MIT. Sem nuvem, contas ou telemetria.

**Estado: fundação Linux implementada. Ainda não transmite de um Android.**
A versão atual oferece interface gráfica de teste, prévia RGB sintética,
diagnósticos e saída real por pyvirtualcam para um dispositivo v4l2loopback
preparado pelo usuário. Não equivale à primeira versão completa do produto.

## Executar

Na raiz do projeto, com Python 3.11+:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e './linux[dev]'
.venv/bin/nexocam
```

A interface permite iniciar a prévia sem driver; selecione um dispositivo virtual
para enviar o padrão à webcam. Minimizar mantém o teste; fechar encerra.

```sh
.venv/bin/nexocam diagnostics
.venv/bin/nexocam synthetic --device /dev/videoN --seconds 10
.venv/bin/python -m pytest linux/tests
```

Substitua `/dev/videoN` pelo dispositivo detectado, nunca por um número presumido.
O diagnóstico retorna código 1 quando não há dispositivo virtual com acesso.

- [Instalação Linux](docs/installation-linux.md)
- [Arquitetura](docs/architecture.md)
- [Protocolo inicial](protocol/README.md)
- [Testes e evidências](docs/testing.md)
- [Problemas comuns](docs/troubleshooting.md)
- [Compatibilidade](docs/compatibility.md)
- [Próximas etapas](docs/roadmap.md)

As dependências Python são baixadas apenas na instalação. A execução atual é
local e não abre portas nem acessa câmeras físicas.
