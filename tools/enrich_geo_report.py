#!/usr/bin/env python3
"""Bind GearDrop's validated UX and improvement plans into a rendered GEO report."""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import re


CSS_START = "/* GEARDROP_AUDIT_SUPPLEMENT_CSS_START */"
CSS_END = "/* GEARDROP_AUDIT_SUPPLEMENT_CSS_END */"
NAV_START = "<!-- GEARDROP_AUDIT_SUPPLEMENT_NAV_START -->"
NAV_END = "<!-- GEARDROP_AUDIT_SUPPLEMENT_NAV_END -->"
BODY_START = "<!-- GEARDROP_AUDIT_SUPPLEMENT_BODY_START -->"
BODY_END = "<!-- GEARDROP_AUDIT_SUPPLEMENT_BODY_END -->"


SUPPLEMENT_CSS = f"""{CSS_START}
.report-nav{{position:sticky;top:0;z-index:18;background:rgba(246,243,237,.96);border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}}
.report-nav .wrap{{display:flex;gap:10px;align-items:center;overflow-x:auto;padding-top:10px;padding-bottom:10px}}
.report-nav a{{white-space:nowrap;text-decoration:none;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:7px 11px;font-size:12px}}
.canonical-scores{{margin:0 0 0 auto;white-space:nowrap;font-size:12px;font-weight:800;color:var(--ink)}}
.score-card.score-block{{grid-column:1/-1}}
.score-card.decision-metric{{min-height:190px}}
.appendix-shell{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:0 24px 24px}}
.appendix-shell>summary{{font-size:18px;padding:20px 0;margin:0}}
.supplement-note{{color:var(--muted);max-width:850px}}
.supplement-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}}
.supplement-card{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px}}
.supplement-card h3{{font-size:20px;line-height:1.25;margin:8px 0}}
.supplement-card p{{margin:7px 0}}
.supplement-meta{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}}
.supplement-meta span{{font-size:11px;color:var(--muted);background:#f0eee8;border-radius:99px;padding:4px 8px}}
.validation-layers,.validation-rules{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:16px 0 24px}}
.validation-rules{{grid-template-columns:repeat(4,minmax(0,1fr))}}
.validation-layer,.validation-rule{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px}}
.validation-layer strong,.validation-rule strong{{display:block;margin-bottom:5px}}
.validation-layer p,.validation-rule p{{font-size:13px;color:var(--muted);margin:0}}
.workstream-list{{display:grid;gap:14px}}
.workstream{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px}}
.workstream h3{{margin:5px 0 12px;font-size:21px}}
.workstream dl{{display:grid;grid-template-columns:140px 1fr;gap:7px 14px;margin:0}}
.workstream dt{{font-size:12px;color:var(--muted);font-weight:800}}
.workstream dd{{margin:0}}
@media(max-width:850px){{.canonical-scores{{display:none}}.supplement-grid,.validation-layers,.validation-rules{{grid-template-columns:1fr}}.workstream dl{{grid-template-columns:1fr}}.workstream dd{{margin-bottom:8px}}}}
@media print{{.report-nav{{display:none}}}}
{CSS_END}"""


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def text(value: object) -> str:
    return escape("" if value is None else str(value), quote=True)


def remove_marked(value: str, start: str, end: str) -> str:
    return re.sub(re.escape(start) + r"[\s\S]*?" + re.escape(end), "", value)


def render_nav(audit: dict) -> str:
    scores = audit.get("scores", {})
    seo = scores.get("seo", {}).get("score", "—")
    geo = scores.get("geo", {}).get("score", "—")
    return f"""{NAV_START}
<nav class="report-nav" aria-label="报告章节"><div class="wrap">
  <a href="#decision-summary">结论</a>
  <a href="#observed-visibility">AI 能见度</a>
  <a href="#website-experience">网站体验</a>
  <a href="#priority-roadmap">路线</a>
  <a href="#improvement-validation">改进验证</a>
  <a href="#evidence-sources">证据</a>
  <p class="canonical-scores">SEO {text(seo)} · GEO {text(geo)}</p>
</div></nav>
{NAV_END}"""


