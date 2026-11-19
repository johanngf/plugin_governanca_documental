#!/usr/bin/env python3
"""Normaliza APENAS a ordem de propriedades w:tblPr em word/document.xml.

Ferramenta de reparo controlado, não um validador OOXML completo.
Requer lxml; não modifica a origem; exige um caminho de saída distinto.
Recusa tabelas com propriedades desconhecidas ou duplicadas: não resolve conflitos.
NÃO modifica w:shd sem w:val, estilos, texto, sumário ou metadados de revisão.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

try:
    from lxml import etree
except ImportError:
    raise SystemExit('Requer lxml instalado; não efetuar correção por substituição textual insegura.')

W='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
ORDER=('tblStyle','tblpPr','tblOverlap','bidiVisual','tblStyleRowBandSize',
       'tblStyleColBandSize','tblW','jc','tblCellSpacing','tblInd',
       'tblBorders','shd','tblLayout','tblCellMar','tblLook','tblPrChange')
RANK={f'{W}{n}':i for i,n in enumerate(ORDER)}
PART='word/document.xml'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def normalized_xml(data):
    parser=etree.XMLParser(resolve_entities=False,no_network=True,remove_blank_text=False)
    tree=etree.fromstring(data, parser=parser)
    count=0
    for index, tblpr in enumerate(tree.iter(f'{W}tblPr'),start=1):
        children=list(tblpr)
        if not children:
            continue
        unexpected=[x.tag for x in children if x.tag not in RANK]
        if unexpected:
            raise ValueError(f'tblPr #{index}: propriedade desconhecida; recusa de edição: {unexpected}')
        duplicated=[k for k,v in collections.Counter(x.tag for x in children).items() if v>1]
        if duplicated:
            raise ValueError(f'tblPr #{index}: propriedade duplicada; requer decisão: {duplicated}')
        ordered=sorted(children,key=lambda x:RANK[x.tag])
        if ordered!=children:
            # Só desloca elementos irmãos do tblPr. Não altera atributos ou conteúdo.
            for c in children:tblpr.remove(c)
            for c in ordered:tblpr.append(c)
            count+=1
    if not count:
        return data,0
    # Preservar indicação original de XML declaration/standalone quando existente.
    declaration=re.match(rb'^\s*<\?xml\s+[^?]*\?>', data)
    new=etree.tostring(tree, encoding='UTF-8',xml_declaration=False)
    if declaration:
        new=declaration.group(0)+new
    # Conferir estabilidade semântica: mover somente os filhos tblPr não pode
    # alterar textos, atributos ou qualquer outra propriedade.
    parsed=etree.fromstring(new,parser=parser)
    if [(el.tag,dict(el.attrib),el.text,el.tail) for el in tree.iter()] != [(el.tag,dict(el.attrib),el.text,el.tail) for el in parsed.iter()]:
        raise ValueError('Serialização introduziu diferença inesperada')
    return new,count


def repair(source,destination=None):
    source=Path(source)
    if destination is not None:
        destination=Path(destination)
        if source.resolve()==destination.resolve():
            raise ValueError('Sobrescrita do original proibida')
        if destination.exists():
            raise ValueError('Destino já existe; sobrescrita proibida')
    with zipfile.ZipFile(source) as zin:
        if zin.testzip() is not None:
            raise ValueError('ZIP com falha CRC')
        names=zin.namelist()
        if len(names)!=len(set(names)):
            raise ValueError('ZIP com nomes de partes duplicados')
        if PART not in names:
            raise ValueError(f'{PART} ausente')
        before=zin.read(PART)
        after, count=normalized_xml(before)
        if destination is not None and count:
            # Reusar atributos ZIP das entradas; somente uma parte pode mudar.
            with zipfile.ZipFile(destination,'w') as zout:
                for info in zin.infolist():
                    zout.writestr(info, after if info.filename==PART else zin.read(info.filename))
        written=bool(count and destination is not None)
        return {'original':str(source),'output':str(destination) if written else None,
                'table_properties_out_of_order':count,
                'table_properties_reordered':count if written else 0,
                'part_changed':PART if written else None,
                'part_hash_before':sha(before),'part_hash_after':sha(after),
                'original_unchanged':True,
                'scope':'Somente ordem w:tblPr; restante do gate formal permanece obrigatório'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx',type=Path)
    ap.add_argument('--output',type=Path,help='Caminho de novo DOCX; jamais modifica a origem')
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args()
    try:
        result=repair(args.docx,args.output)
    except (OSError,zipfile.BadZipFile,etree.XMLSyntaxError,ValueError) as exc:
        print('REPARO BLOQUEADO:',exc,file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('Tabelas com ordem irregular detectadas:',result['table_properties_out_of_order'])
        print('Tabelas efetivamente reordenadas em novo DOCX:',result['table_properties_reordered'])
        print('Saída:',result['output'] or 'nenhuma — sem alteração de arquivo')
    return 0

if __name__=='__main__':
    sys.exit(main())
