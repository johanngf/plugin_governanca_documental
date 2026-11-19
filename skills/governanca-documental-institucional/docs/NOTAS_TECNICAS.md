# Notas técnicas históricas — origem na candidata 1.1.0-rc.4

Documento de engenharia **não normativo**. As fontes canônicas permanecem os quatro DOCX em `references/normativas/`.

## Verificações implementadas

- Duplicidade de `w:style/@w:styleId` em `word/styles.xml`.
- Duplicidade de `w:outlineLvl` em um mesmo `w:pPr`.
- Ordem dos elementos reconhecidos em `w:tblPr` conforme a sequência de `CT_TblPrBase` (incluindo `tblBorders` antes de `tblLayout`/`tblLook`).
- Presença de atributo obrigatório `w:val` em `w:shd`.
- Integridade básica de bookmark/âncora, `w:pPr` no início, campos complexos (inclusive TOC que cruza parágrafos) e `PAGEREF`.
- Comparação opcional de cache `PAGEREF` com mapa produzido por verificação independente de páginas (`--bookmark-pages`).
- Perfil formal opcional `--profile institutional-v3.5` (alias legado `institutional-v3.4`) para estilos `Normal` e `Heading1`/`Heading2`/`Heading3`, incluindo nomes e tamanhos de fontes, e formato Carta/Letter. A seleção exige avaliação de templates específicos.

**Não implementado:** validador integral OOXML/XSD, renderização incorporada, atualização real de TOC, testes no Word para Web, validação de todos os campos PAGE/NUMPAGES armazenados, aplicação de correção e certificação institucional. Nenhum resultado `ok: true` substitui os gates da governança.

## Rastreamento das verificações externas

Consulta em 13/11/2026, para verificar a base de duas regras estruturais utilizadas no script:

- `CT_TblPrBase`/`CT_TblPr` — sequência de filhos de propriedades de tabela, incluindo `tblBorders` antes de `tblLayout` e `tblLook`:
  https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_tblPr_topic_ID0EFWLR.html
- `CT_Shd` — declara `w:val` com `use="required"`:
  https://c-rex.net/samples/ooxml/e1/part4/OOXML_P4_DOCX_shd_topic_ID0EGNAR.html

Essas referências descrevem fragmentos do esquema OOXML, sem substituir teste contra o esquema completo e sem representar afirmação de homologação do artefato.

## Regressão sobre o material recebido

Mapa de páginas utilizado apenas durante a regressão local (não distribuído como fonte autoritativa): `sec01` a `sec04` = página 3; `sec05`, `sec06`, `rev`, `refs` = página 4. Confrontado com renderização local de 4 páginas. A atualização em Word/Word para Web não foi testada.

- **PT-05 original:** duplicidade `TOCHeading`, 3 `outlineLvl` duplicados, 4 caches PAGEREF inconsistentes; adicionalmente 3 tabelas com ordem incorreta e 23 `w:shd` sem `w:val`.
- **PT-06 corrigido:** duplicidades removidas e 4 caches comparados corretos; 3 tabelas e 23 `w:shd` continuam pendentes; a presença de `TOC` não comprova sua regeneração.
- **PT-01:** perfil institucional acusa página A4 e divergências tipográficas; não é uma verificação de acionamento automático da Skill.

## Descoberta independente — quatro fontes originais (histórico, antes do saneamento)

O auditor também encontrou situações estruturais na materialização DOCX das normas vigentes, **sem qualquer alteração nos seus arquivos**:

| Fonte | `w:shd` sem `w:val` | Tabelas com ordem de `tblPr` divergente |
|---|---:|---:|
| Qualidade 1.2 | 16 | 13 |
| Padronização 3.4 | 21 | 11 |
| Contrato 0.7 | 19 | 11 |
| Modelo Formal 0.4 | 348 | 27 |

Esses achados não alteram a autoridade institucional das fontes nem implicam autorização para substituir documentos normativos. Requerem um **trabalho separado de saneamento formal**, com preservação de conteúdo, rastreabilidade e validação cruzada. A candidata não foi homologada para distribuição geral.

## Evolução dirigida BT-01/BT-04 (17/11/2026)