def render_ux(ux: dict) -> str:
    cards: list[str] = []
    for finding in ux.get("findings", []):
        if not isinstance(finding, dict):
            continue
        cards.append(f"""
<article class="supplement-card" data-ux-finding="{text(finding.get('id'))}">
  <div class="supplement-meta"><span>{text(finding.get('id'))}</span><span>{text(finding.get('dimension'))}</span><span>{text(finding.get('severity'))}</span></div>
  <h3>{text(finding.get('title'))}</h3>
  <p>{text(finding.get('summary'))}</p>
  <p><strong>业务影响：</strong>{text(finding.get('business_impact'))}</p>
  <p><strong>完成测试：</strong>{text(finding.get('completion_test'))}</p>
</article>""")
    verdict = ux.get("summary", {}).get("verdict", "")
    return f"""
<section class="report-section" id="website-experience"><div class="wrap">
  <div class="section-head"><div><p class="eyebrow">代表性桌面与移动走查</p><h2>网站体验</h2><p class="supplement-note">{text(verdict)} 网站体验不另外打分，也不计入 SEO 或 GEO readiness。</p></div></div>
  <div class="supplement-grid" id="ux-findings">{''.join(cards)}</div>
</div></section>"""


def render_improvement(plan: dict) -> str:
    layers = "".join(
        f'<article class="validation-layer"><strong>{text(item.get("id"))} · {text(item.get("title"))}</strong><p>{text(item.get("question"))}</p></article>'
        for item in plan.get("validation_layers", []) if isinstance(item, dict)
    )
    rules = "".join(
        f'<article class="validation-rule"><strong>{text(item.get("label"))}</strong><p>{text(item.get("definition"))}</p></article>'
        for item in plan.get("decision_rules", []) if isinstance(item, dict)
    )
    workstreams: list[str] = []
    for item in plan.get("workstreams", []):
        if not isinstance(item, dict):
            continue
        workstreams.append(f"""
<article class="workstream" data-validation-workstream="{text(item.get('id'))}">
  <div class="supplement-meta"><span>{text(item.get('id'))}</span><span>{text(item.get('priority'))}</span><span>{text(item.get('current_status'))}</span><span>{text(' + '.join(item.get('layers', [])))}</span></div>
  <h3>{text(item.get('title'))}</h3>
  <dl>
    <dt>问题</dt><dd>{text(item.get('problem'))}</dd>
    <dt>变更前基线</dt><dd>{text(item.get('baseline'))}</dd>
    <dt>交付物</dt><dd>{text(item.get('deliverable'))}</dd>
    <dt>验证方法</dt><dd>{text(item.get('validation_method'))}</dd>
    <dt>通过条件</dt><dd>{text(item.get('pass_criteria'))}</dd>
    <dt>时间</dt><dd>{text(item.get('timing'))}</dd>
    <dt>执行 / 复核</dt><dd>{text(item.get('implementer'))} / {text(item.get('validator'))}</dd>
  </dl>
</article>""")
    return f"""
<section class="report-section" id="improvement-validation"><div class="wrap">
  <div class="section-head"><div><p class="eyebrow">Implementation ≠ GEO effect ≠ business effect</p><h2>改进验证</h2><p class="supplement-note">每项改进都绑定基线、非实现者复核、通过条件与下一次复测；缺来源时保持未测量。</p></div></div>
  <h3>验证层</h3><div class="validation-layers">{layers}</div>
  <h3>判定规则</h3><div class="validation-rules">{rules}</div>
  <h3 id="validation-workstreams">持续优化工作流</h3><div class="workstream-list">{''.join(workstreams)}</div>
</div></section>"""


