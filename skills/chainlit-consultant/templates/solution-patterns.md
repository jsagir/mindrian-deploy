# Chainlit Solution Patterns for Mindrian

Templates for solving common Mindrian issues using Chainlit features.

---

## Pattern 1: Persistent Sidebar Element

**Problem**: Phase indicators appear inline and disrupt conversation flow.

**Solution**: Use CustomElement with `display="side"` for persistent sidebar.

### Python Implementation

```python
# mindrian_chat.py

async def create_phase_sidebar(phases, current_phase, bot_name):
    """Create or update the phase sidebar element."""
    element = cl.user_session.get("phase_sidebar")
    
    if element is None:
        element = cl.CustomElement(
            name="PhaseSidebar",
            props={
                "phases": [{"name": p["name"], "status": p["status"]} for p in phases],
                "currentPhase": current_phase,
                "botName": bot_name
            },
            display="side"
        )
        cl.user_session.set("phase_sidebar", element)
        # Send with empty message to attach to sidebar
        await cl.Message(content="", elements=[element]).send()
    else:
        # Update existing element
        element.props["phases"] = [{"name": p["name"], "status": p["status"]} for p in phases]
        element.props["currentPhase"] = current_phase
        await element.update()
```

### JSX Component

```jsx
// public/elements/PhaseSidebar.jsx
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ChevronRight, Check, Circle, Loader2 } from "lucide-react"

export default function PhaseSidebar() {
    const { phases, currentPhase, botName } = props;
    
    const getIcon = (index, status) => {
        if (status === "done") return <Check className="h-4 w-4 text-green-500" />;
        if (index === currentPhase) return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
        return <Circle className="h-4 w-4 text-gray-400" />;
    };
    
    const handlePhaseClick = (index) => {
        if (index <= currentPhase + 1) {
            callAction({ name: "navigate_phase", payload: { phase: index }});
        }
    };
    
    return (
        <Card className="w-64">
            <CardHeader className="pb-2">
                <h3 className="font-semibold text-sm">{botName}</h3>
                <p className="text-xs text-muted-foreground">
                    Phase {currentPhase + 1} of {phases.length}
                </p>
            </CardHeader>
            <CardContent className="pt-0">
                {phases.map((phase, i) => (
                    <Button
                        key={i}
                        variant="ghost"
                        className={`w-full justify-start mb-1 ${i === currentPhase ? 'bg-accent' : ''}`}
                        onClick={() => handlePhaseClick(i)}
                        disabled={i > currentPhase + 1}
                    >
                        {getIcon(i, phase.status)}
                        <span className="ml-2 text-sm truncate">{phase.name}</span>
                        {i === currentPhase && <ChevronRight className="ml-auto h-4 w-4" />}
                    </Button>
                ))}
            </CardContent>
        </Card>
    );
}
```

---

## Pattern 2: Interactive Bot Switcher

**Problem**: Bot switching requires finding and clicking specific buttons.

**Solution**: Dropdown selector with bot descriptions.

### Python Implementation

```python
# Add to message with bot options
async def send_with_bot_switcher(content, current_bot_id):
    bots_data = {
        bot_id: {"name": bot["name"], "description": bot.get("description", "")}
        for bot_id, bot in BOTS.items()
        if bot.get("visible", True)
    }
    
    switcher = cl.CustomElement(
        name="BotSwitcher",
        props={
            "currentBot": current_bot_id,
            "bots": bots_data
        },
        display="inline"
    )
    
    await cl.Message(content=content, elements=[switcher]).send()

@cl.action_callback("switch_bot")
async def on_switch_bot(action: cl.Action):
    new_bot_id = action.payload.get("bot_id")
    await handle_agent_switch(new_bot_id)
```

### JSX Component

