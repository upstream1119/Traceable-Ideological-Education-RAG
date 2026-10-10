"""Batch03 static acceptance. No retrieval services, credentials, or indexes."""
import hashlib
import json
import re
import unittest
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from src.utils.validate_jsonl import validate_record
from tests.test_sizheng_chunks_v4 import duplicate_metrics

ROOT = Path(__file__).resolve().parents[1]
DELIVERY = ROOT/'team_deliverables/lizhuoyang/2026-09-courseware-chunks/batch03'
OLD_HASHES = {
    1:'7b359dfa97b51ffb3ecd00a63569b522f0de2719d0c2f5151345f7eb8a3c66a2',
    2:'7325edab55f4a297d08f861372fb4d6878b0398787d97d1d74ff7d818f9a90af',
    3:'19bfb97bca2b07dbd316a117e8e9304a966bf66fd640cc70ce7174b5da8fde11',
    4:'90f44874395e6654c978710855690b18238be944429d9c0dfdfd0763c5d85b63',
}


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def source_fixture():
    from src.etl.build_sizheng_chunks_v5 import SOURCES
    pages = {}
    for name,offset,digest in SOURCES:
        path = ROOT/'data/raw'/name
        if not path.exists():
            raise unittest.SkipTest('Local raw source required; skip is not source verification.')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        for page in json.loads(path.read_text(encoding='utf-8'))['pdf_info']:
            pages[page['page_idx']+offset] = page
    return pages


def text_of(block):
    return re.sub(r'[\s①②③④⑤⑥⑦⑧⑨⑩]+','', ''.join(
        s.get('content','') for line in block.get('lines',[]) for s in line.get('spans',[])
        if s.get('type','text')=='text'))


def full_duplicate_metrics(new,old):
    metrics = duplicate_metrics(new,old)
    metrics.update(old_pairs=len(new)*len(old),within_batch_pairs=len(new)*(len(new)-1)//2,
        literal_equal=[],long_shared_spans=[],long_shared_span_threshold=80,max_shared_span=0)
    for i,row in enumerate(new):
        for previous in old+new[:i]:
            pair=[row['id'],previous['id']]
            if row['text']==previous['text']: metrics['literal_equal'].append(pair)
            a,b=(re.sub(r'\W','',r['text']) for r in (row,previous))
            match=SequenceMatcher(None,a,b,autojunk=False).find_longest_match()
            metrics['max_shared_span']=max(metrics['max_shared_span'],match.size)
            if match.size>=80:
                metrics['long_shared_spans'].append(dict(pair=pair,length=match.size,text=a[match.a:match.a+match.size]))
    return metrics


