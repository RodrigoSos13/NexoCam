# NexoCam

Webcam Android para Linux, localmente por Wi-Fi ou USB, sem nuvem, contas,
telemetria ou gravação de vídeo. Licença MIT. **Versão experimental 0.2.0.dev1.**

Implementado: captura Android CameraX com prévia e troca frontal/traseira;
transmissão JPEG 640×480 com limite de 15 FPS, WebSocket TLS e pareamento manual;
receptor PySide6 com prévia e saída real por pyvirtualcam/v4l2loopback;
reconexão cancelável, descarte de capturas e quadro neutro quando o vídeo para.
O aplicativo Android precisa permanecer visível. A resolução de captura física
pode variar; o quadro transmitido é ajustado para 640×480 preservando proporção.

**Ainda sem validação ponta a ponta com um celular.** A saída sintética foi vista
pelo usuário no OBS; isso não comprova câmera Android, Wi-Fi real ou estabilidade.
Pareamento por QR implementado; USB automatizado, descoberta e pareamento persistente estão pendentes.

## Linux

Na raiz, com Python 3.11+ (atualize a instalação se usou a versão anterior):

```sh
python -m venv .venv
.venv/bin/python -m pip install -e './linux[dev]'
.venv/bin/nexocam
```

1. Selecione a webcam virtual ou “Somente prévia”.
2. Selecione **Receber do Android** e clique em **Iniciar**.
3. Abra **Dados de pareamento**, escolha a interface da rede local e, no Android,
   toque em **Escanear QR Code**. Os campos serão preenchidos. Não compartilhe essa tela.
4. No Android, ative a câmera e toque em **Conectar e transmitir**.
5. No OBS, selecione NexoCam como dispositivo V4L2.

Linux e celular precisam se alcançar na rede local pela porta TCP 8765. O
programa não altera firewall, módulo do kernel ou permissões automaticamente.
O modo de teste sintético continua disponível na seleção de modo.

## Android

Projeto completo em android/, Android mínimo 9 (API 28). Compile com JDK 17 e
SDK API 35; veja [instalação Android](docs/installation-android.md).
APK de desenvolvimento local: `android/app/build/outputs/apk/debug/app-debug.apk`.
Esse arquivo é gerado e ignorado pelo Git. O build release ainda não é assinado.

## Segurança e testes

Identidade TLS persistente somente no computador, com chave privada em diretório
privado fora do repositório. O Android valida o certificado fixado por SHA-256 e
mantém a verificação do nome TLS. O segredo vale cinco minutos para novas
conexões; sessões já autenticadas continuam. Interromper o receptor desconecta
os clientes; reiniciar gera outro segredo e revoga o anterior. Não há tokens
persistentes no Android nem modo Wi-Fi sem TLS.

```sh
.venv/bin/python -m pytest linux/tests
.venv/bin/ruff check linux scripts
.venv/bin/ruff format --check linux scripts
```

- [Instalação Linux](docs/installation-linux.md)
- [Instalação Android](docs/installation-android.md)
- [Arquitetura](docs/architecture.md)
- [Protocolo v1](protocol/README.md)
- [Testes e evidências](docs/testing.md)
- [Problemas comuns](docs/troubleshooting.md)
- [Compatibilidade](docs/compatibility.md)
- [Próximas etapas](docs/roadmap.md)
