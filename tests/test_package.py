"""Verifica identidade canônica na distribuição e portabilidade no diretório instalado."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
SOURCE=REPO/'skills'/'governanca-documental-institucional'


def verify(path,*args):
    return subprocess.run([sys.executable,str(path/'scripts'/'verify_package.py'),*args],
                          text=True,capture_output=True)


class PackageTest(unittest.TestCase):
    def test_exact_original_plugin_inventory(self):
        baseline=json.loads((REPO/'tests'/'source_0.2.2.json').read_text(encoding='utf-8'))
        actual={p.relative_to(REPO).as_posix() for folder in (REPO/'skills',REPO/'.codex-plugin')
                for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        actual.add('plugin.json')
        self.assertEqual(set(baseline['files']),actual)
        for rel,expected in baseline['files'].items():
            with self.subTest(path=rel):
                raw=(REPO/rel).read_bytes()
                self.assertEqual(expected['size_bytes'],len(raw))
                self.assertEqual(expected['sha256'],hashlib.sha256(raw).hexdigest())

    def test_plugin_manifests_and_skill_versions(self):
        root=json.loads((REPO/'plugin.json').read_text(encoding='utf-8'))
        overlay=json.loads((REPO/'.codex-plugin'/'plugin.json').read_text(encoding='utf-8'))
        skill=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual('https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',root['$schema'])
        self.assertEqual('governanca-documental-plugin',root['name'])
        self.assertEqual('0.2.2',root['version'])
        self.assertEqual('1.1.1',skill['skill_version'])
        for key in ('name','version','description','homepage'):
            self.assertEqual(root[key],overlay[key])
        self.assertEqual(root['extensions']['com.openai']['interface'],overlay['interface'])
        self.assertLessEqual(len(overlay['interface']['shortDescription']),30)
        self.assertFalse((REPO/'manifest.json').exists())

    def test_canonical_and_derived_sizes(self):
        manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(['0.8','3.5','1.3','0.5'],[s['version'] for s in manifest['sources']])
        for source in manifest['sources']:
            for kind in ('canonical','derived'):
                entry=source[kind]
                with self.subTest(path=entry['path']):
                    self.assertEqual(entry['size_bytes'],(SOURCE/entry['path']).stat().st_size)

    def test_packaged_skill_name_must_match_directory(self):
        result=verify(SOURCE,'--strict-dir-name')
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)

    def test_runtime_renamed_directory_warns_but_verifies_contents(self):
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/'runtime-renamed-skill-123'
            shutil.copytree(SOURCE,location)
            result=verify(location)
            self.assertEqual(0,result.returncode,result.stdout+result.stderr)
            self.assertIn('AVISO: diretório de instalação',result.stdout)
            self.assertIn('OK: SKILL.md',result.stdout)

    def test_runtime_renamed_directory_fails_in_strict_distribution_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/'runtime-renamed-skill-123'
            shutil.copytree(SOURCE,location)
            result=verify(location,'--strict-dir-name')
            self.assertNotEqual(0,result.returncode)
            self.assertIn('ERRO: diretório de instalação',result.stdout)

    def test_stable_release_requires_stable_status(self):
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/'governanca-documental-institucional'
            shutil.copytree(SOURCE,location)
            manifest=location/'manifest.json'
            data=json.loads(manifest.read_text(encoding='utf-8'))
            data['release_status']='candidate'
            manifest.write_text(json.dumps(data),encoding='utf-8')
            result=verify(location,'--strict-dir-name')
            self.assertNotEqual(0,result.returncode)
            self.assertIn('exige release_status',result.stdout)

    def test_frontmatter_version_must_match_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/'governanca-documental-institucional'
            shutil.copytree(SOURCE,location)
            skill=location/'SKILL.md'
            skill.write_text(skill.read_text(encoding='utf-8').replace('version: "1.1.1"','version: "1.1.2"'),encoding='utf-8')
            result=verify(location,'--strict-dir-name')
            self.assertNotEqual(0,result.returncode)
            self.assertIn('Versão do frontmatter diferente',result.stdout)

    def test_manifest_identity_must_match_frontmatter_even_in_runtime_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            location=Path(temp)/'runtime-renamed-skill-123'
            shutil.copytree(SOURCE,location)
            manifest=location/'manifest.json'
            data=json.loads(manifest.read_text(encoding='utf-8'))
            data['skill_name']='outro-nome'
            manifest.write_text(json.dumps(data),encoding='utf-8')
            result=verify(location)
            self.assertNotEqual(0,result.returncode)
            self.assertIn('Nome canônico do frontmatter diferente do manifesto',result.stdout)


if __name__=='__main__':unittest.main()
