import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, useEffect } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ArtPlaceholder } from "../components/ArtPlaceholder";
import { MetricSelect } from "../components/MetricSelect";
import { playerColors, players, type GameRecord } from "../data/mockData";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Score Trends — Wingspan Field Notes" },
      {
        name: "description",
        content: "Track Wingspan player points, nectar, and daily averages over time.",
      },
      { property: "og:title", content: "Score Trends — Wingspan Field Notes" },
      {
        property: "og:description",
        content: "Track Wingspan player points, nectar, and daily averages over time.",
      },
    ],
  }),
  component: TrendsPage,
});

type Metric = "totalPoints" | "nectarPoints" | "avgPerDay";

const metricOptions = [
  { value: "totalPoints", label: "Total Points" },
  { value: "nectarPoints", label: "Nectar Points per Game" },
  { value: "avgPerDay", label: "Average Total Points per Day" },
];

const metricDescriptions: Record<Metric, string> = {
  totalPoints: "Each player's final score, game by game.",
  nectarPoints: "Nectar collected per game — the Oceania expansion currency.",
  avgPerDay: "The average total points scored by each player on a given day.",
};

function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function TrendsPage() {
  const [metric, setMetric] = useState<Metric>("totalPoints");
  
  // New API State Management
  const [liveGames, setLiveGames] = useState<GameRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data whenever the dropdown metric changes
  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Map frontend dropdown selections to backend SQL parameters
        let score = "total";
        let interval = "game";
        let handler = "sum";

        if (metric === "nectarPoints") {
          score = "nectar";
        } else if (metric === "avgPerDay") {
          score = "total";
          interval = "day";
          handler = "avg";
        }

        const response = await fetch("http://localhost:8000/api/trend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ score, interval, handler, players: [] }), // Empty array fetches all players
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Failed to fetch flock data");
        }

        const data = await response.json();
        setLiveGames(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "An unknown error occurred");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [metric]);

  const chartData = useMemo(() => {
    return liveGames.map((game) => {
      // Determine if the backend returned an integer sequence (game) or a date string (day/month)
      let displayDate = String(game.date);
      if (displayDate.includes("-")) {
        displayDate = formatDate(displayDate);
      } else {
        displayDate = `Game ${displayDate}`;
      }

      const row: Record<string, string | number> = { date: displayDate };
      
      for (const r of game.results) {
        // The Python backend outputs 'totalPoints' for total, and 'nectar' for nectar.
        const valueKey = metric === "nectarPoints" ? "nectar" : "totalPoints";
        // Cast as any because GameRecord types are strict, but backend output is dynamic
        row[r.player] = (r as any)[valueKey] || 0; 
      }
      return row;
    });
  }, [liveGames, metric]);

  const activePlayers = useMemo(() => {
    const names = new Set<string>();
    liveGames.forEach((game) => {
      game.results.forEach((r) => names.add(r.player));
    });
    return Array.from(names);
  }, [liveGames]);

  // A dynamic color palette to replace the hardcoded mock colors
  const colorPalette = [
    "var(--chart-1)",
    "var(--chart-2)",
    "var(--chart-3)",
    "var(--chart-4)",
    "var(--chart-5)",
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-primary">
            Chapter I — Observations
          </p>
          <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">Score Trends</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            A season of games, sketched like a migration chart. Choose a metric
            to trace how each member of the flock has fared.
          </p>
        </div>
        <MetricSelect
          label="Chart metric"
          value={metric}
          options={metricOptions}
          onChange={(v) => setMetric(v as Metric)}
        />
      </div>

      <div className="field-card mt-8 p-4 sm:p-8">
        <p className="mb-6 font-serif text-sm italic text-muted-foreground">
          {metricDescriptions[metric]}
        </p>
        <div className="h-90 w-full min-h-[300px]">
          {isLoading ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Retrieving field notes...
            </div>
          ) : error ? (
            <div className="flex h-full items-center justify-center text-destructive">
              Error: {error}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid strokeDasharray="4 6" stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  stroke="var(--muted-foreground)"
                  tick={{ fontSize: 12, fontFamily: "Nunito Sans, sans-serif" }}
                  tickLine={false}
                />
                <YAxis
                  stroke="var(--muted-foreground)"
                  tick={{ fontSize: 12, fontFamily: "Nunito Sans, sans-serif" }}
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "0.75rem",
                    fontFamily: "Nunito Sans, sans-serif",
                    fontSize: 13,
                    color: "var(--popover-foreground)",
                  }}
                />
                <Legend
                  wrapperStyle={{ fontFamily: "Nunito Sans, sans-serif", fontSize: 13 }}
                />
                {activePlayers.map((p, index) => (
                  <Line
                    key={p}
                    type="monotone"
                    dataKey={p}
                    stroke={colorPalette[index % colorPalette.length]}
                    strokeWidth={2.5}
                    dot={{ r: 4, strokeWidth: 2, fill: "var(--card)" }}
                    activeDot={{ r: 6 }}
                    animationDuration={700}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <ArtPlaceholder label="Bird card art slot — e.g. featured bird of the season" className="h-40" />
        <ArtPlaceholder label="Watercolor habitat background slot" className="h-40" />
        <ArtPlaceholder label="Player avatar / flock illustration slot" className="h-40" />
      </div>
    </div>
  );
}