```jsx
// public/elements/BotSwitcher.jsx
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"

export default function BotSwitcher() {
    const { currentBot, bots } = props;
    
    const handleChange = (value) => {
        callAction({ name: "switch_bot", payload: { bot_id: value }});
    };
    
    const currentBotInfo = bots[currentBot] || { name: "Unknown" };
    
    return (
        <div className="flex items-center gap-2 my-2">
            <span className="text-sm text-muted-foreground">Switch to:</span>
            <Select value={currentBot} onValueChange={handleChange}>
                <SelectTrigger className="w-48">
                    <SelectValue>{currentBotInfo.name}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                    {Object.entries(bots).map(([id, bot]) => (
                        <SelectItem key={id} value={id}>
                            <div className="flex flex-col">
                                <span>{bot.name}</span>
                                <span className="text-xs text-muted-foreground">{bot.description}</span>
                            </div>
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </div>
    );
}
```

---

## Pattern 3: Collapsible Thinking Display

**Problem**: Thinking/reasoning takes up too much space.

**Solution**: Collapsible accordion for thinking sections.

### Python Implementation

```python
async def send_with_thinking(content, thinking_content, bot_name):
    """Send message with collapsible thinking section."""
    thinking_element = cl.CustomElement(
        name="ThinkingAccordion",
        props={
            "title": f"🧠 {bot_name}'s Thinking",
            "content": thinking_content,
            "defaultOpen": False
        },
        display="inline"
    )
    
    await cl.Message(
        content=content,
        elements=[thinking_element]
    ).send()
```

### JSX Component

```jsx
// public/elements/ThinkingAccordion.jsx
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

export default function ThinkingAccordion() {
    const { title, content, defaultOpen } = props;
    
    return (
        <Accordion type="single" collapsible defaultValue={defaultOpen ? "thinking" : undefined}>
            <AccordionItem value="thinking" className="border rounded-md">
                <AccordionTrigger className="px-4 py-2 text-sm">
                    {title}
                </AccordionTrigger>
                <AccordionContent className="px-4 pb-4">
                    <div className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {content}
                    </div>
                </AccordionContent>
            </AccordionItem>
        </Accordion>
    );
}
```

---

## Pattern 4: Research Results Panel

**Problem**: Research results clutter the main conversation.

**Solution**: Side panel with searchable, filterable results.

### Python Implementation

```python
async def display_research_results(results):
    """Display research results in side panel."""
    panel = cl.CustomElement(
        name="ResearchPanel",
        props={
            "results": [
                {
                    "title": r.get("title"),
                    "snippet": r.get("snippet"),
                    "url": r.get("url"),
                    "source": r.get("source"),
                    "relevance": r.get("relevance_score", 0)
                }
                for r in results
            ],
            "query": original_query
        },
        display="side"
    )
    
    await cl.Message(
        content=f"Found {len(results)} relevant sources. See panel for details.",
        elements=[panel]
    ).send()
```

### JSX Component

```jsx
// public/elements/ResearchPanel.jsx
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ExternalLink, Search } from "lucide-react"
import { useState } from "react"

export default function ResearchPanel() {
    const [filter, setFilter] = useState("");
    const { results, query } = props;
    
    const filtered = results.filter(r => 
        r.title.toLowerCase().includes(filter.toLowerCase()) ||
        r.snippet.toLowerCase().includes(filter.toLowerCase())
    );
    
    const insertResult = (result) => {
        sendUserMessage(`Use this source: ${result.title}\n${result.url}`);
    };
    
    return (
        <Card className="w-80 h-[500px] flex flex-col">
            <CardHeader className="pb-2">
                <h3 className="font-semibold text-sm">Research Results</h3>
                <p className="text-xs text-muted-foreground">Query: {query}</p>
                <div className="relative mt-2">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                        placeholder="Filter results..." 
                        className="pl-8"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                    />
                </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden pt-0">
                <ScrollArea className="h-full">
                    {filtered.map((result, i) => (
                        <Card key={i} className="p-3 mb-2 cursor-pointer hover:bg-accent" onClick={() => insertResult(result)}>
                            <div className="flex items-start justify-between">
                                <h4 className="font-medium text-sm line-clamp-2">{result.title}</h4>
                                <a href={result.url} target="_blank" onClick={(e) => e.stopPropagation()}>
                                    <ExternalLink className="h-4 w-4 text-muted-foreground" />
                                </a>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1 line-clamp-3">{result.snippet}</p>
                            <div className="flex gap-1 mt-2">
                                <Badge variant="outline" className="text-xs">{result.source}</Badge>
                                {result.relevance > 0.8 && <Badge className="text-xs">High relevance</Badge>}
                            </div>
                        </Card>
                    ))}
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
```

