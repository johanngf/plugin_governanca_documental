"""Testes negativos do gate: declarações falsas não aprovam um DOCX defeituoso."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

from test_cover_gate_evidence import make_docx

SKILL=Path(__file__).resolve().parents[1]
AUD=SKILL/'scripts/audit_docx.py'
VERIFY=SKILL/'scripts/verify_gate_evidence.py'
RUN=SKILL/'scripts/run_gate.py'

class TestHardenedGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)
        self.doc=self.folder/'artifact.docx'
        self.report=self.folder/'audit.json'
        self.good=[('Finalidade','Nota'),('Versão','0.1'),
                   ('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')]

    def make_report(self,meta=None):
        make_docx(self.doc, self.good if meta is None else meta)
        proc=subprocess.run([sys.executable,str(AUD),str(self.doc),'--check-cover-identification',
                             '--report',str(self.report),'--json'],capture_output=True,text=True)
        self.assertIn(proc.returncode,(0,1),proc.stderr)
        return json.loads(self.report.read_text(encoding='utf8'))

    def check(self, extra=()):
        return subprocess.run([sys.executable,str(VERIFY),str(self.doc),str(self.report),
                               '--require-cover-roles',*extra],capture_output=True,text=True)

    def write(self,obj):
        self.report.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf8')

    def test_legitimate_report_is_rechecked(self):
        self.make_report()
        p=self.check()
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        val=json.loads(p.stdout)
        self.assertTrue(val['recheck_performed'])
        self.assertTrue(val['recheck_ok'])

    def test_forged_cover_roles_rejected_despite_correct_sha(self):
        data=self.make_report([('Finalidade','Nota'),('Versão','0.1')])
        data['ok']=True
        data['issues']=[]
        data['cover_roles']={**data['cover_roles'], 'metadata_table_found':True,
                             'responsavel_present':True,'autoria_present':True,
                             'separate_fields':True,'values_present':True}
        self.write(data)
        p=self.check()
        self.assertEqual(p.returncode,1,p.stdout)
        self.assertIn('Reauditoria do DOCX falhou',p.stdout)

    def test_forged_table_order_rejected(self):
        data=self.make_report()
        with zipfile.ZipFile(self.doc) as z:
            parts={n:z.read(n) for n in z.namelist()}
        x=parts['word/document.xml'].decode()
        x=x.replace('<w:tblPr/>','<w:tblPr><w:tblBorders/><w:tblW w:w="100"/></w:tblPr>')
        parts['word/document.xml']=x.encode()
        with zipfile.ZipFile(self.doc,'w') as z:
            for name,bytes_ in parts.items(): z.writestr(name,bytes_)
        data['artifact_sha256']=hashlib.sha256(self.doc.read_bytes()).hexdigest()
        data['ok']=True
        data['issues']=[]
        self.write(data)
        p=self.check()
        self.assertEqual(p.returncode,1,p.stdout)
        self.assertIn('table_properties_order',p.stdout)

    def test_profile_cannot_be_downgraded(self):
        self.make_report()
        p=self.check(('--expected-profile','institutional-v3.5'))
        self.assertEqual(p.returncode,1,p.stdout)
        self.assertIn('Perfil declarado difere',p.stdout)

    def test_partial_profile_is_not_promoted_to_full(self):
        data=self.make_report()
        data['profile']='institutional-v3.5-selected-rules (partial)'
        self.write(data)
        p=self.check(('--expected-profile','institutional-v3.5'))
        self.assertEqual(p.returncode,1,p.stdout)
        self.assertIn('Perfil não verificável',p.stdout)

    def test_modified_docx_does_not_match_report(self):
        self.make_report()
        with self.doc.open('ab') as f: f.write(b'changed')
        p=self.check()
        self.assertEqual(p.returncode,1,p.stdout)
        self.assertIn('SHA-256',p.stdout)

    def test_runner_good_doc_has_ordered_events_and_no_institutional_release(self):
        make_docx(self.doc,self.good)
        dest=self.folder/'good_gate'
        p=subprocess.run([sys.executable,str(RUN),str(self.doc),'--output-dir',str(dest),
                          '--profile','none'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        record=json.loads((dest/'execution.json').read_text())
        self.assertEqual(record['structural_gate'],'passed_partial_scope')
        self.assertEqual(record['institutional_release'],'not_authorized')
        self.assertEqual(record['artifact_sha256_before'],record['artifact_sha256_after'])
        self.assertTrue((dest/'audit.json').exists())
        self.assertTrue((dest/'verification.json').exists())
        self.assertEqual([x['order'] for x in record['events']],list(range(1,len(record['events'])+1)))
        # Sem sobrescrever evidências.
        again=subprocess.run([sys.executable,str(RUN),str(self.doc),'--output-dir',str(dest),
                              '--profile','none'],capture_output=True,text=True)
        self.assertNotEqual(again.returncode,0)

    def test_runner_blocks_invalid_cover(self):
        make_docx(self.doc,[('Finalidade','Nota'),('Versão','0.1')])
        dest=self.folder/'bad_gate'
        p=subprocess.run([sys.executable,str(RUN),str(self.doc),'--output-dir',str(dest),
                          '--profile','none'],capture_output=True,text=True)
        self.assertEqual(p.returncode,1,p.stdout+p.stderr)
        rec=json.loads((dest/'execution.json').read_text())
        self.assertEqual(rec['structural_gate'],'blocked')
        self.assertNotEqual(rec['institutional_release'],'authorized')

    def test_runner_diagnose_does_not_approve(self):
        make_docx(self.doc,self.good)
        p=subprocess.run([sys.executable,str(RUN),str(self.doc),'--diagnose'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        diag=json.loads(p.stdout)
        self.assertTrue(diag['auditor_accessible'])
        self.assertTrue(diag['docx_readable'])
        self.assertNotIn('approved',diag)

    def test_runner_without_cover_remains_pending(self):
        make_docx(self.doc,self.good)
        dest=self.folder/'exception_gate'
        p=subprocess.run([sys.executable,str(RUN),str(self.doc),'--output-dir',str(dest),
                          '--profile','none','--no-standard-cover','--cover-exception-reason','Template distinto, exame manual pendente'],capture_output=True,text=True)
        self.assertEqual(p.returncode,1,p.stdout+p.stderr)
        record=json.loads((dest/'execution.json').read_text())
        self.assertEqual(record['institutional_release'],'not_authorized')
        self.assertEqual(record['structural_gate'],'pending_cover_exception_review')


    def test_runner_missing_input_is_not_verifiable(self):
        dest=self.folder/'missing_doc_gate'
        p=subprocess.run([sys.executable,str(RUN),str(self.folder/'absent.docx'),
                          '--output-dir',str(dest),'--profile','none'],capture_output=True,text=True)
        self.assertEqual(p.returncode,1,p.stdout+p.stderr)
        record=json.loads((dest/'execution.json').read_text())
        self.assertEqual(record['structural_gate'],'not_verifiable')
        self.assertEqual(record['institutional_release'],'not_authorized')

    def test_cover_exception_requires_reason(self):
        make_docx(self.doc,self.good)
        dest=self.folder/'no_reason'
        p=subprocess.run([sys.executable,str(RUN),str(self.doc),
                          '--output-dir',str(dest),'--profile','none',
                          '--no-standard-cover'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('--cover-exception-reason',p.stderr)
        self.assertFalse(dest.exists())

if __name__=='__main__':unittest.main()
