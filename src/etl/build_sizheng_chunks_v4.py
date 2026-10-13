"""Curated batch 02. Default is read-only; --write creates new files only.

Selections and visual page bounds below were reviewed against the original PDF.
Never derive a physical start page from a merged MinerU paragraph's page index.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DELIVERY = ROOT / 'team_deliverables/lizhuoyang/2026-09-courseware-chunks/batch02'
MINERU = ROOT / 'data/raw/MinerU_中国共产党思想政治教育史 __20260615145108.json'
SOURCE = '中国共产党思想政治教育史'
SOURCE_SHA256 = 'cb494527f5a3e84873e522ecdd8289938fe9530a5be1f7e24501631651b24f94'
PDF_SHA256 = 'e04a86c9564bbdf598ebeb91a15a526b49a4e8aaa91acdb5e2892432a0abae13'
CH8 = '第八章 历史性伟大转折和改革开放起步阶段思想政治教育的拨乱反正'
CH9 = '第九章 开创社会主义现代化建设新局面进程中思想政治教育的全面展开'
RESTORE = CH8 + ' / 第一节 “文化大革命”结束和思想政治教育逐步恢复 / 三、党的十一大和思想政治教育组织机构的恢复重建'
PROGRESS = CH8 + ' / 第二节 真理标准的讨论与思想解放大潮的兴起 / 一、思想政治教育的局部进展'
TRUTH = CH8 + ' / 第二节 真理标准的讨论与思想解放大潮的兴起 / 二、真理标准问题的讨论'
INST = CH9 + ' / 第一节 党的十二大和群众性思想政治教育的有序展开 / 一、思想政治教育制度化建设的新进展'
CIVIC = CH9 + ' / 第一节 党的十二大和群众性思想政治教育的有序展开 / 三、开展群众性精神文明创建活动'
DOCUMENT_NAME_VARIANT = {
    'statement': '教材原文存在名称异写，当前按各页原文保留，未做规范化归一。',
    'occurrences': [
        {'pdf_page': 299, 'printed_page': 285, 'name': '《关于决定办好各级党校的决定》',
         'body_chunk_ids': ['chunk_sizheng_v4_005'], 'source_para_block': 1},
        {'pdf_page': 301, 'printed_page': 287, 'name': '《关于办好各级党校的决定》',
         'body_chunk_ids': [], 'source_para_block': 1,
         'note': '此干部培训段落未入库；同页开始的007选取下一段，不含此名称。'}],
    'same_document_assessment': '两处均指1977年10月中央办党校的决定，疑似同一文件；未核对政策原件，不能据此确定标准名称。',
    'authority_check': '已检索本地教材OCR中的名称出现位置并视觉核对299、301页；未发现可消解异写的目录、注释或独立规范依据。301页注释属于前文徐向前文章。',
    'standard_name': None,
    'normalization_applied': False,
    'citation_error': False,
}


def compact(text):
    return re.sub(r'[\s①②③④⑤⑥⑦⑧⑨⑩]+', '', text)


def block_text(block):
    return ''.join(s.get('content', '') for line in block.get('lines', [])
                   for s in line.get('spans', []) if s.get('type', 'text') == 'text')


def specs():
    rows = []
    def add(title, blocks, section, bounds, entities, tags, time=None, date=None,
            place=None, begin=None, stop=None, prefix=None):
        rows.append(dict(title=title, blocks=blocks, section=section, visual_pdf_bounds=bounds,
                         entities=entities, tags=tags, time=time, date=date, place=place,
                         begin=begin, stop=stop, remove_prefix=prefix))
    P,O,E,T,L,D,C,R = 'person','organization','event','time','place','document','concept','role'
    add('党的十一大的召开与恢复优良传统的要求', [(297,3)], RESTORE, (297,297),
        [('中国共产党第十一次全国代表大会',E),('北京',L),('1977年8月12日至18日',T)],
        ['党的十一大','优良传统'], '1977年8月12日至18日', place='北京')
    add('1976—1977年中央宣传部的恢复重建', [(298,1)], RESTORE, (298,298),
        [('中共中央政治局',O),('中央宣传部',O),('1976年10月7日',T),('1977年1月23日',T),
         ('《关于中央宣传部的任务和组织机构的请示报告》',D),('《关于成立中央宣传部的报告》',D)],
        ['宣传机构恢复','组织建设'], '1976年10月7日；1977年1月23日、同年10月31日')
    add('1980年农村基层宣传网工作制度的恢复', [(298,2)], RESTORE, (298,298),
        [('中宣部',O),('1980年1月',T),('《关于加强当前农村宣传工作的几点意见》',D),('报告员',R),('宣传员',R)],
        ['农村宣传网','基层宣传队伍'], '1980年1月', stop='1981年11月')
    add('1981年厂矿企业宣传网的组织要求', [(298,2)], RESTORE, (298,299),
        [('中宣部',O),('国家经委',O),('1981年11月',T),('《关于试行厂矿企业党的宣传工作条例的通知》',D)],
        ['企业宣传网','宣传工作制度'], '1981年11月', begin='1981年11月', stop='宣传思想工作机构的恢复和建立')
    add('1977年中共中央关于办好各级党校的决定', [(299,1)], RESTORE, (299,299),
        [('中共中央',O),('1977年10月5日',T),('《关于决定办好各级党校的决定》',D),('党校',O)],
        ['党校恢复','干部教育'], '1977年10月5日', date='1977-10-05')
    add('叶剑英在中央党校开学典礼上阐述理论联系实际', [(299,2)], RESTORE, (299,299),
        [('叶剑英',P),('中央党校',O),('开学典礼',E),('1977年10月9日',T),('理论联系实际',C)],
        ['党校开学','理论联系实际'], '1977年10月9日', date='1977-10-09')
    add('邓小平推动纠正教育战线的“两个估计”', [(301,2)], PROGRESS, (301,302),
        [('邓小平',P),('教育部',O),('科学和教育工作座谈会',E),('1977年7月',T),('“两个估计”',C)],
        ['教育拨乱反正','尊重知识人才'], '1977年7月、8月4日至8日、9月19日；背景文件为1971年', prefix='第三，')
    add('1977年恢复高考的招生政策与实施', [(303,1)], PROGRESS, (303,303),
        [('全国高等学校招生工作会议',E),('北京',L),('教育部',O),('国务院',O),('1977年12月',T),
         ('《关于1977年高等学校招生工作意见》',D)],
        ['恢复高考','招生制度'], '1977年8月13日至9月25日；同年10月、12月', place='北京',
        prefix='第五，恢复了高等学校招生考试制度。', stop='1978年4月22日')
    add('1978年全国教育工作会议与邓小平的教育要求', [(303,1)], PROGRESS, (303,303),
        [('邓小平',P),('全国教育工作会议',E),('北京',L),('1978年4月22日至5月16日',T)],
        ['教育工作会议','教育质量'], '1978年4月22日至5月16日', place='北京', begin='1978年4月22日')
    add('1978年武汉文科教学座谈会与高校理论课程恢复', [(303,2)], PROGRESS, (303,304),
        [('邓小平',P),('教育部',O),('高等学校文科教学工作座谈会',E),('武汉',L),('1978年6月8日至29日',T)],
        ['高校理论课程','文科教学'], '1978年6月8日至29日', place='武汉', prefix='第六，重新开设马克思主义理论课程。')
    add('胡耀邦提出党史研究的两条原则', [(304,3)], TRUTH, (304,304),
        [('胡耀邦',P),('中央党校',O),('1977年5月',T),('1977年底',T),('实事求是',C)],
        ['党史研究','真理标准讨论'], '1977年5月；1977年底')
    add('《实践是检验真理的唯一标准》的发表与转载', [(305,0)], TRUTH, (305,305),
        [('胡福明',P),('南京大学',O),('中央党校',O),('新华社',O),('1978年5月9日',T),
         ('《理论动态》',D),('《光明日报》',D),('《实践是检验真理的唯一标准》',D)],
        ['真理标准文章','报刊传播'], '1978年5月9日；同月11日')
    add('邓小平在全军政治工作会议上支持真理标准讨论', [(305,1)], TRUTH, (305,305),
        [('邓小平',P),('全军政治工作会议',E),('1978年6月2日',T),('《实践是检验真理的唯一标准》',D)],
        ['真理标准讨论','实事求是'], '1978年6月2日', date='1978-06-02')
    add('罗瑞卿主持起草的真理标准评论及其论点', [(305,2)], TRUTH, (305,306),
        [('罗瑞卿',P),('1978年6月24日',T),('《人民日报》',D),('《解放军报》',D),('《马克思主义的一个最基本的原则》',D)],
        ['真理标准讨论','理论评论'], '1978年6月24日', date='1978-06-24', begin='1978年6月24日')
    add('十二大党章对思想政治教育的规定', [(326,1)], INST, (326,326),
        [('党的十二大',E),('1982年9月6日',T),('党章',D),('社会主义精神文明',C)],
        ['十二大党章','制度建设'], '1982年9月6日', date='1982-09-06', stop='按照党的十二大关于')
    add('1982年宪法对思想政治教育任务的规定', [(327,1)], INST, (327,327),
        [('第五届全国人民代表大会五次会议',E),('1982年12月4日',T),('《中华人民共和国宪法》',D),('社会主义精神文明',C)],
        ['1982年宪法','思想政治教育制度'], '1982年12月4日', date='1982-12-04')
    add('1983年加强党员教育工作的组织责任', [(327,2),(328,0)], INST, (327,328),
        [('中共中央',O),('1983年2月14日',T),('《关于加强党员教育工作的通知》',D),('组织员制度',C)],
        ['党员教育','组织责任'], '1983年2月14日', date='1983-02-14', stop='1983年10月11日')
    add('1983年全国职工思想政治工作领导体系建设', [(328,1)], INST, (328,329),
        [('中共中央',O),('中央宣传部',O),('国家经委',O),('全国总工会',O),('全国职工思想政治工作领导小组',O),
         ('1983年7月1日',T),('《国营企业职工思想政治工作纲要（试行）》',D)],
        ['职工思想政治工作','领导体制'], '1983年7月1日', date='1983-07-01', begin='为协调各有关方面的力量')
    add('1981年“五讲四美”文明礼貌活动的倡议与启动', [(338,2)], CIVIC+' / （一）开展文明礼貌活动', (338,338),
        [('全国总工会',O),('共青团中央',O),('全国妇联',O),('1981年2月25日',T),('《关于开展文明礼貌活动的倡议》',D),('“五讲四美”',E)],
        ['文明礼貌活动','五讲四美'], '1981年2月25日、2月28日、3月', stop='1981年6月')
    add('“全民文明礼貌月”的提出与确定', [(338,2)], CIVIC+' / （一）开展文明礼貌活动', (338,338),
        [('第五届全国人大四次会议',E),('中央宣传部',O),('中央书记处',O),('1982年',T),('“全民文明礼貌月”',E)],
        ['全民文明礼貌月','群众活动'], '1981年11月30日至12月13日会议；1982年起每年3月', begin='1981年11月30日')
    add('1982年“五讲四美”活动的经常化与制度化', [(338,4)], CIVIC+' / （二）开展“五讲四美三热爱”活动', (338,339),
        [('中共中央办公厅',O),('中央宣传部',O),('共青团中央',O),('1982年2月14日',T),('《关于深入开展“五讲四美”活动的报告》',D),('“五讲四美”活动',E)],
        ['五讲四美','活动制度化'], '1982年2月14日、4月26日至5月5日、5月28日')
    add('1983年“五讲四美三热爱”活动的统一组织', [(339,1)], CIVIC+' / （二）开展“五讲四美三热爱”活动', (339,339),
        [('中央宣传部',O),('文化部',O),('中国科协',O),('中央“五讲四美三热爱”活动委员会',O),
         ('1983年1月31日',T),('1983年3月30日',T),('“三热爱”',C)],
        ['五讲四美三热爱','组织建设'], '1983年1月31日、3月30日', stop='1983年7月2日')
    add('1984年三明会议推广文明城市建设经验', [(339,3)], CIVIC+' / （三）创建文明单位和文明城市活动', (340,340),
        [('中央“五讲四美三热爱”活动委员会',O),('全国“五讲四美三热爱”活动工作会议',E),('福建省三明市',L),('1984年6月11日至18日',T)],
        ['三明会议','文明城市'], '1984年6月11日至18日', place='福建省三明市', begin='1984年6月11日', stop='1985年1月11日')
    add('群众性精神文明创建中的先进人物与学习号召', [(340,1)], CIVIC+' / （三）创建文明单位和文明城市活动', (340,341),
        [('赵春娥',P),('张华',P),('蒋筑英',P),('罗健夫',P),('李俊甲',P),('朱伯儒',P),('张海迪',P),('“五讲四美三热爱”活动',E)],
        ['先进人物','精神文明创建'])
    return rows


def build():
    assert hashlib.sha256(MINERU.read_bytes()).hexdigest() == SOURCE_SHA256
    pages = json.loads(MINERU.read_text(encoding='utf-8'))['pdf_info']
    fragments, page_map = [], []
    for page in pages:
        for block in page['preproc_blocks']:
            if block.get('type') == 'text':
                part = compact(block_text(block))
                fragments.append(part)
                page_map.extend([page['page_idx']+201]*len(part))
    stream = ''.join(fragments)
    chunks, typed, audits = [], [], []
    for i, spec in enumerate(specs(), 1):
        body = compact(''.join(block_text(pages[p-201]['para_blocks'][b]) for p,b in spec['blocks']))
        if spec['remove_prefix']:
            assert body.startswith(spec['remove_prefix'])
            body = body[len(spec['remove_prefix']):]
        for key in ('begin','stop'):
            marker = spec[key]
            if marker:
                assert body.count(marker) == 1, (i,key,marker)
                pos = body.index(marker)
                body = body[pos:] if key == 'begin' else body[:pos]
        assert stream.count(body) == 1, (i,'body location not unique')
        offset = stream.index(body)
        start,end = page_map[offset],page_map[offset+len(body)-1]
        assert (start,end) == spec['visual_pdf_bounds'], (i,start,end)
        cid = f'chunk_sizheng_v4_{i:03}'
        chunks.append(dict(id=cid, source=SOURCE, source_type='textbook', title=spec['title'], text=body,
            chunk_type='textbook_chunk', topic=spec['title'],
            time=dict(start=spec['date'],end=None,display=spec['time']),
            location=dict(name=spec['place'],lng=None,lat=None,coord_sys=None),
            entities=[name for name,kind in spec['entities']],
            tags=['教材切片','思政知识库v4','batch02',*spec['tags']],
            citation=dict(doc=SOURCE,section=spec['section'],page=start)))
        entities = []
        for name,kind in spec['entities']:
            pos = body.index(name)
            left = max(body.rfind('。',0,pos),body.rfind('；',0,pos))+1
            right = body.find('。',pos+len(name))
            evidence = body[left:right+1] if right >= 0 else body[left:]
            entities.append(dict(name=name,type=kind,evidence=evidence))
        typed.append(dict(chunk_id=cid,entities=entities))
        audits.append(dict(chunk_id=cid, doc=SOURCE, section=spec['section'], pdf_start=start,pdf_end=end,
            printed_start=start-14,printed_end=end-14, page_null_reason=None,
            source_selection={k:spec[k] for k in ('blocks','begin','stop','remove_prefix')},
            full_text_physical_match=True, match_count=1,
            characters_by_pdf_page=dict(Counter(page_map[offset:offset+len(body)])),
            start_anchor=body[:36],end_anchor=body[-36:],
            text_sha256=hashlib.sha256(body.encode()).hexdigest(),
            visual_review=dict(method='制作阶段原PDF整页图像逐条对照；用户已确认第二批静态验收通过',
                               text='pass',section='pass',page_bounds='pass',cross_page='pass' if start!=end else 'not_applicable')))
        if cid == 'chunk_sizheng_v4_005':
            audits[-1]['document_name_variant'] = DOCUMENT_NAME_VARIANT
    return chunks,typed,audits


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    batches=build()
    paths=[ROOT/'data/processed/text_chunks_sizheng_v4.jsonl', DELIVERY/'entity_types.jsonl', DELIVERY/'citation_audit.jsonl']
    if args.write:
        if any(p.exists() for p in paths):
            raise SystemExit('Refusing to overwrite existing candidates or audit files.')
        for path,rows in zip(paths,batches):
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('x',encoding='utf-8',newline='\n') as out:
                for row in rows: out.write(json.dumps(row,ensure_ascii=False)+'\n')
    for row,audit in zip(batches[0],batches[2]):
        print(row['id'],len(row['text']),f'{audit["pdf_start"]}-{audit["pdf_end"]}',row['title'])
    print('Created new candidates.' if args.write else 'Read-only reconstruction completed; no files written.')


if __name__ == '__main__':
    main()
