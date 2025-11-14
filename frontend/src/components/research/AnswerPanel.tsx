import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, CheckCircle2 } from "lucide-react";

interface Citation {
  url: string;
  title?: string;
}

interface AnswerPanelProps {
  answer: string;
  citations: Citation[];
}

const AnswerPanel = ({ answer, citations }: AnswerPanelProps) => {
  if (!answer) {
    return null;
  }

  return (
    <Card className="p-6">
      <div className="mb-4 flex items-center gap-2">
        <CheckCircle2 className="h-5 w-5 text-success" />
        <h2 className="text-lg font-semibold text-foreground">Answer</h2>
      </div>
      
      <div className="prose prose-sm max-w-none">
        <p className="whitespace-pre-wrap text-card-foreground leading-relaxed">{answer}</p>
      </div>

      {citations.length > 0 && (
        <div className="mt-6 border-t border-border pt-4">
          <h3 className="mb-3 text-sm font-semibold text-foreground">Citations</h3>
          <div className="flex flex-wrap gap-2">
            {citations.map((citation, index) => (
              <a
                key={index}
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group"
              >
                <Badge
                  variant="secondary"
                  className="flex items-center gap-2 py-1.5 transition-colors hover:bg-accent"
                >
                  <span className="text-xs">{citation.title || `Source ${index + 1}`}</span>
                  <ExternalLink className="h-3 w-3 opacity-70 transition-opacity group-hover:opacity-100" />
                </Badge>
              </a>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

export default AnswerPanel;
