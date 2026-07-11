import { createFileRoute } from "@tanstack/react-router";
import { Egg, Sparkles, Trophy } from "lucide-react";
import { useState } from "react";
import { MetricSelect } from "../components/MetricSelect";
import { playerColors, predictions } from "../data/mockData";

export const Route = createFileRoute("/oracle")({
  head: () => ({
    meta: [
      { title: "Aviary Oracle — Wingspan Field Notes" },
      {
        name: "description",
        content: "Forecasted Wingspan stats: predicted winners, expected points, and egg counts.",
      },
      { property: "og:title", content: "Aviary Oracle — Wingspan Field Notes" },
      {
        property: "og:description",
        content: "Forecasted Wingspan stats: predicted winners, expected points, and egg counts.",
      },
    ],
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

function OraclePage() {
  const [forecast, setForecast] = useState<Forecast>("nextGamePoints");
  const cards = predictions[forecast];
  const Icon = forecastIcons[forecast];

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-primary">
            Chapter III — Auguries
          </p>
          <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">The Aviary Oracle</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            Reading the flight patterns of games past to divine what the next
            game night may hold. Take each augury with a grain of birdseed.
          </p>
        </div>
        <MetricSelect
          label="Forecast"
          value={forecast}
          options={forecastOptions}
          onChange={(v) => setForecast(v as Forecast)}
        />
      </div>

      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <div key={c.player} className="field-card watercolor-wash relative overflow-hidden p-6">
            <div className="flex items-center justify-between">
              <span
                className="flex h-9 w-9 items-center justify-center rounded-full"
                style={{ backgroundColor: `color-mix(in oklab, ${playerColors[c.player]} 20%, transparent)` }}
              >
                <Icon className="h-4.5 w-4.5" style={{ color: playerColors[c.player] }} />
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
                style={{ width: `${c.confidence}%`, backgroundColor: playerColors[c.player] }}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="field-card mt-8 p-6 sm:p-8">
        <h2 className="text-2xl font-semibold">How the Oracle divines</h2>
        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
          These forecasts are simple projections from your game history — recent
          form, running averages, and win momentum. Once your real database is
          connected, this page can run genuine models over the full record.
        </p>
      </div>
    </div>
  );
}