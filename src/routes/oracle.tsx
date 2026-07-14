import { createFileRoute } from "@tanstack/react-router";
import { Egg, Sparkles, Trophy } from "lucide-react";
import { useState, useEffect } from "react";
import { MetricSelect } from "../components/MetricSelect";
import { playerColors } from "../data/mockData";
import { getApiUrl } from "@/lib/api-config";

export const Route = createFileRoute("/oracle")({
  head: () => ({
    meta: [{ title: "Aviary Oracle — Wingspan Field Notes" }],
  }),
  component: OraclePage,
});

type Forecast = "nextGamePoints" | "nextWinner" | "eggCount";

const forecastOptions = [
  { value: "nextGamePoints", label: "Estimated Points Next Game" },
  { value: "nextWinner", label: "Predicted Winner for Next Match" },
  { value: "eggCount", label: "Expected Egg Count" },
];

const forecastIcons: Record<Forecast, typeof Sparkles> = {
  nextGamePoints: Sparkles,
  nextWinner: Trophy,
  eggCount: Egg,
};

export interface Prediction {
  title: string;
  player: string;
  value: string;
  confidence: number;
  note: string;
}

export type OracleData = Record<Forecast, Prediction[]>;

function OraclePage() {
  const [forecast, setForecast] = useState<Forecast>("nextGamePoints");
  const [oracleData, setOracleData] = useState<OracleData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOracle = async () => {
      try {
        const response = await fetch(getApiUrl("/api/oracle"));
        if (!response.ok) throw new Error("Failed to consult the oracle.");
        const data = await response.json();
        setOracleData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred");
      } finally {
        setIsLoading(false);
      }
    };
    fetchOracle();
  }, []);

  const Icon = forecastIcons[forecast];
  const cards = oracleData ? oracleData[forecast] : [];

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-primary">
            Chapter III — Auguries
          </p>
          <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">The Aviary Oracle</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            Reading the flight patterns of games past to divine what the next game night may hold.
            Take each augury with a grain of birdseed.
          </p>
        </div>
        <MetricSelect
          label="Forecast"
          value={forecast}
          options={forecastOptions}
          onChange={(v) => setForecast(v as Forecast)}
        />
      </div>

      <div className="mt-8 min-h-[250px]">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center text-muted-foreground field-card">
            Consulting the bones...
          </div>
        ) : error ? (
          <div className="flex h-64 items-center justify-center text-destructive field-card">
            Error: {error}
          </div>
        ) : cards.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-muted-foreground field-card">
            Not enough historical data to generate this forecast yet.
          </div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {cards.map((c) => (
              <div
                key={c.player}
                className="field-card watercolor-wash relative overflow-hidden p-6"
              >
                <div className="flex items-center justify-between">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-full"
                    style={{
                      backgroundColor: `color-mix(in oklab, ${playerColors[c.player] || "var(--chart-5)"} 20%, transparent)`,
                    }}
                  >
                    <Icon
                      className="h-4.5 w-4.5"
                      style={{ color: playerColors[c.player] || "var(--chart-5)" }}
                    />
                  </span>
                  <span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-bold text-secondary-foreground">
                    {c.confidence}% confidence
                  </span>
                </div>
                <p className="mt-5 text-sm font-semibold text-muted-foreground">{c.player}</p>
                <p className="mt-1 font-serif text-4xl font-semibold">{c.value}</p>
                <p className="mt-3 font-serif text-sm italic text-muted-foreground">"{c.note}"</p>
                <div className="mt-5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${c.confidence}%`,
                      backgroundColor: playerColors[c.player] || "var(--chart-5)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
