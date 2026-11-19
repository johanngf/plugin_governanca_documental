"""Regressão dirigida dos cenários BT-01 e BT-04 sobre anexos externos.

Uso: python tests/regression_bt01_bt04.py --bt01 BT01.docx --original A01.docx --corrigido BT05.docx
Não inclui nem modifica arquivos privados no pacote da Skill.
"""
import argparse
import collections
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/filename)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

audit=load('audit','audit_docx.py')
repair=load('repair','normalize_docx_tables.py')


def codes(result):
    return collections.Counter(i['code'] for i in result['issues'])


def run(bt01,original,corrigido):
    bm={'sec01':3,'sec02':3,'sec03':3,'sec04':3,'sec05':4,'sec06':4,'rev':4,'refs':4}
    a=audit.audit(bt01,profile='institutional-v3.4')
    b=audit.audit(original,profile='institutional-v3.4',page_map=bm)
    c=audit.audit(corrigido,profile='institutional-v3.4',page_map=bm)
    assert codes(a)['table_properties_order']==3, codes(a)
    assert codes(b)['duplicate_style_id']==1, codes(b)
    assert codes(b)['duplicate_outline_lvl']==3, codes(b)
    assert codes(b)['table_properties_order']==3, codes(b)
    assert codes(b)['shading_missing_val']==1, codes(b)
    assert codes(b)['pageref_cache_mismatch']==4, codes(b)
    assert codes(c)['duplicate_style_id']==0, codes(c)
    assert codes(c)['duplicate_outline_lvl']==0, codes(c)
    assert codes(c)['table_properties_order']==0, codes(c)
    assert codes(c)['shading_missing_val']==0, codes(c)
    assert codes(c)['pageref_cache_mismatch']==0, codes(c)
    with tempfile.TemporaryDirectory() as d:
        dest=Path(d)/'bt01_reparado.docx'
        original_hash=hashlib.sha256(bt01.read_bytes()).hexdigest()
        result=repair.repair(bt01,dest)
        assert result['table_properties_reordered']==3
        assert hashlib.sha256(bt01.read_bytes()).hexdigest()==original_hash
        with zipfile.ZipFile(bt01) as za,zipfile.ZipFile(dest) as zb:
            diff=[name for name in za.namelist() if za.read(name)!=zb.read(name)]
            assert diff==['word/document.xml'],diff
        after=audit.audit(dest,profile='institutional-v3.4')
        assert codes(after)['table_properties_order']==0,codes(after)
        assert not after['errors'],after['issues']
    print('BT-01: 3 defeitos reproduzidos; 3 reordenados em cópia; auditor sem erros direcionados')
    print('BT-04: identificação dirigida de estilo duplicado, 3 outlineLvl, 3 tabelas, sombreamento, 4 PAGEREF')
    print('BT-05: artefato corrigido sem as classes acima')
    print('PASS: regressões dirigidas BT-01 / BT-04 com artefatos reais')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bt01',type=Path,required=True)
    ap.add_argument('--original',type=Path,required=True)
    ap.add_argument('--corrigido',type=Path,required=True)
    arg=ap.parse_args()
    run(arg.bt01,arg.original,arg.corrigido)
