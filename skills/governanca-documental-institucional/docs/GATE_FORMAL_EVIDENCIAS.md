# Gate formal do DOCX — identificação da capa e evidência reproduzível

Este documento é **orientação operacional de implementação** da Skill, não fonte normativa. Aplicar as quatro fontes canônicas do pacote; a regra de separação de papéis provém da seção 11.2 da Padronização v3.5.

## Capa e identificação

Na **capa padronizada**, conferir dois campos separados:

- `Responsável pelo documento`: pessoa/unidade com ownership institucional (não presumir solicitante como responsável).
- `Autoria`: responsável intelectual pelo conteúdo, não a própria IA. Se não houver atribuição comprovada, registrar literalmente a falta de informação, de modo claro, em vez de criar pessoa fictícia.

`Coautoria`, colaboração, revisão e aprovação permanecem condicionais às regras normativas. Não tratar o simples preenchimento de rótulos como verificação da identidade real nem como autorização de publicação. Templates específicos legitimamente prevalentes exigem análise de suas próprias exigências e registro explícito do desvio da capa padrão.

## Comandos e trilha de execução para capa padronizada

Execute **depois da última materialização** e em um diretório de saída que ainda não exista:

```bash
python scripts/run_gate.py /caminho/documento-final.docx --diagnose
python scripts/run_gate.py /caminho/documento-final.docx --output-dir /caminho/evidencias-novas --profile institutional-v3.5
```

A pasta terá `audit.json`, `verification.json`, `execution.json` e logs de erro quando executáveis. `execution.json` registra a ordem local `document_frozen → audit_started → audit_finished → audit_report_persisted → verification_started → verification_finished → document_hash_reconfirmed`. Os hashes do DOCX inicial e final precisam coincidir. A ordem registrada por um processo local **não é trilha auditável do host nem prova independente da anterioridade à entrega**.

O comando executa o verificador em modo **estrito**, que reabre o DOCX e reexecuta as verificações objetivas do auditor empacotado; não confia somente nos campos do relatório. A verificação da capa padrão é obrigatória por padrão. O código de saída `0` significa **exclusivamente** que a auditoria estrutural parcial passou; não significa liberação institucional. Documentos com erros são bloqueados, e auditoria impossível é classificada como não verificável.

Para auditoria manual dos dois componentes, quando o orquestrador estiver indisponível:

```bash
python scripts/audit_docx.py /caminho/documento-final.docx --profile institutional-v3.5 --check-cover-identification --report /caminho/gate-final.json --json
python scripts/verify_gate_evidence.py /caminho/documento-final.docx /caminho/gate-final.json --require-cover-roles --expected-profile institutional-v3.5
```

Um template específico **legitimamente excepcional** pode ser auditado com `--no-standard-cover --cover-exception-reason "referência ao template e justificativa"` na primeira sequência. Isso **não** aprova os papéis da capa: o registro assinala `pending_cover_exception_review`, exige a conferência formal separada do template e retorna código não zero. Nunca usar como atalho para ignorar omissões de campos.

**Anexar DOCX e evidências reais**. Não reutilizar relatório de uma execução anterior, não sobrescrever pastas e não editar o DOCX após o gate sem nova auditoria.

## Auditor independente

Um auditor tecnicamente equivalente pode ser usado quando o `audit_docx.py` não estiver acessível ou outra implementação for necessária. Nesse caso, produzir relatório JSON exportável com os mesmos campos essenciais do auditor empacotado:

- `artifact_sha256`: SHA-256 calculado **sobre os bytes do DOCX final realmente inspecionado**.
- `auditor` ou `auditor_version`: ferramenta e versão/identificação verificáveis, não substituídas por texto genérico não demonstrado.
- `profile`: perfil ou regras efetivamente verificadas; **não declarar `institutional-v3.5` se a ferramenta não cobriu esse perfil**.
- `ok`: booleano relativo ao escopo concreto executado; `issues`: lista de objetos com `severity` e diagnóstico; `gate_limits` ou `limitations`: lista dos limites.
- `cover_roles` (capa padrão): `checked`, `metadata_table_found`, `responsavel_present`, `autoria_present`, `separate_fields`, `values_present` e `method`. Registrar apenas verificações realmente realizadas; não transcrever status positivos de um exemplo. A conferência deve ser feita contra a capa do DOCX.

Validar `python scripts/verify_gate_evidence.py DOCX JSON --require-cover-roles --expected-profile institutional-v3.5`. O script rejeita hash divergente, ausências, perfil incompatível, erros reportados **e** defeitos detectados por nova auditoria do DOCX. Se o auditor independente cobriu apenas regras selecionadas, não nomear seu perfil como o perfil institucional integral: o gate será parcial/pendente até que uma ferramenta adequada reavalie a cobertura faltante. A reauditoria continua parcial em OOXML, não autentica a origem histórica do JSON nem substitui os demais gates. Quando o host impedir o export ou a verificação técnica, declarar a limitação e não afirmar gate aprovado.

## Liberação

Separar no relato final: (1) execução do auditor com JSON e hash, (2) verificação documental da capa e sua atribuição, (3) validação visual de todas as páginas, (4) gate de conteúdo e decisão institucional, (5) limitações. Não confundir `ok=true` parcial com liberação institucional. Registrar a ordem das operações com logs do ambiente quando disponível; **timestamp autodeclarado não comprova, por si só, anterioridade à entrega**.
