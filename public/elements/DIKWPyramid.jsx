/**
 * DIKWPyramid - Interactive Ackoff's DIKW Pyramid Visualization
 *
 * Clickable pyramid levels that trigger exploration of each knowledge layer.
 * Supports highlighting current level and showing scores.
 */

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Info } from 'lucide-react';

export default function DIKWPyramid() {
    const { highlightLevel, scores, showDescriptions } = props;

    const levels = [
        {
            name: 'Wisdom',
            color: 'from-purple-500 to-purple-600',
            bgColor: 'bg-purple-500',
            description: 'Applying knowledge with judgment and experience',
            question: 'What should we do?',
            width: '40%',
            score: scores?.wisdom
        },
        {
            name: 'Knowledge',
            color: 'from-blue-500 to-blue-600',
            bgColor: 'bg-blue-500',
            description: 'Understanding patterns and relationships',
            question: 'How does it work?',
            width: '55%',
            score: scores?.knowledge
        },
        {
            name: 'Information',
            color: 'from-green-500 to-green-600',
            bgColor: 'bg-green-500',
            description: 'Processed data with context and meaning',
            question: 'What does it mean?',
            width: '70%',
            score: scores?.information
        },
        {
            name: 'Data',
            color: 'from-yellow-500 to-yellow-600',
            bgColor: 'bg-yellow-500',
            description: 'Raw facts, observations, and measurements',
            question: 'What are the facts?',
            width: '85%',
            score: scores?.data
        },
    ];

    const handleLevelClick = (levelName) => {
        callAction({
            name: 'explore_dikw_level',
            payload: { level: levelName.toLowerCase() }
        });
    };

    return (
        <Card className="w-full max-w-lg bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
            <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                    <span>📊</span>
                    <span>Ackoff's DIKW Pyramid</span>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
                <div className="flex flex-col items-center py-4 space-y-1">
                    {levels.map((level, i) => {
                        const isHighlighted = highlightLevel?.toLowerCase() === level.name.toLowerCase();

                        return (
                            <div
                                key={level.name}
                                className="relative group cursor-pointer transition-all duration-300"
                                style={{ width: level.width }}
                                onClick={() => handleLevelClick(level.name)}
                            >
                                {/* Pyramid Level */}
                                <div
                                    className={`
                                        bg-gradient-to-r ${level.color}
                                        text-white text-center py-3 px-4 rounded-sm
                                        shadow-md hover:shadow-lg
                                        transform hover:scale-105 transition-all duration-200
                                        ${isHighlighted ? 'ring-4 ring-white ring-opacity-75 scale-105' : ''}
                                    `}
                                >
                                    <div className="flex items-center justify-center gap-2">
                                        <span className="font-bold">{level.name}</span>
                                        {level.score !== undefined && (
                                            <Badge variant="secondary" className="bg-white/20 text-white">
                                                {level.score}/10
                                            </Badge>
                                        )}
                                    </div>

                                    {/* Show description on hover or if showDescriptions is true */}
                                    {(showDescriptions || isHighlighted) && (
                                        <div className="text-xs mt-1 opacity-90">
                                            {level.question}
                                        </div>
                                    )}
                                </div>

                                {/* Tooltip on hover */}
                                <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2
                                                opacity-0 group-hover:opacity-100 transition-opacity
                                                bg-gray-900 text-white text-xs p-2 rounded-md
                                                whitespace-nowrap z-10 pointer-events-none">
                                    <div className="font-semibold">{level.name}</div>
                                    <div className="text-gray-300">{level.description}</div>
                                    <div className="text-indigo-300 mt-1">{level.question}</div>
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-1 text-xs text-gray-500 dark:text-gray-400 pt-2 border-t">
                    <Info className="w-3 h-3" />
                    <span>Click any level to explore</span>
                </div>

                {/* Current Focus */}
                {highlightLevel && (
                    <div className="bg-indigo-50 dark:bg-indigo-900/30 p-3 rounded-lg text-center">
                        <div className="text-xs text-indigo-600 dark:text-indigo-400 uppercase tracking-wide">
                            Current Focus
                        </div>
                        <div className="font-semibold text-indigo-800 dark:text-indigo-200">
                            {highlightLevel} Level
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
