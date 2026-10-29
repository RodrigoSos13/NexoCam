# Segurança

NexoCam 0.2.0.dev1 é experimental. O transporte e a captura Android estão
implementados, mas ainda não validados com aparelho físico. Não exponha o servidor
à internet; o uso previsto é entre dispositivos locais escolhidos pelo usuário.

- TLS obrigatório, certificado local fixado por SHA-256 e verificação de validade/nome.
- Segredo temporário aleatório de 256 bits, mantido em memória, válido por cinco
  minutos para novas conexões. Sessões autenticadas não expiram nesse intervalo.
- Interromper desconecta os clientes; reiniciar gera outro segredo e revoga o antigo.
- Chave TLS no computador em diretório 0700, arquivo 0600, fora do repositório.
- Apenas o IP é persistido no Android; sem tokens em DataStore ou estado salvo.
- Sem telemetria, serviços externos, gravação de vídeo ou execução do receptor como root.
- Câmera exige ação/consentimento e para quando o aplicativo deixa de estar visível.
- Limites de mensagens/dimensões, filas limitadas, timeouts e uma sessão de vídeo ativa.

O TrustManager Android usa política de certificado exato fixado; não é uma exceção
genérica de validação TLS. O aviso CustomX509TrustManager do lint é documentado
em docs/architecture.md. Testes não substituem uma auditoria independente das
bibliotecas, do protocolo ou da implementação. Não há modo de distribuição sem TLS.

Não publique segredos, chaves, capturas da tela de pareamento ou logs de quadros.
O certificado público em android/app/src/test/resources é apenas uma fixture de
teste, sem chave privada. Builds, SDK, JDK e dados locais são ignorados pelo Git.

Reporte vulnerabilidades de forma privada pelo canal indicado pelo mantenedor no
repositório oficial. Ainda não há contato privado configurado neste código; não
publique detalhes exploráveis ou credenciais em issues públicas.

Pareamento por QR: o código contém o segredo temporário, é gerado em memória e
não deve ser publicado. Escaneie somente a tela do computador escolhido. O leitor
Android é interno, offline, não grava fotos, preenche os campos e envia uma confirmação curta autenticada por
TLS para fechar o QR no computador. Iniciar vídeo continua exigindo confirmação. QR não altera regras de firewall.
