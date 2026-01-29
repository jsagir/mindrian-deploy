/**
 * ScenarioSetupForm - Structured Input Form for Scenario Analysis
 *
 * Used with cl.AskElementMessage to collect structured scenario setup data:
 * - Domain selection
 * - Focal question
 * - Time horizon
 * - Key stakeholders
 */

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useState } from 'react';

export default function ScenarioSetupForm() {
    const { onSubmit, initialValues = {} } = props;

    const [formData, setFormData] = useState({
        domain: initialValues.domain || '',
        focalQuestion: initialValues.focalQuestion || '',
        timeHorizon: initialValues.timeHorizon || '2035',
        stakeholders: initialValues.stakeholders || '',
        decisionContext: initialValues.decisionContext || ''
    });

    const [errors, setErrors] = useState({});

    const timeHorizonOptions = [
        { value: '2030', label: '2030 (5 years)' },
        { value: '2035', label: '2035 (10 years)' },
        { value: '2040', label: '2040 (15 years)' },
        { value: '2050', label: '2050 (25 years)' },
    ];

    const validateForm = () => {
        const newErrors = {};

        if (!formData.domain.trim()) {
            newErrors.domain = 'Domain is required';
        }

        if (!formData.focalQuestion.trim()) {
            newErrors.focalQuestion = 'Focal question is required';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        if (validateForm()) {
            // Call the submit callback with form data
            callAction({
                name: 'form_submit',
                payload: {
                    formType: 'scenario_setup',
                    data: formData
                }
            });
        }
    };

    const handleChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: null }));
        }
    };

    return (
        <Card className="w-full max-w-lg bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950 dark:to-slate-900 border-2 border-indigo-200 dark:border-indigo-800">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <span>🔮</span>
                    <span>Scenario Analysis Setup</span>
                </CardTitle>
                <CardDescription>
                    Define your scenario exploration parameters
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Domain */}
                    <div className="space-y-2">
                        <Label htmlFor="domain" className="text-sm font-medium">
                            Domain / Industry *
                        </Label>
                        <Input
                            id="domain"
                            placeholder="e.g., Healthcare, Renewable Energy, Higher Education"
                            value={formData.domain}
                            onChange={(e) => handleChange('domain', e.target.value)}
                            className={errors.domain ? 'border-red-500' : ''}
                        />
                        {errors.domain && (
                            <p className="text-xs text-red-500">{errors.domain}</p>
                        )}
                    </div>

                    {/* Focal Question */}
                    <div className="space-y-2">
                        <Label htmlFor="focalQuestion" className="text-sm font-medium">
                            Focal Question *
                        </Label>
                        <Textarea
                            id="focalQuestion"
                            placeholder="What decision are you trying to inform? e.g., 'Should we invest in telehealth services?'"
                            value={formData.focalQuestion}
                            onChange={(e) => handleChange('focalQuestion', e.target.value)}
                            className={`min-h-[80px] ${errors.focalQuestion ? 'border-red-500' : ''}`}
                        />
                        {errors.focalQuestion && (
                            <p className="text-xs text-red-500">{errors.focalQuestion}</p>
                        )}
                        <p className="text-xs text-gray-500">
                            The question your scenario exploration will help answer
                        </p>
                    </div>

                    {/* Time Horizon */}
                    <div className="space-y-2">
                        <Label htmlFor="timeHorizon" className="text-sm font-medium">
                            Time Horizon
                        </Label>
                        <Select
                            value={formData.timeHorizon}
                            onValueChange={(value) => handleChange('timeHorizon', value)}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select time horizon" />
                            </SelectTrigger>
                            <SelectContent>
                                {timeHorizonOptions.map(opt => (
                                    <SelectItem key={opt.value} value={opt.value}>
                                        {opt.label}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                        <p className="text-xs text-gray-500">
                            How far into the future should we look?
                        </p>
                    </div>

                    {/* Stakeholders */}
                    <div className="space-y-2">
                        <Label htmlFor="stakeholders" className="text-sm font-medium">
                            Key Stakeholders
                        </Label>
                        <Input
                            id="stakeholders"
                            placeholder="e.g., Patients, Providers, Payers, Regulators"
                            value={formData.stakeholders}
                            onChange={(e) => handleChange('stakeholders', e.target.value)}
                        />
                        <p className="text-xs text-gray-500">
                            Who will be affected by these futures? (comma-separated)
                        </p>
                    </div>

                    {/* Decision Context */}
                    <div className="space-y-2">
                        <Label htmlFor="decisionContext" className="text-sm font-medium">
                            Decision Context
                        </Label>
                        <Textarea
                            id="decisionContext"
                            placeholder="Any additional context about your situation..."
                            value={formData.decisionContext}
                            onChange={(e) => handleChange('decisionContext', e.target.value)}
                            className="min-h-[60px]"
                        />
                    </div>

                    {/* Submit Button */}
                    <div className="pt-4">
                        <Button
                            type="submit"
                            className="w-full bg-indigo-600 hover:bg-indigo-700"
                        >
                            Begin Scenario Analysis
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
}
