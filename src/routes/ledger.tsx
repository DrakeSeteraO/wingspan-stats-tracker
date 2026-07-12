import { createFileRoute } from "@tanstack/react-router";
import { Egg, Feather, Trophy } from "lucide-react";
import { useState, useEffect } from "react";
import { MetricSelect } from "../components/MetricSelect";
import { ArtPlaceholder } from "../components/ArtPlaceholder";
import { mostPlayedBirds, playerColors } from "../data/mockData";
import { getApiUrl } from "@/lib/api-config";

export const Route = createFileRoute("/ledger")({
  head: () => ({
    meta: [
      { title: "The Ledger — Wingspan Field Notes" },
      {
        name: "description",
        content:
          "Exact Wingspan statistics: wins per player, record scores, and most played birds.",
      },
      { property: "og:title", content: "The Ledger — Wingspan Field Notes" },
      {
        property: "og:description",
        content:
          "Exact Wingspan statistics: wins per player, record scores, and most played birds.",
      },
    ],
  }),
  component: LedgerPage,
});

type View = "wins" | "highScore" | "birds";

const viewOptions = [
  { value: "wins", label: "Total Wins per Player" },
  { value: "highScore", label: "High Scores" },
  { value: "birds", label: "Most Played Bird" },
];

// --- Types matching the Python API ---
export interface LedgerRecord {
  name: string;
  username: string;
  games: number;
  average: number;
  total: number;
  wins: number;
  win_rate: number;
  win_rate_2p?: number;
  win_rate_3p?: number;
  win_rate_4p?: number;
}

export interface PlayerHighScoreData {
  name: string;
  score: number;
  date: string | number;
}

export interface RecordHighScore {
  name: string;
  score: number;
  achiever: string;
  date: string | number;
}

export interface HighScoreReturn {
  personal: PlayerHighScoreData[];
  overall: RecordHighScore[];
}

