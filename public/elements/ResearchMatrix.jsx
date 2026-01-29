/**
 * ResearchMatrix - Display Research Results in a Visual Grid
 *
 * Shows research findings organized by category (WHY, WHAT IF, HOW, etc.)
 * with source counts and expandable details.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, ChevronDown, ChevronUp, Search, CheckCircle, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export default function ResearchMatrix() {
    const { categories, totalSources, query } = props;
    const [expandedCategory, setExpandedCategory] = useState(null);

    const categoryConfig = {
        why: { icon: '🤔', label: 'WHY', color: 'bg-purple-500', description: 'Root causes' },
        what_if: { icon: '💡', label: 'WHAT IF', color: 'bg-blue-500', description: 'Possibilities' },
        how: { icon: '🔧', label: 'HOW', color: 'bg-green-500', description: 'Implementation' },
        validation: { icon: '✅', label: 'VALIDATION', color: 'bg-teal-500', description: 'Evidence' },
        challenge: { icon: '⚠️', label: 'CHALLENGE', color: 'bg-orange-500', description: 'Counter-evidence' },
    };

    const toggleExpand = (cat) => {
        setExpandedCategory(expandedCategory === cat ? null : cat);
    };

    if (!categories) {
        return (
            <Card className="w-full max-w-lg">
                <CardContent className="p-6 text-center text-gray-500">
                    No research results available
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="w-full max-w-2xl bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
            <CardHeader className="pb-2">
                <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Search className="w-5 h-5" />
                        <span>Research Matrix</span>
                    </div>
                    <Badge variant="secondary">
                        {totalSources || 0} sources
                    </Badge>
                </CardTitle>
                {query && (
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                        Query: "{query}"
                    </div>
                )}
            </CardHeader>
            <CardContent className="space-y-3">
                {Object.entries(categories).map(([catKey, catData]) => {
                    const config = categoryConfig[catKey] || { icon: '📄', label: catKey.toUpperCase(), color: 'bg-gray-500' };
                    const sourceCount = catData?.source_count || catData?.results?.length || 0;
                    const isExpanded = expandedCategory === catKey;

                    return (
                        <div key={catKey} className="border rounded-lg overflow-hidden">
                            {/* Category Header */}
                            <div
                                className={`flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors`}
                                onClick={() => toggleExpand(catKey)}
                            >
                                <div className="flex items-center gap-2">
                                    <span className={`${config.color} text-white px-2 py-1 rounded text-xs font-bold`}>
                                        {config.icon} {config.label}
                                    </span>
                                    <span className="text-sm text-gray-600 dark:text-gray-400">
                                        {config.description}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Badge variant={sourceCount > 0 ? "default" : "secondary"}>
                                        {sourceCount} sources
                                    </Badge>
                                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                                </div>
                            </div>

                            {/* Expanded Content */}
                            {isExpanded && catData?.results && (
                                <div className="border-t bg-white dark:bg-gray-900 p-3 space-y-2">
                                    {catData.results.map((result, i) => (
                                        <div key={i} className="text-sm border-l-2 border-indigo-300 pl-3 py-1">
                                            {result.query && (
                                                <div className="text-xs text-gray-500 mb-1">
                                                    Query: {result.query}
                                                </div>
                                            )}
                                            {result.answer && (
                                                <div className="text-gray-700 dark:text-gray-300">
                                                    {result.answer}
                                                </div>
                                            )}
                                            {result.results && result.results.length > 0 && (
                                                <div className="mt-2 space-y-1">
                                                    {result.results.slice(0, 3).map((r, j) => (
                                                        <a
                                                            key={j}
                                                            href={r.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="flex items-center gap-1 text-xs text-blue-600 hover:underline"
                                                        >
                                                            <ExternalLink className="w-3 h-3" />
                                                            {r.title?.slice(0, 60) || 'Source'}
                                                        </a>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}

                {/* Action Buttons */}
                <div className="flex gap-2 pt-3 border-t">
                    <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => callAction({name: 'deep_research', payload: {}})}
                    >
                        <Search className="w-4 h-4 mr-1" />
                        More Research
                    </Button>
                    <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => callAction({name: 'synthesize_conversation', payload: {}})}
                    >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Synthesize
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}
