# PWS Navigator Demo Script & Talking Points
## For Lawrence Aronhime - University of Sao Paulo & Executive Meetings

---

## 1-Minute Elevator Pitch

> "Mindrian is an AI-powered innovation coaching platform that uses knowledge graph technology to help students and professionals discover **unexpected connections between domains**. Instead of just answering questions, Mindrian maps thousands of innovation concepts and frameworks, finds the **bridge concepts** that connect different fields, and guides users through structured problem-solving methodology. Think of it as a GPS for innovation thinking."

---

## Demo Flow (10-15 minutes)

### Act 1: The Knowledge Landscape (2 min)

**What to show:** Open Mindrian, start a conversation with Lawrence bot.

**Say:** "Mindrian has ingested all of our Problems Worth Solving course material - lectures, frameworks, case studies. But it doesn't just store text. It builds a **knowledge graph** with over 8,000 concepts organized into 39+ communities."

**Action:** Type: "What domains does the knowledge base cover?"

**Key stat:** "We have 8,425 concept nodes, 123,000 co-occurrence edges, and 143 domain nodes - all interconnected."

### Act 2: The PWS Navigator - Cross-Domain Discovery (5 min)

**What to show:** Click the "PWS Navigator" button after asking about a topic.

**Say:** "This is what makes us unique. Austin Granmoe's research on Large Scale Networks showed that the most innovative ideas come from **interclass edges** - connections between different knowledge communities. Our PWS Navigator does exactly this in real time."

**Demo query:** "I'm interested in how questioning techniques connect to scenario planning"

**What happens:**
- Navigator identifies the user's home domain (Community 18: Questions, Inquiry, Questioning)
- Finds cross-domain bridges to Scenario Planning (Community 26)
- Surfaces bridge concepts like:
  - **"Questions"** → connects inquiry techniques with alternative futures
  - **"Systems"** → bridges questioning methodology with systems thinking
  - **"Techniques"** → links inquiry practices to scenario construction methods
- Generates innovation prompts: "How might 'Questioning' connect inquiry with scenario planning?"

**Say:** "Notice the bridge concepts. 'Questions' isn't just a word - it's a concept that has strong connections to BOTH the inquiry/questioning domain AND the scenario planning domain. That's where innovation happens - at the intersection."

### Act 3: Bridge Exploration (3 min)

**What to show:** Click one of the "Explore" buttons to deep-dive.

**Say:** "Students can click any bridge to explore further. This turns a passive reading experience into an active exploration engine."

**Demo:** Click "Explore: Scenario Planning" button.

**What to highlight:**
- The Mermaid diagram showing cross-domain connections
- Bridge scores showing relative connection strength
- Innovation questions generated automatically

### Act 4: Integration with PWS Methodology (3 min)

**What to show:** Switch to a specialized bot (TTA or JTBD) and show how the same knowledge graph enriches the conversation.

**Say:** "The Navigator isn't standalone - it's woven into every conversation. When a student discusses 'customer discovery' with our JTBD bot, the graph automatically surfaces that this concept bridges to 'reverse salient' in technology analysis. The student discovers connections they wouldn't have found in a textbook."

**Key differentiation:** "Traditional AI just retrieves relevant text. Mindrian retrieves **relationships** - showing students HOW concepts connect, not just WHAT they are."

---

## Talking Points for University of Sao Paulo

### Academic Value

1. **Research-backed approach**: Built on Granmoe's "Large Scale Networks for Idea Generation" methodology - using knowledge graph topology (modularity classes, interclass edges, betweenness centrality) for structured idea generation.

2. **Pedagogical innovation**: Moves from passive content delivery to **active knowledge exploration**. Students don't just learn frameworks - they discover how frameworks connect to create new insights.

3. **Scalable coaching**: One professor's methodology, delivered consistently to hundreds of students simultaneously, with personalized guidance through the knowledge graph.

