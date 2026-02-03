/**
 * PhaseProgress - Interactive Workshop Progress Visualization
 *
 * Shows current phase, progress bar, and action buttons for phase navigation.
 * Uses Shadcn UI components + Lucide icons.
 */

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, Circle, PlayCircle, ChevronRight, HelpCircle } from 'lucide-react';

export default function PhaseProgress() {
    const { phases, currentPhase, botName, botIcon } = props;

    if (!phases || phases.length === 0) {
        return <div className="text-gray-500">No phases configured</div>;
    }

    const totalPhases = phases.length;
    const completedPhases = phases.filter(p => p.status === 'done' || p.status === 'completed').length;
    const progressPercent = (completedPhases / totalPhases) * 100;

    const currentPhaseName = phases[currentPhase]?.name || 'Unknown';
    const nextPhaseName = currentPhase + 1 < totalPhases ? phases[currentPhase + 1]?.name : null;

    return (
        <Card className="w-full max-w-md bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 border-2 border-indigo-200 dark:border-indigo-800">
            <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-lg">
                    <span>{botIcon || '🎯'}</span>
                    <span>{botName || 'Workshop'} Progress</span>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                        <span>Phase {currentPhase + 1} of {totalPhases}</span>
                        <span>{Math.round(progressPercent)}% Complete</span>
                    </div>
                    <Progress value={progressPercent} className="h-2" />
                </div>

                {/* Phase List */}
                <div className="space-y-1 max-h-48 overflow-y-auto">
                    {phases.map((phase, i) => {
                        const isDone = phase.status === 'done' || phase.status === 'completed';
                        const isCurrent = i === currentPhase;
                        const isPending = !isDone && !isCurrent;

                        return (
                            <div
                                key={i}
                                className={`flex items-center gap-2 p-2 rounded-md transition-all ${
                                    isCurrent
                                        ? 'bg-indigo-100 dark:bg-indigo-900/50 border border-indigo-300 dark:border-indigo-700'
                                        : isDone
                                            ? 'bg-green-50 dark:bg-green-900/20'
                                            : 'opacity-60'
                                }`}
                            >
                                {isDone && <CheckCircle className="text-green-500 w-5 h-5 flex-shrink-0" />}
                                {isCurrent && <PlayCircle className="text-indigo-500 w-5 h-5 flex-shrink-0 animate-pulse" />}
                                {isPending && <Circle className="text-gray-400 w-5 h-5 flex-shrink-0" />}
                                <span className={`text-sm ${isCurrent ? 'font-semibold text-indigo-700 dark:text-indigo-300' : ''}`}>
                                    {phase.name}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Current Phase Highlight */}
                <div className="bg-indigo-50 dark:bg-indigo-900/30 p-3 rounded-lg border border-indigo-200 dark:border-indigo-700">
                    <div className="text-xs text-indigo-600 dark:text-indigo-400 uppercase tracking-wide mb-1">
                        Currently Working On
                    </div>
                    <div className="font-semibold text-indigo-800 dark:text-indigo-200">
                        {currentPhaseName}
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                    <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => callAction({name: 'help_start_phase', payload: {phase: currentPhase, phase_name: currentPhaseName}})}
                    >
                        <HelpCircle className="w-4 h-4 mr-1" />
                        Help Me
                    </Button>

                    {nextPhaseName && (
                        <Button
                            size="sm"
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700"
                            onClick={() => callAction({name: 'next_phase', payload: {action: 'next'}})}
                        >
                            Next Phase
                            <ChevronRight className="w-4 h-4 ml-1" />
                        </Button>
                    )}

                    {!nextPhaseName && (
                        <Button
                            size="sm"
                            className="flex-1 bg-green-600 hover:bg-green-700"
                            onClick={() => callAction({name: 'synthesize_conversation', payload: {}})}
                        >
                            Complete Workshop
                        </Button>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
