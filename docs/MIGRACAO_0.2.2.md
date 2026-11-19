# Registro técnico da migração local para o plugin 0.2.2

Data de referência: 19/11/2026, America/Sao_Paulo. Registro técnico de desenvolvimento, sem aprovação institucional do plugin ou dos documentos produzidos por ele.

## Fonte, identidade e base

Fonte fornecida pelo responsável: `~/Downloads/Governanca_Documental_Plugin_Importavel_v0.2.2_ESTAVEL.zip`.
SHA-256 do ZIP: `dc5fab000eb67e8a0efcabc6681ea80e73fe3c845b394793f703ac7fc2ac4b4c`.
O ZIP contém 31 arquivos, sob `governanca-documental-plugin/`, com manifesto portátil Agent Plugins 1.0 e overlay `.codex-plugin/plugin.json`, ambos na versão 0.2.2. A Skill tem versão 1.1.1 em seu frontmatter e manifesto. A raiz do repositório corresponde à raiz interna desse plugin; não foi acrescentado outro nível de diretórios.

Os quatro DOCX e `portable_gate.py` coincidem com os cinco hashes expressos no prompt. O inventário `tests/source_0.2.2.json` registra os bytes, tamanhos e SHA-256 de todos os 31 arquivos do ZIP. A identidade foi conferida contra o arquivo fornecido; não foi verificada assinatura digital externa. Os arquivos da distribuição foram preservados sem alterações de conteúdo.

Repositório: `https://github.com/johanngf/plugin_governanca_documental.git`.
Branch local: `feat/migracao-plugin-0.2.2`.
Commit-base: `589a2970b9dab38859a00bb9eff3810881eafde6`.
A árvore estava limpa antes da migração. `git ls-remote --symref origin HEAD refs/heads/main refs/tags/v1.0.0` confirmou `HEAD -> main` e a mesma base no remoto. A primeira tentativa sem acesso de rede falhou por resolução DNS; a consulta com acesso autorizado passou. Não foi necessário atualizar commits locais, pois as bases eram iguais.

Tag histórica `v1.0.0`: objeto `16d00594a6fcf53db396456e3c5853b13a75e745`, igual no remoto e no clone. Nenhum commit, tag ou histórico foi reescrito. Nenhum commit da migração foi criado; alterações permanecem na working tree, sem staging. O repositório `gf_ferramentas_internas` permaneceu limpo e não foi alterado. Nenhuma alteração no portal foi realizada.

## Mapa de alterações

28 arquivos adicionados, 8 modificados e 12 excluídos, por comparação de caminhos com o commit-base, sem inferir renomes. O Git pode apresentar as substituições de normas e transcrições como renomes por similaridade.

O pacote novo substitui a distribuição independente. O manifesto duplicado da raiz foi removido porque não integra a estrutura original. O build antigo só produzia a Skill independente e foi removido; não há procedimento oficial no ZIP para empacotar o plugin completo, portanto não foi gerado ZIP candidato. `rebuild_portable_gate.py` mantém apenas o payload interno e foi usado exclusivamente em modo `--check`.

Os antigos roteiros e relatórios de homologação foram retirados da árvore corrente, pois não integram o pacote 0.2.2. Continuam consultáveis no histórico e em `v1.0.0`. README e changelog apontam explicitamente a versão corrente e o renomeamento do repositório. Os testes próprios foram conservados e adaptados; três verificações complementares conferem inventário exato, manifestos e tamanhos. `.gitignore` foi conservado: suas regras já cobrem caches Python, `dist/` e `.tmp/`.

### Adicionados

