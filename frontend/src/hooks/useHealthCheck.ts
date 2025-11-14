import { useState, useEffect } from "react";
import { HEALTH_CHECK_ENDPOINT } from "@/config/api";

export type HealthStatus = "online" | "offline" | "checking";

export const useHealthCheck = (intervalMs: number = 30000) => {
  const [status, setStatus] = useState<HealthStatus>("checking");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(HEALTH_CHECK_ENDPOINT, {
          method: "GET",
          signal: AbortSignal.timeout(5000),
        });

        if (response.ok) {
          setStatus("online");
        } else {
          setStatus("offline");
        }
      } catch (error) {
        setStatus("offline");
      }
    };

    // Check immediately on mount
    checkHealth();

    // Set up interval for periodic checks
    const interval = setInterval(checkHealth, intervalMs);

    return () => clearInterval(interval);
  }, [intervalMs]);

  return status;
};