4. **Cross-disciplinary by design**: The graph has 39+ concept communities spanning innovation, technology, business, psychology, systems thinking, scenario planning, and more. Students naturally discover interdisciplinary connections.

### Technical Differentiators

| Feature | Traditional LMS | ChatGPT | Mindrian |
|---------|----------------|---------|----------|
| Knowledge structure | Flat files | None | 8,425-node knowledge graph |
| Cross-domain discovery | Manual | Random | Algorithmic bridge detection |
| Methodology guidance | Static worksheets | Generic | 15+ specialized AI coaches |
| Progress tracking | Checkbox | None | Semantic phase detection |
| Innovation methodology | Read about it | Hallucinate it | **Navigate through it** |

### For the Executives (Wed/Fri)

**Business angle:**
- SaaS platform, per-seat licensing for universities
- Enterprise tier for corporate innovation teams
- White-label option for consulting firms
- LightRAG integration for custom knowledge bases (each client can have their own)

**Competitive moat:**
- 8,425+ PWS-specific concept nodes (not general knowledge)
- 123K edge co-occurrence graph (built from proprietary course material)
- 15+ methodology-specific AI coaches (not generic chatbots)
- Real-time cross-domain bridge detection (unique to Mindrian)

---

## Technical Architecture (If Asked)

```
User Query → Knowledge Graph (Neo4j)
                ↓
        Community Detection (Modularity Classes)
                ↓
        Bridge Concept Identification (Interclass Edges)
                ↓
        Innovation Prompt Generation (LLM)
                ↓
        Interactive Exploration (Chainlit UI)
```

**Stack:** Python, Neo4j, Gemini AI, Chainlit, LightRAG, PostgreSQL
**Hosting:** Render.com (auto-scaling)
**Graph:** 8,425 LazyGraphConcept nodes, 39 communities, 123K CO_OCCURS edges

---

## Connection to Granmoe's Paper

| Paper Concept | Mindrian Implementation |
|---------------|------------------------|
| Wikipedia link scraping for knowledge graphs | Neo4j graph built from PWS course material + research papers |
| Gephi modularity class detection | LazyGraphConcept community_id (pre-computed) |
| Interclass edge ratios for innovation potential | `find_bridges()` - cross-community CO_OCCURS analysis |
| Manual Gephi exploration | Automated PWS Navigator with one-click exploration |
| Static graph → manual insight | Dynamic graph → AI-generated innovation prompts |

**Key quote from paper:** "Connections between nodes from different modularity classes are often the most fertile ground for novel idea generation."

**Mindrian's implementation:** We operationalize this principle in real-time. Instead of students manually using Gephi, our PWS Navigator automatically detects these interclass bridges and generates innovation questions from them.

---

## Q&A Preparation

**Q: How is this different from ChatGPT?**
A: ChatGPT retrieves text. Mindrian navigates **relationships**. When you ask ChatGPT about "reverse salients," it gives you a definition. When you explore it in Mindrian, you discover it bridges technology analysis (S-Curves) with systems thinking (leverage points) with problem classification. That structural insight is what generates innovation.

**Q: What content is in the graph?**
A: All PWS course lectures, workshop materials, case studies, and key innovation research papers. 8,425 concept nodes across 39 communities, with 123K weighted co-occurrence edges mapping how concepts relate.

**Q: Can we add our own content?**
A: Yes. LightRAG integration allows any institution to build their own knowledge graph from their materials. The graph builds automatically from text ingestion.

**Q: How do students interact?**
A: Through natural conversation with specialized AI coaches (15+ different methodology experts), plus interactive tools: PWS Navigator for cross-domain exploration, Mermaid diagrams for visualization, opportunity bank for tracking ideas, and structured workshops for each PWS framework.

**Q: What's the research basis?**
A: PWS methodology by Lawrence Aronhime (published textbook), enhanced with computational methods from Granmoe's network analysis research, graph-based RAG from Microsoft Research, and community detection algorithms from network science.
