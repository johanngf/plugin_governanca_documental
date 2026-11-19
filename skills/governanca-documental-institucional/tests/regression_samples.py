"""Regressão dos artefatos externos, sem incorporá-los à distribuição.

Uso: python tests/regression_samples.py ORIGINAL CORRIGIDO PT01 MAPA_PAGINAS.json
"""
from pathlib import Path
import importlib.util
import sys
import collections

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('audit_docx',ROOT/'scripts'/'audit_docx.py')
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

def main(paths):
    if len(paths)!=4:
        raise SystemExit('Uso: regression_samples.py original.docx corrigido.docx pt01.docx mapa.json')
    import json
    mp=json.loads(Path(paths[3]).read_text(encoding='utf8'))
    before,after,pt01=[mod.audit(Path(p),'institutional-v3.4',mp if idx<2 else None) for idx,p in enumerate(paths[:3])]
    a=[i['code'] for i in before['issues']]
    b=[i['code'] for i in after['issues']]
    c=[i['code'] for i in pt01['issues']]
    assert 'duplicate_style_id' in a and 'duplicate_style_id' not in b
    assert 'duplicate_outline_lvl' in a and 'duplicate_outline_lvl' not in b
    assert a.count('pageref_cache_mismatch')==4 and b.count('pageref_cache_mismatch')==0
    assert b.count('table_properties_order')==3 and 'shading_missing_val' in b
    assert 'role_font_name' not in a and 'role_font_name' not in b
    assert 'page_size_not_letter' in c and 'role_font_size' in c
    assert 'field_unbalanced' not in b
    print('PASS: regressão dos três documentos recebidos')
    for title,obj in [('PT-05 original',before),('PT-06 corrigido',after),('PT-01 nota',pt01)]:
        print(title, 'erros=',len(obj['errors']),'avisos=',len(obj['warnings']),dict(collections.Counter(i['code'] for i in obj['issues'])))
    return 0

if __name__=='__main__':
    sys.exit(main(sys.argv[1:]))
