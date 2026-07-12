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
import { players, type GameRecord } from "../data/mockData";
import { Switch } from "@/components/ui/switch";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { ChevronDown } from "lucide-react";
import { getApiUrl } from "@/lib/api-config";

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

const scoreOptions = [
  { value: "total", label: "Total" },
  { value: "bird", label: "Bird" },
  { value: "bonus_card", label: "Bonus Card" },
  { value: "goals", label: "End of Round Goals" },
  { value: "eggs", label: "Eggs" },
  { value: "food", label: "Food on Cards" },
  { value: "tucked", label: "Tucked Cards" },
  { value: "nectar", label: "Nectar" },
];

const intervalOptions = [
  { value: "game", label: "Individual Game" },
  { value: "day", label: "Day" },
  { value: "month", label: "Month" },
  { value: "year", label: "Year" },
  { value: "all", label: "All Time" },
];

const handlerOptions = [
  { value: "sum", label: "Sum" },
  { value: "avg", label: "Avg" },
  { value: "max", label: "Max" },
  { value: "min", label: "Min" },
];

function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function TrendsPage() {
  const [score, setScore] = useState<string>("total");
  const [interval, setInterval] = useState<string>("game");
  const [handler, setHandler] = useState<string>("sum");
  const [selectedPlayers, setSelectedPlayers] = useState<string[]>([]); // [] = All
  const [showTrend, setShowTrend] = useState<boolean>(true);
  
  // New API State Management
  const [liveGames, setLiveGames] = useState<GameRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch data whenever any filter changes
  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const response = await fetch(getApiUrl("/api/trend"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            score,
            interval,
            handler,
            players: selectedPlayers, // [] means all players (backend contract)
          }),
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
  }, [score, interval, handler, selectedPlayers]);

