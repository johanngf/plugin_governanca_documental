# Governança Documental Institucional — Plugin

Código-fonte corrente: **plugin 0.2.2**, contendo a **Skill `governanca-documental-institucional` 1.1.1**, integrado na `main` pelo [PR #1](https://github.com/johanngf/plugin_governanca_documental/pull/1), no commit `a9f3a0435009d74a199f3f52977246f1f3d409fc`. Em 19/11/2026, a **release instalável 0.2.2 ainda não foi publicada**; a release histórica da Skill `v1.0.0` permanece preservada. A integração do código não instala o plugin em contas nem comprova importação funcional no host.

O repositório foi renomeado de `skill_governanca_documental` para [`plugin_governanca_documental`](https://github.com/johanngf/plugin_governanca_documental). A tag histórica [`v1.0.0`](https://github.com/johanngf/plugin_governanca_documental/tree/v1.0.0) registra a distribuição anterior da Skill independente, com seus procedimentos e evidências próprios. Ela não representa a versão corrente do plugin.

## Estrutura e autoridade

A raiz do repositório corresponde ao diretório `governanca-documental-plugin/` do ZIP original:

- `plugin.json`: manifesto portátil Agent Plugins 1.0, versão 0.2.2.
- `.codex-plugin/plugin.json`: manifesto de compatibilidade, versão 0.2.2.
- `skills/governanca-documental-institucional/`: Skill 1.1.1 integral, incluindo manifesto, documentação, scripts, testes e referências.
- `tests/`: verificações complementares do repositório e inventário de proveniência dos 31 arquivos originais.

As quatro fontes canônicas são os DOCX empacotados: Contrato Operacional 0.8, Padronização 3.5, Qualidade e Construção de Conteúdo 1.3 e Modelo Formal do Workflow 0.5. As transcrições Markdown são auxiliares e não têm autoridade normativa independente. A Skill aplica as quatro normas e tem versão própria; não é uma quinta norma.

O [portal de consulta](https://johanngf.github.io/gf_ferramentas_internas/governanca/) é referência complementar, não é fonte normativa e sua disponibilidade não é obrigatória para executar o plugin.

## Origem e distribuição

Fonte desta migração: `Governanca_Documental_Plugin_Importavel_v0.2.2_ESTAVEL.zip`, SHA-256 `dc5fab000eb67e8a0efcabc6681ea80e73fe3c845b394793f703ac7fc2ac4b4c`. Os 31 arquivos do plugin foram transportados sem alterações de conteúdo. O inventário em `tests/source_0.2.2.json` registra caminhos, tamanhos e hashes para confronto com o ZIP fornecido. Hashes conferem identidade; não constituem assinatura digital ou autenticação independente da origem.

A publicação pública do pacote completo 0.2.2, incluindo as quatro normas atualizadas, foi autorizada em princípio pelo responsável. O commit, o push e o merge da migração já foram concluídos pelo PR #1. A etapa pós-merge prepara documentação, CI e evidências locais; novas alterações, push, merge, tag e publicação da release dependem de autorização específica. O portal ainda apresenta a distribuição anterior e sua atualização permanece uma atividade posterior. O acesso público não concede licença irrestrita de uso, modificação ou redistribuição; autoria e titularidade permanecem sob a organização. O escopo institucional de aplicação é preservado.

O pacote original não fornece procedimento de build do plugin completo. O antigo `scripts/build_release.py`, voltado à Skill independente, foi retirado; não deve ser usado para produzir o plugin 0.2.2. Nenhum novo ZIP candidato foi gerado nesta migração. O ZIP fornecido permanece a referência para uma futura distribuição, sujeita à revisão e autorização. Um snapshot automático de código do GitHub não deve ser presumido equivalente ao pacote importável homologado.

## Validação local

Os verificadores de integridade e o auditor usam Python 3.10+ e sua biblioteca padrão. O reparador `normalize_docx_tables.py` já exige **lxml**, também importado pela suíte original da Skill. Para executar a suíte completa, instale essa dependência no ambiente de testes (validada nesta etapa com `lxml==6.1.3`):

```bash
python3 -m pip install --only-binary=:all: lxml==6.1.3
```

Na raiz do repositório:

```bash
python3 skills/governanca-documental-institucional/scripts/sync_sources.py --check
python3 skills/governanca-documental-institucional/scripts/verify_package.py --strict-dir-name
python3 skills/governanca-documental-institucional/scripts/rebuild_portable_gate.py --check
python3 skills/governanca-documental-institucional/scripts/portable_gate.py --verify-payload --compare-source
python3 -m unittest discover -s skills/governanca-documental-institucional/tests -v
python3 -m unittest discover -s tests -v
```

O verificador original confere versões, fontes, hashes, transcrições e bootstrap. Os testes do repositório complementam a conferência de tamanhos e da identidade byte a byte de todos os arquivos distribuídos. Para detalhes de execução, consulte os documentos originais em `skills/governanca-documental-institucional/docs/`, em especial `EXECUCAO_PORTATIL.md` e `GATE_FORMAL_EVIDENCIAS.md`.

O workflow `.github/workflows/validate.yml` executa esses seis comandos em pull requests e pushes para `main`, em Ubuntu 24.04 com Python 3.12. Foi integrado pelo PR #2, no commit `446f175a73055006cd3258a8623bdc15453514f9`. A [primeira execução nesse commit](https://github.com/johanngf/plugin_governanca_documental/actions/runs/44596360350) passou nos quatro verificadores, mas falhou ao importar a suíte original por ausência de `lxml`; os testes do repositório não executaram nessa rodada. Os testes locais anteriores utilizavam `lxml` pré-instalado, limitação que não havia sido identificada na preparação inicial.

O ajuste local do CI instala `lxml==6.1.3`, dependência já exigida pelo reparador, antes das verificações. Foi validado em ambiente Python 3.12.3 isolado, sem alterar o pacote original. Mantém permissões de leitura, sem segredos configurados, upload de artefatos ou publicação. O push e a integração desse ajuste ainda dependem de autorização; a execução remota da correção não ocorreu e não se declara CI aprovado.

A suíte original inclui um teste condicional com amostra externa em `/mnt/data/`; ele é ignorado quando a amostra não está disponível. Os scripts `regression_samples.py` e `regression_bt01_bt04.py` exigem artefatos externos não incluídos no pacote. Sua presença não comprova execução desses cenários nesta migração.

## Limites da evidência

A auditoria OOXML é parcial e os gates automatizados têm escopo limitado. A execução depende de leitura íntegra, escrita, Python e acesso aos bytes do DOCX no host consumidor. Os resultados automatizados não substituem inspeção visual, avaliação semântica, validação humana ou aprovação institucional.

As evidências históricas incluídas no manifesto original têm o escopo e a proveniência nele declarados. Esta migração não repetiu testes funcionais do host, Word para Web, acionamento implícito ou gates documentais completos. Não há certificação universal nem garantia de acionamento implícito em todos os ambientes. Referências históricas a versões anteriores nos arquivos originais foram preservadas para manter o pacote exato.

O registro histórico da preparação local permanece em [docs/MIGRACAO_0.2.2.md](docs/MIGRACAO_0.2.2.md). O estado pós-merge, a reexecução dos testes e a conferência do ZIP original estão em [docs/PRE_RELEASE_0.2.2.md](docs/PRE_RELEASE_0.2.2.md).