class SizhengV5Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=read(ROOT/'data/processed/text_chunks_sizheng_v5.jsonl')
        cls.old=[r for v in range(1,5) for r in read(ROOT/f'data/processed/text_chunks_sizheng_v{v}.jsonl')]
        cls.audit=read(DELIVERY/'citation_audit.jsonl')
        cls.typed=read(DELIVERY/'entity_types.jsonl')
        cls.queries=json.loads((ROOT/'tests/queries_sizheng_v5_batch03.json').read_text(encoding='utf-8'))

    def test_01_schema_and_ids(self):
        self.assertEqual(len(self.rows),15)
        self.assertEqual(len(self.old),293)
        seen=set()
        for i,row in enumerate(self.rows,1):
            self.assertEqual(validate_record(row,i,seen),([],[]))
            self.assertEqual(row['id'],f'chunk_sizheng_v5_{i:03}')
            self.assertEqual(set(row),set(self.old[-1]))
            self.assertEqual(row['source_type'],'textbook')
            self.assertEqual(row['chunk_type'],'textbook_chunk')
            self.assertEqual(row['source'],row['citation']['doc'])
        self.assertFalse(seen & {r['id'] for r in self.old})

    def test_02_previous_versions_unchanged(self):
        for v,digest in OLD_HASHES.items():
            raw=(ROOT/f'data/processed/text_chunks_sizheng_v{v}.jsonl').read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)

    def test_03_original_text_and_physical_bounds(self):
        fragments=[];mapping=[]
        for page_no,page in sorted(source_fixture().items()):
            for block in page['preproc_blocks']:
                if block.get('type')=='text':
                    text=text_of(block);fragments.append(text);mapping.extend([page_no]*len(text))
        stream=''.join(fragments)
        for row,audit in zip(self.rows,self.audit):
            self.assertEqual(row['id'],audit['chunk_id'])
            self.assertEqual(hashlib.sha256(row['text'].encode()).hexdigest(),audit['text_sha256'])
            bodies=row['text'].split('\n\n')
            spans=audit['source_selection']['spans']
            self.assertEqual(len(bodies),len(spans))
            previous=-1
            for part,span in zip(bodies,spans):
                self.assertEqual(stream.count(part),1)
                pos=stream.index(part)
                self.assertGreater(pos,previous)
                self.assertEqual(pos,span['normalized_source_offset'])
                self.assertEqual(span['character_count'],len(part))
                self.assertEqual((mapping[pos],mapping[pos+len(part)-1]),(span['pdf_start'],span['pdf_end']))
                self.assertEqual({str(k):v for k,v in Counter(mapping[pos:pos+len(part)]).items()},span['characters_by_pdf_page'])
                previous=pos+len(part)-1
            self.assertEqual(audit['pdf_start'],spans[0]['pdf_start'])
            self.assertEqual(audit['pdf_end'],spans[-1]['pdf_end'])
            self.assertEqual(row['citation']['page'],audit['pdf_start'])
            self.assertEqual(row['citation']['section'],audit['section'])
            self.assertEqual(audit['full_text_physical_match'],len(bodies)==1)
            self.assertEqual(audit['visual_review']['text'],'pass')
            self.assertEqual(audit['visual_review']['reviewer_kind'],'agent_visual_review')
            self.assertFalse(audit['human_confirmed'])

    def test_04_sections_and_cross_page_continuity(self):
        titles={text_of(b) for p in source_fixture().values() for b in p['para_blocks'] if b.get('type')=='title'}
        for row in self.rows:
            for component in row['citation']['section'].split(' / '):
                self.assertIn(re.sub(r'\s','',component),titles)
        expected={'chunk_sizheng_v5_003':(310,311),'chunk_sizheng_v5_005':(345,346),'chunk_sizheng_v5_014':(479,480)}
        self.assertEqual({a['chunk_id']:(a['pdf_start'],a['pdf_end']) for a in self.audit if a['cross_page']},expected)
        for audit in self.audit:
            self.assertEqual(audit['visual_review']['cross_page'],'pass' if audit['cross_page'] else 'not_applicable')
        self.assertEqual((self.audit[6]['source_selection']['para_page'],self.audit[6]['pdf_start']),(388,389))

    def test_05_entities_and_dates(self):
        self.assertEqual(len(self.typed),len(self.rows))
        allowed={'person','organization','event','time','place','document','concept','role','group'}
        for row,typed in zip(self.rows,self.typed):
            self.assertEqual(row['id'],typed['chunk_id'])
            self.assertEqual(row['entities'],[e['name'] for e in typed['entities']])
            self.assertEqual(len(row['entities']),len(set(row['entities'])))
            for entity in typed['entities']:
                self.assertIn(entity['type'],allowed)
                self.assertIn(entity['name'],entity['evidence'])
                self.assertIn(entity['evidence'],row['text'])
            self.assertTrue(all(row['location'][k] is None for k in ('lng','lat','coord_sys')))
            if row['location']['name']: self.assertIn(row['location']['name'],row['text'])
            if row['time']['start']:
                y,m,d=map(int,row['time']['start'].split('-'))
                self.assertIn(f'{y}年{m}月{d}日',row['text'])
            if row['time']['end']:
                y,m,d=map(int,row['time']['end'].split('-'))
                self.assertEqual(str(y),row['time']['start'][:4])
                self.assertTrue(f'至{m}月{d}日' in row['text'] or f'至{d}日' in row['text'])
        for n in (2,3,7,8,9,12,13,14):
            self.assertIsNone(self.rows[n-1]['time']['start'])
        self.assertEqual(self.rows[13]['time']['display'],'2013年8月')

    def test_06_approved_scope_and_special_boundaries(self):
        self.assertEqual(Counter(a['candidate_id'] for a in self.audit),
            Counter({'C01':3,'C02':1,'C03':1,'C04':1,'C05':1,'C06':1,'C08':1,'C09':1,'C10':1,'C11':2,'C12':1,'C13':1}))
        self.assertNotIn('四有',self.rows[3]['text'])
        self.assertNotIn('6月9日',self.rows[5]['text'])
        self.assertNotIn('1995年',self.rows[6]['text'])
        self.assertNotIn('1998年',self.rows[7]['text'])
        self.assertNotIn('大学生',self.rows[9]['text'])
        self.assertNotIn('未成年人',self.rows[10]['text'])
        self.assertNotRegex(self.rows[14]['text'],r'1929|生命线|不竭力量|参观|420')
        self.assertEqual(len(self.rows[14]['text'].split('\n\n')),2)
        self.assertIn('2014年',self.rows[14]['title'])
        for numeral in '一二三四五六': self.assertIn(numeral+'是关于',self.rows[1]['text'])

    def test_07_cleanliness(self):
        for row in self.rows:
            self.assertNotRegex(row['text'],r'仅供个人科研教学使用|欢迎关注公众号|思考题|目录|[①②③④⑤⑥⑦⑧⑨⑩�]|\?{4,}|[ \t\r]')
            self.assertIn(row['text'][-1],'。！？；”')
            if row['id']!='chunk_sizheng_v5_015': self.assertNotIn('\n',row['text'])

    def test_08_full_duplicate_comparison(self):
        metrics=full_duplicate_metrics(self.rows,self.old)
        self.assertEqual(metrics['old_pairs'],4395)
        self.assertEqual(metrics['within_batch_pairs'],105)
        self.assertEqual(metrics['pairs'],4500)
        for name in ('literal_equal','normalized_equal','whole_text_containment','high_similarity','long_shared_spans'):
            self.assertEqual(metrics[name],[],name)

    def test_09_question_evidence_uniqueness(self):
        self.assertEqual(len(self.queries),10)
        by_id={r['id']:r for r in self.rows}
        audits={a['chunk_id']:a for a in self.audit}
        for q in self.queries:
            hits=[r['id'] for r in self.old+self.rows if all(a in r['text'] for a in q['evidence_anchors'])]
            self.assertEqual(hits,q['expected_chunk_ids'])
            row=by_id[hits[0]];audit=audits[hits[0]]
            self.assertTrue(all(f in row['text'] for f in q['answer_facts']))
            self.assertEqual(q['evidence_text'],row['text'])
            self.assertEqual(q['expected_citation'],row['citation'])
            self.assertEqual(q['pdf_evidence_pages'],list(range(audit['pdf_start'],audit['pdf_end']+1)))
            self.assertEqual(q['test_scope'],'static_evidence_uniqueness_not_runtime_retrieval')

    def test_10_reproducible_read_only_build(self):
        source_fixture()
        from src.etl.build_sizheng_chunks_v5 import build
        self.assertEqual(build(),(self.rows,self.typed,self.audit))


if __name__=='__main__':
    unittest.main()