- `.codex-plugin/plugin.json`
- `docs/MIGRACAO_0.2.2.md`
- `plugin.json`
- `skills/governanca-documental-institucional/docs/EXECUCAO_PORTATIL.md`
- `skills/governanca-documental-institucional/docs/GATE_FORMAL_EVIDENCIAS.md`
- `skills/governanca-documental-institucional/docs/NOTAS_TECNICAS.md`
- `skills/governanca-documental-institucional/docs/TESTE_INTEROPERABILIDADE_WORD_WEB.md`
- `skills/governanca-documental-institucional/references/consulta/Contrato_Operacional_Execucao_Documental_por_IA_v0.8.md`
- `skills/governanca-documental-institucional/references/consulta/Diretriz_Padronizacao_Documental_Institucional_v3.5.md`
- `skills/governanca-documental-institucional/references/consulta/Diretriz_Qualidade_Construcao_Conteudo_Documental_Institucional_v1.3.md`
- `skills/governanca-documental-institucional/references/consulta/Modelo_Formal_Workflow_Execucao_Documental_IA_v0.5.md`
- `skills/governanca-documental-institucional/references/normativas/Contrato_Operacional_Execucao_Documental_por_IA_v0.8.docx`
- `skills/governanca-documental-institucional/references/normativas/Diretriz_Padronizacao_Documental_Institucional_v3.5.docx`
- `skills/governanca-documental-institucional/references/normativas/Diretriz_Qualidade_Construcao_Conteudo_Documental_Institucional_v1.3.docx`
- `skills/governanca-documental-institucional/references/normativas/Modelo_Formal_Workflow_Execucao_Documental_IA_v0.5.docx`
- `skills/governanca-documental-institucional/scripts/normalize_docx_tables.py`
- `skills/governanca-documental-institucional/scripts/portable_gate.py`
- `skills/governanca-documental-institucional/scripts/rebuild_portable_gate.py`
- `skills/governanca-documental-institucional/scripts/run_gate.py`
- `skills/governanca-documental-institucional/scripts/verify_gate_evidence.py`
- `skills/governanca-documental-institucional/tests/regression_bt01_bt04.py`
- `skills/governanca-documental-institucional/tests/regression_samples.py`
- `skills/governanca-documental-institucional/tests/test_audit_docx.py`
- `skills/governanca-documental-institucional/tests/test_cover_gate_evidence.py`
- `skills/governanca-documental-institucional/tests/test_gate_and_repair.py`
- `skills/governanca-documental-institucional/tests/test_hardened_gate.py`
- `skills/governanca-documental-institucional/tests/test_portable_gate.py`
- `tests/source_0.2.2.json`

### Modificados

- `CHANGELOG.md`
- `README.md`
- `skills/governanca-documental-institucional/SKILL.md`
- `skills/governanca-documental-institucional/manifest.json`
- `skills/governanca-documental-institucional/scripts/audit_docx.py`
- `skills/governanca-documental-institucional/scripts/verify_package.py`
- `tests/test_audit_docx.py`
- `tests/test_package.py`

### Excluídos

- `manifest.json`
- `scripts/build_release.py`
- `skills/governanca-documental-institucional/references/consulta/Contrato_Operacional_Execucao_Documental_por_IA_v0.7.md`
- `skills/governanca-documental-institucional/references/consulta/Diretriz_Padronizacao_Documental_Institucional_v3.4.md`
- `skills/governanca-documental-institucional/references/consulta/Diretriz_Qualidade_Construcao_Conteudo_Documental_Institucional_v1.2.md`
- `skills/governanca-documental-institucional/references/consulta/Modelo_Formal_Workflow_Execucao_Documental_IA_v0.4.md`
- `skills/governanca-documental-institucional/references/normativas/Contrato_Operacional_Execucao_Documental_por_IA_v0.7.docx`
- `skills/governanca-documental-institucional/references/normativas/Diretriz_Padronizacao_Documental_Institucional_v3.4.docx`
- `skills/governanca-documental-institucional/references/normativas/Diretriz_Qualidade_Construcao_Conteudo_Documental_Institucional_v1.2.docx`
- `skills/governanca-documental-institucional/references/normativas/Modelo_Formal_Workflow_Execucao_Documental_IA_v0.4.docx`
- `tests/ACCEPTANCE.md`
- `tests/HOMOLOGACAO.md`

### Arquivos anteriores sem alteração de conteúdo

- `.gitignore`
- `skills/governanca-documental-institucional/scripts/sync_sources.py`

## DOCX incorporados e bootstrap

| Arquivo | Bytes | SHA-256 |
| --- | ---: | --- |
| `Contrato_Operacional_Execucao_Documental_por_IA_v0.8.docx` | 59199 | `67e9a966b466e4e181f2e4451d5b53aa16c6528a6711ac69126ed42e9dbba6c1` |
| `Diretriz_Padronizacao_Documental_Institucional_v3.5.docx` | 59058 | `8193c355bc558161167eb904646f43441f4dad72bd1ec4f885d0715796b30263` |
| `Diretriz_Qualidade_Construcao_Conteudo_Documental_Institucional_v1.3.docx` | 37072 | `c826a93c75a9f63c5faec2795cb862a6e8850fbf62c6d38d1e6c4e4b978ebfb1` |
| `Modelo_Formal_Workflow_Execucao_Documental_IA_v0.5.docx` | 53592 | `4db0d953432e8281ec623b5c8cca5b507cea56a680eb5a747a60a7873ebe2f39` |
| `portable_gate.py` | 23920 | `a722e25e2034fd5461cf36bafe32eb0c16ec3e5c16ad6af4895ee99cebf6805e` |

