# NexoCam

Webcam Android para Linux, localmente por Wi-Fi ou USB, sem nuvem, contas,
telemetria ou gravação de vídeo. Licença MIT. **Versão experimental 0.2.0.dev1.**

Implementado: captura Android CameraX com prévia e troca frontal/traseira;
transmissão JPEG 640×480 de até 30 FPS negociados, WebSocket TLS e pareamento manual;
receptor PySide6 com prévia e saída real por pyvirtualcam/v4l2loopback;
reconexão cancelável, descarte de capturas e quadro neutro quando o vídeo para.
O aplicativo Android precisa permanecer visível. A resolução de captura física
pode variar; o quadro transmitido é ajustado para 640×480 preservando proporção.

**Fluxo com câmera real recebido no OBS confirmado pelo usuário em 29/10/2026.**
FPS, latência e estabilidade prolongada ainda não foram medidos. A nova interface
Android 0.2.13-dev e a ajuda sob demanda exigem nova validação no aparelho.
Pareamento por QR e configuração USB via ADB implementados; validação física do
USB, descoberta em rede e pareamento persistente estão pendentes.

## Linux

Na raiz, com Python 3.11+ (atualize a instalação se usou a versão anterior):

```sh
python -m venv .venv
.venv/bin/python -m pip install -e './linux[dev]'
.venv/bin/nexocam
```

1. Escolha a webcam virtual ou “Somente prévia” em **Usar imagem em**.
   Conecte o celular por cabo USB e autorize o computador no Android.
2. Clique em **Conectar celular**. O USB é verificado automaticamente.
3. No Android, toque em **Escanear QR para começar**, leia o QR do computador
   e confirme **Conectar e transmitir**. Não compartilhe a tela de pareamento.
4. No OBS, selecione NexoCam como dispositivo V4L2. “Somente prévia” mostra
   apenas no receptor, sem saída para outros aplicativos.

Para usar Wi-Fi, selecione **Wi-Fi** na janela do QR. Linux e celular precisam
se alcançar na rede local pela porta TCP 8765. Em **Problemas com o Wi-Fi?**,
**Liberar acesso no firewall…** permite autorizar pelo sistema uma
regra UFW para a interface e sub-rede selecionadas. Assim, mudanças no IP do celular
dentro dessa rede não exigem nova regra. Ao trocar de rede, repita a liberação.
O programa não altera firewall sem essa ação nem modifica módulo do kernel ou permissões.
Teste sintético e diagnósticos ficam em **Opções avançadas**. As estatísticas
podem ser abertas abaixo da prévia.

### Conectar por cabo USB

1. Instale Android Platform Tools (ADB), conecte um cabo de dados e ative
   **Depuração USB** nas opções do desenvolvedor do celular. Autorize o computador
   na janela exibida no Android. Não é necessário root.
2. Clique em **Conectar celular**. O receptor verifica o cabo automaticamente.
3. No Android, escaneie o QR exibido e toque em **Conectar e transmitir**.

O programa configura ADB Reverse e mantém TLS e segredo temporário. Não depende
de Wi-Fi ou liberação no firewall. Ao encerrar a sessão, remove somente o
encaminhamento criado por ela; encaminhamentos existentes não são sobrescritos.
Após retirar/reconectar o cabo, use **Mostrar QR e instruções** → **Verificar cabo novamente**.
ADB é procurado no PATH, ANDROID_HOME, ANDROID_SDK_ROOT e no SDK local `.tools/sdk`.
USB pode reduzir oscilações da rede; a latência total ainda precisa ser medida
e continua dependendo de CameraX, JPEG, FPS negociado e do consumidor de vídeo.
Atualize Android e receptor para negociar até 30 FPS. Com um dos lados antigo,
o protocolo mantém 15 FPS. A taxa real depende do aparelho e do tempo de ACK.

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
