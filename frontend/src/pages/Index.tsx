import { useState } from "react";
import { toast } from "sonner";
import Header from "@/components/research/Header";
import ResearchForm from "@/components/research/ResearchForm";
import Timeline, { TimelineEvent } from "@/components/research/Timeline";
import AnswerPanel from "@/components/research/AnswerPanel";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { API_ENDPOINTS } from "@/config/api";

interface Citation {
  url: string;
  title?: string;
}

const Index = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);

  const handleResearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setTimeline([]);
    setAnswer("");
    setCitations([]);

    // Add initial event
    const startTime = new Date().toLocaleTimeString();
    setTimeline([
      {
        id: "start",
        timestamp: startTime,
        message: `Started research for: "${query}"`,
      },
    ]);

    try {
      const response = await fetch(API_ENDPOINTS.research, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error(`Backend error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();

      // Add processing events
      const processingTime = new Date().toLocaleTimeString();
      setTimeline((prev) => [
        ...prev,
        {
          id: "processing",
          timestamp: processingTime,
          message: "Processing research data...",
        },
      ]);

      // Simulate timeline events (replace with actual backend events if available)
      if (data.events && Array.isArray(data.events)) {
        data.events.forEach((event: any, index: number) => {
          setTimeout(() => {
            const eventTime = new Date().toLocaleTimeString();
            setTimeline((prev) => [
              ...prev,
              {
                id: `event-${index}`,
                timestamp: eventTime,
                message: event.message || event,
              },
            ]);
          }, index * 300);
        });
      }

      // Add completion event
      const completionTime = new Date().toLocaleTimeString();
      setTimeline((prev) => [
        ...prev,
        {
          id: "complete",
          timestamp: completionTime,
          message: "Research completed successfully",
        },
      ]);

      // Set answer and citations
      setAnswer(data.answer || "No answer provided by the backend.");
      setCitations(data.citations || []);

      toast.success("Research completed!");
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to connect to backend";
      setError(errorMessage);
      
      const errorTime = new Date().toLocaleTimeString();
      setTimeline((prev) => [
        ...prev,
        {
          id: "error",
          timestamp: errorTime,
          message: `Error: ${errorMessage}`,
          type: "error",
        },
      ]);

      toast.error("Research failed", {
        description: errorMessage,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mx-auto max-w-6xl space-y-8">
          {/* Research Form */}
          <div className="rounded-2xl bg-card p-6 shadow-sm">
            <ResearchForm onSubmit={handleResearch} isLoading={isLoading} />
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Results Grid */}
          {(timeline.length > 0 || answer) && (
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Timeline */}
              <div className="order-2 lg:order-1">
                <Timeline events={timeline} />
              </div>

              {/* Answer Panel */}
              <div className="order-1 lg:order-2">
                <AnswerPanel answer={answer} citations={citations} />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
