import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
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
import { games, playerColors, players } from "../data/mockData";

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
  avgPerDay: "Running average of each player's total points across game days.",
};

function formatDate(iso: string) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function TrendsPage() {
  const [metric, setMetric] = useState<Metric>("totalPoints");

  const chartData = useMemo(() => {
    const running: Record<string, { sum: number; n: number }> = {};
    return games.map((game) => {
      const row: Record<string, string | number> = { date: formatDate(game.date) };
      for (const r of game.results) {
        if (metric === "avgPerDay") {
          const acc = (running[r.player] ??= { sum: 0, n: 0 });
          acc.sum += r.totalPoints;
          acc.n += 1;
          row[r.player] = Math.round((acc.sum / acc.n) * 10) / 10;
        } else {
          row[r.player] = r[metric];
        }
      }
      return row;
    });
  }, [metric]);

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
        <div className="h-90 w-full">
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
              {players.map((p) => (
                <Line
                  key={p}
                  type="monotone"
                  dataKey={p}
                  stroke={playerColors[p]}
                  strokeWidth={2.5}
                  dot={{ r: 4, strokeWidth: 2, fill: "var(--card)" }}
                  activeDot={{ r: 6 }}
                  animationDuration={700}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
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
