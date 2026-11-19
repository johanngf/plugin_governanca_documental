"""Regressões BT-01: capa padronizada e evidência vinculada ao DOCX final."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

SKILL=Path(__file__).resolve().parents[1]
AUD=SKILL/'scripts/audit_docx.py'
VERIFY=SKILL/'scripts/verify_gate_evidence.py'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'

def make_docx(path, metadata):
    rows=[]
    for label,value in metadata:
        rows.append(f'<w:tr><w:tc><w:p><w:r><w:t>{label}</w:t></w:r></w:p></w:tc>'
                    f'<w:tc><w:p><w:r><w:t>{value}</w:t></w:r></w:p></w:tc></w:tr>')
    xml=(f'<w:document xmlns:w="{W}"><w:body><w:tbl><w:tblPr/>'
         f'<w:tblGrid/>{"".join(rows)}</w:tbl>'
         f'<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Corpo</w:t></w:r></w:p>'
         f'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr></w:body></w:document>')
    styles=(f'<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Heading1">'
            f'<w:pPr><w:outlineLvl w:val="0"/></w:pPr></w:style></w:styles>')
    with zipfile.ZipFile(path,'w') as z:
        z.writestr('word/document.xml',xml)
        z.writestr('word/styles.xml',styles)

class TestCoverGateEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.doc=self.folder/'doc.docx'
        self.report=self.folder/'audit.json'

    def audit(self,meta):
        make_docx(self.doc,meta)
        proc=subprocess.run([sys.executable,str(AUD),str(self.doc),'--check-cover-identification',
                             '--report',str(self.report),'--json'],capture_output=True,text=True)
        data=json.loads(self.report.read_text())
        return proc,data

    def test_missing_both_labels_is_blocking(self):
        proc,data=self.audit([('Finalidade','Nota'),('Versão','0.1'),('Situação','Preliminar')])
        self.assertEqual(proc.returncode,1)
        self.assertFalse(data['ok'])
        self.assertEqual(sum(x['code']=='cover_role_missing' for x in data['issues']),2)

    def test_individual_labels_explicitly_unassigned_are_accepted(self):
        proc,data=self.audit([('Finalidade','Nota'),('Versão','0.1'),
                              ('Responsável pelo documento','Não informado'),
                              ('Autoria','Não atribuída')])
        self.assertEqual(proc.returncode,0)
        self.assertTrue(data['cover_roles']['separate_fields'])
        self.assertTrue(data['cover_roles']['values_present'])
        self.assertEqual(data['auditor_version'],'1.1.0')
        checked=subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),'--require-cover-roles'],
                               capture_output=True,text=True)
        self.assertEqual(checked.returncode,0)
        self.assertTrue(json.loads(checked.stdout)['ok'])

    def test_blank_value_is_blocking(self):
        proc,data=self.audit([('Finalidade','Nota'),('Versão','0.1'),
                              ('Responsável pelo documento',''),('Autoria','Não atribuída')])
        self.assertEqual(proc.returncode,1)
        self.assertIn('cover_role_value_blank',[x['code'] for x in data['issues']])

    def test_only_one_role_is_blocking(self):
        proc,data=self.audit([('Finalidade','Nota'),('Versão','0.1'),
                              ('Responsável pelo documento','Não informado')])
        self.assertEqual(proc.returncode,1)
        self.assertFalse(data['cover_roles']['autoria_present'])

    def test_audit_is_opt_in_for_cover_check(self):
        make_docx(self.doc,[('Finalidade','Nota'),('Versão','0.1')])
        proc=subprocess.run([sys.executable,str(AUD),str(self.doc),'--json'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)
        self.assertIsNone(json.loads(proc.stdout)['cover_roles'])

    def test_modified_docx_invalidates_evidence(self):
        self.audit([('Finalidade','Nota'),('Versão','0.1'),('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')])
        with self.doc.open('ab') as f:f.write(b'changed')
        proc=subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),'--require-cover-roles'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,1)
        self.assertIn('SHA-256',proc.stdout)

    def test_independent_report_missing_limits_is_rejected(self):
        self.audit([('Finalidade','Nota'),('Versão','0.1'),('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')])
        data=json.loads(self.report.read_text()); data.pop('gate_limits')
        self.report.write_text(json.dumps(data))
        proc=subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),'--require-cover-roles'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,1)
        self.assertIn('limitações',proc.stdout)

    def test_external_report_with_equivalent_schema(self):
        self.audit([('Finalidade','Nota'),('Versão','0.1'),('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')])
        data=json.loads(self.report.read_text());data.pop('auditor_version')
        data['auditor']='auditor independente de teste';data['limitations']=data.pop('gate_limits')
        self.report.write_text(json.dumps(data))
        proc=subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),'--require-cover-roles'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0)

    def test_missing_cover_evidence_rejected(self):
        self.audit([('Finalidade','Nota'),('Versão','0.1'),('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')])
        data=json.loads(self.report.read_text());data.pop('cover_roles')
        self.report.write_text(json.dumps(data))
        proc=subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),'--require-cover-roles'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,1)
        self.assertIn('cover_roles',proc.stdout)

if __name__=='__main__':unittest.main()
