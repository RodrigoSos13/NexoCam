# Arquitetura e decisões

Monorepositório Android/Linux com protocolo independente das interfaces.
Fase atual: fundação Linux 0.1.0.dev1. Ainda não há captura Android ou rede.

Python ≥3.11, PySide6 para UI, NumPy para RGB uint8, pyvirtualcam para V4L2.
Dependências introduzidas somente onde usadas; OpenCV, websockets e bibliotecas
criptográficas serão adicionados junto com processamento JPEG e TLS.
Faixas compatíveis ficam no pyproject; não representam lock reproduzível exato.

`devices/v4l2.py` usa VIDIOC_QUERYCAP e aceita somente driver `v4l2 loopback`.
Não confia no rótulo nem assume número de dispositivo. Permissões são examinadas
antes de abrir; abertura real continua sujeita a corrida, dispositivo ocupado
ou restrições do driver, reportadas ao usuário. Nenhum subprocesso privilegiado.

`video/virtual_camera.py` possui o recurso V4L2 em context manager. O stream envia
RGB a 640×480/15 FPS alvo e fecha no mesmo thread. `video/stream.py` compartilha o
padrão entre CLI e UI. O gerador sintético é ferramenta de validação permanente,
não substitui a captura Android futura. Ao parar tenta enviar quadro neutro.

UI no thread Qt principal; geração e escrita em QThread. Mailbox protegida por
lock com capacidade de um quadro, consumida por timer: sinais por quadro não
acumulam imagens no event loop. Diagnósticos com subprocess timeout ficam em
worker separado. Encerramento é assíncrono, aguardando workers sem bloquear UI.
Minimizar mantém o teste; fechar encerra e libera recursos. Bandeja opcional.
A chamada nativa send pode depender da resposta do driver; testar hardware real.

Fase 2: CameraX/Kotlin/Compose Android 9+, ImageProxy sempre fechado, descarte de
quadros, servidor asyncio em thread próprio, TLS e pareamento por identidade
fixada. UI e transporte compartilham estado explícito, sem referências Qt na rede.
O caminho manual autenticado precede descoberta. Android ficará visível na versão
inicial; serviço foreground camera só após validação das restrições por versão.
Fase 3: ADB Reverse reaproveita transporte. Fase 4: configurações, reconexão,
pareamento persistente, diagnósticos completos e experiência de instalação.
Fase 5: medir antes de mudar codecs. Nenhuma fase futura é declarada pronta.

Referências consultadas em 27/10/2026:
- https://letmaik.github.io/pyvirtualcam/ — Camera, RGB, backend e fechamento.
- https://github.com/v4l2loopback/v4l2loopback — exclusive_caps, carga e kernel.
- https://pypi.org/project/PySide6/ — pacote oficial Qt for Python.
