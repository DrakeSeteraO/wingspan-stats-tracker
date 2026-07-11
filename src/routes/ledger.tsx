import { createFileRoute } from "@tanstack/react-router";
import { Egg, Feather, Trophy } from "lucide-react";
import { useMemo, useState } from "react";
import { MetricSelect } from "../components/MetricSelect";
import { ArtPlaceholder } from "../components/ArtPlaceholder";
import { games, mostPlayedBirds, playerColors, players } from "../data/mockData";

export const Route = createFileRoute("/ledger")({
  head: () => ({
    meta: [
      { title: "The Ledger — Wingspan Field Notes" },
      {
        name: "description",
        content: "Exact Wingspan statistics: wins per player, record scores, and most played birds.",
      },
      { property: "og:title", content: "The Ledger — Wingspan Field Notes" },
      {
        property: "og:description",
        content: "Exact Wingspan statistics: wins per player, record scores, and most played birds.",
      },
    ],
  }),
  component: LedgerPage,
});

type View = "wins" | "highScore" | "birds";

const viewOptions = [
  { value: "wins", label: "Total Wins per Player" },
  { value: "highScore", label: "Highest Single-Game Score" },
  { value: "birds", label: "Most Played Bird" },
];

function LedgerPage() {
  const [view, setView] = useState<View>("wins");

  const winStats = useMemo(
    () =>
      players
        .map((p) => {
          const results = games.flatMap((g) => g.results.filter((r) => r.player === p));
          const wins = games.filter((g) => g.winner === p).length;
          const totalPoints = results.reduce((s, r) => s + r.totalPoints, 0);
          return {
            player: p,
            wins,
            games: results.length,
            winRate: Math.round((wins / games.length) * 100),
            avgPoints: Math.round((totalPoints / results.length) * 10) / 10,
            totalEggs: results.reduce((s, r) => s + r.eggs, 0),
          };
        })
        .sort((a, b) => b.wins - a.wins),
    [],
  );

  const highScores = useMemo(
    () =>
      players
        .map((p) => {
          let best = { points: 0, date: "" };
          for (const g of games) {
            const r = g.results.find((x) => x.player === p);
            if (r && r.totalPoints > best.points) best = { points: r.totalPoints, date: g.date };
          }
          return { player: p, ...best };
        })
        .sort((a, b) => b.points - a.points),
    [],
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-primary">
            Chapter II — The Record Book
          </p>
          <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">The Ledger</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            Exact figures, carefully inked. Every win, record score, and
            favorite bird from the flock's game nights.
          </p>
        </div>
        <MetricSelect
          label="Statistic"
          value={view}
          options={viewOptions}
          onChange={(v) => setView(v as View)}
        />
      </div>

      {view === "wins" && (
        <div className="field-card mt-8 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/60 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                <th className="px-4 py-4 sm:px-6">Player</th>
                <th className="px-4 py-4 text-right">Wins</th>
                <th className="hidden px-4 py-4 text-right sm:table-cell">Games</th>
                <th className="px-4 py-4 text-right">Win Rate</th>
                <th className="hidden px-4 py-4 text-right sm:table-cell">Avg Points</th>
                <th className="hidden px-4 py-4 text-right md:table-cell">Total Eggs</th>
              </tr>
            </thead>
            <tbody>
              {winStats.map((s, i) => (
                <tr key={s.player} className="border-b border-border/60 last:border-0">
                  <td className="px-4 py-4 sm:px-6">
                    <span className="flex items-center gap-3 font-semibold">
                      <span
                        className="h-3 w-3 rounded-full"
                        style={{ backgroundColor: playerColors[s.player] }}
                      />
                      {s.player}
                      {i === 0 && <Trophy className="h-4 w-4 text-nectar" />}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right font-serif text-lg font-semibold">{s.wins}</td>
                  <td className="hidden px-4 py-4 text-right text-muted-foreground sm:table-cell">{s.games}</td>
                  <td className="px-4 py-4 text-right">{s.winRate}%</td>
                  <td className="hidden px-4 py-4 text-right sm:table-cell">{s.avgPoints}</td>
                  <td className="hidden px-4 py-4 text-right md:table-cell">{s.totalEggs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {view === "highScore" && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {highScores.map((s, i) => (
            <div key={s.player} className="field-card p-6">
              <div className="flex items-center justify-between">
                <span
                  className="h-3 w-3 rounded-full"
                  style={{ backgroundColor: playerColors[s.player] }}
                />
                {i === 0 && <Trophy className="h-4 w-4 text-nectar" />}
              </div>
              <p className="mt-4 text-sm font-semibold text-muted-foreground">{s.player}'s best</p>
              <p className="mt-1 font-serif text-4xl font-semibold">{s.points}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                {new Date(s.date + "T00:00:00").toLocaleDateString("en-US", {
                  month: "long",
                  day: "numeric",
                  year: "numeric",
                })}
              </p>
            </div>
          ))}
        </div>
      )}

      {view === "birds" && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {mostPlayedBirds.map((b, i) => (
            <div key={b.bird} className="field-card flex gap-4 p-5">
              <ArtPlaceholder label="Bird art" className="h-24 w-20 shrink-0" />
              <div className="min-w-0">
                <p className="flex items-center gap-2 font-serif text-lg font-semibold leading-tight">
                  {b.bird}
                  {i === 0 && <Feather className="h-4 w-4 shrink-0 text-primary" />}
                </p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {b.habitat}
                </p>
                <p className="mt-3 text-sm">
                  Played <span className="font-bold">{b.timesPlayed}×</span>
                </p>
                <p className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Egg className="h-3.5 w-3.5" /> {b.avgPoints} avg pts
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}