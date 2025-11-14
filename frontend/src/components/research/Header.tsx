import { Sparkles } from "lucide-react";
import { useHealthCheck } from "@/hooks/useHealthCheck";
import { ThemeToggle } from "@/components/ThemeToggle";

const Header = () => {
  const healthStatus = useHealthCheck();

  return (
    <header className="border-b border-border bg-card">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary">
              <Sparkles className="h-5 w-5 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-semibold text-foreground">Research Assistant</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
            <div
              className={`h-2.5 w-2.5 rounded-full ${
                healthStatus === "online"
                  ? "bg-green-500"
                  : healthStatus === "offline"
                  ? "bg-red-500"
                  : "bg-yellow-500 animate-pulse"
              }`}
              title={
                healthStatus === "online"
                  ? "Backend online"
                  : healthStatus === "offline"
                  ? "Backend offline"
                  : "Checking connection..."
              }
            />
            <span className="text-xs text-muted-foreground">
              {healthStatus === "online"
                ? "Connected"
                : healthStatus === "offline"
                ? "Disconnected"
                : "Checking..."}
            </span>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
