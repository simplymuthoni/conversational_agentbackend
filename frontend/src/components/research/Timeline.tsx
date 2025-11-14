import { Clock } from "lucide-react";
import { Card } from "@/components/ui/card";

export interface TimelineEvent {
  id: string;
  timestamp: string;
  message: string;
  type?: "info" | "success" | "error";
}

interface TimelineProps {
  events: TimelineEvent[];
}

const Timeline = ({ events }: TimelineProps) => {
  if (events.length === 0) {
    return null;
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-lg font-semibold text-foreground">Activity Timeline</h2>
      <div className="space-y-4">
        {events.map((event, index) => (
          <div key={event.id} className="relative flex gap-4">
            {/* Timeline line */}
            {index < events.length - 1 && (
              <div className="absolute left-[11px] top-8 h-[calc(100%+1rem)] w-0.5 bg-timeline-line" />
            )}
            
            {/* Timeline dot */}
            <div className="relative flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-timeline-dot">
              <div className="h-2 w-2 rounded-full bg-primary-foreground" />
            </div>
            
            {/* Event content */}
            <div className="flex-1 pb-4">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>{event.timestamp}</span>
              </div>
              <p className="mt-1 text-sm text-card-foreground">{event.message}</p>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default Timeline;
