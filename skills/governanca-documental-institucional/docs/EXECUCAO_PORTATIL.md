# Execução portátil do gate — Skill 1.1.0

Documento técnico auxiliar, **não normativo**. Este procedimento não modifica os quatro DOCX canônicos.

## Problema tratado

Em alguns hosts, os scripts da Skill são legíveis como **recursos textuais** mas não existem como caminhos locais. `portable_gate.py` reúne uma **cópia verificável dos três scripts oficiais** (`audit_docx.py`, `verify_gate_evidence.py`, `run_gate.py`) num único recurso de texto recuperável. Não implementa outro auditor nem fornece execução remota; a disponibilidade de uma ferramenta Python continua indispensável.

## Pré-requisitos

- DOCX final materializado e acessível como bytes no runtime Python.
- Host capaz de **ler integralmente o recurso** `scripts/portable_gate.py`, **escrever exatamente o texto** em arquivo local e executar Python (sem internet nem dependências extras).
- `manifest.json` da Skill disponível para conferência do valor `runtime_bootstrap.sha256`.
- Pasta de saída **nova**, separada do DOCX; não sobrescrever relatórios.

## Fluxo seguro

1. **Verifique execução direta primeiro:** se `scripts/run_gate.py`, `audit_docx.py` e `verify_gate_evidence.py` estão montados, execute `run_gate.py` diretamente.
2. **Se faltarem arquivos montados, obtenha a versão textual integral** de `scripts/portable_gate.py` pela interface de recursos da Skill. Não resuma, traduza, reconstrua, modifique nem confunda com o conteúdo deste documento.
3. **Materialize o recurso exatamente** em arquivo temporário, por exemplo `/tmp/gd-portable/portable_gate.py`. A ferramenta de escrita deve suportar arquivos sem truncamento. Não utilize URLs externas.
4. **Confira SHA-256 do arquivo salvo** com o valor `runtime_bootstrap.sha256` em `manifest.json`. Se não coincidir, **pare**; não execute uma versão reconstruída ou recortada.
5. **Valide o payload:** `python /tmp/gd-portable/portable_gate.py --verify-payload`. A ferramenta verifica SHA-256 do ZIP interno e dos três scripts recuperados.
6. **Execute:** `python /tmp/gd-portable/portable_gate.py /caminho/arquivo-final.docx --output-dir /caminho/gate-novo --profile institutional-v3.5`.
7. **Colete evidências:** `audit.json`, `verification.json`, `execution.json` e `bootstrap.json`; confira `structural_gate`, `artifact_sha256` e limitações. Se qualquer etapa falhar, não declarar gate aprovado nem substituir os resultados por relato em prosa.
8. **Complete separadamente** a inspeção visual, gate semântico, referências, limites de workflow e decisão institucional. `institutional_release` permanece `not_authorized` no gate automatizado, inclusive se a parcela estrutural passar.

### Exemplo de hash do recurso (após materializá-lo)

```bash
python -c "import hashlib,pathlib; p=pathlib.Path('/tmp/gd-portable/portable_gate.py'); print(hashlib.sha256(p.read_bytes()).hexdigest())"
```

**Nota de portabilidade:** é possível que a interface consiga retornar o texto completo da Skill, mas não transportar esse texto de volta ao runtime de escrita em uma única operação íntegra. Nesse caso, a recuperação NÃO está demonstrada; registrar a limitação. Não conte com a execução em todo host ChatGPT somente porque o recurso existe.

**Nota de segurança:** o hash publicado em um manifesto não é assinatura digital nem garante autenticidade do plugin; ele serve à conferência de identidade dos arquivos da distribuição examinada. O payload executa apenas os scripts do próprio plugin, via `sys.executable`, sem shell nem download.

**Template excepcional:** a opção `--no-standard-cover --cover-exception-reason '...'` propaga a pendência de conferência específica de capa; não aprova a exceção automaticamente.

**Verificação do mantenedor:** com o pacote montado, execute `python scripts/portable_gate.py --verify-payload --compare-source`. Isso compara a cópia recuperável, byte a byte, com os três scripts originais distribuídos.
