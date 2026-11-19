# Verificação pós-merge e pré-release do plugin 0.2.2

Data de referência: 19/11/2026, America/Sao_Paulo. Registro técnico de desenvolvimento; não constitui aprovação institucional ou autorização de publicação.

**Atualização:** as seções iniciais registram a preparação anterior ao PR #2. A seção final documenta a integração posterior, a falha observada no CI e a correção local; seu parecer substitui o GO inicial.

## Base e estado remoto

A `main` local e o remoto foram conferidos antes das alterações e coincidem em `a9f3a0435009d74a199f3f52977246f1f3d409fc`. Não havia commits posteriores no remoto no momento da consulta, nem alterações locais preexistentes. Não foi necessário atualizar o conteúdo da `main`.

O [PR #1](https://github.com/johanngf/plugin_governanca_documental/pull/1) consta como integrado nesse commit em 19/11/2026, às 15:30:12, America/Sao_Paulo. O código-fonte do plugin 0.2.2 e da Skill 1.1.1 está integrado; isso não equivale à publicação do instalável, instalação no host ou aprovação institucional.

A consulta à [coleção de releases](https://api.github.com/repos/johanngf/plugin_governanca_documental/releases?per_page=100) retornou somente a release publicada `v1.0.0`, imutável, com o asset histórico `governanca-documental-institucional-v1.0.0.zip`. Não há release pública 0.2.2 nessa consulta. A tag `v1.0.0` continua no objeto `16d00594a6fcf53db396456e3c5853b13a75e745`, que aponta para `589a2970b9dab38859a00bb9eff3810881eafde6`; nenhuma tag foi criada ou movida.

Branch desta execução: `chore/pos-merge-pre-release-0.2.2`, criada da `main` conferida. As alterações de pós-merge permanecem na working tree, sem commit, staging ou push. O registro `docs/MIGRACAO_0.2.2.md` foi preservado integralmente como relato da preparação local original; suas pendências descrevem aquele momento histórico.

## Problemas confirmados e alterações

O README ainda tratava commit, push e merge da migração como pendentes. Não havia workflow de CI no repositório. Não foi encontrada divergência de integridade no pacote integrado.

Arquivos alterados nesta execução:

- `README.md`: distingue código integrado, release não publicada, histórico preservado e próxima etapa do portal; documenta o CI preparado e suas limitações.
- `CHANGELOG.md`: acrescenta entrada pós-merge sem reescrever as entradas históricas.
- `.github/workflows/validate.yml` (novo): automatiza as verificações existentes em pull requests e pushes para `main`.
- `docs/PRE_RELEASE_0.2.2.md` (novo): registra base, resultados, conferência do asset e limites da recomendação.

Os 31 arquivos do pacote original, os quatro DOCX, os dois manifestos, a Skill, seus scripts e testes permanecem idênticos ao commit-base e ao ZIP. `tests/source_0.2.2.json`, os testes próprios do repositório e `docs/MIGRACAO_0.2.2.md` também não foram alterados. Não há mudança no produto, nas normas, na versão ou nas dependências de runtime.

O arquivo `governanca/index.html` do clone local de `gf_ferramentas_internas` ainda aponta ao instalável e às referências da Skill `v1.0.0`. Esse repositório não foi modificado. A consulta à página publicada pela ferramenta web ficou indisponível; não se declara validação do deploy atual. A atualização do portal para a nova distribuição continua sendo uma tarefa posterior, conforme o escopo recebido.

## Validação na main antes de editar

Ambiente local: Python **3.12.3**, GCC 13.3.0, Linux x86_64, kernel `6.8.0-149-generic`, glibc 2.39. Os comandos foram executados da raiz do repositório, na `main` limpa, em `a9f3a0435009d74a199f3f52977246f1f3d409fc`:

```bash
python3 skills/governanca-documental-institucional/scripts/sync_sources.py --check
python3 skills/governanca-documental-institucional/scripts/verify_package.py --strict-dir-name
python3 skills/governanca-documental-institucional/scripts/rebuild_portable_gate.py --check
python3 skills/governanca-documental-institucional/scripts/portable_gate.py --verify-payload --compare-source
python3 -m unittest discover -s skills/governanca-documental-institucional/tests -v
python3 -m unittest discover -s tests -v
```

Todos terminaram com código 0. As quatro fontes e suas transcrições coincidem com os hashes e tamanhos do inventário; a conferência das transcrições contra os DOCX e a integridade do bootstrap passaram. O payload recuperável coincide com os três scripts centrais originais. Os dois manifestos têm identidade e apresentação consistentes, plugin 0.2.2 e Skill 1.1.1.

| Suíte | Descobertos | Aprovados | Ignorados | Falhas/erros |
| --- | ---: | ---: | ---: | ---: |
| Original da Skill | 49 | 48 | 1 | 0 |
| Repositório | 11 | 11 | 0 | 0 |
| Total por execução | 60 | 59 | 1 | 0 |

O teste `test_actual_v35_sample_works_outside_skill_dir` foi ignorado por ausência da amostra externa esperada em `/mnt/data/`. Os scripts de regressão `regression_samples.py` e `regression_bt01_bt04.py` não foram executados: exigem artefatos externos não fornecidos. Esses cenários não são contabilizados como aprovados.

## CI preparado e verificação local

O workflow tem um job em `ubuntu-24.04`, Python `3.12`, limite de dez minutos e permissão `contents: read`. Usa apenas checkout e setup de Python, com credenciais de checkout não persistidas. Não requer segredos configurados, dependências do projeto, cache, upload de artefatos normativos, deploy ou publicação.

As duas Actions foram fixadas por SHA, conferidos nos repositórios oficiais: [checkout v7.0.1](https://github.com/actions/checkout/tree/3d3c42e5aac5ba805825da76410c181273ba90b1) e [setup-python v7.1.0](https://github.com/actions/setup-python/tree/6d4fd22b20465ccc0f7354476588e8df7c9ca0e0). Os respectivos `action.yml` foram consultados para conferir os inputs usados; ambos declaram runtime Node 24.

O YAML foi analisado com PyYAML já disponível no ambiente, sem adicionar dependência ao projeto. Foram conferidos eventos, permissões, versão de Python e correspondência exata dos seis comandos com os comandos solicitados. Os seis passos `run` foram então executados localmente a partir do YAML e passaram, com os mesmos quantitativos da tabela. Não se somam as duas execuções como cobertura adicional.

As Actions de checkout/setup-python e o runner Ubuntu do GitHub não foram executados localmente. O workflow novo não foi enviado nem executado remotamente. A compatibilidade operacional completa e o resultado de CI no GitHub devem ser verificados após push autorizado; não se declara workflow verde.

## ZIP original de release

Local verificado: `~/Downloads/Governanca_Documental_Plugin_Importavel_v0.2.2_ESTAVEL.zip`.

- Tamanho do arquivo: **313.955 bytes**.
- SHA-256 esperado e observado: `dc5fab000eb67e8a0efcabc6681ea80e73fe3c845b394793f703ac7fc2ac4b4c`.
- Diretório interno único: `governanca-documental-plugin/`.
- **31 entradas**, todas arquivos previstos no inventário; sem duplicatas, extras, diretórios inesperados, symlinks, entradas criptografadas ou caminhos perigosos.
- CRC de todas as entradas aprovado; nomes conferidos contra o inventário exato, com rejeição de caminhos absolutos, `..`, barras invertidas e dois-pontos.
- Cada arquivo interno comparado byte a byte com a árvore atual e por SHA-256/tamanho com `tests/source_0.2.2.json`: **31 correspondências**.
- Manifestos portátil e de compatibilidade: plugin 0.2.2, nome e apresentação coerentes. Diretório canônico da Skill presente, Skill 1.1.1 e exatamente quatro DOCX normativos confirmados.

O ZIP original foi somente lido: não foi alterado, extraído para instalação, repacotado, enviado ou publicado. Não foi criado pacote substituto nem usado snapshot automático do GitHub como instalador. Hashes conferem identidade dos bytes examinados; não são assinatura digital ou comprovação independente de autoria.

## Evidências locais e diff

As evidências completas estão em `dist/pre-release-0.2.2/`, ignorado pelo Git:

- `environment.json`: SHA e ambiente antes das alterações.
- `main-validation.log`: comandos e saídas completos na `main` limpa.
- `workflow-local-validation.log`: validação local dos comandos extraídos do YAML.
- `zip-verification.json`: inventário, tamanhos, hashes e correspondências das 31 entradas.
- `remote-summary.json`: resumo das consultas de PR e releases.
- `pos-merge-completo.patch` e `completo.stat`: diff completo e resumo, incluindo os arquivos novos sem staging.
- `tracked.stat`: resultado de `git diff --stat`, que isoladamente omite arquivos novos.

O diff completo compara uma cópia do commit-base com a árvore atual por `git diff --no-index --binary --no-renames --no-prefix a b`. O índice real permanece intacto. Gerar o diff não equivale à aprovação humana.

## Recomendação e riscos residuais

**GO para solicitar autorização de publicação da release `v0.2.2`**, com as limitações registradas. A base integrada passou nos verificadores e testes locais, e o ZIP original corresponde integralmente ao inventário e à árvore. Não foi identificado bloqueio de integridade do asset.

Essa recomendação permite submeter as evidências ao responsável; não autoriza publicar. As quatro alterações auxiliares permanecem locais para revisão. Eventuais commit, push e integração deste CI exigem autorização e sua execução remota precisa ser observada separadamente. A tag e a release também exigem autorização explícita, com decisão sobre o commit de destino e uso do ZIP original conferido.

Não houve importação do ZIP no ChatGPT/Codex, teste funcional do host, nova interoperabilidade Word para Web ou demonstração de acionamento implícito. Os testes Python cobrem integridade e regressões locais, incluindo auditoria OOXML parcial; não aprovam integralmente conteúdo, apresentação, workflow ou liberação institucional. As evidências históricas do manifesto original mantêm seu escopo próprio.

Nenhum push, merge, tag, release, upload de ZIP, instalação, deploy, mudança de visibilidade/permissões ou atualização do portal foi realizado nesta execução.

## Atualização após o PR #2 — 19/11/2026

Na auditoria de encerramento, a árvore já estava limpa em `main`, no commit `446f175a73055006cd3258a8623bdc15453514f9`, merge do PR #2. O commit intermediário `4de5561` contém exatamente as quatro alterações auxiliares descritas acima. Essa integração ocorreu externamente à preparação local relatada; não foi realizada pelo agente nesta execução.

A [execução remota 44596360350](https://github.com/johanngf/plugin_governanca_documental/actions/runs/44596360350), desse commit, terminou com falha. Checkout, setup de Python e os quatro verificadores passaram. A suíte original encontrou um erro de importação em `test_gate_and_repair`: o script original `normalize_docx_tables.py` requer `lxml`, ausente no runner. A rodada remota descobriu 42 casos, com 40 aprovações, 1 erro de importação e 1 teste ignorado; oito testes do módulo não chegaram a ser carregados. A suíte do repositório ficou sem execução após essa falha. Ambiente remoto: Ubuntu 24.04.5 e CPython 3.12.16.

A afirmação inicial de que a biblioteca padrão bastava para toda a suíte estava incorreta. O reparador já exige `lxml` nos bytes homologados; o ambiente local anterior tinha `lxml 5.2.1` pré-instalado. Isso explica a diferença observada sem indicar corrupção do pacote. A importação foi conferida no arquivo original, sem modificá-lo.

Ajuste localizado proposto antes de implementar: instalar a dependência já existente do reparador no ambiente do CI, manter todos os testes e corrigir a documentação auxiliar. Não se introduziu uma nova dependência no produto nem se alterou o escopo dos gates. Não foi usado skip adicional, `continue-on-error`, reconstrução de scripts ou modificação dos arquivos homologados.

Branch da correção local: `fix/ci-lxml-pre-release-0.2.2`, criada da base `446f175a73055006cd3258a8623bdc15453514f9`. Alterados somente `.github/workflows/validate.yml`, `README.md`, `CHANGELOG.md` e este registro. Sem commit ou staging. O registro histórico `docs/MIGRACAO_0.2.2.md`, o inventário e os 31 arquivos continuam inalterados.

O workflow prepara `lxml==6.1.3` com `python3 -m pip install --only-binary=:all: lxml==6.1.3` antes dos seis checks. A versão foi conferida na [metainformação oficial do PyPI](https://pypi.org/project/lxml/6.1.3/) e validada em ambiente temporário isolado Python 3.12.3. Não foram adicionados arquivos ao pacote ou dependências ao runtime compartilhado. O ambiente temporário foi criado sem pip, pois o Python do host não fornece `ensurepip`; a instalação foi direcionada a ele pelo pip do host, sem instalar pacotes de sistema.

Primeiro, a falha por ausência de `lxml` foi reproduzida no ambiente isolado: 42 casos, 1 erro de importação e 1 ignorado. Depois da instalação da wheel, os mesmos seis comandos passaram: quatro verificadores aprovados, 48 testes originais aprovados e 1 ignorado, mais 11 testes do repositório aprovados. Total da rodada corrigida: **59 aprovações, 1 ignorado, nenhuma falha**. O YAML foi analisado e os comandos executados a partir dele. Essa evidência valida o ajuste local; não equivale à execução remota da correção em CPython 3.12.16.

Evidências complementares em `dist/pre-release-0.2.2/`: `ci-remote-failure.txt` (resumo e trecho do log remoto), `ci-missing-lxml-reproduction.log`, `ci-lxml-isolated-validation.log`, `ci-lxml-completo.patch` e `ci-lxml-completo.stat` (diff da correção contra `446f175`). Os artefatos anteriores permanecem como evidência histórica da preparação inicial. O ZIP original continua com o mesmo SHA-256 e os mesmos 31 arquivos.

**Parecer atualizado: NO-GO para solicitar publicação com o CI atualmente falhando.** A correção está preparada e passou localmente, pronta para revisão humana. A próxima decisão é autorizar sua integração e observar uma nova execução remota; o resultado dessa execução deve embasar a revisão do parecer. Nenhum push, merge, rerun de workflow, tag, release ou upload foi realizado para essa correção. A release pública existente continua sendo somente `v1.0.0`, conforme nova consulta à coleção de releases. Importação funcional do ZIP e homologação institucional continuam sem execução nesta atividade.