const activePlayers = useMemo(() => {
    const names = new Set<string>();
    liveGames.forEach((game) => {
      game.results.forEach((r) => names.add(r.player));
    });
    return Array.from(names);
  }, [liveGames]);

  const chartData = useMemo(() => {
    // 1. Build the base data rows
    const baseData = liveGames.map((game) => {
      let displayDate = String(game.date);
      if (displayDate.includes("-")) {
        displayDate = formatDate(displayDate);
      } else {
        displayDate = `Game ${displayDate}`;
      }

      const row: Record<string, string | number> = { date: displayDate };
      
      for (const r of game.results) {
        // Backend returns { player, <metricKey>: value } where metricKey is
        // "totalPoints" when score === "total", otherwise the raw score name.
        const valueKey = score === "total" ? "totalPoints" : score;
        row[r.player] = (r as any)[valueKey] ?? 0;
      }
      return row;
    });

    // 2. Calculate Linear Regression (Line of Best Fit) for each player
    activePlayers.forEach((player) => {
      let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
      let count = 0;

      // Gather stats for the math
      baseData.forEach((row, x) => {
        const y = row[player] as number | undefined;
        if (y !== undefined) {
          sumX += x;
          sumY += y;
          sumXY += x * y;
          sumXX += x * x;
          count++;
        }
      });

      // Calculate slope (m) and intercept (b)
      if (count > 1) {
        const m = (count * sumXY - sumX * sumY) / (count * sumXX - sumX * sumX);
        const b = (sumY - m * sumX) / count;

        // Apply the newly calculated trendline points to the data object
        baseData.forEach((row, x) => {
          row[`${player}_trend`] = Math.round((m * x + b) * 10) / 10;
        });
      }
    });

    return baseData;
  }, [liveGames, score, activePlayers]);


  // A dynamic color palette to replace the hardcoded mock colors
  const colorPalette = [
    "var(--chart-1)",
    "var(--chart-2)",
    "var(--chart-3)",
    "var(--chart-4)",
    "var(--chart-5)",
  ];

  const allPlayersSelected = selectedPlayers.length === 0;
  const togglePlayer = (name: string) => {
    setSelectedPlayers((prev) =>
      prev.includes(name) ? prev.filter((p) => p !== name) : [...prev, name],
    );
  };
  const playersLabel = allPlayersSelected
    ? "All players"
    : selectedPlayers.length === 1
      ? selectedPlayers[0]
      : `${selectedPlayers.length} selected`;

  const currentScoreLabel =
    scoreOptions.find((o) => o.value === score)?.label ?? score;
  const currentHandlerLabel =
    handlerOptions.find((o) => o.value === handler)?.label ?? handler;
  const currentIntervalLabel =
    intervalOptions.find((o) => o.value === interval)?.label ?? interval;

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
      </div>

      {/* Control panel */}
      <div className="field-card mt-8 p-4 sm:p-6 lg:p-8">
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 lg:gap-8">
          <MetricSelect
            label="Score"
            value={score}
            options={scoreOptions}
            onChange={setScore}
          />
          <MetricSelect
            label="Interval"
            value={interval}
            options={intervalOptions}
            onChange={setInterval}
          />
          <MetricSelect
            label="Handler"
            value={handler}
            options={handlerOptions}
            onChange={setHandler}
          />
          <label className="flex flex-col gap-1.5">
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
              Players
            </span>
            <Popover>
              <PopoverTrigger asChild>
                <button
                  type="button"
                  className="inline-flex w-full items-center justify-between rounded-full border border-border bg-card py-2.5 pl-5 pr-4 text-sm font-semibold text-card-foreground shadow-feather outline-none transition-colors hover:border-ring focus:border-ring"
                >
                  <span className="truncate">{playersLabel}</span>
                  <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-primary" />
                </button>
              </PopoverTrigger>
              <PopoverContent align="start" className="w-56 p-2">
                <label className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted">
                  <Checkbox
                    checked={allPlayersSelected}
                    onCheckedChange={() => setSelectedPlayers([])}
                  />
                  <span className="text-sm font-semibold">All players</span>
                </label>
                <div className="my-1 h-px bg-border" />
                {players.map((p) => (
                  <label
                    key={p}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 hover:bg-muted"
                  >
                    <Checkbox
                      checked={selectedPlayers.includes(p)}
                      onCheckedChange={() => togglePlayer(p)}
                    />
                    <span className="text-sm">{p}</span>
                  </label>
                ))}
              </PopoverContent>
            </Popover>
          </label>
        </div>

        <div className="mt-5 flex items-center justify-between gap-4 border-t border-border pt-4">
          <p className="font-serif text-sm italic text-muted-foreground">
            {currentHandlerLabel} of {currentScoreLabel.toLowerCase()} by{" "}
            {currentIntervalLabel.toLowerCase()}.
          </p>
          <label className="flex cursor-pointer items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
              Trend line
            </span>
            <Switch checked={showTrend} onCheckedChange={setShowTrend} />
          </label>
        </div>
      </div>

      <div className="field-card mt-8 p-4 sm:p-8">
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
                {/* Real Data Lines */}
                {activePlayers.map((p, index) => (
                  <Line
                    key={p}
                    type="monotone"
                    dataKey={p}
                    name={p}
                    stroke={colorPalette[index % colorPalette.length]}
                    strokeWidth={2.5}
                    dot={{ r: 4, strokeWidth: 2, fill: "var(--card)" }}
                    activeDot={{ r: 6 }}
                    animationDuration={700}
                  />
                ))}

                {/* Dotted Trend Lines */}
                {showTrend && activePlayers.map((p, index) => (
                  <Line
                    key={`${p}_trend`}
                    type="linear"
                    dataKey={`${p}_trend`}
                    name={`${p} Trend`}
                    stroke={colorPalette[index % colorPalette.length]}
                    strokeWidth={2}
                    strokeDasharray="5 5" // Makes it dotted
                    dot={false} // Removes the points on the trendline
                    activeDot={false} // Stops the user from hovering directly on the trendline
                    legendType="none" // Hides the extra lines from the legend
                    animationDuration={700}
                    opacity={0.4} // Fades it into the background
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