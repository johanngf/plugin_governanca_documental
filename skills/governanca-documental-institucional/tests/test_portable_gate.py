"""Regressão da rc.6: distribuição textual autossuficiente, sem scripts montados."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_cover_gate_evidence import make_docx

ROOT=Path(__file__).resolve().parents[1]
PORTABLE=ROOT/'scripts/portable_gate.py'

class TestPortableGate(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root=Path(td.name)
        self.standalone=self.root/'isolado'/'portable_gate.py'
        self.standalone.parent.mkdir()
        self.standalone.write_text(PORTABLE.read_text(encoding="utf-8"),encoding="utf-8")
        self.doc=self.root/'nota.docx'
        self.metadata=[('Finalidade','Minuta'),('Versão','0.1'),
                       ('Responsável pelo documento','Não informado'),('Autoria','Não atribuída')]

    def call(self,*args,loader=None):
        return subprocess.run([sys.executable,str(loader or self.standalone),*map(str,args)],
                              capture_output=True,text=True)

    def test_portable_source_matches_manifest(self):
        data=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(data['runtime_bootstrap']['sha256'],
                         hashlib.sha256(PORTABLE.read_bytes()).hexdigest())
        p=self.call('--verify-payload')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertTrue(json.loads(p.stdout)['payload_verified'])

    def test_payload_matches_original_scripts(self):
        p=self.call('--verify-payload','--compare-source',loader=PORTABLE)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertTrue(json.loads(p.stdout)['sources_matched'])

    def test_without_original_scripts_runs_original_gate_on_valid_docx(self):
        make_docx(self.doc,self.metadata)
        out=self.root/'gate1'
        p=self.call(self.doc,'--output-dir',out,'--profile','none')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads((out/'execution.json').read_text())['structural_gate'],'passed_partial_scope')
        self.assertEqual(json.loads((out/'execution.json').read_text())['institutional_release'],'not_authorized')
        boot=json.loads((out/'bootstrap.json').read_text())
        self.assertEqual(boot['artifact_sha256_before'],boot['artifact_sha256_after'])
        self.assertTrue(boot['artifact_unchanged'])
        self.assertFalse(boot['host_attestation'])
        self.assertTrue((out/'audit.json').is_file())
        self.assertTrue((out/'verification.json').is_file())

    def test_invalid_docx_blocks_in_isolated_mode(self):
        make_docx(self.doc,[('Finalidade','Minuta'),('Versão','0.1')])
        out=self.root/'gate2'
        p=self.call(self.doc,'--output-dir',out,'--profile','none')
        self.assertEqual(p.returncode,1,p.stdout+p.stderr)
        r=json.loads((out/'execution.json').read_text())
        self.assertEqual(r['structural_gate'],'blocked')
        self.assertEqual(r['institutional_release'],'not_authorized')

    def test_missing_docx_never_creates_fake_evidence(self):
        p=self.call(self.doc,'--output-dir',self.root/'gate3')
        self.assertNotEqual(p.returncode,0)
        self.assertFalse((self.root/'gate3').exists())

    def test_existing_output_cannot_be_overwritten(self):
        make_docx(self.doc,self.metadata)
        out=self.root/'gate4';out.mkdir()
        (out/'keep').write_text('original')
        p=self.call(self.doc,'--output-dir',out,'--profile','none')
        self.assertNotEqual(p.returncode,0)
        self.assertEqual((out/'keep').read_text(),'original')

    def test_tampered_payload_fails_before_execution(self):
        code=self.standalone.read_text(encoding='utf-8')
        m=re.search(r"ZIP_SHA256 = '([0-9a-f]{64})'",code)
        self.assertIsNotNone(m)
        code=code[:m.start(1)]+'0'*64+code[m.end(1):]
        self.standalone.write_text(code,encoding='utf-8')
        p=self.call('--verify-payload')
        self.assertNotEqual(p.returncode,0)
        self.assertIn('divergente',p.stderr)
        make_docx(self.doc,self.metadata)
        out=self.root/'should-not-execute'
        p=self.call(self.doc,'--output-dir',out,'--profile','none')
        self.assertNotEqual(p.returncode,0)
        self.assertFalse(out.exists())

    def test_tampered_embedded_script_fails_early(self):
        code=self.standalone.read_text(encoding='utf-8')
        marker="'audit_docx.py': '"
        self.assertIn(marker,code)
        code=code.replace(marker,marker+'0',1)
        self.standalone.write_text(code,encoding='utf-8')
        p=self.call('--verify-payload')
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('divergente',p.stderr)

    def test_cover_exception_cannot_be_silent(self):
        make_docx(self.doc,self.metadata)
        p=self.call(self.doc,'--output-dir',self.root/'gate-exception','--profile','none','--no-standard-cover')
        self.assertEqual(p.returncode,2,p.stderr)
        self.assertIn('--cover-exception-reason',p.stderr)
        self.assertFalse((self.root/'gate-exception').exists())

    def test_actual_v35_sample_works_outside_skill_dir(self):
        sample=Path('/mnt/data/nota_institucional_preliminar_demandas_internas (1).docx')
        if not sample.is_file():
            self.skipTest('Amostra externa não está disponível no runtime')
        out=self.root/'actual_gate'
        p=self.call(sample,'--output-dir',out,'--profile','institutional-v3.5')
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        report=json.loads((out/'audit.json').read_text())
        self.assertTrue(report['ok'])
        self.assertEqual(report['artifact_sha256'],hashlib.sha256(sample.read_bytes()).hexdigest())

if __name__=='__main__':
    unittest.main()
