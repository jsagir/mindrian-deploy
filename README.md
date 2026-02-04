# Welcome to Mindrian

**Your AI-Powered Innovation Workshop Platform**

Mindrian helps you discover problems worth solving through structured thinking frameworks. Whether you're an entrepreneur, researcher, or student exploring innovation, Mindrian guides you through proven methodologies.

**Live Demo:** https://mindrian.onrender.com
**Course:** EN.663.635 Problems Worth Solving - Johns Hopkins University

---

## Available Workshops

| Workshop | What It Does | Best For |
|----------|-------------|----------|
| **Lawrence** | Your thinking partner for discovering valuable problems | Starting exploration, general guidance |
| **Larry Playground** | Full-featured lab with research tools + multi-agent analysis | Deep research, complex problems |
| **Trending to the Absurd (TTA)** | Take trends to extremes to find future problems | Spotting emerging opportunities |
| **Jobs to Be Done (JTBD)** | Discover what customers actually hire products for | Customer research, product design |
| **S-Curve Analysis** | Analyze technology timing and disruption | Market timing, investment decisions |
| **Red Teaming** | Stress-test your assumptions as devil's advocate | Validating ideas, finding weaknesses |
| **Ackoff's Pyramid** | Validate understanding before taking action (DIKW) | Decision-making, avoiding blind spots |
| **Scenario Analysis** | Explore multiple plausible futures | Strategic planning |
| **Beautiful Question** | WHY → WHAT IF → HOW methodology | Breaking assumptions |
| **Nested Hierarchies** | Systems analysis for leverage points | Complex problems |

---

## How to Use Mindrian

### Getting Started

1. **Visit** https://mindrian.onrender.com
2. **Choose a workshop** from the dropdown (top-left)
3. **Click a starter prompt** or type your own question
4. **Follow the conversation** - the AI will guide you through the methodology

### Tips for Best Results

- **Upload documents** - PDFs, Word docs, and images are supported. Just drag and drop.
- **Be specific** - The more context you provide, the better the guidance.
- **Use the buttons** - Action buttons (Research, Synthesize, etc.) trigger specialized workflows.
- **Adjust detail level** - Use the Settings gear (top-right) to control response length.
- **Ask for examples** - Request real-world examples to understand frameworks better.

### Features

- **Voice input** - Click the microphone to speak your thoughts
- **Document analysis** - Upload PDFs, Word docs, presentations
- **Research tools** - One-click access to patents, news, academic papers, trends
- **Progress tracking** - See where you are in multi-phase workshops
- **Export** - Download conversation summaries as markdown

---

## Research Tools

Mindrian includes powerful research capabilities that analyze results in context of YOUR problem:

| Tool | What It Searches | Use For |
|------|-----------------|---------|
| **Deep Research** | Web (Tavily), PWS knowledge base | General exploration |
| **Patent Search** | Google Patents | Innovation landscape, prior art |
| **News Search** | NewsMesh, Tavily | Current events, market signals |
| **Academic Search** | arXiv | Research papers, scientific findings |
| **Trends Search** | SerpAPI Google Trends | Market interest, timing |
| **Government Data** | FRED, World Bank | Economic indicators, statistics |
| **Dataset Search** | Kaggle, Socrata | Data for analysis |

### Smart Research Contextualization

Research results aren't just dumped - they're analyzed for relevance to YOUR current exploration. You'll see:
- Which results actually matter to your problem
- Why each result is relevant
- Actionable recommendations based on findings

---

## Frequently Asked Questions

**Q: What is PWS?**
A: Problems Worth Solving - a framework for finding problems valuable enough to actually solve. Instead of building solutions for problems nobody cares about, PWS helps you identify high-value opportunities.

**Q: What's the difference between Lawrence and Larry Playground?**
A: Lawrence is the focused thinking partner - concise, conversational. Larry Playground has all the tools enabled: research, multi-agent analysis, visualizations. Use Lawrence for quick guidance, Larry Playground for deep exploration.

**Q: Can I upload files?**
A: Yes! PDFs, Word documents, PowerPoint, images, text files, and code files are all supported. Just drag and drop or use the paperclip icon.

**Q: Is my conversation saved?**
A: Yes, conversations persist across sessions. You can close your browser and return later to continue.

**Q: How do I get more detailed responses?**
A: Use the Settings gear (top-right) and increase the "Response Detail" slider.

**Q: Can I use voice input?**
A: Yes! Click the microphone icon to speak instead of type.

---

## New Features (v3.1)

### Smart Onboarding
First-time users get a guided introduction to PWS concepts with the option to take a 2-minute tour or dive right in.

### Research Contextualization
All research results (patents, news, papers, trends) are now analyzed for relevance to YOUR specific problem, not just returned as raw data.

### API Health Monitoring
Automated daily health checks ensure all integrations are working properly.

### Streaming File Processing
When you upload documents, you now see real-time progress:
```
├─ Detecting file type... ✓ Document (.pdf)
├─ Extracting PDF text... ✓ 6,824 chars
└─ ✅ Complete!
```

### LangGraph Intelligence Layer
Behind the scenes, complex multi-step workflows use LangGraph for reliable execution with automatic retry and fallback handling.

---

## Legal Disclaimers

### Research Results Disclaimer

Research results provided by Mindrian (including patent searches, news articles, academic papers, government data, and trend analysis) are:

- **For informational purposes only** - Not legal, financial, or professional advice
- **Potentially incomplete** - Results depend on third-party APIs and may not include all relevant sources
- **Time-sensitive** - Information may become outdated; verify current status for important decisions
- **AI-analyzed** - Relevance assessments are generated by AI and may contain errors

**Always verify important information** from primary sources before making decisions.

### General Platform Disclaimer

Mindrian is an educational tool designed to support innovation thinking. The platform:

- Does not guarantee the accuracy, completeness, or timeliness of any information
- Is not a substitute for professional advice (legal, financial, business, medical, etc.)
- May experience service interruptions or data loss
- Stores conversation data for session persistence and quality improvement

Use of this platform constitutes acceptance of these terms.

### Intellectual Property

- User-uploaded content remains the property of the user
- AI-generated content is provided as-is without warranty
- PWS methodology is based on coursework from Johns Hopkins University

---

## Technical Details

For developers and those interested in the technical implementation:

### Stack
- **Frontend:** Chainlit 2.9+
- **AI Model:** Google Gemini 2.5-flash / 3-flash-preview
- **Knowledge Base:** Gemini File Search (RAG) + Neo4j GraphRAG
- **Database:** PostgreSQL (Supabase)
- **Deployment:** Render

### Documentation
- [CLAUDE.md](./CLAUDE.md) - Technical reference for developers
- [docs/EDWARDS_ONBOARDING.md](./docs/EDWARDS_ONBOARDING.md) - System architecture overview

### Repository
- **GitHub:** https://github.com/jsagir/mindrian-deploy
- **Issues:** https://github.com/jsagir/mindrian-deploy/issues

---

## About

Mindrian was developed to support the **Problems Worth Solving** methodology created by Professor Lawrence Aronhime at Johns Hopkins University. The platform applies 30+ years of innovation teaching to help users discover valuable problems.

**Core Insight:** Most innovation fails not because of bad solutions, but because people solve the wrong problems.

---

Built with Chainlit + Google Gemini + Neo4j + Supabase
