"""Regressão BT-01/BT-04: reparo conservador + trilha de auditoria."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts'/'normalize_docx_tables.py'
AUDIT=ROOT/'scripts'/'audit_docx.py'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

spec=importlib.util.spec_from_file_location('normalize_docx_tables',SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def doc(table_xml,shade=''):
    return (f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>Texto original</w:t></w:r></w:p>'
            f'<w:tbl><w:tblPr>{table_xml}</w:tblPr><w:tblGrid/><w:tr><w:tc><w:p><w:r><w:t>Conteúdo da tabela</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
            f'<w:p>{shade}</w:p><w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr>'
            f'</w:body></w:document>')


def styles():
    return (f'<w:styles xmlns:w="{W}">' 
            '<w:style w:styleId="Normal" w:type="paragraph" />'
            '</w:styles>')


class TestGateAndRepair(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.original=Path(self.tmp.name)/'original.docx'
        self.output=Path(self.tmp.name)/'repaired.docx'
        self.bad_table='<w:tblW w:w="4000" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0"/><w:tblBorders/>'
        self.good_table='<w:tblW w:w="4000" w:type="dxa"/><w:tblBorders/><w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0"/>'

    def make(self,table=None):
        with zipfile.ZipFile(self.original,'w') as z:
            z.writestr('word/document.xml',doc(table if table is not None else self.bad_table))
            z.writestr('word/styles.xml',styles())
            z.writestr('custom/keep.xml','<other>untouched</other>')

    def test_bt01_order_correction_and_preservation(self):
        self.make()
        orig_hash=hashlib.sha256(self.original.read_bytes()).hexdigest()
        result=mod.repair(self.original,self.output)
        self.assertEqual(result['table_properties_reordered'],1)
        self.assertEqual(orig_hash,hashlib.sha256(self.original.read_bytes()).hexdigest())
        with zipfile.ZipFile(self.original) as a, zipfile.ZipFile(self.output) as b:
            differing=[name for name in a.namelist() if a.read(name)!=b.read(name)]
            self.assertEqual(differing,['word/document.xml'])
            self.assertIn(b'<w:tblBorders/>',b.read('word/document.xml'))
            self.assertIn(b'Texto original',b.read('word/document.xml'))
            self.assertIn(b'Conte\xc3\xbado da tabela',b.read('word/document.xml'))
        check=subprocess.run([sys.executable,str(AUDIT),str(self.output),'--json'],capture_output=True,text=True,check=True)
        j=json.loads(check.stdout)
        self.assertFalse(any(i['code']=='table_properties_order' for i in j['issues']))

    def test_profile_alias_v35_matches_v34(self):
        self.make(self.good_table)
        from importlib.util import spec_from_file_location, module_from_spec
        spec=spec_from_file_location('audit_profile', AUDIT)
        am=module_from_spec(spec); spec.loader.exec_module(am)
        old=am.audit(self.original,profile='institutional-v3.4')
        new=am.audit(self.original,profile='institutional-v3.5')
        self.assertEqual(old['issues'],new['issues'])
        self.assertEqual(old['ok'],new['ok'])

    def test_inspection_without_output_does_not_claim_repair(self):
        self.make()
        original_hash=hashlib.sha256(self.original.read_bytes()).hexdigest()
        r=mod.repair(self.original)
        self.assertEqual(r['table_properties_out_of_order'],1)
        self.assertEqual(r['table_properties_reordered'],0)
        self.assertIsNone(r['part_changed'])
        self.assertIsNone(r['output'])
        self.assertEqual(hashlib.sha256(self.original.read_bytes()).hexdigest(),original_hash)

    def test_nochange_input_has_no_new_output(self):
        self.make(self.good_table)
        r=mod.repair(self.original,self.output)
        self.assertEqual(r['table_properties_reordered'],0)
        self.assertFalse(self.output.exists())

    def test_duplicate_rejected_without_output(self):
        self.make(self.bad_table+'<w:tblBorders/>')
        with self.assertRaisesRegex(ValueError,'duplicada'):
            mod.repair(self.original,self.output)
        self.assertFalse(self.output.exists())

    def test_unknown_rejected_without_output(self):
        self.make(self.bad_table+'<w:notARealProperty/>')
        with self.assertRaisesRegex(ValueError,'desconhecida'):
            mod.repair(self.original,self.output)
        self.assertFalse(self.output.exists())

    def test_cannot_modify_original_or_overwrite_existing_output(self):
        self.make()
        with self.assertRaisesRegex(ValueError,'original'):
            mod.repair(self.original,self.original)
        self.output.write_bytes(b'existing')
        with self.assertRaisesRegex(ValueError,'Destino'):
            mod.repair(self.original,self.output)
        self.assertEqual(self.output.read_bytes(),b'existing')

    def test_gate_evidence_hash_and_error_status(self):
        self.make()
        report=Path(self.tmp.name)/'gate.json'
        proc=subprocess.run([sys.executable,str(AUDIT),str(self.original),'--report',str(report),'--json'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,1)
        j=json.loads(report.read_text())
        self.assertEqual(j['artifact_sha256'],hashlib.sha256(self.original.read_bytes()).hexdigest())
        self.assertIn('table_properties_order',[i['code'] for i in j['issues']])
        self.assertFalse(j['ok'])
        self.assertEqual(j['auditor_version'],'1.1.0')
        self.assertEqual(j,json.loads(proc.stdout))
        second=subprocess.run([sys.executable,str(AUDIT),str(self.original),'--report',str(report)],capture_output=True,text=True)
        self.assertEqual(second.returncode,2)
        self.assertIn('já existe',second.stderr)


if __name__=='__main__': unittest.main()
