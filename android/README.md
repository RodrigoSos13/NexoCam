# NexoCam Android

Kotlin, Compose Material 3, CameraX, coroutines/Flow, DataStore e OkHttp.
Android 9+ (API 28), compile/target API 35. JDK 17, Gradle Wrapper 8.11.1,
AGP 8.9.2, Kotlin 2.1.20. Veja ../docs/installation-android.md.

```sh
./gradlew ktlintCheck testDebugUnitTest lintDebug assembleDebug assembleRelease
```

O release é gerado sem assinatura. Somente CAMERA e INTERNET são solicitadas.
Não há serviço em segundo plano: sair da tela encerra câmera e transmissão.
Pareamento por QR offline ou manual: IPv4, SHA-256 do certificado e segredo temporário.
Apenas o endereço é persistido; credenciais ficam na memória da tela/sessão.

A instalação e a transmissão reais no aparelho ainda precisam ser validadas.