## Validação executada

Antes da migração, o verificador oficial e a suíte original foram executados na fonte extraída: integridade aprovada e 49 testes descobertos, sendo 48 aprovados e 1 ignorado por ausência de amostra externa.

Na árvore migrada, da raiz do repositório, todos os comandos abaixo terminaram com código 0:

```bash
python3 skills/governanca-documental-institucional/scripts/sync_sources.py --check
python3 skills/governanca-documental-institucional/scripts/verify_package.py --strict-dir-name
python3 skills/governanca-documental-institucional/scripts/rebuild_portable_gate.py --check
python3 skills/governanca-documental-institucional/scripts/portable_gate.py --verify-payload --compare-source
python3 -m unittest discover -s skills/governanca-documental-institucional/tests -v
python3 -m unittest discover -s tests -v
```

Resultados: quatro DOCX e quatro transcrições coerentes, hashes e tamanhos corretos, bootstrap íntegro e cópia dos três scripts centrais coincidente com os originais. Suíte original: 48 aprovados e 1 ignorado, de 49 descobertos. Suíte do repositório: 11 aprovados. Total: 59 aprovações, 1 teste ignorado, nenhuma falha. O log completo está em `dist/review/validation.log`, ignorado pelo Git.

`git diff --check` passou para os arquivos rastreados. JSON dos manifestos e do inventário foi analisado; frontmatter YAML analisado com PyYAML já disponível, sem adicionar dependências ao projeto. Conferência de nomes de arquivos, symlinks e padrões de chave privada, AWS access key e tokens GitHub não encontrou ocorrências; a busca de credenciais limita-se aos padrões pesquisados. Não foram incorporados anexos privados de teste. Detalhes em `dist/review/review-checks.txt`.

## Diff para revisão

`dist/review/tracked.stat` registra o resultado de `git diff --stat` da working tree. Esse comando isoladamente omite arquivos novos sem staging. Por isso, `dist/review/migracao-completa.patch` contém o diff completo, com arquivos novos e deltas binários, comparando uma cópia de `HEAD` com a árvore corrente via `git diff --no-index --binary --no-renames --no-prefix a b`. `dist/review/completo.stat` e `dist/review/alteracoes.tsv` complementam o mapa de alterações. Esses arquivos são evidências locais ignoradas, não um pacote instalável. O índice real foi preservado.

Os principais efeitos do diff são a troca dos manifestos de distribuição, das quatro normas e transcrições, o transporte integral do gate portátil e sua suíte, e a adaptação da documentação e dos testes do repositório. A disponibilidade do diff não equivale a revisão humana concluída.

## Limitações e pendências

- `test_actual_v35_sample_works_outside_skill_dir` não executou por ausência da amostra externa esperada em `/mnt/data/`. Não foi criada uma amostra substituta.
- `regression_samples.py` e `regression_bt01_bt04.py` não foram executados: exigem DOCX externos e, no primeiro caso, mapa de páginas não fornecidos no pacote. Os testes unitários distribuídos cobrem regressões sintéticas, sem comprovar esses cenários externos.
- Não foram executados testes funcionais no host consumidor, Word para Web, acionamento implícito, inspeção visual nem gates semânticos e institucionais completos. A auditoria OOXML é parcial; a execução portátil depende das capacidades do host e exige validação humana.
- O pacote original contém referências históricas a Skill 1.1.0, candidatas e `maintenance_revision.plugin_version = 0.2.1`. Foram preservadas como parte dos bytes homologados; os manifestos efetivos declaram plugin 0.2.2 e Skill 1.1.1. Essas referências não foram promovidas a evidência nova.
- A versão 1.0.0 é identificada como histórica na documentação corrente. As quatro normas permanecem canônicas; transcrições são auxiliares e o portal é complementar, sem obrigatoriedade de acesso para execução.
- A integridade local não comprova certificação universal, aceitação pela interface de instalação ou autenticidade criptográfica da autoria do pacote.

Próximas etapas dependem de decisão do responsável: revisão humana do diff; eventual commit e push autorizados; revisão e merge autorizados; preparação e publicação de release autorizadas; somente depois, atualização do portal em tarefa separada. Esta execução termina na preparação local. Não foram feitos push, merge, release, instalação, publicação, deploy ou mudança de configuração/visibilidade do repositório.
