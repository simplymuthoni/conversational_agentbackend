import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2 } from "lucide-react";

interface ResearchFormProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const ResearchForm = ({ onSubmit, isLoading }: ResearchFormProps) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <Textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your research question here…"
          disabled={isLoading}
          className="min-h-[120px] resize-none bg-background pr-12 text-base"
        />
      </div>
      <Button
        type="submit"
        disabled={!query.trim() || isLoading}
        className="w-full sm:w-auto"
        size="lg"
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Researching...
          </>
        ) : (
          <>
            <Send className="mr-2 h-4 w-4" />
            Ask
          </>
        )}
      </Button>
    </form>
  );
};

export default ResearchForm;
