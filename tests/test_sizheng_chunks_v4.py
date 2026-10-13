"""Batch02 data acceptance; read-only, without remote services or vector indexes."""
import hashlib
import json
import re
import unittest
from difflib import SequenceMatcher
from pathlib import Path

from src.utils.validate_jsonl import validate_record

ROOT=Path(__file__).resolve().parents[1]
DELIVERY=ROOT/'team_deliverables/lizhuoyang/2026-09-courseware-chunks/batch02'


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def duplicate_metrics(new, old):
    """Compare new/old and within-batch pairs; quick_ratio is an upper bound."""
    prepared={r['id']:re.sub(r'\W','',r['text']) for r in old+new}
    grams={key:{text[i:i+5] for i in range(len(text)-4)} for key,text in prepared.items()}
    result=dict(pairs=0, normalized_equal=[], whole_text_containment=[], high_similarity=[],
                sequence_threshold=0.85, fivegram_threshold=0.8,
                max_fivegram=dict(pair=[],ratio=0), full_sequence_comparisons=0)
    for i,row in enumerate(new):
        for previous in old+new[:i]:
            a,b=row['id'],previous['id'];x,y=prepared[a],prepared[b]
            result['pairs']+=1
            if x==y: result['normalized_equal'].append([a,b])
            if x in y or y in x: result['whole_text_containment'].append([a,b])
            g=len(grams[a]&grams[b])/min(len(grams[a]),len(grams[b]))
            if g>result['max_fivegram']['ratio']: result['max_fivegram']=dict(pair=[a,b],ratio=g)
            sm=SequenceMatcher(None,x,y,autojunk=False)
            # The upper-bound gate cannot hide a ratio >= 0.85.
            ratio=None
            if sm.quick_ratio()>=0.85:
                ratio=sm.ratio();result['full_sequence_comparisons']+=1
            if (ratio is not None and ratio>=0.85) or g>=0.8:
                result['high_similarity'].append(dict(pair=[a,b],sequence=ratio,fivegram=g))
    return result


