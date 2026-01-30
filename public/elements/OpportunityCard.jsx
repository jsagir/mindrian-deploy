/**
 * OpportunityCard - Bank of Opportunities Item
 *
 * Displays a discovered opportunity with actions to explore or dismiss
 * Used in the Bank of Opportunities feature
 *
 * Props:
 * - id: string (unique identifier)
 * - title: string (opportunity title)
 * - problem: string (problem description)
 * - evidence_quality: number (1-5 stars)
 * - domain: string (e.g., "Healthcare", "FinTech")
 * - priority: 'high' | 'medium' | 'low'
 * - source: string (where it was discovered)
 * - frameworks: string[] (relevant frameworks)
 * - created_at: string (timestamp)
 */

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Lightbulb, Star, Trash2, ArrowRight, Clock, Tag, Sparkles } from 'lucide-react';

export default function OpportunityCard() {
  const {
    id = '',
    title = 'Untitled Opportunity',
    problem = '',
    evidence_quality = 3,
    domain = 'General',
    priority = 'medium',
    source = '',
    frameworks = [],
    created_at = '',
    show_delete_confirm = false
  } = props;

  // Priority styling
  const priorityConfig = {
    high: {
      border: 'border-l-red-500',
      bg: 'bg-red-50',
      badge: 'bg-red-100 text-red-700',
      label: 'High Priority'
    },
    medium: {
      border: 'border-l-yellow-500',
      bg: 'bg-yellow-50',
      badge: 'bg-yellow-100 text-yellow-700',
      label: 'Medium Priority'
    },
    low: {
      border: 'border-l-green-500',
      bg: 'bg-green-50',
      badge: 'bg-green-100 text-green-700',
      label: 'Low Priority'
    }
  };

  const priorityStyle = priorityConfig[priority] || priorityConfig.medium;

  // Evidence quality stars
  const EvidenceStars = ({ quality }) => (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map(i => (
              <Star
                key={i}
                className={`h-4 w-4 ${
                  i <= quality
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-200'
                }`}
              />
            ))}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p>Evidence Quality: {quality}/5</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return '';
    }
  };

  return (
    <Card className={`border-l-4 ${priorityStyle.border} overflow-hidden transition-all hover:shadow-md`}>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-semibold leading-tight">{title}</h4>
              {source && (
                <p className="text-xs text-muted-foreground mt-1">
                  Discovered via {source}
                </p>
              )}
            </div>
          </div>
          <Badge variant="outline" className="flex-shrink-0">{domain}</Badge>
        </div>
      </CardHeader>

      <CardContent className="pb-3">
        <p className="text-sm text-muted-foreground mb-3">{problem}</p>

        {/* Metadata row */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-3">
            <EvidenceStars quality={evidence_quality} />
            <Badge className={`${priorityStyle.badge} text-xs`}>
              {priorityStyle.label}
            </Badge>
          </div>
          {created_at && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              {formatDate(created_at)}
            </div>
          )}
        </div>

        {/* Frameworks tags */}
        {frameworks && frameworks.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {frameworks.map((f, i) => (
              <Badge key={i} variant="secondary" className="text-xs">
                <Tag className="h-3 w-3 mr-1" />
                {f}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-0 gap-2">
        {/* Explore Button */}
        <Button
          size="sm"
          className="flex-1"
          onClick={() => sendUserMessage(`Let's explore the "${title}" opportunity deeper. What frameworks should I use to validate this?`)}
        >
          <Sparkles className="h-4 w-4 mr-1" />
          Explore
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>

        {/* Delete with confirmation */}
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button size="sm" variant="ghost" className="px-2">
              <Trash2 className="h-4 w-4 text-muted-foreground" />
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remove Opportunity?</AlertDialogTitle>
              <AlertDialogDescription>
                This will remove "{title}" from your opportunity bank. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Keep it</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => callAction({
                  name: 'remove_opportunity',
                  payload: { id, title }
                })}
              >
                Remove
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  );
}
