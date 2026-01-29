/**
 * ProblemDefinitionForm - Structured PWS Problem Input
 *
 * Used with cl.AskElementMessage to collect structured problem definition:
 * - Problem statement
 * - Who experiences it
 * - Impact/consequences
 * - Current solutions
 * - Why now
 */

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { AlertCircle, Users, TrendingUp, Lightbulb, Clock } from 'lucide-react';
import { useState } from 'react';

export default function ProblemDefinitionForm() {
    const { onSubmit, initialValues = {}, showCameraTest = true } = props;

    const [formData, setFormData] = useState({
        problemStatement: initialValues.problemStatement || '',
        whoExperiences: initialValues.whoExperiences || '',
        impact: initialValues.impact || '',
        currentSolutions: initialValues.currentSolutions || '',
        whyNow: initialValues.whyNow || ''
    });

    const [errors, setErrors] = useState({});
    const [cameraTestPassed, setCameraTestPassed] = useState(null);

    const validateForm = () => {
        const newErrors = {};

        if (!formData.problemStatement.trim()) {
            newErrors.problemStatement = 'Problem statement is required';
        } else if (formData.problemStatement.length < 20) {
            newErrors.problemStatement = 'Please provide more detail (at least 20 characters)';
        }

        if (!formData.whoExperiences.trim()) {
            newErrors.whoExperiences = 'Please specify who experiences this problem';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        if (validateForm()) {
            callAction({
                name: 'form_submit',
                payload: {
                    formType: 'problem_definition',
                    data: {
                        ...formData,
                        cameraTestPassed
                    }
                }
            });
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: null }));
        }
    };

    const runCameraTest = () => {
        // Simple heuristic: does the problem statement describe observable behavior?
        const statement = formData.problemStatement.toLowerCase();
        const observableKeywords = ['see', 'hear', 'notice', 'observe', 'measure', 'count', 'watch', 'record', '%', 'times', 'minutes', 'hours', 'days'];
        const abstractKeywords = ['feel', 'think', 'believe', 'seems', 'maybe', 'might', 'probably', 'generally'];

        const observableCount = observableKeywords.filter(k => statement.includes(k)).length;
        const abstractCount = abstractKeywords.filter(k => statement.includes(k)).length;

        const passed = observableCount > abstractCount;
        setCameraTestPassed(passed);
    };

    return (
        <Card className="w-full max-w-lg bg-gradient-to-br from-amber-50 to-white dark:from-amber-950 dark:to-slate-900 border-2 border-amber-200 dark:border-amber-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <AlertCircle className="text-amber-600 w-5 h-5" />
                    <span>Define Your Problem</span>
                </CardTitle>
                <CardDescription>
                    A well-defined problem is half-solved. Be specific and observable.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Problem Statement */}
                    <div className="space-y-2">
                        <Label htmlFor="problemStatement" className="text-sm font-medium flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" />
                            Problem Statement *
                        </Label>
                        <Textarea
                            id="problemStatement"
                            placeholder="Describe the problem in specific, observable terms. What exactly is happening (or not happening)?"
                            value={formData.problemStatement}
                            onChange={(e) => handleChange('problemStatement', e.target.value)}
                            className={`min-h-[100px] ${errors.problemStatement ? 'border-red-500' : ''}`}
                        />
                        {errors.problemStatement && (
                            <p className="text-xs text-red-500">{errors.problemStatement}</p>
                        )}

                        {/* Camera Test */}
                        {showCameraTest && formData.problemStatement.length > 20 && (
                            <div className="mt-2">
                                <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={runCameraTest}
                                    className="text-xs"
                                >
                                    📷 Run Camera Test
                                </Button>
                                {cameraTestPassed !== null && (
                                    <p className={`text-xs mt-1 ${cameraTestPassed ? 'text-green-600' : 'text-amber-600'}`}>
                                        {cameraTestPassed
                                            ? '✅ Good! Your problem sounds observable.'
                                            : '⚠️ Consider making your problem more observable. Could a camera record this?'}
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Who Experiences */}
                    <div className="space-y-2">
                        <Label htmlFor="whoExperiences" className="text-sm font-medium flex items-center gap-2">
                            <Users className="w-4 h-4" />
                            Who Experiences This? *
                        </Label>
                        <Input
                            id="whoExperiences"
                            placeholder="e.g., First-time homebuyers in urban areas, age 25-35"
                            value={formData.whoExperiences}
                            onChange={(e) => handleChange('whoExperiences', e.target.value)}
                            className={errors.whoExperiences ? 'border-red-500' : ''}
                        />
                        {errors.whoExperiences && (
                            <p className="text-xs text-red-500">{errors.whoExperiences}</p>
                        )}
                        <p className="text-xs text-gray-500">
                            Be specific: Who exactly suffers from this problem?
                        </p>
                    </div>

                    {/* Impact */}
                    <div className="space-y-2">
                        <Label htmlFor="impact" className="text-sm font-medium flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Impact / Consequences
                        </Label>
                        <Textarea
                            id="impact"
                            placeholder="What happens because of this problem? Lost time, money, opportunity?"
                            value={formData.impact}
                            onChange={(e) => handleChange('impact', e.target.value)}
                            className="min-h-[60px]"
                        />
                    </div>

                    {/* Current Solutions */}
                    <div className="space-y-2">
                        <Label htmlFor="currentSolutions" className="text-sm font-medium flex items-center gap-2">
                            <Lightbulb className="w-4 h-4" />
                            Current Solutions / Workarounds
                        </Label>
                        <Textarea
                            id="currentSolutions"
                            placeholder="How do people currently deal with this? What alternatives exist?"
                            value={formData.currentSolutions}
                            onChange={(e) => handleChange('currentSolutions', e.target.value)}
                            className="min-h-[60px]"
                        />
                    </div>

                    {/* Why Now */}
                    <div className="space-y-2">
                        <Label htmlFor="whyNow" className="text-sm font-medium flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Why Now?
                        </Label>
                        <Input
                            id="whyNow"
                            placeholder="What makes this problem timely? Why solve it now?"
                            value={formData.whyNow}
                            onChange={(e) => handleChange('whyNow', e.target.value)}
                        />
                    </div>

                    {/* Submit Button */}
                    <div className="pt-4">
                        <Button
                            type="submit"
                            className="w-full bg-amber-600 hover:bg-amber-700"
                        >
                            Submit Problem Definition
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}
