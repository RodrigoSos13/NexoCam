# Contribuir

Use Python 3.11+, venv e instalação editável com extras dev do README.
Antes de enviar mudanças: `ruff check linux`, `ruff format --check linux` e
`pytest linux/tests`. Descreva resultado e limitações de testes reais.

Não adicione Docker, serviços externos, segredos, gravação automática ou comandos
privilegiados silenciosos. Preserve limites de filas e fechamento de recursos.
Alterações de protocolo exigem atualizar protocol/README.md e testes.
