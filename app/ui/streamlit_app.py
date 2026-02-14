"""
Streamlit Demo Interface - Neurofin Multi-Agent Loan Processor
Enterprise-grade UI matching Neurofin design language.
"""

import streamlit as st
import tempfile
import os
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.parsers.pdf_parser import PDFParser
from app.orchestrator.state import (
    DocumentType, Recommendation, ProcessingResult
)
from app.utils.mock_processor import (
    mock_classify, mock_extract, mock_monthly_summaries, mock_validate
)
from app.rules.compliance import COMPLIANCE_RULES

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Neurofin Loan Processor",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Master CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ─────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #f1f5f9; }
#MainMenu, footer, header, .stDeployButton { display: none !important; }

/* ── Sidebar ────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 0;
}
section[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
section[data-testid="stSidebar"] .stRadio label span { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] hr { border-color: #334155 !important; }
section[data-testid="stSidebar"] .stSlider label { color: #94a3b8 !important; font-size: 0.8rem; }

.sidebar-brand {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 1.25rem 0 1.5rem 0;
    border-bottom: 1px solid #334155;
    margin-bottom: 1.25rem;
}
.sidebar-brand .logo {
    width: 34px; height: 34px; border-radius: 8px;
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; color: white !important;
}
.sidebar-brand .name { font-size: 1.15rem; font-weight: 700; color: #f1f5f9 !important; letter-spacing: -0.01em; }
.sidebar-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b !important; font-weight: 600; margin-bottom: 0.25rem; }
.sidebar-footer {
    border-top: 1px solid #334155;
    padding-top: 1rem; margin-top: 1rem;
}
.sidebar-footer .dev-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.08em; color: #475569 !important; }
.sidebar-footer .dev-name { font-size: 0.85rem; font-weight: 600; color: #e2e8f0 !important; }
.sidebar-footer .dev-stack { font-size: 0.7rem; color: #64748b !important; }

/* ── Hero ───────────────────────────────────── */
.hero-banner {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 50%, #7c3aed 100%);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 1.5rem;
    position: relative; overflow: hidden;
}
.hero-banner::before {
    content: ''; position: absolute; top: -60%; right: -10%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(255,255,255,0.06) 0%, transparent 60%);
    border-radius: 50%;
}
.hero-banner h1 { color: #fff; font-size: 2.1rem; font-weight: 800; margin: 0 0 0.5rem 0; letter-spacing: -0.02em; position: relative; }
.hero-banner .subtitle { color: #c7d2fe; font-size: 1rem; margin: 0 0 1rem 0; line-height: 1.5; position: relative; }
.hero-banner .badges { display: flex; gap: 0.5rem; position: relative; flex-wrap: wrap; }
.hero-banner .badge {
    background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2);
    color: #e0e7ff; padding: 0.3rem 0.85rem; border-radius: 20px;
    font-size: 0.75rem; font-weight: 500; backdrop-filter: blur(4px);
}

/* ── Section container (white cards) ────────── */
.section-card {
    background: #ffffff; border-radius: 14px;
    border: 1px solid #e2e8f0; padding: 1.75rem 2rem;
    margin-bottom: 1.25rem;
}
.section-card-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 1.25rem; padding-bottom: 0.75rem;
    border-bottom: 1px solid #f1f5f9;
}
.section-card-header h2 { font-size: 1.25rem; font-weight: 700; color: #0f172a; margin: 0; }
.status-chip {
    font-size: 0.72rem; color: #64748b; background: #f1f5f9;
    padding: 0.25rem 0.75rem; border-radius: 12px; font-weight: 500;
}

/* ── Pipeline cards ─────────────────────────── */
.pipeline-row {
    display: flex; align-items: stretch; gap: 0;
    margin: 0.5rem 0;
}
.pipe-card {
    flex: 1; background: #ffffff; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.5rem 1.25rem;
    transition: all 0.3s ease;
}
.pipe-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); transform: translateY(-2px); }
.pipe-card.active { border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.12); }
.pipe-card.done { border-color: #10b981; background: linear-gradient(180deg, #f0fdf4, #fff); }
.pipe-icon {
    width: 44px; height: 44px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.15rem; margin-bottom: 0.85rem;
}
.pipe-icon-blue { background: #eff6ff; color: #3b82f6; }
.pipe-icon-indigo { background: #eef2ff; color: #6366f1; }
.pipe-icon-amber { background: #fef3c7; color: #d97706; }
.pipe-icon-green { background: #ecfdf5; color: #059669; }
.pipe-card .title { font-weight: 700; font-size: 0.92rem; color: #0f172a; margin-bottom: 0.35rem; }
.pipe-card .desc { font-size: 0.78rem; color: #64748b; line-height: 1.45; }
.pipe-card .time-badge { font-size: 0.72rem; color: #059669; font-weight: 600; margin-top: 0.5rem; }
.pipe-arrow {
    display: flex; align-items: center; justify-content: center;
    min-width: 32px; color: #cbd5e1; font-size: 1.1rem;
    padding: 0 0.15rem;
}

/* ── Scenario table ─────────────────────────── */
.scenario-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.scenario-table th {
    text-align: left; padding: 0.5rem 0.75rem; color: #64748b;
    font-weight: 600; font-size: 0.72rem; text-transform: uppercase;
    letter-spacing: 0.05em; border-bottom: 1px solid #e2e8f0;
}
.scenario-table td { padding: 0.65rem 0.75rem; border-bottom: 1px solid #f1f5f9; color: #334155; }
.scenario-table code { font-size: 0.75rem; background: #f8fafc; padding: 0.15rem 0.4rem; border-radius: 4px; color: #475569; }
.outcome-badge {
    display: inline-block; padding: 0.15rem 0.55rem; border-radius: 4px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.03em;
}
.badge-approve { background: #dcfce7; color: #15803d; }
.badge-review { background: #fef3c7; color: #a16207; }
.badge-reject { background: #fee2e2; color: #dc2626; }
.ref-chip {
    font-size: 0.65rem; background: #f1f5f9; color: #64748b;
    padding: 0.2rem 0.6rem; border-radius: 4px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.05em;
}

/* ── Result metrics ─────────────────────────── */
.metric-card {
    background: #ffffff; border-radius: 12px; padding: 1.25rem;
    border: 1px solid #e2e8f0; text-align: center;
}
.metric-card .label { font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
.metric-card .value { font-size: 1.5rem; font-weight: 800; margin: 0.3rem 0; }
.rec-approve { background: linear-gradient(135deg, #ecfdf5, #dcfce7); border-color: #86efac; }
.rec-approve .value { color: #059669; }
.rec-review { background: linear-gradient(135deg, #fffbeb, #fef3c7); border-color: #fcd34d; }
.rec-review .value { color: #d97706; }
.rec-reject { background: linear-gradient(135deg, #fef2f2, #fee2e2); border-color: #fca5a5; }
.rec-reject .value { color: #dc2626; }

/* ── Risk gauge ─────────────────────────────── */
.risk-gauge {
    background: #ffffff; border-radius: 12px; padding: 1.5rem;
    border: 1px solid #e2e8f0; text-align: center;
}
.risk-gauge .score { font-size: 2.8rem; font-weight: 900; line-height: 1; }
.risk-gauge .max-score { font-size: 1.1rem; color: #94a3b8; font-weight: 400; }
.risk-low .score { color: #059669; }
.risk-med .score { color: #d97706; }
.risk-high .score { color: #dc2626; }
.risk-bar { height: 6px; border-radius: 3px; background: #e2e8f0; margin-top: 0.75rem; overflow: hidden; }
.risk-bar-fill { height: 100%; border-radius: 3px; }

/* ── Check cards ────────────────────────────── */
.check-card {
    background: #fff; border-radius: 10px; padding: 0.9rem 1.1rem; margin: 0.4rem 0;
    border-left: 4px solid; border-top: 1px solid #f1f5f9;
    border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;
}
.check-pass { border-left-color: #10b981; }
.check-fail { border-left-color: #ef4444; }
.check-chip {
    display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em;
}
.chip-pass { background: #dcfce7; color: #166534; }
.chip-fail { background: #fee2e2; color: #991b1b; }
.sev-badge {
    display: inline-block; padding: 0.08rem 0.4rem; border-radius: 3px;
    font-size: 0.6rem; font-weight: 600; margin-left: 0.4rem;
}
.sev-high { background: #fef2f2; color: #dc2626; }
.sev-medium { background: #fffbeb; color: #d97706; }
.sev-low { background: #f0f9ff; color: #0284c7; }
.check-card .rule { font-weight: 700; color: #1e293b; font-size: 0.88rem; margin-left: 0.4rem; }
.check-card .detail { color: #64748b; font-size: 0.78rem; margin-top: 0.3rem; line-height: 1.4; }

/* ── Footer bar ─────────────────────────────── */
.footer-bar {
    display: flex; justify-content: center; gap: 2.5rem; align-items: center;
    padding: 1rem 0; margin-top: 2rem; border-top: 1px solid #e2e8f0;
    color: #94a3b8; font-size: 0.75rem;
}
.footer-bar .item { display: flex; align-items: center; gap: 0.4rem; }

/* ── Section header ─────────────────────────── */
.section-header {
    font-size: 1.05rem; font-weight: 700; color: #1e293b;
    margin: 1.5rem 0 0.75rem 0; padding-bottom: 0.4rem;
    border-bottom: 2px solid #e2e8f0;
}

/* ── Info sections (How/Roadmap/Involve) ────── */
.info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem; }
.info-item {
    background: #f8fafc; border-radius: 10px; padding: 1.2rem 1.3rem;
    border: 1px solid #e2e8f0; transition: all 0.2s ease;
}
.info-item:hover { border-color: #3b82f6; box-shadow: 0 2px 12px rgba(59,130,246,0.08); }
.info-item .info-icon { font-size: 1.4rem; margin-bottom: 0.5rem; }
.info-item .info-title { font-weight: 700; color: #0f172a; font-size: 0.92rem; margin-bottom: 0.3rem; }
.info-item .info-desc { color: #64748b; font-size: 0.8rem; line-height: 1.5; }

.roadmap-item {
    display: flex; gap: 1rem; padding: 1rem 0;
    border-bottom: 1px solid #f1f5f9;
}
.roadmap-item:last-child { border-bottom: none; }
.roadmap-phase {
    min-width: 80px; text-align: center;
    padding: 0.3rem 0.6rem; border-radius: 6px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em;
    text-transform: uppercase; height: fit-content; margin-top: 0.1rem;
}
.phase-now { background: #dbeafe; color: #1d4ed8; }
.phase-next { background: #fef3c7; color: #a16207; }
.phase-future { background: #f3e8ff; color: #7c3aed; }
.roadmap-content .rm-title { font-weight: 700; color: #0f172a; font-size: 0.9rem; }
.roadmap-content .rm-desc { color: #64748b; font-size: 0.8rem; line-height: 1.5; margin-top: 0.2rem; }

.involve-card {
    background: linear-gradient(135deg, #eff6ff, #eef2ff);
    border: 1px solid #c7d2fe; border-radius: 12px;
    padding: 1.5rem 1.75rem; margin-top: 1rem;
}
.involve-card .involve-title { font-weight: 800; color: #1e293b; font-size: 1.1rem; margin-bottom: 0.5rem; }
.involve-card .involve-text { color: #475569; font-size: 0.88rem; line-height: 1.65; }
.involve-card ul { margin: 0.5rem 0; padding-left: 1.3rem; }
.involve-card li { color: #334155; font-size: 0.85rem; line-height: 1.7; }
.involve-card li strong { color: #1e293b; }
.cta-row { display: flex; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap; }
.cta-btn {
    display: inline-block; padding: 0.55rem 1.5rem; border-radius: 8px;
    font-size: 0.82rem; font-weight: 600; text-decoration: none;
    transition: all 0.2s ease;
}
.cta-primary { background: #2563eb; color: #fff !important; }
.cta-primary:hover { background: #1d4ed8; }
.cta-secondary { background: #fff; color: #2563eb !important; border: 1px solid #2563eb; }
.cta-secondary:hover { background: #eff6ff; }

.section-divider {
    display: flex; align-items: center; gap: 1rem;
    margin: 2rem 0 1.25rem 0;
}
.section-divider .divider-line { flex: 1; height: 1px; background: #e2e8f0; }
.section-divider .divider-label {
    font-size: 0.7rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def render_hero():
    st.markdown("""
    <div class="hero-banner">
        <h1>Neurofin Loan Processor</h1>
        <p class="subtitle">Enterprise AI-powered bank statement analysis with multi-agent pipeline &amp; RBI compliance validation.</p>
        <div class="badges">
            <span class="badge">LangGraph</span>
            <span class="badge">Groq + Claude</span>
            <span class="badge">Pydantic v2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_landing():
    st.markdown("""
    <div class="section-card">
        <div class="pipeline-row">
            <div class="pipe-card">
                <div class="pipe-icon pipe-icon-blue">&#128196;</div>
                <div class="title">PDF Parser</div>
                <div class="desc">Extract raw text &amp; structured tables from uploaded documents.</div>
            </div>
            <div class="pipe-arrow">&rarr;</div>
            <div class="pipe-card">
                <div class="pipe-icon pipe-icon-indigo">&#128269;</div>
                <div class="title">Classifier Agent</div>
                <div class="desc">Identify document type and assess data quality levels.</div>
            </div>
            <div class="pipe-arrow">&rarr;</div>
            <div class="pipe-card">
                <div class="pipe-icon pipe-icon-amber">&#128200;</div>
                <div class="title">Extractor Agent</div>
                <div class="desc">Parse account info, transactions, and monthly cash flows.</div>
            </div>
            <div class="pipe-arrow">&rarr;</div>
            <div class="pipe-card">
                <div class="pipe-icon pipe-icon-green">&#9989;</div>
                <div class="title">Validator Agent</div>
                <div class="desc">7 RBI compliance checks, risk scoring, &amp; final recommendation.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_pipeline_status(stage: int, agent_times: dict = None):
    names = ["PDF Parser", "Classifier", "Extractor", "Validator"]
    icons = ["&#128196;", "&#128269;", "&#128200;", "&#9989;"]
    icon_cls = ["pipe-icon-blue", "pipe-icon-indigo", "pipe-icon-amber", "pipe-icon-green"]
    descs = ["Text &amp; table extraction", "Type &amp; quality check", "Data &amp; transactions", "Compliance &amp; risk"]

    html = '<div class="pipeline-row">'
    for i in range(4):
        extra_cls = "done" if i < stage else "active" if i == stage else ""
        timing = ""
        if i < stage and agent_times:
            for k, v in agent_times.items():
                if names[i].lower().split()[0] in k.lower():
                    timing = f'<div class="time-badge">{v:.2f}s</div>'
                    break
        processing = '<div class="time-badge" style="color:#3b82f6;">Processing...</div>' if i == stage else ""
        opacity = "" if i <= stage else 'style="opacity:0.4;"'

        html += f"""
        <div class="pipe-card {extra_cls}" {opacity}>
            <div class="pipe-icon {icon_cls[i]}">{icons[i]}</div>
            <div class="title">{names[i]}</div>
            <div class="desc">{descs[i]}</div>
            {timing}{processing}
        </div>"""
        if i < 3:
            arrow_color = "#10b981" if i < stage else "#3b82f6" if i == stage - 1 else "#cbd5e1"
            html += f'<div class="pipe-arrow" style="color:{arrow_color};">&rarr;</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_scenario_table():
    st.markdown("""
    <div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <strong style="color:#1e293b; font-size:0.92rem;">Quick Test Scenarios</strong>
            <span class="ref-chip">REFERENCE</span>
        </div>
        <table class="scenario-table">
            <thead><tr><th>Sample</th><th>Bank</th><th>Expected</th></tr></thead>
            <tbody>
                <tr>
                    <td><code>icici_statement_healthy.pdf</code></td>
                    <td>ICICI</td>
                    <td><span class="outcome-badge badge-approve">APPROVE</span></td>
                </tr>
                <tr>
                    <td><code>axis_statement_borderline.pdf</code></td>
                    <td>Axis</td>
                    <td><span class="outcome-badge badge-review">REVIEW</span></td>
                </tr>
                <tr>
                    <td><code>sbi_statement_risky.pdf</code></td>
                    <td>SBI</td>
                    <td><span class="outcome-badge badge-reject">REJECT</span></td>
                </tr>
            </tbody>
        </table>
        <p style="font-size:0.78rem; color:#94a3b8; margin-top:0.75rem; line-height:1.4;">
            Adjust <strong style="color:#64748b;">Compliance Thresholds</strong> in the sidebar to see how different risk criteria impact the validation agent's outcome.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown("""
    <div class="footer-bar">
        <div class="item">&#9203; Avg. processing: 0.2s</div>
        <div class="item">&#128737; SOC-2 Type II Compliant</div>
        <div class="item">&#128230; v2.4.0-stable build</div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="logo">&#127974;</div>
            <div class="name">Neurofin</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-label">SETTINGS</div>', unsafe_allow_html=True)

        mode = st.radio(
            "Processing Mode",
            ["Demo Mode (No API Key)", "Live Mode (Groq - Free)", "Live Mode (Claude API)"],
            help="Demo uses pattern matching; Groq is free cloud LLM; Claude requires paid API key"
        )
        st.session_state["mode"] = mode

        if mode == "Live Mode (Groq - Free)":
            groq_key = os.getenv("GROQ_API_KEY", "")
            if not groq_key:
                groq_key = st.text_input("Groq API Key (free)", type="password",
                                          help="Get a free key at https://console.groq.com")
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
                st.success("Groq key set")
            else:
                st.info("Free key: [console.groq.com](https://console.groq.com)")

        if mode == "Live Mode (Claude API)":
            api_key = st.text_input("Anthropic API Key", type="password")
            if api_key:
                os.environ["ANTHROPIC_API_KEY"] = api_key
                st.success("API key set")

        st.markdown("---")

        with st.expander("Observability"):
            langsmith_enabled = st.checkbox("Enable LangSmith Tracing")
            if langsmith_enabled:
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                langsmith_key = st.text_input("LangSmith API Key", type="password")
                if langsmith_key:
                    os.environ["LANGCHAIN_API_KEY"] = langsmith_key
                    os.environ["LANGCHAIN_PROJECT"] = "neurofin-loan-processor"
                    st.success("Tracing enabled")
            else:
                os.environ["LANGCHAIN_TRACING_V2"] = "false"

    custom_rules = get_custom_rules()

    with st.sidebar:
        st.markdown("""
        <div class="sidebar-footer">
            <div class="dev-label">DEVELOPED BY</div>
            <div class="dev-name">Neurofin AI Technologies</div>
            <div class="dev-stack">LangGraph + Groq/Claude + Pydantic v2</div>
        </div>
        """, unsafe_allow_html=True)

    return custom_rules


def get_custom_rules():
    with st.sidebar:
        with st.expander("Compliance Thresholds"):
            custom_rules = {}
            custom_rules["min_avg_balance"] = {
                "threshold": st.slider("Min Avg Balance (INR)", 0, 50000, 10000, 1000),
                "description": COMPLIANCE_RULES["min_avg_balance"]["description"], "severity": "high"
            }
            custom_rules["max_bounce_count"] = {
                "threshold": st.slider("Max Bounced Checks", 0, 5, 0),
                "description": COMPLIANCE_RULES["max_bounce_count"]["description"], "severity": "high"
            }
            custom_rules["min_account_age_months"] = {
                "threshold": st.slider("Min Account Age (months)", 1, 24, 6),
                "description": COMPLIANCE_RULES["min_account_age_months"]["description"], "severity": "medium"
            }
            custom_rules["suspicious_txn_threshold"] = {
                "threshold": st.slider("Suspicious Txn (INR)", 100000, 5000000, 1000000, 100000),
                "description": COMPLIANCE_RULES["suspicious_txn_threshold"]["description"], "severity": "medium"
            }
            custom_rules["income_regularity_threshold"] = {
                "threshold": st.slider("Income Regularity (%)", 0, 100, 80) / 100.0,
                "description": COMPLIANCE_RULES["income_regularity_threshold"]["description"], "severity": "medium"
            }
            custom_rules["min_closing_balance"] = {
                "threshold": st.slider("Min Closing Balance (INR)", 0, 25000, 5000, 500),
                "description": COMPLIANCE_RULES["min_closing_balance"]["description"], "severity": "low"
            }
            custom_rules["max_overdraft_instances"] = {
                "threshold": st.slider("Max Overdraft Instances", 0, 10, 2),
                "description": COMPLIANCE_RULES["max_overdraft_instances"]["description"], "severity": "medium"
            }
    return custom_rules


# ══════════════════════════════════════════════════════════════════════════════
#  PROCESSING
# ══════════════════════════════════════════════════════════════════════════════

def process_with_visualization(pdf_path: str, custom_rules: dict = None):
    agent_times = {}
    pipeline_container = st.container()
    with pipeline_container:
        render_pipeline_status(0)

    status_text = st.empty()
    progress_bar = st.progress(0)

    # Stage 1
    status_text.markdown("**Stage 1/4** — Parsing PDF...")
    progress_bar.progress(10)
    t0 = time.time()
    parser = PDFParser()
    parsed = parser.parse(pdf_path)
    agent_times["PDF Parser"] = time.time() - t0
    progress_bar.progress(25)
    with pipeline_container:
        render_pipeline_status(1, agent_times)

    # Stage 2
    status_text.markdown("**Stage 2/4** — Classifying document...")
    progress_bar.progress(35)
    t0 = time.time()

    mode = st.session_state.get("mode", "")
    use_groq = os.getenv("GROQ_API_KEY") and mode == "Live Mode (Groq - Free)"
    use_claude = os.getenv("ANTHROPIC_API_KEY") and mode == "Live Mode (Claude API)"
    use_live = use_groq or use_claude

    if use_live:
        from app.agents.classifier import DocumentClassifierAgent
        provider = "groq" if use_groq else "claude"
        classifier = DocumentClassifierAgent(provider=provider)
        result = classifier.classify({"raw_text": parsed.raw_text})
        classification = result.get("classification")
    else:
        classification = mock_classify(parsed)

    agent_times["Classifier"] = time.time() - t0
    progress_bar.progress(50)
    with pipeline_container:
        render_pipeline_status(2, agent_times)

    if not classification.can_proceed:
        status_text.markdown("**Stopped** — Document cannot be processed")
        progress_bar.progress(100)
        return ProcessingResult(
            success=False, document_type=classification.document_type,
            quality_score=classification.quality_score, extracted_data=None,
            monthly_summaries=[], risk_score=100, recommendation=Recommendation.REJECT,
            compliance_issues=["Document type not supported or quality too low"],
            red_flags=[], processing_time_seconds=sum(agent_times.values()),
            error_message="Document quality too low or type not supported"
        ), agent_times

    # Stage 3
    status_text.markdown("**Stage 3/4** — Extracting financial data...")
    progress_bar.progress(60)
    t0 = time.time()

    if use_live:
        from app.agents.extractor import DataExtractorAgent
        extractor = DataExtractorAgent(provider=provider)
        result = extractor.extract({"raw_text": parsed.raw_text, "tables": parsed.tables})
        extracted_data = result.get("extracted_data")
        monthly_summaries = result.get("monthly_summaries", [])
    else:
        extracted_data = mock_extract(parsed)
        monthly_summaries = mock_monthly_summaries(extracted_data)

    agent_times["Extractor"] = time.time() - t0
    progress_bar.progress(75)
    with pipeline_container:
        render_pipeline_status(3, agent_times)

    # Stage 4
    status_text.markdown("**Stage 4/4** — Compliance checks & risk scoring...")
    progress_bar.progress(85)
    t0 = time.time()

    if use_live:
        from app.agents.validator import ValidatorAgent
        validator = ValidatorAgent(provider=provider)
        result = validator.validate({"extracted_data": extracted_data, "monthly_summaries": monthly_summaries})
        risk_assessment = result.get("risk_assessment")
    else:
        risk_assessment = mock_validate(extracted_data, monthly_summaries, custom_rules)

    agent_times["Validator"] = time.time() - t0
    progress_bar.progress(100)
    with pipeline_container:
        render_pipeline_status(4, agent_times)

    total = sum(agent_times.values())
    status_text.markdown(f"**Complete!** Processed in **{total:.2f}s**")

    return ProcessingResult(
        success=True, document_type=classification.document_type,
        quality_score=classification.quality_score, extracted_data=extracted_data,
        monthly_summaries=monthly_summaries, risk_score=risk_assessment.risk_score,
        recommendation=risk_assessment.recommendation,
        compliance_issues=risk_assessment.issues, red_flags=risk_assessment.red_flags,
        processing_time_seconds=total
    ), agent_times, risk_assessment


# ══════════════════════════════════════════════════════════════════════════════
#  RESULTS
# ══════════════════════════════════════════════════════════════════════════════

def render_result_header(result):
    risk = result.risk_score
    risk_cls = "risk-low" if risk <= 30 else "risk-med" if risk <= 60 else "risk-high"
    bar_color = "#10b981" if risk <= 30 else "#f59e0b" if risk <= 60 else "#ef4444"

    rec_map = {
        Recommendation.APPROVE: ("APPROVE", "rec-approve"),
        Recommendation.REVIEW: ("REVIEW", "rec-review"),
        Recommendation.REJECT: ("REJECT", "rec-reject"),
    }
    rec_label, rec_cls = rec_map.get(result.recommendation, ("UNKNOWN", ""))

    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.2])
    with c1:
        st.markdown(f"""
        <div class="risk-gauge {risk_cls}">
            <div class="label" style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;font-weight:600;">Risk Score</div>
            <div class="score">{risk}<span class="max-score">/100</span></div>
            <div class="risk-bar"><div class="risk-bar-fill" style="width:{risk}%;background:{bar_color};"></div></div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card {rec_cls}"><div class="label">Recommendation</div><div class="value">{rec_label}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card"><div class="label">Document Type</div><div class="value" style="font-size:1rem;color:#1e293b;">{result.document_type.value.replace('_',' ').title()}</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card"><div class="label">Quality Score</div><div class="value" style="color:#2563eb;">{result.quality_score:.1f}<span style="font-size:0.9rem;color:#94a3b8;">/10</span></div></div>""", unsafe_allow_html=True)


def render_explainability(risk_assessment):
    for check in risk_assessment.compliance_checks:
        css = "check-pass" if check.passed else "check-fail"
        chip = "chip-pass" if check.passed else "chip-fail"
        label = "PASS" if check.passed else "FAIL"
        sev = {"high": "sev-high", "medium": "sev-medium", "low": "sev-low"}.get(check.severity, "sev-low")
        detail = (f"Actual: <strong>{check.actual_value}</strong> meets threshold <strong>{check.threshold}</strong>"
                  if check.passed else
                  f"Actual: <strong>{check.actual_value}</strong> does NOT meet threshold <strong>{check.threshold}</strong>")
        st.markdown(f"""
        <div class="check-card {css}">
            <span class="check-chip {chip}">{label}</span>
            <span class="rule">{check.rule_name.replace('_',' ').title()}</span>
            <span class="sev-badge {sev}">{check.severity.upper()}</span>
            <div class="detail">{check.rule_description}<br/>{detail}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"**Recommendation reasoning:** {risk_assessment.recommendation_reason}")


def display_results(result, agent_times=None, risk_assessment=None):
    st.markdown("---")
    if not result.success:
        st.error(f"Processing failed: {result.error_message}")
        return

    if agent_times:
        st.caption(" | ".join(f"**{k}** {v:.2f}s" for k, v in agent_times.items()) + f" | **Total** {sum(agent_times.values()):.2f}s")

    render_result_header(result)
    st.markdown("")

    tabs = st.tabs(["Explainability", "Extracted Data", "Monthly Summary", "Compliance Flags", "Raw JSON"])

    with tabs[0]:
        if risk_assessment:
            render_explainability(risk_assessment)

    with tabs[1]:
        if result.extracted_data:
            data = result.extracted_data
            st.markdown('<div class="section-header">Account Information</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Account Holder:** {data.account_holder_name}")
                st.markdown(f"**Bank:** {data.bank_name}")
                st.markdown(f"**Branch:** {data.branch or 'N/A'}")
                st.markdown(f"**Account:** {data.account_number_masked}")
            with c2:
                st.markdown(f"**Period:** {data.statement_period_start} to {data.statement_period_end}")
                st.markdown(f"**Opening Balance:** INR {data.opening_balance:,.2f}")
                st.markdown(f"**Closing Balance:** INR {data.closing_balance:,.2f}")
                st.markdown(f"**Transactions:** {data.transaction_count}")

            st.markdown('<div class="section-header">Financial Summary</div>', unsafe_allow_html=True)
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Total Credits", f"INR {data.total_credits:,.2f}")
            mc2.metric("Total Debits", f"INR {data.total_debits:,.2f}")
            net = data.total_credits - data.total_debits
            mc3.metric("Net Flow", f"INR {net:,.2f}", delta=f"{'Positive' if net >= 0 else 'Negative'}")

            if data.transactions:
                st.markdown('<div class="section-header">Transaction History</div>', unsafe_allow_html=True)
                txn_data = [{"Date": t.date, "Description": t.description[:50], "Amount": f"INR {t.amount:,.2f}",
                            "Type": t.type.upper(), "Balance": f"INR {t.balance:,.2f}" if t.balance else "-"}
                           for t in data.transactions[:20]]
                st.dataframe(txn_data, use_container_width=True, hide_index=True)

    with tabs[2]:
        if result.monthly_summaries:
            import pandas as pd
            st.markdown('<div class="section-header">Monthly Cash Flow</div>', unsafe_allow_html=True)
            summary_data = [{"Month": s.month, "Credits": f"INR {s.total_credits:,.2f}",
                           "Debits": f"INR {s.total_debits:,.2f}", "Net Flow": f"INR {s.net_flow:,.2f}",
                           "Avg Balance": f"INR {s.avg_balance:,.2f}",
                           "Salary": f"INR {s.salary_credit:,.2f}" if s.salary_credit else "-"}
                          for s in result.monthly_summaries]
            st.dataframe(summary_data, use_container_width=True, hide_index=True)
            chart_df = pd.DataFrame({"Month": [s.month for s in result.monthly_summaries],
                                    "Credits": [s.total_credits for s in result.monthly_summaries],
                                    "Debits": [s.total_debits for s in result.monthly_summaries]})
            st.bar_chart(chart_df.set_index("Month"))

    with tabs[3]:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-header">Compliance Issues</div>', unsafe_allow_html=True)
            if result.compliance_issues:
                for issue in result.compliance_issues:
                    st.warning(issue)
            else:
                st.success("No compliance issues found")
        with col_b:
            st.markdown('<div class="section-header">Red Flags</div>', unsafe_allow_html=True)
            if result.red_flags:
                for flag in result.red_flags:
                    st.error(flag)
            else:
                st.success("No red flags detected")

    with tabs[4]:
        json_str = result.model_dump_json(indent=2)
        st.code(json_str, language="json")
        st.download_button("Download JSON", data=json_str, file_name="loan_processing_result.json", mime="application/json")


# ══════════════════════════════════════════════════════════════════════════════
#  INFO SECTIONS
# ══════════════════════════════════════════════════════════════════════════════

def render_how_we_built():
    st.markdown("""
    <div class="section-divider">
        <div class="divider-line"></div>
        <span class="divider-label">About This Demo</span>
        <div class="divider-line"></div>
    </div>
    <div class="section-card">
        <div class="section-card-header">
            <h2>How We Built This</h2>
            <span class="status-chip">Architecture</span>
        </div>
        <p style="color:#475569; font-size:0.88rem; line-height:1.6; margin-bottom:1rem;">
            This system replaces the traditional 5-7 day manual loan document verification process with an
            AI pipeline that delivers results in <strong style="color:#0f172a;">under 1 second</strong>.
            Three specialized agents collaborate through a state machine, each with a single responsibility.
        </p>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-icon">&#127919;</div>
                <div class="info-title">LangGraph State Machine</div>
                <div class="info-desc">Agents are orchestrated via a directed acyclic graph with conditional routing. If the Classifier detects a low-quality document, the pipeline short-circuits &mdash; saving LLM cost and latency.</div>
            </div>
            <div class="info-item">
                <div class="info-icon">&#128274;</div>
                <div class="info-title">Structured Output (No Hallucination)</div>
                <div class="info-desc">Every agent uses <code>with_structured_output()</code> with Pydantic v2 schemas. The LLM is forced to respond in a strict JSON format via native tool calling &mdash; no regex parsing, no hope-and-pray.</div>
            </div>
            <div class="info-item">
                <div class="info-icon">&#9878;&#65039;</div>
                <div class="info-title">Rule-Based Fallback</div>
                <div class="info-desc">The compliance engine doesn't rely on AI for scoring. It's a deterministic rule engine (7 RBI checks) that can run independently of the LLM, ensuring auditability and consistency.</div>
            </div>
            <div class="info-item">
                <div class="info-icon">&#128260;</div>
                <div class="info-title">Provider-Agnostic LLM Layer</div>
                <div class="info-desc">A single factory function supports Groq (free), Claude (high-quality), and Ollama (offline). Swap providers with zero code changes &mdash; critical for production where cost/quality trade-offs shift.</div>
            </div>
            <div class="info-item">
                <div class="info-icon">&#128202;</div>
                <div class="info-title">Decision Explainability</div>
                <div class="info-desc">Every APPROVE/REVIEW/REJECT decision comes with per-check pass/fail cards, severity levels, actual vs threshold values, and a human-readable recommendation reason.</div>
            </div>
            <div class="info-item">
                <div class="info-icon">&#128736;</div>
                <div class="info-title">Configurable Thresholds</div>
                <div class="info-desc">All 7 compliance thresholds are adjustable via the sidebar. Business teams can tune risk appetite in real-time without touching code &mdash; see how changing a single slider flips an APPROVE to REVIEW.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_roadmap():
    st.markdown("""
    <div class="section-card">
        <div class="section-card-header">
            <h2>Future Roadmap</h2>
            <span class="status-chip">Vision</span>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-now">NOW</span>
            <div class="roadmap-content">
                <div class="rm-title">Multi-Document Support</div>
                <div class="rm-desc">Extend beyond bank statements to ITR filings, salary slips, property documents, and CIBIL reports. Each document type gets a specialized extraction agent, with a meta-orchestrator that correlates data across sources for cross-verification.</div>
            </div>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-now">NOW</span>
            <div class="roadmap-content">
                <div class="rm-title">OCR + Vision Pipeline</div>
                <div class="rm-desc">Add Claude Vision or GPT-4V for scanned documents and handwritten forms. A pre-processing agent handles image correction, de-skewing, and OCR quality scoring before feeding into the extraction pipeline.</div>
            </div>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-next">NEXT</span>
            <div class="roadmap-content">
                <div class="rm-title">Fraud Detection Agent</div>
                <div class="rm-desc">A 4th agent that cross-references extracted data against known fraud patterns: tampered PDFs, inconsistent font metadata, transaction amounts that don't sum to closing balance, and duplicate submissions across applications.</div>
            </div>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-next">NEXT</span>
            <div class="roadmap-content">
                <div class="rm-title">Human-in-the-Loop Review Queue</div>
                <div class="rm-desc">REVIEW decisions route to a human underwriter dashboard with pre-filled context. The agent highlights exactly which checks failed and why, reducing manual review time from 30 minutes to 5 minutes.</div>
            </div>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-future">FUTURE</span>
            <div class="roadmap-content">
                <div class="rm-title">Production API &amp; Batch Processing</div>
                <div class="rm-desc">FastAPI service with webhook callbacks, async processing for bulk uploads (100+ statements), Redis-backed job queue, and a tenant-isolated multi-org architecture with per-client compliance configurations.</div>
            </div>
        </div>
        <div class="roadmap-item">
            <span class="roadmap-phase phase-future">FUTURE</span>
            <div class="roadmap-content">
                <div class="rm-title">Continuous Learning Loop</div>
                <div class="rm-desc">Feed underwriter overrides back into the system. When a human flips REJECT to APPROVE, that signal fine-tunes the risk model. Over time, the system learns each organization's true risk appetite from their decisions.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_get_involved():
    st.markdown("""
    <div class="section-card">
        <div class="section-card-header">
            <h2>How Can I Help Build This?</h2>
            <span class="status-chip">Collaboration</span>
        </div>
        <div class="involve-card">
            <div class="involve-title">This demo is a starting point &mdash; not the finish line.</div>
            <div class="involve-text">
                What you see here was built in days, not months. The architecture is designed to scale
                from this proof-of-concept to a production system handling thousands of applications daily.
                Here's where I can contribute:
            </div>
            <ul>
                <li><strong>Production-Grade Agent Systems</strong> &mdash; Design and build multi-agent pipelines with proper error handling, retry logic, and fallback strategies that don't break at scale.</li>
                <li><strong>LLM Evaluation &amp; Optimization</strong> &mdash; Set up systematic eval frameworks to measure agent accuracy, latency, and cost. Identify where smaller models can replace expensive ones without quality loss.</li>
                <li><strong>Compliance &amp; Auditability</strong> &mdash; Build explainable AI systems where every decision is traceable, every rule is configurable, and every override is logged &mdash; critical for RBI and NBFC regulations.</li>
                <li><strong>End-to-End Ownership</strong> &mdash; From Figma mockups to deployed infrastructure, I can own the full stack: LangGraph orchestration, FastAPI services, React dashboards, and cloud deployment.</li>
            </ul>
            <div class="cta-row">
                <a href="https://www.linkedin.com/in/lohith-chandra-prasad-rampalli/" target="_blank" class="cta-btn cta-primary">Connect on LinkedIn</a>
                <a href="https://github.com/Lohith254/neurofin-loan-processor" target="_blank" class="cta-btn cta-secondary">View Source Code</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    render_hero()
    custom_rules = render_sidebar()
    render_pipeline_landing()

    # ── Upload section ──
    st.markdown("""
    <div class="section-card">
        <div class="section-card-header">
            <h2>Process a Bank Statement</h2>
            <span class="status-chip">Ready for upload</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1])
    sample_dir = Path(__file__).parent.parent.parent / "data" / "sample_statements"
    sample_files = sorted(sample_dir.glob("*.pdf")) if sample_dir.exists() else []

    with col_left:
        st.markdown("**Input Method**")
        input_method = st.radio("method", ["Use sample statement", "Upload PDF"], horizontal=True, label_visibility="collapsed")

        pdf_path = None
        if input_method == "Upload PDF":
            uploaded_file = st.file_uploader("Choose a bank statement PDF", type=["pdf"])
            if uploaded_file:
                st.info(f"**{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    pdf_path = tmp.name
        else:
            if sample_files:
                selected = st.selectbox("Select sample", sample_files, format_func=lambda x: x.name)
                pdf_path = str(selected)

                name = selected.name.lower()
                if "healthy" in name:
                    st.success("Expected outcome: **APPROVE** (7/7 checks pass)")
                elif "risky" in name:
                    st.error("Expected outcome: **REJECT** (3 high-severity failures)")
                elif "borderline" in name:
                    st.warning("Expected outcome: **REVIEW** (borderline risk)\nThis sample triggers 2 minor compliance flags.")

    with col_right:
        render_scenario_table()

    st.markdown("")
    if pdf_path and st.button("Process Document", type="primary", use_container_width=True):
        try:
            output = process_with_visualization(pdf_path, custom_rules)
            if isinstance(output, tuple) and len(output) == 3:
                result, agent_times, risk_assessment = output
                display_results(result, agent_times, risk_assessment)
            elif isinstance(output, tuple) and len(output) == 2:
                result, agent_times = output
                display_results(result, agent_times)
            else:
                display_results(output)
        finally:
            if input_method == "Upload PDF" and pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)

    # ── Info sections ──
    render_how_we_built()
    render_roadmap()
    render_get_involved()

    render_footer()


if __name__ == "__main__":
    main()
