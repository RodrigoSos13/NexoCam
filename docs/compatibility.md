# Compatibilidade

Usuário confirmou Android → receptor Linux → webcam virtual → OBS em 29/10/2026.
Modelo exato, versão Android, FPS e estabilidade ainda não foram registrados.

| Android/modelo | Distribuição | Kernel | Ambiente | Wi-Fi | USB | Consumidor | Resultado |
|---|---|---|---|---|---|---|---|
| Sem aparelho na sessão de teste | CachyOS | 7.3.0-4-cachyos | Qt offscreen | TLS localhost testado | Pendente | Nenhum | Testes automatizados; não comprova câmera física |
| Não se aplica (padrão sintético) | CachyOS (ambiente informado) | Não reconfirmado no teste visual | Sessão gráfica do usuário | Não se aplica | Não se aplica | OBS 32.2.2 | Screenshot do usuário mostra barras via fonte de vídeo; movimento/FPS/estabilidade não confirmados |

Build Android debug/release unsigned comprovado com JDK17/API35. Testes unitários
não comprovam execução em Android9, Android recente ou aparelho Samsung.
Meet, Discord, outras distribuições e captura real no OBS permanecem pendentes.
Contribua com versões exatas, resolução, FPS observado e testes de desconexão,
sem publicar IPs pessoais, tokens ou vídeos sem consentimento.

A nova interface 0.2.3-dev e confirmação automática do QR ainda precisam de teste físico.
