# Changelog

## Correção local do CI pré-release — 2026-11-19

- Após integração do PR #2 em `446f175`, a execução remota `44596360350` revelou ausência de `lxml`: quatro verificadores aprovados, erro de importação da suíte original e suíte do repositório não executada.
- Corrigida a afirmação de biblioteca padrão suficiente para a suíte completa: o reparador original já depende de `lxml`, pré-instalado no ambiente dos testes locais anteriores.
- Preparada instalação de `lxml==6.1.3` somente no ambiente do CI, sem alterar os 31 arquivos do plugin ou o inventário. Sem suprimir testes ou ignorar erros.
- Registro pré-release complementado com a falha remota, reprodução isolada e ajuste local; nova execução remota permanece pendente de push autorizado.

## Pós-merge e pré-release do plugin 0.2.2 — 2026-11-19 (preparação local)

- Migração integrada na `main` pelo PR #1, no commit `a9f3a0435009d74a199f3f52977246f1f3d409fc`; README atualizado para distinguir integração de código e publicação do instalável.
- Release instalável 0.2.2 ainda não publicada; release histórica `v1.0.0` preservada. Atualização do portal permanece fora desta etapa.
- Reexecutados na `main`, antes de alterações, os quatro verificadores e as duas suítes existentes com Python 3.12.3: 59 testes aprovados, 1 ignorado por falta de amostra externa e nenhuma falha.
- ZIP original conferido por SHA-256, CRC, estrutura, inventário e comparação byte a byte dos 31 arquivos com a árvore integrada; nenhum arquivo do pacote ou do inventário foi alterado.
- Preparado CI mínimo com os mesmos seis comandos em pull requests e pushes para `main`, sem publicação ou upload de artefatos. Execução remota pendente de push autorizado.
- Acrescentado registro técnico de pré-release; preservado integralmente o registro histórico `docs/MIGRACAO_0.2.2.md`. Novas alterações permanecem locais para revisão humana.

## Plugin 0.2.2 / Skill 1.1.1 — 2026-11-19 (migração local, publicação pendente)

- Repositório renomeado de `skill_governanca_documental` para `plugin_governanca_documental`; distribuição corrente passa a ser o plugin completo.
- Incorporados, byte a byte, os 31 arquivos do ZIP original 0.2.2: manifestos portátil e de compatibilidade, Skill 1.1.1, documentação, scripts e testes.
- Substituídas as quatro normas por Contrato 0.8, Padronização 3.5, Qualidade 1.3 e Modelo Formal 0.5, com suas transcrições derivadas e hashes originais.
- Retirados o manifesto duplicado da raiz e o build da Skill independente; nenhum build de plugin foi inventado. Procedimentos e evidências da Skill 1.0.0 seguem preservados no histórico e na tag `v1.0.0`.
- Adaptados os testes do repositório e adicionado inventário de proveniência para conferir todos os arquivos transportados, incluindo tamanhos e SHA-256.
- Publicação pública futura do pacote completo e das normas autorizada pelo responsável; preparação local não autoriza push, merge, release nem alteração do portal.
- Mantidas as ressalvas originais: auditoria OOXML parcial, execução condicional ao host e validação humana; nenhuma homologação universal ou nova execução funcional do host é declarada.

As entradas abaixo descrevem a distribuição histórica da Skill independente.

## 1.0.0 — 2026-10-28

- Promovida a distribuição estável após a bateria funcional H00–H07, com limites de evidência registrados em `tests/HOMOLOGACAO.md`.
- H07: DOCX institucional em conversa independente, fontes e execução documental condizentes com a Skill e indicação visual apresentada pelo usuário; não há log direto do evento de acionamento automático.
- Reexecutados oito testes automatizados: integridade de fontes, portabilidade do diretório, auditoria OOXML, coerência de status de release e de versão entre frontmatter e manifesto.
- `build_release.py` passa a ler a versão do manifesto, evitando divergência entre o nome do ZIP e a distribuição.
- Nenhuma alteração nas quatro fontes normativas, nos espelhos Markdown derivados ou no workflow operacional `SKILL.md` (exceto metadado de versão).
- Distribuição pública do pacote 1.0.0, incluindo as quatro fontes normativas e transcrições, expressamente autorizada. A autorização não abrange automaticamente novos materiais ou versões futuras e não concede licença irrestrita; a aplicação continua institucional. Publicação no GitHub e instalação no ChatGPT permanecem ações separadas.

## 1.0.0-rc.2 — 2026-10-27

- Incorporadas evidências dos testes H00–H06; permanência de pendência para acionamento automático (não testado).
- Corrigida a validação de identidade da Skill quando o host renomeia a pasta de instalação: identidade conferida entre `SKILL.md` e `manifest.json`; nome físico divergente gera aviso no modo runtime.
- Acrescentado `--strict-dir-name` obrigatório no empacotamento e CI, preservando conformidade com a especificação Agent Skills no diretório distribuído.
- Incluídos testes de regressão para diretório renomeado, verificação estrita e divergência real de identidade.
- Não houve alteração das quatro fontes normativas, das transcrições ou das regras operacionais da Skill.
- **Pendente antes da versão estável:** homologação da rc.2 instalada e acionamento automático em conversa independente.


## 1.0.0-rc.1 — 2026-10-26

- Primeira distribuição candidata independente de projeto.
- Incluídas quatro fontes vigentes, sem modificá-las: Qualidade 1.2, Padronização 3.4, Contrato 0.7 e Modelo Formal 0.4.
- Definido ponto de entrada `SKILL.md` com classificação proporcional, gates, bloqueios localizados e regras de execução.
- Acrescentados manifesto, transcrições de leitura derivadas e validação de integridade.
- Acrescentada auditoria OOXML auxiliar para regressão do problema de títulos/bookmarks.
- **Pendente:** homologação da Skill instalada em ambiente limpo e teste de interoperabilidade na aplicação consumidora.
