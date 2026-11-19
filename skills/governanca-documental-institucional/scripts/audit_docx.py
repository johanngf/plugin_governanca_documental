#!/usr/bin/env python3
"""Auditoria determinística e PARCIAL de DOCX/OOXML.

Não substitui gate semântico, inspeção visual, validação integral XSD,
interpretação de templates nem testes no ambiente consumidor (Word/Word Web).
Não modifica o arquivo de entrada.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

# CT_TblPrBase (ECMA-376/ISO 29500): ver fontes em docs/NOTAS_TECNICAS.md.
TBLPR_SEQUENCE = ('tblStyle', 'tblpPr', 'tblOverlap', 'bidiVisual',
    'tblStyleRowBandSize', 'tblStyleColBandSize', 'tblW', 'jc',
    'tblCellSpacing', 'tblInd', 'tblBorders', 'shd', 'tblLayout',
    'tblCellMar', 'tblLook', 'tblPrChange')
TBLPR_RANK = {name: index for index, name in enumerate(TBLPR_SEQUENCE)}
# Papel -> fonte e tamanho em pontos, seção 7 da Padronização 3.5.
ROLE_STYLES = {'Normal': ('Arial', 10), 'Heading1': ('Calibri', 15.5),
               'Heading2': ('Calibri', 12), 'Heading3': ('Calibri', 10.5)}


def local(tag):
    return tag.rsplit('}', 1)[-1]


def text_of(node):
    return ''.join(el.text or '' for el in node.iter(W+'t')).strip()


def read_word_parts(z):
    roots = {}
    for name in z.namelist():
        if name.endswith('.xml') and name.startswith('word/'):
            roots[name] = ET.fromstring(z.read(name))
    if 'word/document.xml' not in roots:
        raise ValueError('word/document.xml ausente')
    return roots


def get_style_map(root, report):
    by_id = collections.defaultdict(list)
    if root is None:
        report('error', 'styles_missing', 'word/styles.xml ausente', 'word/styles.xml')
        return {}
    for s in root.findall(W+'style'):
        sid = s.get(W+'styleId')
        if sid:
            by_id[sid].append(s)
    for sid, arr in sorted(by_id.items()):
        if len(arr) > 1:
            report('error', 'duplicate_style_id',
                   f'Identificador de estilo {sid!r} definido {len(arr)} vezes', 'word/styles.xml')
    return {sid: arr[0] for sid, arr in by_id.items()}


def style_outline(styles, sid, seen=None):
    seen = seen or set()
    if sid in seen or sid not in styles:
        return None
    s = styles[sid]
    ppr = s.find(W+'pPr')
    if ppr is not None:
        el = ppr.find(W+'outlineLvl')
        if el is not None and el.get(W+'val') is not None:
            return int(el.get(W+'val'))
    b = s.find(W+'basedOn')
    if b is not None and b.get(W+'val'):
        return style_outline(styles, b.get(W+'val'), seen | {sid})
    return None


def font_theme(roots):
    root = roots.get('word/theme/theme1.xml')
    if root is None:
        return {}
    result = {}
    for tag, key in [('majorFont', 'major'), ('minorFont', 'minor')]:
        node = next(root.iter(A+tag), None)
        latin = node.find(A+'latin') if node is not None else None
        if latin is not None:
            result[key] = latin.get('typeface')
    return result


def effective_prop(styles, sid, prop):
    seen = set()
    while sid and sid not in seen and sid in styles:
        seen.add(sid)
        s = styles[sid]
        rpr = s.find(W+'rPr')
        if rpr is not None and rpr.find(W+prop) is not None:
            return rpr.find(W+prop)
        base = s.find(W+'basedOn')
        sid = base.get(W+'val') if base is not None else None
    return None


def check_typography(styles, roots, report):
    theme = font_theme(roots)
    for sid, (font, pt) in ROLE_STYLES.items():
        if sid not in styles:
            report('warning', 'role_style_absent', f'Estilo {sid} ausente; verificar template', 'word/styles.xml')
            continue
        rfonts = effective_prop(styles, sid, 'rFonts')
        sz = effective_prop(styles, sid, 'sz')
        if sz is None or sz.get(W+'val') is None:
            report('warning', 'font_size_unresolved', f'{sid}: tamanho não resolvido', 'word/styles.xml')
        else:
            actual = float(sz.get(W+'val')) / 2
            if abs(actual-pt) > .01:
                report('error', 'role_font_size', f'{sid}: {actual:g} pt; esperado {pt:g} pt', 'word/styles.xml')
        if rfonts is None:
            report('warning', 'font_unresolved', f'{sid}: fonte não resolvida', 'word/styles.xml')
            continue
        ascii_name = rfonts.get(W+'ascii') or rfonts.get(W+'hAnsi')
        themed = rfonts.get(W+'asciiTheme') or rfonts.get(W+'hAnsiTheme')
        theme_key = 'major' if themed and themed.startswith('major') else 'minor' if themed and themed.startswith('minor') else None
        theme_name = theme.get(theme_key) if theme_key else None
        if theme_name and theme_name.casefold() != font.casefold():
            report('error', 'role_font_theme', f'{sid}: tema resolve {theme_name!r}; esperado {font!r}', 'word/theme/theme1.xml')
        if ascii_name and ascii_name.casefold() != font.casefold():
            # Quando existem duas fontes conflitantes, não inventar qual será exibida.
            severity = 'warning' if theme_name and theme_name.casefold() == font.casefold() else 'error'
            report(severity, 'role_font_name', f'{sid}: fonte direta {ascii_name!r}; esperado {font!r}', 'word/styles.xml')
        if not ascii_name and not theme_name:
            report('warning', 'font_unresolved', f'{sid}: fonte não resolvida (tema não encontrado)', 'word/styles.xml')


def inspect_fields(root, report, bookmarks, page_map):
    # Cada campo complexo é um bloco begin...separator...end; caches são texto visível
    # entre separator e end. Campos simples são inspecionados separadamente.
    fields=[]
    # Campos complexos podem atravessar vários parágrafos (ex.: TOC com PAGEREF
    # aninhados). A pilha, portanto, cobre a parte inteira, não cada parágrafo.
    stack=[]
    for el in root.iter():
        if el.tag == W+'fldChar':
            typ = el.get(W+'fldCharType')
            if typ == 'begin':
                stack.append({'instr':'', 'cache':'', 'sep':False})
            elif typ == 'separate':
                if not stack:
                    report('error', 'field_unbalanced', 'Separador de campo sem início', 'word/document.xml')
                else:
                    stack[-1]['sep'] = True
            elif typ == 'end':
                if not stack:
                    report('error', 'field_unbalanced', 'Fim de campo sem início', 'word/document.xml')
                else:
                    fields.append(stack.pop())
        elif el.tag == W+'instrText' and stack and el.text:
            stack[-1]['instr'] += el.text
        elif el.tag == W+'t' and stack and stack[-1]['sep'] and el.text:
            stack[-1]['cache'] += el.text
    if stack:
        report('error', 'field_unbalanced', f'{len(stack)} campo(s) sem encerramento em word/document.xml', 'word/document.xml')
    for el in root.iter(W+'fldSimple'):
        fields.append({'instr':el.get(W+'instr') or '', 'cache': text_of(el), 'sep': True})
    n_pageref=0
    n_toc=0
    checked=0
    for f in fields:
        instr=f['instr'].strip()
        if re.search(r'\bTOC\b', instr, re.I):
            n_toc+=1
        m=re.search(r'\bPAGEREF\s+([^\s\\]+)', instr, re.I)
        if not m:
            continue
        n_pageref+=1
        bookmark=m.group(1).strip('"')
        if bookmark not in bookmarks:
            report('error', 'pageref_missing_bookmark', f'PAGEREF aponta para {bookmark!r} inexistente', 'word/document.xml')
            continue
        cache=f['cache'].strip()
        if bookmark in page_map:
            expected=str(page_map[bookmark])
            checked+=1
            if cache != expected:
                report('error', 'pageref_cache_mismatch',
                       f'PAGEREF {bookmark!r}: cache={cache!r}, página conferida={expected!r}', 'word/document.xml')
        elif not cache:
            report('warning', 'pageref_cache_empty', f'PAGEREF {bookmark!r} sem resultado armazenado', 'word/document.xml')
    if n_pageref and not page_map:
        report('warning', 'pageref_cache_not_verified',
               f'{n_pageref} PAGEREF(s) encontrados; caches não comparados com páginas renderizadas (forneça --bookmark-pages)', 'word/document.xml')
    elif n_pageref and checked < n_pageref:
        report('warning', 'pageref_cache_partially_verified',
               f'{checked}/{n_pageref} PAGEREF(s) comparados com mapa externo de páginas', 'word/document.xml')
    if n_pageref and not n_toc:
        report('warning', 'toc_not_detected',
               'Sumário possivelmente manual: ausência de campo TOC não comprova desconformidade; validar atualização e navegação', 'word/document.xml')
    if n_toc:
        report('warning', 'toc_update_not_tested',
               'Campo TOC presente; atualização real e navegação no editor não verificadas pelo auditor', 'word/document.xml')
    return {'pageref': n_pageref, 'toc': n_toc, 'cache_checked': checked}


def check_cover_roles(root, report):
    """Verificação limitada à tabela de metadados da capa padronizada.

    Não tenta inferir identidade humana, autenticar autoria ou reconhecer
    templates alternativos. Para outros modelos, revisar o gate manualmente.
    """
    body = root.find(W + 'body')
    tables = body.findall(W + 'tbl') if body is not None else []
    # A primeira tabela de metadados costuma conter Finalidade/Escopo/Versão.
    # Excluímos tabelas do corpo para reduzir falsos positivos.
    chosen = None
    for table in tables[:3]:
        labels = []
        for tr in table.findall(W + 'tr'):
            cells = tr.findall(W + 'tc')
            if cells:
                labels.append(' '.join(text_of(cells[0]).casefold().split()))
        if any(x in labels for x in ('finalidade', 'escopo', 'versão', 'situação')):
            chosen = table
            break
    found = {}
    if chosen is not None:
        for index, tr in enumerate(chosen.findall(W + 'tr')):
            cells = tr.findall(W + 'tc')
            if len(cells) < 2:
                continue
            label = ' '.join(text_of(cells[0]).casefold().split())
            for key, expected in [('responsavel', 'responsável pelo documento'),
                                  ('autoria', 'autoria')]:
                if label == expected:
                    found.setdefault(key, []).append((index, bool(''.join(text_of(c) for c in cells[1:]).strip())))
    present = {key: len(found.get(key, [])) == 1 for key in ('responsavel','autoria')}
    separate = (all(present.values()) and
                found['responsavel'][0][0] != found['autoria'][0][0])
    values_present = all(present.values()) and all(found[k][0][1] for k in ('responsavel','autoria'))
    if chosen is None:
        report('error','cover_metadata_table_not_found',
               'Não foi identificada a tabela de metadados da capa padronizada; revisar manualmente o template aplicável',
               'word/document.xml')
    for key, title in [('responsavel','Responsável pelo documento'),('autoria','Autoria')]:
        if not present[key]:
            report('error','cover_role_missing',
                   f'Capa padronizada: campo separado {title!r} ausente ou duplicado',
                   'word/document.xml')
        elif not found[key][0][1]:
            report('error','cover_role_value_blank',
                   f'Capa padronizada: campo {title!r} sem valor; explicitar não informado quando for o caso',
                   'word/document.xml')
    if all(present.values()) and not separate:
        report('error','cover_roles_not_separate',
               'Responsável pelo documento e Autoria precisam ser campos separados na capa',
               'word/document.xml')
    return {'checked':True, 'method':'cover_metadata_table_first_three',
            'metadata_table_found':chosen is not None,
            'responsavel_present':present['responsavel'],
            'autoria_present':present['autoria'],
            'separate_fields':separate,
            'values_present':bool(values_present),
            'limits':'Confere presença e separação de rótulos na tabela padronizada; não verifica atribuição intelectual real, aprovação ou templates excepcionais.'}


def audit(path, profile='none', page_map=None, check_cover_identification=False):
    issues=[]
    def report(severity, code, message, part=None):
        issues.append({'severity':severity, 'code':code, 'message':message, 'part':part})
    page_map=page_map or {}
    headings=[]
    starts=[]
    ends=[]
    bookmark_names=collections.defaultdict(list)
    anchors=[]
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:
            report('error', 'zip_crc', f'Falha CRC no componente {bad!r}', bad)
        roots=read_word_parts(z)
    styles=get_style_map(roots.get('word/styles.xml'), report)
    root=roots['word/document.xml']
    for part, part_root in roots.items():
        # Atributo obrigatório de CT_Shd, independente da aparência no renderizador.
        shade_count=0
        for el in part_root.iter(W+'shd'):
            if el.get(W+'val') is None:
                shade_count+=1
        if shade_count:
            report('error', 'shading_missing_val', f'{shade_count} w:shd sem w:val obrigatório', part)
        # Duplicações de outlineLvl no mesmo bloco de propriedades de parágrafo.
        for el in part_root.iter(W+'pPr'):
            n=len(el.findall(W+'outlineLvl'))
            if n>1:
                report('error', 'duplicate_outline_lvl', f'{n} w:outlineLvl dentro de um mesmo w:pPr', part)
        # Ordem relativa segundo CT_TblPrBase; atributos e extensões não são abrangidos.
        for i, tblpr in enumerate(part_root.iter(W+'tblPr'), start=1):
            names=[local(x.tag) for x in tblpr if x.tag.startswith(W)]
            recognized=[n for n in names if n in TBLPR_RANK]
            rank=[TBLPR_RANK[n] for n in recognized]
            if rank != sorted(rank):
                report('error', 'table_properties_order',
                       f'tblPr #{i} com ordem inválida: {", ".join(recognized)}', part)
            duplicates=[k for k,n in collections.Counter(recognized).items() if n>1]
            if duplicates:
                report('error', 'table_properties_duplicate', f'tblPr #{i} duplicado(s): {", ".join(duplicates)}', part)
    for p in root.iter(W+'p'):
        children=list(p)
        pos=[i for i, ch in enumerate(children) if ch.tag==W+'pPr']
        if pos and pos != [0]:
            report('error', 'paragraph_properties_order', 'w:pPr não é o primeiro filho de w:p: '+text_of(p)[:65], 'word/document.xml')
        if len(pos)>1:
            report('error', 'duplicate_paragraph_properties', 'Mais de um w:pPr no mesmo parágrafo', 'word/document.xml')
        pp=p.find(W+'pPr')
        ps=pp.find(W+'pStyle') if pp is not None else None
        sid=ps.get(W+'val') if ps is not None else None
        ol=pp.find(W+'outlineLvl') if pp is not None else None
        try:
            lev=int(ol.get(W+'val')) if ol is not None and ol.get(W+'val') is not None else style_outline(styles, sid)
        except ValueError:
            lev=None
            report('error','outline_level_invalid',f'Nível estrutural inválido no estilo {sid}', 'word/document.xml')
        content=text_of(p)
        if lev is not None and lev<=8 and content:
            headings.append({'text':content[:160], 'style':sid, 'outlineLvl':lev})
        elif sid and re.fullmatch(r'Heading[1-9]', sid, re.I) and content:
            report('warning','heading_level_unresolved', f'Título sem nível estrutural resolvido: {content[:100]}','word/document.xml')
    if not headings:
        report('warning', 'heading_none', 'Nenhum título estrutural reconhecido; verificar se aplicável', 'word/document.xml')
    for b in root.iter(W+'bookmarkStart'):
        bid=b.get(W+'id'); name=b.get(W+'name')
        if bid is not None:starts.append(bid)
        if name:bookmark_names[name].append(bid)
    for b in root.iter(W+'bookmarkEnd'):
        bid=b.get(W+'id')
        if bid is not None:ends.append(bid)
    for h in root.iter(W+'hyperlink'):
        anchor=h.get(W+'anchor')
        if anchor:anchors.append(anchor)
    for name, ids in sorted(bookmark_names.items()):
        if len(ids)>1: report('error','bookmark_duplicate',f'Bookmark {name!r} duplicado','word/document.xml')
    for missing in sorted(set(starts)-set(ends)):
        report('error','bookmark_end_missing',f'Bookmark {missing!r} sem término','word/document.xml')
    for missing in sorted(set(ends)-set(starts)):
        report('error','bookmark_start_missing',f'Bookmark {missing!r} sem início','word/document.xml')
    for anchor in sorted(set(anchors)):
        if anchor not in bookmark_names:
            report('error','hyperlink_anchor_missing',f'Hyperlink interno sem bookmark: {anchor!r}', 'word/document.xml')
    fields=inspect_fields(root,report,bookmark_names,page_map)
    cover_roles=check_cover_roles(root,report) if check_cover_identification else None
    if profile in ('institutional-v3.4','institutional-v3.5'):
        check_typography(styles,roots,report)
        for i, sect in enumerate(root.iter(W+'sectPr'),start=1):
            pg=sect.find(W+'pgSz')
            if pg is None:
                report('warning','page_size_unknown', f'Seção {i}: pgSz ausente', 'word/document.xml')
            else:
                w=int(pg.get(W+'w') or 0); h=int(pg.get(W+'h') or 0)
                if (w,h) != (12240, 15840):
                    report('error','page_size_not_letter',f'Seção {i}: {w} × {h} twips; esperado Carta/Letter (12240 × 15840)', 'word/document.xml')
    errors=[i for i in issues if i['severity']=='error']
    warnings=[i for i in issues if i['severity']=='warning']
    return {'file':str(path), 'profile':profile, 'ok':not errors, 'errors':[i['message'] for i in errors],
            'warnings':[i['message'] for i in warnings], 'issues':issues,
            'heading_count':len(headings), 'headings':headings,
            'bookmark_count':len(starts), 'internal_hyperlink_count':len(anchors),
            'toc_field_detected':bool(fields['toc']), 'pageref_field_count':fields['pageref'],
            'pageref_cache_checked':fields['cache_checked'], 'cover_roles':cover_roles,
            'scope':'Auditoria OOXML e tipografia por papel PARCIAL; não constitui aprovação de gate formal ou de liberação institucional.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx',type=Path)
    ap.add_argument('--json',action='store_true')
    ap.add_argument('--profile',choices=['none','institutional-v3.4','institutional-v3.5'],default='none',
                    help='Perfil institucional é opt-in porque templates específicos podem prevalecer')
    ap.add_argument('--check-cover-identification',action='store_true',
                    help='Verifica campos separados de Responsável pelo documento e Autoria na capa padronizada; para templates excepcionais, executar gate manual e registrar a justificativa')
    ap.add_argument('--bookmark-pages',type=Path,help='JSON {"nomeBookmark": númeroPágina} produzido por conferência independente da paginação')
    ap.add_argument('--report',type=Path,help='Grava relatório JSON ligado ao hash SHA-256 do DOCX efetivamente auditado; não sobrescreve relatório existente')
    args=ap.parse_args()
    try:
        pages=json.loads(args.bookmark_pages.read_text(encoding='utf8')) if args.bookmark_pages else None
        if pages is not None and (not isinstance(pages,dict) or any(not isinstance(v,int) or v<1 for v in pages.values())):
            raise ValueError('Mapa de bookmarks deve ser um JSON com números inteiros positivos')
        result=audit(args.docx,profile=args.profile,page_map=pages,check_cover_identification=args.check_cover_identification)
        result['artifact_sha256']=hashlib.sha256(args.docx.read_bytes()).hexdigest()
        result['auditor_version']='1.1.0'
        result['gate_limits']=['sem verificação completa por esquema OOXML/XSD', 'sem inspeção visual',
                              'sem aprovação semântica', 'sem teste no Word para Web']
        if args.report:
            if args.report.exists():
                raise ValueError('Relatório de destino já existe; substituição não permitida')
            args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    except (ValueError,OSError,KeyError,ET.ParseError,zipfile.BadZipFile,TypeError) as exc:
        print('ERRO de inspeção:',exc,file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('OK (parcial)' if result['ok'] else 'REPROVADO (parcial)', '—',args.docx)
        print('Títulos:',result['heading_count'],'bookmarks:',result['bookmark_count'],'PAGEREF:',result['pageref_field_count'])
        for i in result['issues']:
            print(i['severity'].upper(),i['code'],i['message'])
    return 0 if result['ok'] else 1

if __name__=='__main__':
    sys.exit(main())
