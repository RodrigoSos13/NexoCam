# Solução de problemas

- **Webcam virtual indisponível:** execute `nexocam diagnostics`; confira módulo
  disponível versus carregado e permissões. Veja installation-linux.md.
- **Câmera física recusada:** selecione apenas um dispositivo v4l2loopback. O nome
  NexoCam por si só não identifica um driver virtual.
- **Dispositivo ocupado:** interrompa outro produtor; não remova webcams em uso.
- **Navegador não encontra NexoCam:** inicie a saída virtual antes de abrir a lista
  de câmeras; confira permissões do site e sandbox do aplicativo.
- **Sem sessão gráfica:** execute diagnósticos ou synthetic pelo terminal. Testes
  Qt usam `QT_QPA_PLATFORM=offscreen`, que não valida Wayland real.
- **Erro de pip:** confirme versão Python e disponibilidade de wheels; use o venv.
- **Padrão aparece parado:** o marcador branco inferior deve se mover. Compare a
  prévia e o consumidor. Barras são sintéticas, não a câmera do celular.

Não envie logs contendo imagens, tokens, fingerprints de pareamento com segredo
ou chaves. Não há gravação de vídeo ou logs de quadros na implementação atual.

## Transmissão Android (0.2)

- **Servidor não inicia:** feche outra instância usando a porta TCP 8765. Não
  execute duas versões do receptor ao mesmo tempo; outra saída V4L2 pode estar ocupada.
- **Falha na conexão:** celular e Linux precisam se alcançar no IPv4 escolhido,
  sem isolamento Wi-Fi de clientes, com TCP 8765 permitido pelo firewall. O app
  não muda regras automaticamente. Confira fingerprint diretamente no computador.
- **Pareamento rejeitado:** segredo vale cinco minutos para novas conexões. Pare
  e reinicie o receptor, copie o novo segredo e conecte novamente.
- **TLS expirado ou identidade incompleta:** restaure certificado e chave juntos;
  para renovar deliberadamente, faça backup privado e gere uma nova identidade,
  depois confirme sua nova impressão digital no Android. Não aceite certificados
  arbitrários para contornar o erro.
- **Sem vídeo ao sair da tela Android:** comportamento esperado nesta versão;
  não há serviço de câmera em segundo plano. Ative a câmera e conecte novamente.
- **Retrato com barras:** saída é 640×480 com proporção preservada; gire o aparelho
  para paisagem para aproveitar melhor o quadro. A orientação exige teste no aparelho.
- **Celular aparece como MTP, mas não no ADB:** depuração USB/autorização são
  necessárias para instalar via ADB ou testar Reverse. Para Wi-Fi, instalar o APK
  manualmente é suficiente; o cabo não inicia a transmissão por conta própria.

### Erro de formato antes de conectar

Na versão Android 0.2.0-dev, a mensagem de erro pode ficar acima da prévia, fora
da área visível enquanto os campos são preenchidos. Ela não significa falha de
rede: a tentativa ainda não foi iniciada. Volte ao topo para conferir o estado.

Android 0.2.1-dev exibe o estado também ao lado dos controles de conexão e mostra
qual campo tem formato inválido. Informe somente um IPv4, sem esquema, porta ou
lista de endereços. Escolha o IPv4 da interface Wi-Fi/Ethernet que alcança o celular,
não os endereços de bridges de containers. Fingerprint e segredo continuam exigindo
64 caracteres hexadecimais; espaços copiados e maiúsculas são normalizados. A
fingerprint também aceita separadores de dois-pontos. Isso não aceita caracteres
fora de hexadecimal nem desativa a validação do certificado ou a autenticação.
