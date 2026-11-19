"""Regressão sem dependências externas: python -m unittest discover -s tests -v."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('audit_docx', ROOT/'scripts'/'audit_docx.py')
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'


def styles(duplicate=False, outline=False, bad_font=False):
    defs=[]
    for sid,font,size,level in [('Normal','Arial',20,None),('Heading1','Arial' if bad_font else 'Calibri',31,0),('Heading2','Calibri',24,1),('Heading3','Calibri',21,2)]:
        ol='' if level is None else f'<w:outlineLvl w:val="{level}"/>'
        if outline and sid=='Heading1':ol+=ol
        ppr=f'<w:pPr>{ol}</w:pPr>' if ol else ''
        defs.append(f'<w:style w:type="paragraph" w:styleId="{sid}">{ppr}<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:sz w:val="{size}"/></w:rPr></w:style>')
    if duplicate:defs.append(defs[1])
    return f'<w:styles xmlns:w="{W}">'+''.join(defs)+'</w:styles>'


def document(table_bad=False, shade_bad=False, toc=False, ref=False, cache='3', malformed=False):
    body='<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:bookmarkStart w:id="1" w:name="sec01"/><w:r><w:t>Título válido</w:t></w:r><w:bookmarkEnd w:id="1"/></w:p>'
    if shade_bad:
        body+='<w:p><w:pPr><w:shd w:fill="F7F9FB"/></w:pPr><w:r><w:t>Teste</w:t></w:r></w:p>'
    if table_bad:
        body+='<w:tbl><w:tblPr><w:tblW w:w="4000" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders/></w:tblPr><w:tblGrid/><w:tr><w:tc><w:p/></w:tc></w:tr></w:tbl>'
    if toc:
        body+='<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> TOC \\o "1-3" </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r></w:p>'
    if ref:
        body+=f'<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText> PAGEREF sec01 \\h </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r><w:t>{cache}</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    if toc:
        body+='<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
    if malformed:
        body+='<w:p><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:p>'
    body+='<w:sectPr><w:pgSz w:w="12240" w:h="15840"/></w:sectPr>'
    return f'<w:document xmlns:w="{W}"><w:body>{body}</w:body></w:document>'


class TestAuditDocx(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'sample.docx'

    def audit(self, *, styles_xml=None, document_xml=None, profile='none', map=None):
        with zipfile.ZipFile(self.path,'w') as z:
            z.writestr('word/document.xml', document_xml or document())
            z.writestr('word/styles.xml',styles_xml or styles())
        return mod.audit(self.path, profile, map)

    def codes(self,result):
        return [x['code'] for x in result['issues']]

    def test_valid_minimal_file_and_calibri_heading(self):
        result=self.audit(profile='institutional-v3.4')
        self.assertTrue(result['ok'],result['issues'])
        self.assertEqual(result['heading_count'],1)
        self.assertNotIn('role_font_name',self.codes(result))

    def test_duplicate_style_detected(self):
        result=self.audit(styles_xml=styles(duplicate=True))
        self.assertIn('duplicate_style_id',self.codes(result))
        self.assertFalse(result['ok'])

    def test_duplicate_outline_detected(self):
        result=self.audit(styles_xml=styles(outline=True))
        self.assertIn('duplicate_outline_lvl',self.codes(result))

    def test_table_property_order_detected(self):
        result=self.audit(document_xml=document(table_bad=True))
        self.assertIn('table_properties_order',self.codes(result))

    def test_shading_val_required(self):
        result=self.audit(document_xml=document(shade_bad=True))
        self.assertIn('shading_missing_val',self.codes(result))

    def test_wrong_heading_font_detected_under_profile(self):
        result=self.audit(styles_xml=styles(bad_font=True), profile='institutional-v3.4')
        self.assertIn('role_font_name',self.codes(result))
        self.assertFalse(result['ok'])
        result2=self.audit(styles_xml=styles(bad_font=True))
        self.assertNotIn('role_font_name',self.codes(result2))

    def test_toc_across_paragraphs_not_unbalanced(self):
        result=self.audit(document_xml=document(toc=True,ref=True))
        self.assertTrue(result['toc_field_detected'])
        self.assertEqual(result['pageref_field_count'],1)
        self.assertNotIn('field_unbalanced',self.codes(result))

    def test_pageref_cache_checked_only_with_external_map(self):
        result=self.audit(document_xml=document(ref=True,cache='3'))
        self.assertIn('pageref_cache_not_verified',self.codes(result))
        self.assertNotIn('pageref_cache_mismatch',self.codes(result))
        result2=self.audit(document_xml=document(ref=True,cache='3'),map={'sec01':4})
        self.assertIn('pageref_cache_mismatch',self.codes(result2))
        result3=self.audit(document_xml=document(ref=True,cache='4'),map={'sec01':4})
        self.assertNotIn('pageref_cache_mismatch',self.codes(result3))
        self.assertEqual(result3['pageref_cache_checked'],1)

    def test_absent_toc_not_automatic_error(self):
        result=self.audit(document_xml=document(ref=True))
        self.assertIn('toc_not_detected',self.codes(result))
        self.assertTrue(result['ok'])

    def test_unbalanced_field_detected(self):
        result=self.audit(document_xml=document(malformed=True))
        self.assertIn('field_unbalanced',self.codes(result))


if __name__=='__main__':
    unittest.main()
