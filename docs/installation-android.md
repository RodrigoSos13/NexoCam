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
Para atualizar o APK de desenvolvimento já instalado neste aparelho, mantenha
`ANDROID_USER_HOME` apontando para `.tools/android-user`, onde fica a chave debug
original. Usar outra chave faz o Android recusar a atualização por assinatura.

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

## Cabo USB pelo receptor Linux

Conecte um cabo de dados, ative Depuração USB nas opções do desenvolvedor e
autorize o computador no Android. Instale Android Platform Tools no Linux se
ADB não estiver disponível. Regras udev podem ser necessárias conforme a distribuição.

Inicie o receptor e escolha **Cabo USB** → **Verificar cabo novamente** no pareamento.
O receptor seleciona exclusivamente um aparelho USB autorizado e configura
`adb reverse --no-rebind tcp:8765 tcp:8765`. Havendo mais de um aparelho USB,
desconecte os demais antes de preparar. O QR usa `127.0.0.1`, com a mesma identidade
TLS e segredo temporário; escaneie e confirme **Conectar e transmitir** no Android.
O APK atual já aceita esse endereço; essa funcionalidade não exige um novo APK.

O vídeo usa o cabo mesmo sem Wi-Fi. Não precisa liberar TCP 8765 no firewall para
esse transporte. O modo usa ADB Reverse, não UVC nativo. Encaminhamentos para outro
destino são preservados e geram um aviso de conflito. Um encaminhamento igual já
existente pode ser reutilizado e não é removido ao encerrar a sessão. Somente o
encaminhamento criado pelo NexoCam é removido no encerramento normal, se ainda
apontar para a mesma porta. Após retirar/reconectar o cabo, prepare o USB novamente.

Validação automatizada cobre configuração, erros, propriedade, limpeza e QR;
vídeo real pelo cabo e redução de latência ainda exigem teste físico.
Referência: [ADB Reverse na documentação oficial](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/user/adb.1.md).

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

### Processamento e fluidez — 0.2.6-dev

Esta mudança exige atualizar o APK. A captura usa a conversão direta
[ImageProxy.toBitmap do CameraX](https://developer.android.com/reference/androidx/camera/core/ImageProxy#toBitmap()),
elimina o JPEG intermediário e faz rotação/escala ao desenhar o quadro final.
A compressão JPEG ocorre uma única vez; a prévia reutiliza o bitmap preparado,
antes dos artefatos da compressão, sem decodificar o JPEG no celular.
A prévia local não depende do ACK do computador. O envio continua com no máximo
um quadro em voo e sem fila crescente. O alvo do protocolo permanece 15 FPS.

Para investigar quedas de captura, `adb -d logcat -s NexoCamPerf` mostra a cada
cinco segundos apenas resolução de captura, FPS e tempo médio/máximo de
processamento. Não registra imagens, quadros ou credenciais de pareamento.

### Prévia local — 0.2.7-dev

Atualize o APK. A prévia local passa a usar até 30 FPS, conforme a câmera permitir.
Somente os quadros elegíveis para transmissão são comprimidos como JPEG, mantendo
até 15 FPS no protocolo atual e um único quadro em voo. Sem sessão de vídeo,
a prévia não comprime JPEG. O FPS de NexoCamPerf mede a prévia/captura; o indicador
desktop mede o vídeo recebido/exibido e pode ser menor. Não representa uma medição
da latência absoluta entre a cena e a tela.

### Tela ligada durante a transmissão — 0.2.8-dev

O NexoCam mantém automaticamente a tela ligada enquanto conecta, transmite ou
tenta reconectar, com a câmera ativa. Desconectar, desativar a câmera ou sair
do aplicativo libera o desligamento normal. A prévia sem conexão não mantém a
tela acordada. Não há nova permissão nem mudança no tempo de tela global do
Android. O botão físico de bloquear a tela continua funcionando e encerra a
câmera, como antes. Implementado com keepScreenOn na View da Activity, conforme
a [orientação do Android](https://developer.android.com/develop/background-work/background-tasks/awake/screen-on).

### Fluxo simplificado e USB padrão — 0.2.9-dev

No desktop, escolha a saída de imagem antes de clicar em **Conectar celular**.
O USB é a opção inicial e o cabo é verificado automaticamente. Se houver erro,
a mensagem indica o que falta; após autorizar ou reconectar, use **Verificar cabo
novamente**. Wi-Fi continua disponível no seletor do pareamento e sua escolha
é mantida enquanto a sessão estiver aberta. Uma nova sessão começa por USB.

No Android, a tela inicial oferece **Escanear QR para começar**. A leitura ativa
a prévia; depois toque em **Conectar e transmitir**. A configuração manual fica
no botão **Conexão manual**, sem exigir preencher campos no fluxo por QR.
Estatísticas, teste sintético e diagnósticos do desktop ficam recolhidos;
problemas de firewall aparecem em **Problemas com o Wi-Fi?**.

### Transmissão a 30 FPS — 0.2.10-dev

Atualize tanto o APK quanto o receptor Linux e reabra ambos. O receptor anuncia
as taxas suportadas e o Android passa a transmitir até 30 FPS quando disponível.
Com receptor ou Android antigo, continua em 15 FPS. A prévia local continua de
até 30 FPS e não depende do envio. A saída V4L2 do receptor é aberta para 30 FPS;
o teste sintético mantém 15 FPS.

NexoCamPerf agora mostra `fps` (captura/prévia) e `encoded_fps` (quadros preparados
para envio), além dos tempos de processamento. No desktop, Estatísticas mostra
imagens novas exibidas no último segundo. Taxa negociada não garante taxa real:
processamento, câmera, transporte e ACK podem reduzi-la. Não há acúmulo de quadros
para tentar compensar atrasos.

### Janela de envio — 0.2.11-dev

Atualize e reabra ambos os aplicativos. O receptor atualizado anuncia uma janela
de dois quadros, permitindo sobrepor captura e espera pela confirmação anterior.
O cliente não acumula uma fila: se os dois espaços estiverem ocupados, descarta
o envio daquela captura e mantém a prévia. Receptores sem essa capacidade
continuam com um único quadro em voo.

`adb -d logcat -s NexoCamPerf NexoCamTransport` mostra somente contadores:
`target_fps`, `frame_window`, `acked_fps`, `ack_ms` e `max_ack_ms`. Isso permite
distinguir o teto negociado da taxa real confirmada e de tempos elevados de ACK.

### TCP de baixa latência — 0.2.12-dev

A fábrica de sockets do cliente ativa TCP_NODELAY antes da conexão usada pelo
OkHttp. Isso evita a espera do algoritmo de Nagle nos envios de vídeo, mantendo
o mesmo TLS e pareamento. Atualize o APK; o receptor que já negocia 30 FPS e
janela de dois não precisa ser atualizado novamente para essa opção do cliente.

### Instruções sob demanda — 0.2.13-dev

A tela inicial mostra apenas “Escaneie o QR do computador para começar.”, com
texto menor e centralizado. O botão **Como conectar** abre instruções roláveis
separadas para USB, Wi-Fi e uso durante a transmissão. A entrada manual está em
**Como conectar → Conexão manual**. Depois do pareamento, a orientação inicial
muda para “Pronto para ativar a câmera.” quando a câmera estiver desativada.
