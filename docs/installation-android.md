# Instalação Android

## Compilar

Requisitos: JDK 17, SDK Android API 35, build-tools 35.0.0, Gradle Wrapper incluído.
Não use o Java 27 do sistema com esse Gradle. Não altere o Java global; aponte
JAVA_HOME para o JDK 17 no terminal ou configure o Gradle JDK no Android Studio.
Configure ANDROID_HOME ou crie android/local.properties com `sdk.dir=/caminho/do/sdk`.
Esse arquivo deve permanecer fora do Git. A instalação inicial baixa dependências;
a transmissão funciona sem internet depois de instalada.

No diretório android:

```sh
./gradlew assembleDebug testDebugUnitTest lintDebug ktlintCheck
./gradlew assembleRelease
```

Para corrigir formatação, execute `./gradlew ktlintFormat` separadamente antes do
check. O wrapper verifica o SHA-256 da distribuição Gradle. A versão atual usa um
conjunto estável de dependências validado pelo build, não as últimas versões de
cada biblioteca. Revise atualizações e compatibilidade antes de migrar.

APK debug: `app/build/outputs/apk/debug/app-debug.apk` (assinado com chave de
desenvolvimento local). Release: `app/build/outputs/apk/release/app-release-unsigned.apk`.
A chave debug fica no diretório local de ferramentas/usuário, nunca deve ir ao Git.
Para releases públicas, use uma chave privada externa e `apksigner`; não assine
releases com chave debug e não coloque senhas nos scripts ou na linha de comando.
Ainda não há distribuição assinada pronta.

Neste ambiente as ferramentas foram baixadas para `.tools/`, ignorada pelo Git:
JDK em `.tools/jdk/`, SDK em `.tools/sdk`, cache Gradle em `.tools/gradle-home`.
O Java do sistema não foi substituído. Aponte as variáveis para essas pastas se
quiser reutilizá-las. Android Studio também pode abrir o projeto android/.

## Instalar e usar

Transfira o APK debug ao celular e abra-o para instalar, autorizando a origem
quando solicitado pelo Android. Alternativamente, com depuração USB habilitada,
autorização concedida no aparelho e `adb devices` mostrando `device`:

```sh
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

1. Abra o receptor Linux, selecione Receber do Android e Iniciar.
2. No celular, abra NexoCam e toque em Ativar câmera. Conceda CAMERA.
3. No Linux, abra Dados de pareamento e selecione a interface conectada ao celular
   (por exemplo, o Wi-Fi do hotspot). No Android, toque em Escanear QR Code e aponte
   para o QR mostrado no computador. IP, impressão digital e segredo serão preenchidos.
   Confira o IP e confirme a conexão. O preenchimento manual continua disponível.
4. Toque em Conectar e transmitir. O certificado será verificado antes do segredo.
5. Confira prévia recebida no Linux e depois selecione NexoCam no OBS.
6. Teste troca de câmera, desconexão e encerramento. Mantenha o Android visível:
   ao trocar de aplicativo ou bloquear a tela, a sessão e a câmera são encerradas.

Segredo expirado: interrompa e reinicie o receptor para gerar outro. Falha de
identidade: confira a impressão digital diretamente na interface do computador;
nunca desative a verificação TLS. Reiniciar o receptor não altera seu certificado.
Se houver mais de um IPv4, escolha a interface da rede que o celular alcança.
A porta TCP 8765 precisa ser permitida pelo firewall; não exponha o serviço à internet.

## Cabo — diagnóstico manual de transporte, ainda sem integração gráfica

A fase de detecção e gerenciamento automático ADB ainda está pendente. Para
experimentar manualmente o mesmo protocolo, com um único aparelho autorizado:
`adb reverse tcp:8765 tcp:8765`; use `127.0.0.1` como IP no Android, mantendo a
mesma impressão digital e segredo. Remova somente esse encaminhamento se foi
você quem o criou: `adb reverse --remove tcp:8765`. Verifique previamente
`adb reverse --list` para não sobrescrever encaminhamento de outro aplicativo.
Isso exige depuração USB e não é UVC nativo. Ainda não foi validado em aparelho.

## Pareamento por QR — Android 0.2.2-dev

Atualize o APK e reinicie o receptor Linux para usar o botão Escanear QR Code.
O leitor ZXing é embarcado; não exige Google Play Services, download de modelos,
contas ou internet para escanear. A câmera de transmissão é liberada antes de
abrir o leitor. Não salva foto do QR. A leitura apenas preenche os campos, sem
conectar automaticamente; ao retornar, a prévia é ativada mediante a permissão
já concedida e você confirma Conectar e transmitir.

O QR contém um segredo e vale o mesmo prazo de cinco minutos da sessão. Não
publique ou fotografe essa tela. Só escaneie o QR exibido no seu computador.
Não há alteração de firewall: no hotspot, escolha o novo IPv4 da interface Wi-Fi,
e qualquer regra limitada à rede anterior precisará ser revista pelo usuário.

## Interface Android 0.2.3-dev

A tela principal prioriza a imagem. O botão Conexão abre um popup com IP,
fingerprint e segredo; desconecte antes de editar. Concluir fecha o popup e mantém
as alterações na memória. Escanear QR Code continua disponível na tela principal.
Após leitura, o app confirma o segredo por TLS e a janela do QR no computador
fecha automaticamente. Essa confirmação não inicia vídeo: toque em Conectar e
transmitir. É necessário atualizar o APK e reiniciar o receptor Linux.

Antes da conexão, a prévia é CameraX. Ao transmitir, a imagem exibida vem do JPEG
preparado para envio, respeitando rotação e proporção. Não é uma confirmação de
consumo pelo OBS nem uma medição de latência. O JPEG para prévia é decodificado
no executor de captura e publicado por StateFlow sem fila de eventos por quadro.

## Formato e ícone de câmera — 0.2.4-dev

Atualize o APK e reabra o receptor. O formato Horizontal/Vertical é selecionado
no desktop, inclusive com transmissão ativa. A prévia Android acompanha o JPEG
preparado para envio. A escolha é aplicada sem reconectar; a captura continua
corrigindo a rotação do sensor e preserva proporção. Vertical pode apresentar
barras conforme a posição do celular e a saída usada pelo consumidor.
O botão com câmera e setas alterna frontal/traseira; possui descrição TalkBack.

### Correção de orientação — 0.2.5-dev

Horizontal agora gira os pixels para o enquadramento deitado; Vertical produz
quadro em pé. Antes, o app apenas encaixava a cena em um canvas diferente, o que
podia manter uma imagem vertical mesmo selecionando Horizontal. A prévia local
agora também usa o JPEG preparado, mesmo antes de conectar, sem transmitir esses
quadros antes da autenticação/início explícito. Para ver a cena em pé, segure o
telefone de acordo com o formato: uma rotação digital não muda a posição física
dos objetos. A troca ao vivo continua no seletor do desktop.