- **BT-01 (geração):** acrescentado `scripts/normalize_docx_tables.py` como reparo auxiliar *somente para `word/document.xml`*, exigindo `--output` e preservando a origem. O mecanismo reorganiza `w:tblPr` conforme a sequência conhecida. Em caso de filhos desconhecidos ou duplicados, **recusa** o reparo; não tenta substituir uma validação XSD completa. Recomendação primária: corrigir a rotina de geração. Reexecutar auditoria, gates e comparação do arquivo resultante.
- **BT-04 (auditoria):** tornou-se obrigatório executar o auditor disponível sobre o DOCX efetivo antes do parecer/liberação. `audit_docx.py --report` grava JSON com hash SHA-256 e classe de limitações. A mera leitura do script e a ausência de erros no subconjunto auditado **não** aprovam por si os gates semântico, visual, formal completo ou consumidor.
- **Reprodutibilidade:** scripts e testes de regressão verificam os defeitos reais da amostra original e a correção de ordenação das três tabelas BT-01. `lxml` é dependência **opcional do reparador**, não do auditor (que usa biblioteca padrão). Se indisponível, não executar reparo automatizado nem declarar sucesso.
- **Fontes canônicas:** os quatro DOCX e transcrições derivadas são mantidos idênticos à candidata anterior. Seus achados estruturais preexistentes continuam pendentes de processo separado, sem retificação silenciosa.
- **Rastreabilidade técnica externa** (verificação dirigida em 17/11/2026): sequência de `CT_TblPrBase` https://schemas.liquid-technologies.com/officeopenxml/2006/ct_tblprbase.html ; atributo obrigatório `CT_Shd/@w:val` https://schemas.liquid-technologies.com/officeopenxml/2006/shd.html . São fontes explicativas de esquema, não certificação integral.

## Atualização normativa e versionamento 1.1.0-rc.3 — 17/11/2026

- Após autorização humana de versionamento, os quatro DOCX passaram para Qualidade v1.3, Padronização v3.5, Contrato v0.8 e Modelo Formal v0.5. O saneamento estrutural OOXML foi realizado previamente em cópias, com evidência de preservação textual e visual; esta etapa acrescentou capa, histórico e referências de rastreabilidade.
- Apenas uma versão de cada fonte está empacotada em `references/normativas/`. Derivados `.md` foram regenerados, e o `manifest.json` registra os hashes finais.
- O perfil `institutional-v3.5` verifica os mesmos parâmetros tipográficos do perfil v3.4, pois a v3.5 não alterou esses parâmetros. `institutional-v3.4` permanece como alias para a bateria histórica, sem pretender aplicar versões diferentes.
- Limitações: validador OOXML parcial; 14 páginas no Contrato v0.8 em razão do novo histórico, com Referências iniciadas em página própria e Sumário ajustado; sem teste na instalação do plugin em host externo nem atualização efetiva de campos em Word para Web nesta revisão.
- As irregularidades descritas na seção histórica anterior foram corrigidas nas quatro novas fontes; não representam achados abertos nas revisões presentes. O pacote permanece candidato até validação de ativação e liberação do ciclo institucional.

## Refinamento dirigido BT-01 — candidata 1.1.0-rc.4

- Mantidas integralmente as quatro fontes canônicas Qualidade 1.3, Padronização 3.5, Contrato 0.8 e Modelo 0.5, com hashes originais intactos.
- `audit_docx.py --check-cover-identification` verifica na tabela de metadados da capa padronizada a presença de **dois campos distintos**: `Responsável pelo documento` e `Autoria`, com valores não vazios. Essa análise é opt-in porque templates institucionais específicos podem adotar composição diferente. A verificação não identifica pessoas nem certifica a autoria intelectual ou aprovação.
- `verify_gate_evidence.py` rejeita relatório JSON sem campos essenciais, com SHA divergente, com `ok=false`, com erros reportados, ou com evidência incompleta de identificação de capa quando ela é exigida. Pode validar um relatório de auditor independente somente após sua normalização fiel para o esquema declarado. Não autentica logs nem prova ordem temporal do gate.
- A Skill instrui a entregar o relatório JSON ao lado do DOCX; uma resposta textual dizendo que auditou não constitui evidência suficiente. Não autoriza afirmar resultados de ferramentas indisponíveis.
- Regressões dirigidas: BT-01 da terceira bateria deve falhar por dois papéis ausentes; BT-05 aprovado anteriormente deve passar na conferência de presença dos papéis, mantendo avisos conhecidos sobre campos que requerem validação independente.
