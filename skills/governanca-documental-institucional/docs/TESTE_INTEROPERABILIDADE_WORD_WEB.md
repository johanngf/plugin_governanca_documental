# Ensaio controlado de interoperabilidade — Word para Web

Documento **auxiliar de teste**, não fonte normativa. Não pressupõe que o host tenha executado este teste nem que todas as funções estejam disponíveis em todas as contas.

## Entrada

Usar cópia de DOCX previamente auditado e com título hierárquico, campo de página, sumário automático (quando aplicável), hyperlinks/bookmarks e controle de revisão. Preservar bytes e hash do original. Um DOCX sem sumário não testa atualização de sumário.

## Execução manual, pelo usuário que tenha acesso ao Word para Web

1. Carregar cópia no OneDrive e abrir no Word para Web. Registrar se a abertura apresentou alerta de conversão, correção ou perda de recursos.
2. Conferir as seções no painel de navegação por títulos, quando disponível. Testar pelo menos um título do início e um do final; não aceitar identificadores técnicos no lugar de nomes.
3. Testar links de sumário e hyperlinks internos. Separar navegação bem-sucedida de ausência de recurso na interface.
4. Em **cópia de trabalho**, alterar temporariamente um título, tentar atualizar o sumário pelo recurso disponibilizado (quando existir), conferir se a alteração foi refletida e restaurar o título. Se a atualização não estiver disponível, classificar como `recurso não disponível/não verificável`, não como aprovação automática.
5. Salvar a alteração controlada, obter uma cópia do DOCX, fechar e reabrir; verificar se conteúdo, estilos, links, cabeçalhos, rodapés e paginação permaneceram legíveis. Registrar a operação efetivamente realizada — abertura não comprova salvamento.
6. Entregar os dois DOCX, uma nota dos passos realizados, capturas de eventuais problemas e os hashes. Reauditar o arquivo baixado e comparar alterações OOXML explicáveis.

## Resultados separáveis

- `abertura`: passou / falhou / não verificável
- `painel_titulos`: passou / falhou / não disponível
- `hyperlinks`: passou / falhou / não disponível
- `atualizacao_sumario`: passou / falhou / não disponível / não aplicável
- `edicao_salvamento_download`: passou / falhou / não realizado
- `reabertura`: passou / falhou / não realizado
- `comparacao_estrutural`: passou / falhou / pendente

**Não certificar compatibilidade universal** com Word para Web a partir de um único ensaio nem alterar o artefato original para forçar um resultado positivo.