function LedgerPage() {
  const [view, setView] = useState<View>("wins");

  // Ledger State
  const [ledgerData, setLedgerData] = useState<LedgerRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // High Score State
  const [highScoreData, setHighScoreData] = useState<HighScoreReturn | null>(null);
  const [isHighScoreLoading, setIsHighScoreLoading] = useState(true);
  const [highScoreError, setHighScoreError] = useState<string | null>(null);

  // Win Rate Toggle State
  const [winRatePlayerCount, setWinRatePlayerCount] = useState(0);
  const select_win_rate = ["OVERALL", "2 PLAYER", "3 PLAYER", "4 PLAYER"];

  const win_rate_clicked = () => {
    setWinRatePlayerCount((winRatePlayerCount) => (winRatePlayerCount + 1) % 4);
  };

  // Fetch all API data when the component mounts
  useEffect(() => {
    const fetchAllData = async () => {
      setIsLoading(true);
      setError(null);
      setIsHighScoreLoading(true);
      setHighScoreError(null);

      try {
        const [ledgerRes, highRes] = await Promise.all([
          fetch(getApiUrl("/api/ledger"), {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          }),
          fetch(getApiUrl("/api/high-score"), {
            method: "GET",
            headers: { "Content-Type": "application/json" },
          }),
        ]);

        if (!ledgerRes.ok) throw new Error("Failed to fetch ledger data");
        if (!highRes.ok) throw new Error("Failed to fetch high score data");

        const ledgerDataRaw: LedgerRecord[] = await ledgerRes.json();
        const highDataRaw: HighScoreReturn = await highRes.json();

        // Save ledger data
        setLedgerData(ledgerDataRaw.sort((a, b) => b.wins - a.wins));

        // Sort personal records highest to lowest, then save high score data
        highDataRaw.personal.sort((a, b) => b.score - a.score);
        setHighScoreData(highDataRaw);
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "An unknown error occurred";
        setError(errMsg);
        setHighScoreError(errMsg);
      } finally {
        setIsLoading(false);
        setIsHighScoreLoading(false);
      }
    };

    fetchAllData();
  }, []);

  // Helper to cleanly format string/int dates from the API
  const formatDate = (dateVal: string | number | undefined) => {
    if (!dateVal) return "No date found";
    // If it's a raw date string without a time, append T00:00:00 to prevent timezone shift bugs
    const dateStr = String(dateVal).includes("T") ? String(dateVal) : `${dateVal}T00:00:00`;
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-primary">
            Chapter II — The Record Book
          </p>
          <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">The Ledger</h1>
          <p className="mt-3 max-w-xl text-muted-foreground">
            Exact figures, carefully inked. Every win, record score, and favorite bird from the
            flock's game nights.
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
        <div className="field-card mt-8 overflow-hidden min-h-[300px]">
          {isLoading ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
              Retrieving the record book...
            </div>
          ) : error ? (
            <div className="flex h-64 items-center justify-center text-destructive">
              Error: {error}
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/60 text-xs font-bold uppercase tracking-widest text-muted-foreground">
                  <th className="px-4 py-4 sm:px-6">Player</th>
                  <th className="px-4 py-4 text-right">Wins</th>
                  <th className="hidden px-4 py-4 text-right sm:table-cell">Games</th>
                  <th className="px-4 py-4 text-right">
                    <button onClick={win_rate_clicked} className="hover:text-primary transition-colors">
                      {select_win_rate[winRatePlayerCount]} WIN RATE
                    </button>
                  </th>
                  <th className="hidden px-4 py-4 text-right sm:table-cell">Avg Score</th>
                  <th className="hidden px-4 py-4 text-right md:table-cell">Total Score</th>
                </tr>
              </thead>
              <tbody>
                {ledgerData.map((s, i) => (
                  <tr key={s.username} className="border-b border-border/60 last:border-0">
                    <td className="px-4 py-4 sm:px-6">
                      <span className="flex items-center gap-3 font-semibold">
                        <span
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: playerColors[s.name] || "var(--chart-5)" }}
                        />
                        {s.name}
                        {i === 0 && <Trophy className="h-4 w-4 text-nectar" />}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-right font-serif text-lg font-semibold">
                      {s.wins}
                    </td>
                    <td className="hidden px-4 py-4 text-right text-muted-foreground sm:table-cell">
                      {s.games}
                    </td>
                    <td className="px-4 py-4 text-right">
                      {
                        [s.win_rate, s.win_rate_2p ?? 0, s.win_rate_3p ?? 0, s.win_rate_4p ?? 0][
                          winRatePlayerCount
                        ]
                      }
                      %
                    </td>
                    <td className="hidden px-4 py-4 text-right sm:table-cell">{s.average}</td>
                    <td className="hidden px-4 py-4 text-right md:table-cell">
                      {s.total.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* New API-Driven High Scores View */}
      {view === "highScore" && (
        <div className="min-h-[300px]">
          {isHighScoreLoading ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground field-card mt-8">
              Digging through the archives...
            </div>
          ) : highScoreError ? (
            <div className="flex h-64 items-center justify-center text-destructive field-card mt-8">
              Error: {highScoreError}
            </div>
          ) : highScoreData && (
            <>
              {/* 1. Personal Records Section */}
              <h2 className="mt-10 text-2xl font-semibold">Personal Bests</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {highScoreData.personal.map((s, i) => (
                  <div key={s.name} className="field-card p-6">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-3 font-semibold">
                        <span
                          className="h-3 w-3 rounded-full"
                          style={{ backgroundColor: playerColors[s.name] || "var(--chart-5)" }}
                        />
                        {s.name}
                      </span>
                      {i === 0 && <Trophy className="h-4 w-4 text-nectar" />}
                    </div>
                    <p className="mt-4 text-sm font-semibold text-muted-foreground">Highest Score</p>
                    <p className="mt-1 font-serif text-4xl font-semibold">{s.score}</p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      {formatDate(s.date)}
                    </p>
                  </div>
                ))}
              </div>

              {/* 2. Global Records Section */}
              <h2 className="mt-12 text-2xl font-semibold">Global Records</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {highScoreData.overall.map((s) => (
                  <div key={s.name} className="field-card p-6 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-primary">{s.name}</span>
                        <Trophy className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <p className="mt-2 font-serif text-4xl font-semibold">{s.score}</p>
                    </div>
                    <div className="mt-4 pt-4 border-t border-border/60">
                      <p className="text-sm font-semibold flex items-center gap-2">
                        <span
                          className="h-2 w-2 rounded-full"
                          style={{ backgroundColor: playerColors[s.achiever] || "var(--chart-5)" }}
                        />
                        {s.achiever}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatDate(s.date)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Most Played Birds View (Mock Data) */}
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