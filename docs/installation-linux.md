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

## Interface desktop atualizada

O painel lateral reúne origem, saída de vídeo e ações. Selecione a webcam virtual
para usar o vídeo no OBS; Somente prévia exibe a imagem apenas no NexoCam. Iniciar
sessão abre a recepção; Conectar celular · QR Code reabre o pareamento; Encerrar
sessão libera os recursos. Diagnósticos fica no cabeçalho. Em janelas menores,
o painel lateral e o diálogo de pareamento têm rolagem. A prévia se ajusta à janela
sem recortar ou alterar os quadros transmitidos. Métricas são da saída e incluem
quadros neutros/repetidos, não FPS de captura do celular.

Esta atualização altera somente o receptor Linux. Feche a instância antiga e
execute `.venv/bin/nexocam` novamente para carregar o tema novo.

## Formato horizontal ou vertical

Formato fica no painel lateral. Horizontal é o padrão ao abrir o receptor; você
pode selecionar Vertical antes ou durante uma transmissão Android. O APK deve
ser 0.2.4-dev ou posterior. O fluxo continua na mesma conexão e a prévia muda para
640×480 ou 480×640. O seletor gira os pixels quando necessário para produzir o formato escolhido,
sem esticar a imagem. Para manter a cena em pé, posicione o aparelho de acordo
com o formato (deitado para Horizontal, em pé para Vertical).

A webcam virtual continua anunciando 640×480 durante a sessão. O vídeo vertical
é acomodado com barras laterais para evitar reabrir o dispositivo enquanto OBS
ou outro consumidor o utiliza. Para uma composição vertical no OBS, ajuste a cena
ou recorte as barras. Ainda não há troca ao vivo das dimensões V4L2 anunciadas.
O modo de teste sintético conserva o formato horizontal.
