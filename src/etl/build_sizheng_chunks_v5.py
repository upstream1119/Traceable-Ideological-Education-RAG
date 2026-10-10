"""Batch03 approved textbook excerpts; read-only unless --write, never overwrites.

Physical page bounds were visually checked against the original PDF on 2026-10-10.
The agent review recorded here is not the responsible person's batch acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / 'team_deliverables/lizhuoyang/2026-09-courseware-chunks/batch03'
SOURCE = '中国共产党思想政治教育史'
PDF_SHA256 = 'e04a86c9564bbdf598ebeb91a15a526b49a4e8aaa91acdb5e2892432a0abae13'
SOURCES = [
    ('MinerU_中国共产党思想政治教育史 __20260615145108.json', 201, 'cb494527f5a3e84873e522ecdd8289938fe9530a5be1f7e24501631651b24f94'),
    ('MinerU_中国共产党思想政治教育史 __20260615145133.json', 401, 'c7ad75e0fe479415bae5ab344c33bac70a54fc55a3020a24f440016463112f5d'),
]
CH8 = '第八章 历史性伟大转折和改革开放起步阶段思想政治教育的拨乱反正'
CH9 = '第九章 开创社会主义现代化建设新局面进程中思想政治教育的全面展开'
CH10 = '第十章 社会主义市场经济条件下思想政治教育的与时俱进'
CH11 = '第十一章 全面建设小康社会进程中思想政治教育的科学发展'
CH12 = '第十二章 在实现中华民族伟大复兴道路上开创思想政治教育新局面'
MEETING = CH8+' / 第三节 党的十一届三中全会和思想政治教育的历史性转折 / 一、党的思想路线、政治路线的重新恢复和确立'
EDUCATION = CH9+' / 第一节 党的十二大和群众性思想政治教育的有序展开 / 五、坚持“三个面向”和培养“四有新人”'
DISCIPLINE = CH9+' / 第三节 新时期思想政治教育的理论建设 / 一、思想政治教育的科学研究与学科建设'
SCHOOL = CH10+' / 第一节 党的十四大和各条战线思想政治教育的稳步推进 / 三、学校思想政治教育的加强和改进'
CADRE = CH11+' / 第一节 党的十六大和思想政治教育的扎实推进 / 三、新时期的干部学校教育'
YOUTH = CH11+' / 第一节 党的十六大和思想政治教育的扎实推进 / 四、青少年思想政治教育的加强与改进'
PROJECT = CH11+' / 第二节 构建社会主义和谐社会与思想政治教育的和谐发展 / 三、实施马克思主义理论研究和建设工程'
PUBLICITY = CH12+' / 第三节 加强社会主义意识形态建设 / 一、召开全国宣传思想工作会议'
GUTIAN = CH12+' / 第四节 全面加强党和军队的思想政治教育 / 四、古田全军政治工作会议的召开'


def compact(text):
    return re.sub(r'[\s①②③④⑤⑥⑦⑧⑨⑩]+', '', text)


def block_text(block):
    return ''.join(s.get('content', '') for line in block.get('lines', [])
                   for s in line.get('spans', []) if s.get('type', 'text') == 'text')


def source_pages(raw_dir=None):
    pages = {}
    for name, offset, digest in SOURCES:
        path = (Path(raw_dir) if raw_dir else ROOT/'data/raw') / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
        for page in json.loads(path.read_text(encoding='utf-8'))['pdf_info']:
            pages[page['page_idx']+offset] = page
    return pages


def specs():
    rows = []
    def add(candidate, title, page, block, section, bounds, entities, tags,
            begin=None, stop=None, time=None, date=None, end_date=None, place=None,
            parts=None, note='', context=None):
        rows.append(dict(candidate=candidate,title=title,page=page,block=block,section=section,
            bounds=bounds,entities=entities,tags=tags,begin=begin,stop=stop,time=time,
            date=date,end_date=end_date,place=place,parts=parts,note=note,context=context or []))
    P,O,E,T,L,D,C,R,G = 'person','organization','event','time','place','document','concept','role','group'
    add('C01','1978年中央工作会议的召开时间、地点与目的',310,2,MEETING,(310,310),
        [('中共中央',O),('北京',L),('1978年11月10日至12月15日',T),('中央工作会议',E),('党的十一届三中全会',E)],
        ['中央工作会议','会议基本事实'],time='1978年11月10日至12月15日',date='1978-11-10',end_date='1978-12-15',place='北京')
    add('C01','1978年中央工作会议讨论的六项议题',310,3,MEETING,(310,310),
        [('中央工作会议',E),('1979年',T),('真理标准问题讨论',E),('民主集中制',C)],
        ['中央工作会议','六项议题'],stop='在中央工作会议闭幕会上',context=['chunk_sizheng_v5_001'],
        note='会议年份来自紧邻前段001；正文的1979年是工作重点转移目标年，不作为会议时间。')
    add('C01','邓小平在中央工作会议闭幕会上的讲话',310,3,MEETING,(310,311),
        [('邓小平',P),('中央工作会议',E),('《解放思想，实事求是，团结一致向前看》',D),('党的十一届三中全会',E)],
        ['闭幕讲话','思想路线'],begin='在中央工作会议闭幕会上',context=['chunk_sizheng_v5_001'],
        note='仅取讲话题名、重点论述及教材对该讲话的说明；未取311页下方后续大段引语，未补讲话具体日期。')
    add('C02','1983年邓小平为北京景山学校题词',345,1,EDUCATION,(345,345),
        [('1983年10月1日',T),('邓小平',P),('北京景山学校',O)],
        ['三个面向','学校教育'],begin='1983年10月1日',stop='此后，各级各类学校',time='1983年10月1日',date='1983-10-01',
        note='仅取题词及其指导方针说明；排除此前十二大党章四有要求及此后四有新人实践段。学校名称不推导独立地点字段。')
    add('C03','1984年四部门在北京联合召开高校思想政治工作会议',345,2,EDUCATION,(345,346),
        [('1984年6月7日至16日',T),('中共中央宣传部',O),('教育部',O),('共青团中央',O),('全国教育工会',O),('北京',L),('全国高等学校思想政治工作会议',E)],
        ['高校思想政治工作会议','联合组织'],time='1984年6月7日至16日',date='1984-06-07',end_date='1984-06-16',place='北京',
        note='345页页末“全国”接346页“教育工会”；与1978年教育会议和武汉文科座谈会不同。')
    add('C04','1984年教育部在十二所院校设置思想政治教育专业',360,1,DISCIPLINE,(360,360),
        [('教育部',O),('1984年4月13日',T),('《教育部关于在十二所院校设置思想政治教育专业的意见》',D),('南开大学',O),('复旦大学',O),('武汉大学',O),('思想政治教育',C)],
        ['思想政治教育专业','专业设置'],stop='6月9日',time='1984年4月13日',date='1984-04-13',
        note='只取4月13日文件、12所院校试点及培养规格；保留教材列举的三所院校，不补完整名单，不取6月后续文件。')
    add('C05','1994年学校德育意见与学校管理责任',388,5,SCHOOL+' / （二）学校德育体系的重新规划',(389,389),
        [('1994年8月',T),('《中共中央关于进一步加强和改进学校德育工作的若干意见》',D),('学校党组织',O),('校长',R),('行政系统',O)],
        ['学校德育','管理责任'],begin='1994年8月《中共中央',stop='1995年',time='1994年8月',
        note='MinerU para_blocks合并段归属388页，但所选文字全部在实际PDF389页；与同页1995年两课事项分开。')
    add('C06','1995年国家教委两课教学改革文件及课程定位',389,2,SCHOOL+' / （三）思想政治教育的改革和发展',(389,389),
        [('1995年10月',T),('国家教育委员会',O),('《关于高校马克思主义理论课和思想品德课教学改革的若干意见》',D),('《中共中央关于进一步加强和改进学校德育工作的若干意见》',D),('“两课”',C)],
        ['两课改革','高校课程定位'],begin='1995年10月',stop='1998年',time='1995年10月',
        note='虽提及作为落实依据的1994年文件，本条证据主体为1995年国家教委文件；不重复C05管理责任。')
    add('C08','2005年浦东、井冈山、延安三所干部学院建成开学',432,1,CADRE,(432,432),
        [('全国组织工作会议',E),('上海浦东',L),('江西井冈山',L),('陕西延安',L),('2005年3月',T),('浦东、井冈山、延安三所干部学院',G),('开学典礼',E)],
        ['干部学院','干部教育培训基地'],begin='全国组织工作会议特别提出',stop='2006年1月',time='2005年3月',
        note='截去无独立指代的“这次”，保留原文三个地点和三所学院的集合名称；不补个别学院全称、人物或具体日。location单值保持null，多地点见entities。')
    add('C09','2004年未成年人思想道德建设文件及落实会议',435,2,YOUTH+' / （一）加强未成年人思想道德建设',(435,435),
        [('2004年2月26日',T),('中共中央',O),('国务院',O),('《关于进一步加强和改进未成年人思想道德建设的若干意见》',D),('全国加强和改进未成年人思想道德建设工作会议',E),('同年5月',T)],
        ['未成年人','思想道德建设'],begin='2004年2月26日',time='2004年2月26日；同年5月',date='2004-02-26')
    add('C10','2004年大学生思想政治教育意见及2005年落实会议',438,1,YOUTH+' / （二）加强与改进大学生思想政治教育',(438,438),
        [('2004年8月26日',T),('2005年1月',T),('中共中央',O),('国务院',O),('《关于进一步加强和改进大学生思想政治教育的意见》',D),('全国加强和改进大学生思想政治教育工作会议',E)],
        ['大学生思想政治教育','政策落实会议'],time='2004年8月26日；2005年1月',date='2004-08-26')
    add('C11','2004年马克思主义理论研究和建设工程的文件部署',443,4,PROJECT,(443,443),
        [('2004年初',T),('中共中央',O),('中共中央办公厅',O),('《关于进一步繁荣发展哲学社会科学的意见》',D),('《中央宣传思想工作领导小组关于实施马克思主义理论研究和建设工程的意见》',D),('马克思主义理论研究和建设工程',E)],
        ['马克思主义理论研究和建设工程','文件部署'],begin='2004年初',time='2004年初')
    add('C11','2004年工程工作会议的研究重点与建设目标',443,5,PROJECT,(443,443),
        [('2004年4月',T),('马克思主义理论研究和建设工程',E),('邓小平理论',C),('“三个代表”重要思想',C),('十年左右',T)],
        ['马克思主义理论研究和建设工程','学科教材队伍建设'],begin='2004年4月',time='2004年4月',
        note='十年左右是原文目标时长，不推算或断言具体完成日期。')
    add('C12','2013年北京全国宣传思想工作会议与习近平讲话',479,4,PUBLICITY,(479,480),
        [('2013年8月',T),('全国宣传思想工作会议',E),('北京',L),('习近平',P)],
        ['宣传思想工作会议','习近平讲话'],time='2013年8月',place='北京',
        note='479页“回顾总”与480页“结了”连续；教材此段只有2013年8月，不补具体日期。')
    add('C13','2014年古田全军政治工作会议的召开、任务与讲话日期',500,2,GUTIAN,(500,500),
        [('习近平',P),('全军政治工作会议',E),('2014年10月30日至11月2日',T),('福建省上杭县古田镇',L),('10月31日',T),('中央军委',O)],
        ['2014年古田全军政治工作会议','军队思想政治建设'],time='2014年10月30日至11月2日；10月31日讲话',date='2014-10-30',end_date='2014-11-02',place='福建省上杭县古田镇',
        parts=[{'begin':'根据中央军委习近平主席的提议','stop':'中央军委委员'}, {'begin':'会议主要任务是：','stop':None}],
        note='按原顺序摘取同段两处连续原文，用空行分隔；省略中间代表组成与参观活动，不改写句子。未取后页历史作用引语，不与1929年古田会议混同。')
    return rows


def build(raw_dir=None):
    pages = source_pages(raw_dir)
    fragments, page_map = [], []
    for n, page in sorted(pages.items()):
        for block in page['preproc_blocks']:
            if block.get('type') == 'text':
                part = compact(block_text(block))
                fragments.append(part)
                page_map.extend([n]*len(part))
    stream = ''.join(fragments)
    chunks, typed, audits = [], [], []
    for i, spec in enumerate(specs(), 1):
        original = compact(block_text(pages[spec['page']]['para_blocks'][spec['block']]))
        selections = spec['parts'] or [dict(begin=spec['begin'],stop=spec['stop'])]
        parts, spans = [], []
        for selection in selections:
            body = original
            for key in ('begin','stop'):
                marker = selection[key]
                if marker:
                    assert body.count(marker) == 1, (i,key,marker)
                    at = body.index(marker)
                    body = body[at:] if key == 'begin' else body[:at]
            assert body and stream.count(body) == 1, (i,'source match not unique')
            pos = stream.index(body)
            a,z = page_map[pos],page_map[pos+len(body)-1]
            spans.append(dict(**selection,normalized_source_offset=pos,character_count=len(body),
                pdf_start=a,pdf_end=z,match_count=1,start_anchor=body[:36],end_anchor=body[-36:],
                characters_by_pdf_page={str(k):v for k,v in Counter(page_map[pos:pos+len(body)]).items()},
                page_transitions=[dict(from_pdf=page_map[j-1],to_pdf=page_map[j],
                    before=stream[max(pos,j-24):j],after=stream[j:min(pos+len(body),j+24)])
                    for j in range(pos+1,pos+len(body)) if page_map[j]!=page_map[j-1]]))
            parts.append(body)
        assert all(x['normalized_source_offset']+x['character_count'] <= y['normalized_source_offset']
                   for x,y in zip(spans,spans[1:])), 'Excerpt order/overlap'
        start,end = spans[0]['pdf_start'],spans[-1]['pdf_end']
        assert (start,end) == spec['bounds'], (i,start,end)
        body = '\n\n'.join(parts)
        cid = f'chunk_sizheng_v5_{i:03}'
        chunks.append(dict(id=cid,source=SOURCE,source_type='textbook',title=spec['title'],text=body,
            chunk_type='textbook_chunk',topic=spec['title'],
            time=dict(start=spec['date'],end=spec['end_date'],display=spec['time']),
            location=dict(name=spec['place'],lng=None,lat=None,coord_sys=None),
            entities=[name for name,kind in spec['entities']],
            tags=['教材切片','思政知识库v5','batch03',*spec['tags']],
            citation=dict(doc=SOURCE,section=spec['section'],page=start)))
        entities = []
        for name,kind in spec['entities']:
            pos = body.index(name)
            left = max(body.rfind('。',0,pos),body.rfind('；',0,pos),body.rfind('\n',0,pos))+1
            right = body.find('。',pos+len(name))
            evidence = body[left:right+1] if right >= 0 else body[left:]
            entities.append(dict(name=name,type=kind,evidence=evidence))
        typed.append(dict(chunk_id=cid,entities=entities))
        cross = start != end
        audits.append(dict(chunk_id=cid,candidate_id=spec['candidate'],doc=SOURCE,
            chapter=spec['section'].split(' / ')[0],section=spec['section'],
            pdf_start=start,pdf_end=end,cross_page=cross,printed_start=start-14,printed_end=end-14,
            page_null_reason=None,pdf_sha256=PDF_SHA256,
            section_evidence=[dict(heading=component,pdf_page=max(n for n,p in pages.items()
                if n<=start and any(b.get('type')=='title' and compact(block_text(b))==compact(component)
                for b in p['para_blocks']))) for component in spec['section'].split(' / ')],
            source_selection=dict(mineru_file=SOURCES[0 if spec['page']<401 else 1][0],
                mineru_sha256=SOURCES[0 if spec['page']<401 else 1][2],
                para_page=spec['page'],para_block=spec['block'],spans=spans,
                join='blank_line' if len(parts)>1 else 'none'),
            full_text_physical_match=len(parts)==1,all_selected_spans_physical_match=True,
            text_sha256=hashlib.sha256(body.encode()).hexdigest(),
            start_anchor=parts[0][:36],end_anchor=parts[-1][-36:],
            source_location='PDF正文段落；按首尾锚点及逐段选取范围回查，印刷页仅为辅助对照。',
            context_chunk_ids=spec['context'],notes=spec['note'],
            visual_review=dict(date='2026-10-10',reviewer='Codex',reviewer_kind='agent_visual_review',
                method='原始PDF整页图像逐条视觉核对，并以preproc_blocks独立验证物理页；非仅OCR段落页码推断',
                text='pass',section='pass',page_bounds='pass',citation='pass',
                cross_page='pass' if cross else 'not_applicable'),
            human_confirmed=False,human_acceptance='pending'))
    return chunks,typed,audits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--raw-dir',type=Path)
    args = parser.parse_args()
    batches = build(args.raw_dir)
    paths = [ROOT/'data/processed/text_chunks_sizheng_v5.jsonl',DELIVERY/'entity_types.jsonl',DELIVERY/'citation_audit.jsonl']
    if args.write:
        if any(p.exists() for p in paths):
            raise SystemExit('Refusing to overwrite existing files.')
        for path,rows in zip(paths,batches):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x',encoding='utf-8',newline='\n') as out:
                for row in rows: out.write(json.dumps(row,ensure_ascii=False)+'\n')
    for row,audit in zip(batches[0],batches[2]):
        print(row['id'],audit['candidate_id'],len(row['text']),audit['pdf_start'],audit['pdf_end'],row['title'])
    print('Created candidates.' if args.write else 'Read-only reconstruction; no writes.')


if __name__ == '__main__':
    main()
