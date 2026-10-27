# Instalação Linux

Python 3.11+ com venv/pip. Instale em ambiente virtual conforme README, sem sudo.
O pacote inclui launcher `.desktop` e ícone em `.venv/share`. Para integração com
o menu, copie manualmente o ícone para `~/.local/share/icons/hicolor/scalable/apps/`
e o desktop para `~/.local/share/applications/`, ajustando Exec para o caminho
absoluto de `.venv/bin/nexocam`; esses diretórios não são alterados pelo programa.

## Preparar V4L2

Primeiro execute `nexocam diagnostics`. Se o módulo já estiver disponível, não
instale outro pacote. O ambiente inspecionado possui v4l2loopback 0.15.4 no kernel
CachyOS 7.3.0-4-cachyos; não havia dispositivo carregado na inspeção.

A carga requer privilégios e é uma ação explícita do administrador. Exemplo para
criar um dispositivo com número escolhido automaticamente:

```sh
sudo modprobe v4l2loopback devices=1 card_label=NexoCam exclusive_caps=1
```

Este comando não é executado pelo aplicativo. Se já existem dispositivos loopback,
consulte `v4l2loopback-ctl --help` para adicionar um sem descarregar o módulo em uso.
Não descarregue módulos usados por OBS ou outros programas. Confirme com
`v4l2-ctl --list-devices`, atualize os diagnósticos e selecione o dispositivo.

Se ausente, instale a versão adequada ao kernel seguindo a documentação da distro:

- Arch/CachyOS: verifique primeiro o módulo fornecido pelo kernel; caso necessário,
  pacote `v4l2loopback-dkms` e headers exatos do kernel em uso; utilitários `v4l-utils`.
- Debian/Ubuntu: pacotes `v4l2loopback-dkms`, `v4l-utils`, headers do kernel em uso.
- Fedora: consulte os repositórios de módulos disponíveis para sua versão; o projeto
  ainda não validou um procedimento de instalação Fedora.

DKMS exige compilador e headers compatíveis. Secure Boot pode exigir assinatura e
inscrição da chave pelo administrador. Não desative recursos de segurança por rotina.
Não mude permissões para 666: use ACL/regras da distro ou grupo de vídeo quando
apropriado, seguido de nova sessão. O receptor nunca deve rodar como root.

Wayland/X11 não controlam a escrita V4L2. Flatpak, sandbox de navegador e portais
podem afetar a visibilidade da câmera. Inicie a saída antes de abrir o consumidor
quando usar exclusive_caps=1. Não há compatibilidade de consumidores comprovada.