class SizhengV4Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=read(ROOT/'data/processed/text_chunks_sizheng_v4.jsonl')
        cls.by_id={row['id']:row for row in cls.rows}
        cls.audit=read(DELIVERY/'citation_audit.jsonl')
        cls.typed=read(DELIVERY/'entity_types.jsonl')
        cls.old=[r for suffix in ('demo','sizheng_v1','sizheng_v2','sizheng_v3')
                 for r in read(ROOT/f'data/processed/text_chunks_{suffix}.jsonl')]

    def test_schema_and_ids(self):
        self.assertEqual(len(self.rows),24)
        seen=set()
        for i,row in enumerate(self.rows,1):
            self.assertEqual(validate_record(row,i,seen),([],[]))
            self.assertEqual(row['id'],f'chunk_sizheng_v4_{i:03}')
            self.assertEqual(set(row),set(self.old[-1]))
            self.assertEqual(row['source_type'],'textbook')
            self.assertEqual(row['chunk_type'],'textbook_chunk')
            self.assertEqual(row['source'],row['citation']['doc'])
            self.assertIsInstance(row['citation']['page'],int)
        self.assertFalse(seen & {r['id'] for r in self.old})

    def test_previous_versions_unchanged(self):
        expected={
            # Canonical LF hashes, so Windows checkout line endings are immaterial.
            'sizheng_v1':'7b359dfa97b51ffb3ecd00a63569b522f0de2719d0c2f5151345f7eb8a3c66a2',
            'sizheng_v2':'7325edab55f4a297d08f861372fb4d6878b0398787d97d1d74ff7d818f9a90af',
            'sizheng_v3':'19bfb97bca2b07dbd316a117e8e9304a966bf66fd640cc70ce7174b5da8fde11'}
        for suffix,digest in expected.items():
            raw=(ROOT/f'data/processed/text_chunks_{suffix}.jsonl').read_bytes().replace(b'\r\n',b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)

    def test_entities_and_time_have_evidence(self):
        self.assertEqual(len(self.typed),24)
        allowed={'person','organization','event','time','place','document','concept','role','group'}
        for row,typed in zip(self.rows,self.typed):
            self.assertEqual(typed['chunk_id'],row['id'])
            self.assertEqual(row['entities'],[e['name'] for e in typed['entities']])
            self.assertEqual(len(row['entities']),len(set(row['entities'])))
            for entity in typed['entities']:
                self.assertIn(entity['type'],allowed)
                self.assertIn(entity['name'],entity['evidence'])
                self.assertIn(entity['evidence'],row['text'])
            loc=row['location']
            if loc['name']: self.assertIn(loc['name'],row['text'])
            self.assertTrue(all(loc[k] is None for k in ('lat','lng','coord_sys')))
            self.assertIsNone(row['time']['end'])
            if row['time']['start']:
                y,m,d=map(int,row['time']['start'].split('-'))
                self.assertIn(f'{y}年{m}月{d}日',row['text'])

    def test_cleanliness_and_duplicate_bodies(self):
        known={re.sub(r'\W','',r['text']) for r in self.old}
        for row in self.rows:
            self.assertNotRegex(row['text'],r'仅供个人科研教学使用|欢迎关注公众号|思考题|目录|[①②③④⑤⑥⑦⑧⑨⑩�]|\?{4,}|\s{2,}')
            self.assertIn(row['text'][-1],'。！？；”')
            cleaned=re.sub(r'\W','',row['text'])
            self.assertNotIn(cleaned,known)
            known.add(cleaned)
        metrics=duplicate_metrics(self.rows,self.old)
        self.assertEqual(metrics['pairs'],7692)
        self.assertEqual(metrics['whole_text_containment'],[])
        self.assertEqual(metrics['high_similarity'],[])

    def test_complete_body_physical_start_and_end(self):
        raw=ROOT/'data/raw/MinerU_中国共产党思想政治教育史 __20260615145108.json'
        if not raw.exists(): self.skipTest('Requires local source; a skip is not citation verification.')
        source=json.loads(raw.read_text(encoding='utf-8'))['pdf_info']
        stream=[]; mapping=[]
        for p in source:
            text=''.join(s.get('content','') for b in p['preproc_blocks'] if b.get('type')=='text'
                         for line in b.get('lines',[]) for s in line.get('spans',[]) if s.get('type','text')=='text')
            text=re.sub(r'[\s①②③④⑤⑥⑦⑧⑨⑩]+','',text)
            stream.append(text);mapping.extend([p['page_idx']+201]*len(text))
        stream=''.join(stream)
        self.assertEqual(len(self.audit),24)
        for row,audit in zip(self.rows,self.audit):
            with self.subTest(chunk=row['id']):
                self.assertEqual(row['id'],audit['chunk_id'])
                body=row['text'];self.assertEqual(stream.count(body),1)
                pos=stream.index(body)
                self.assertEqual(mapping[pos],audit['pdf_start'])
                self.assertEqual(mapping[pos+len(body)-1],audit['pdf_end'])
                self.assertEqual(row['citation']['page'],audit['pdf_start'])
                self.assertEqual(row['citation']['section'],audit['section'])
                self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),audit['text_sha256'])
        self.assertEqual(self.by_id['chunk_sizheng_v4_017']['citation']['page'],327)
        self.assertEqual(self.by_id['chunk_sizheng_v4_023']['citation']['page'],340)

    def test_questions_resolve_unique_evidence_and_citation(self):
        cases=json.loads((ROOT/'tests/queries_sizheng_v4_batch02.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual(len(cases),5)
        audit={a['chunk_id']:a for a in self.audit}
        for case in cases:
            hits=[r['id'] for r in self.old+self.rows if all(s in r['text'] for s in case['evidence_anchors'])]
            self.assertEqual(hits,case['expected_chunk_ids'],case['id'])
            for cid in hits:
                expected=case['expected_citation'];row=self.by_id[cid]
                self.assertEqual(row['citation']['doc'],expected['doc'])
                self.assertTrue(row['citation']['section'].endswith(expected['section_suffix']))
                self.assertEqual(audit[cid]['pdf_start'],expected['pdf_start'])
                self.assertEqual(audit[cid]['pdf_end'],expected['pdf_end'])

    def test_distinct_events_are_split(self):
        def body(n):return self.by_id[f'chunk_sizheng_v4_{n:03}']['text']
        self.assertNotIn('1978年4月22日',body(8))
        self.assertTrue(body(9).startswith('1978年4月22日'))
        self.assertNotIn('1981年11月',body(3))
        self.assertTrue(body(4).startswith('1981年11月'))
        self.assertNotIn('1983年10月11日',body(17))
        self.assertNotIn('1986年',body(15))
        self.assertNotIn('1985年1月11日',body(23))


if __name__=='__main__': unittest.main()