def shape_client_decision(report: str) -> str:
    score_index = 0

    def mark_score(match: re.Match[str]) -> str:
        nonlocal score_index
        raw_classes = match.group(1).split()
        classes = [item for item in raw_classes if item not in {"score-block", "decision-metric"}]
        classes.append("score-block" if score_index == 0 else "decision-metric")
        score_index += 1
        return f'class="{" ".join(classes)}"'

    output = re.sub(r'class="([^"]*\bscore-card\b[^"]*)"', mark_score, report)

    translations = {
        '<span class="pill area">Both</span>': '<span class="pill area">SEO + GEO</span>',
        '<span class="pill sev critical">critical</span>': '<span class="pill sev critical">严重</span>',
        '<span class="pill sev high">high</span>': '<span class="pill sev high">高</span>',
        '<span class="pill sev medium">medium</span>': '<span class="pill sev medium">中</span>',
        '<span class="pill">owned</span>': '<span class="pill">自有来源</span>',
        '<span class="pill">tool</span>': '<span class="pill">工具验证</span>',
        '<span class="pill">first_party_data</span>': '<span class="pill">第一方数据</span>',
        '<span class="pill">independent</span>': '<span class="pill">独立来源</span>',
    }
    for old, new in translations.items():
        output = output.replace(old, new)

    evidence_pattern = re.compile(
        r'(<section class="report-section" id="evidence-sources"><div class="wrap">)'
        r'(?!<details class="appendix-shell" open>)([\s\S]*?)(</div></section>)'
    )
    output = evidence_pattern.sub(
        r'\1<details class="appendix-shell" open><summary>证据附录</summary>\2</details>\3',
        output,
        count=1,
    )
    return output


def enrich(report: str, audit: dict, ux: dict, improvement: dict) -> str:
    output = remove_marked(report, CSS_START, CSS_END)
    output = remove_marked(output, NAV_START, NAV_END)
    output = remove_marked(output, BODY_START, BODY_END)
    output = re.sub(r"\n{2,}(?=</style>)", "\n", output, count=1)
    output = re.sub(r"</header>\s*<main>", "</header><main>", output, count=1)
    output = output.replace("</style>", SUPPLEMENT_CSS + "\n</style>", 1)

    replacements = {
        '<section class="report-section"><div class="wrap"><div class="section-head"><h2>执行摘要</h2>': '<section class="report-section" id="decision-summary"><div class="wrap"><div class="section-head"><h2>执行摘要</h2>',
        '<section class="report-section"><div class="wrap"><div class="section-head"><h2>AI 可见性实测</h2>': '<section class="report-section" id="observed-visibility"><div class="wrap"><div class="section-head"><h2>AI 可见性实测</h2>',
        '<section class="report-section"><div class="wrap"><div class="section-head"><h2>90 天优先路线</h2>': '<section class="report-section" id="priority-roadmap"><div class="wrap"><div class="section-head"><h2>90 天优先路线</h2>',
        '<section class="report-section"><div class="wrap"><div class="section-head"><h2>证据与来源</h2>': '<section class="report-section" id="evidence-sources"><div class="wrap"><div class="section-head"><h2>证据与来源</h2>',
    }
    for old, new in replacements.items():
        output = output.replace(old, new, 1)

    nav = render_nav(audit)
    if "</header>" not in output:
        raise ValueError("rendered report is missing the header anchor")
    output = output.replace("</header>", f"</header>\n{nav}\n", 1)
    supplement = f"{BODY_START}\n{render_ux(ux)}\n{render_improvement(improvement)}\n{BODY_END}\n"
    evidence_anchor = '<section class="report-section" id="evidence-sources">'
    if evidence_anchor not in output:
        raise ValueError("rendered report is missing the evidence section anchor")
    output = re.sub(
        r"[ \t\r\n]+(?=" + re.escape(evidence_anchor) + r")",
        "\n",
        output,
        count=1,
    )
    output = output.replace(evidence_anchor, supplement + evidence_anchor, 1)
    return shape_client_decision(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--website-experience", type=Path, required=True)
    parser.add_argument("--improvement-validation", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    original = args.report.read_text(encoding="utf-8")
    enriched = enrich(
        original,
        load_object(args.audit),
        load_object(args.website_experience),
        load_object(args.improvement_validation),
    )
    if args.check:
        if enriched != original:
            print(f"stale report supplement: {args.report}")
            return 1
        print(f"report supplement is current: {args.report}")
        return 0
    args.report.write_text(enriched, encoding="utf-8")
    print(f"enriched report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
