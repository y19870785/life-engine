"""Render an inspected, public probe transcript; no model-generated screenshot content."""
import argparse
import html
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('transcript', type=Path)
    args = parser.parse_args()
    data = json.loads(args.transcript.read_text(encoding='utf-8-sig'))
    assert data['profile_files_unchanged'] and data['llm_requested']
    assert not data['live_gateway_verified']
    steps = {item['step']: item['result'] for item in data['transcript']}
    assert steps['llm_final_state']['mode'] == 'soul'
    assert steps['llm_memory_verified']['scope'] == 'persona'
    panels = [
        ('01 · 身份区分', '你现在是谁？', steps['identity']),
        ('02 · 世界书进入剧情', '星港的月塔里有什么？', steps['lore']),
        ('03 · 实际数据库核验', '模型调用 remember 后读取 SQLite',
         json.dumps(steps['llm_memory_verified'], ensure_ascii=False, indent=2)),
        ('04 · 退出后恢复', '你现在是谁，还在扮演吗？', steps['soul_identity']),
    ]
    cards = ''.join('<section><h2>'+html.escape(title)+'</h2><p class="query">'+html.escape(query)+
                    '</p><div class="answer">'+html.escape(answer)+'</div></section>'
                    for title, query, answer in panels)
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<title>Life Engine · Hermes 隔离验收</title><style>
*{box-sizing:border-box}body{margin:0;background:#eef2f3;color:#182a35;font-family:"Microsoft YaHei",sans-serif}
main{max-width:1260px;margin:auto;padding:40px 44px}header{margin-bottom:24px}
.eyebrow{color:#14776d;font-size:15px;letter-spacing:2px}h1{font-size:36px;margin:10px 0}
.subtitle{font-size:17px;color:#556b77;line-height:1.7}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
section{background:#fff;border:1px solid #d7e1e5;border-radius:16px;padding:24px}
h2{margin:0 0 16px;font-size:21px}.query{color:#476677;background:#f0f6f7;padding:10px 12px;border-radius:7px;font-size:15px}
.answer{white-space:pre-wrap;line-height:1.85;font-size:16px;overflow-wrap:anywhere}
footer{margin-top:22px;font-size:14px;color:#556b77;line-height:1.8}.badge{color:#146353;font-weight:bold}
</style><main><header><div class="eyebrow">LIFE ENGINE / v0.4 DEVELOPMENT PREVIEW</div>
<h1>角色会变，原有身份与经历会留下</h1>
<div class="subtitle">真实 Hermes v0.21.2 · 默认 Profile · deepseek-v4-flash · 2026-09-15<br>
隔离引擎数据与会话库的验收记录展示页；不是在线 Gateway 或聊天渠道截图。</div></header>
<div class="grid">'''+cards+'''</div><footer><span class="badge">已核验：persona / card_id / session_id 写入 · 最终 mode=soul · SOUL 与配置文件未变</span><br>
模型原文节选，未改写回答；完整结果见相邻 roleplay-hermes.json。虚构故事允许模型发挥，不能作为现实事实。<br>
本截图不代表长期稳定性、多会话隔离或 OpenClaw 在线联调已通过。</footer></main></html>'''
    args.transcript.with_suffix('.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    main()
