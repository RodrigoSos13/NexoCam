# Testes

## Evidências locais — 27/10/2026

CachyOS, kernel 7.3.0-4-cachyos, Python 3.14.8. Dependências instaladas em .venv;
versões exatas em linux/requirements-tested-py314.txt. Esse snapshot só reproduz
este ambiente Python 3.14, não é lock multiplataforma nem matriz comprovada.

- `python -m pytest linux/tests -q`: 16 testes aprovados, processo encerrou com 0.
- `ruff check linux` e `ruff format --check linux`: aprovados.
- `python -m pip check`: nenhuma dependência inconsistente.
- `python -m compileall -q linux/src`: aprovado.
- `python -m build linux`: wheel e sdist gerados (linux/dist/).
- Wheel instalado sem dependências em diretório temporário separado: importação
  comprovada fora do código-fonte e geração de quadro RGB aprovada.
- Interface Qt: início, atualização de prévia e encerramento em modo offscreen.
- Protocolo: JSON, envelope, versão e limites. Autenticação não está implementada.
- Vídeo: RGB, cores, movimento, isolamento de memória e quadro neutro.
- Recursos: recusa de câmera física, identificação loopback via ioctl simulado,
  cancelamento, mailbox latest-only e fechamento em erro.
- Diagnóstico real: módulo disponível, não carregado, nenhum /dev/video*.
- CLI synthetic com caminho ausente: mensagem e saída 1, sem traceback.

O teste Qt inicialmente revelou problema de destruição no teardown do teste;
a fixture mantém QApplication viva e libera objetos pendentes explicitamente.
As chamadas V4L2 em testes usam doubles; não comprovam o driver real.
Workflow CI preparado para Python 3.11–3.14, mas não executado no GitHub.

## Validação real pendente

A tentativa autorizada de carga com `sudo -n modprobe ...` não pôde continuar:
o sudo exige senha. Não houve carga do módulo. A senha deve ser fornecida pelo
usuário em seu próprio terminal, nunca enviada pelo chat.

1. Prepare o módulo seguindo installation-linux.md e execute o diagnóstico.
2. Abra `.venv/bin/nexocam` na sessão KDE/Wayland. Teste prévia, diagnósticos,
   seleção do dispositivo, iniciar/parar repetidamente, minimizar e fechar ativo.
3. Selecione a saída virtual e inicie o teste. Abra OBS ou outro consumidor;
   confirme barras coloridas e marcador inferior em movimento. Anote FPS real.
4. Interrompa; confira quadro neutro quando retido pelo consumidor, e confirme que
   outro produtor consegue abrir o dispositivo. Repita desconexão e encerramento.
5. Teste Meet e Discord separadamente; registre dados em compatibility.md.

Android, autenticação, JPEG, rede, reconexão, configurações persistentes e ADB
terão testes nas fases correspondentes; não há resultados para essas funções.