---

## Pattern 5: Grading Scorecard

**Problem**: Grading criteria and scores shown as plain text.

**Solution**: Visual scorecard with progress bars.

### Python Implementation

```python
async def display_grading_results(criteria_scores, overall_score, feedback):
    """Display grading as visual scorecard."""
    scorecard = cl.CustomElement(
        name="GradingScorecard",
        props={
            "criteria": [
                {"name": c["name"], "score": c["score"], "max": c.get("max", 10), "feedback": c.get("feedback")}
                for c in criteria_scores
            ],
            "overall": overall_score,
            "summary": feedback
        },
        display="inline"
    )
    
    await cl.Message(
        content="Here's your PWS assessment:",
        elements=[scorecard]
    ).send()
```

### JSX Component

```jsx
// public/elements/GradingScorecard.jsx
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
import { Info } from "lucide-react"

export default function GradingScorecard() {
    const { criteria, overall, summary } = props;
    
    const getScoreColor = (score, max) => {
        const pct = (score / max) * 100;
        if (pct >= 80) return "bg-green-500";
        if (pct >= 60) return "bg-yellow-500";
        return "bg-red-500";
    };
    
    return (
        <Card className="w-full max-w-md">
            <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                    <h3 className="font-semibold">PWS Assessment</h3>
                    <div className="text-2xl font-bold">{overall}<span className="text-sm text-muted-foreground">/100</span></div>
                </div>
            </CardHeader>
            <CardContent>
                {criteria.map((c, i) => (
                    <div key={i} className="mb-4">
                        <div className="flex justify-between items-center mb-1">
                            <div className="flex items-center gap-1">
                                <span className="text-sm">{c.name}</span>
                                {c.feedback && (
                                    <HoverCard>
                                        <HoverCardTrigger>
                                            <Info className="h-3 w-3 text-muted-foreground" />
                                        </HoverCardTrigger>
                                        <HoverCardContent className="text-sm">
                                            {c.feedback}
                                        </HoverCardContent>
                                    </HoverCard>
                                )}
                            </div>
                            <span className="text-sm font-medium">{c.score}/{c.max}</span>
                        </div>
                        <Progress 
                            value={(c.score / c.max) * 100} 
                            className={`h-2 ${getScoreColor(c.score, c.max)}`}
                        />
                    </div>
                ))}
            </CardContent>
            {summary && (
                <CardFooter className="border-t pt-4">
                    <p className="text-sm text-muted-foreground">{summary}</p>
                </CardFooter>
            )}
        </Card>
    );
}
```

---

## Pattern 6: Action Button Bar

**Problem**: Action buttons disappear or are inconsistent.

**Solution**: Persistent action bar component.

### JSX Component

```jsx
// public/elements/ActionBar.jsx
import { Button } from "@/components/ui/button"
import { Search, FileText, Brain, BookOpen, RotateCcw } from "lucide-react"

export default function ActionBar() {
    const { actions, disabled } = props;
    
    const icons = {
        research: Search,
        synthesize: FileText,
        think: Brain,
        example: BookOpen,
        reset: RotateCcw
    };
    
    const handleClick = (actionName) => {
        callAction({ name: actionName, payload: {} });
    };
    
    return (
        <div className="flex gap-2 py-2 border-t mt-4">
            {actions.map((action) => {
                const Icon = icons[action.id] || BookOpen;
                return (
                    <Button
                        key={action.id}
                        variant="outline"
                        size="sm"
                        onClick={() => handleClick(action.id)}
                        disabled={disabled}
                    >
                        <Icon className="h-4 w-4 mr-1" />
                        {action.label}
                    </Button>
                );
            })}
        </div>
    );
}
```
