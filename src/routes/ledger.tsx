import { createFileRoute } from "@tanstack/react-router";
import { Egg, Feather, Trophy, ArrowDownWideNarrow } from "lucide-react";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
    ],
  }),
  component: LedgerPage,
});

type View = "wins" | "highScore" | "birds";

// The keys we allow users to sort the table by
type SortKey = "wins" | "games" | "win_rate" | "average" | "total";

const viewOptions = [
  { value: "wins", label: "Total Wins per Player" },
  { value: "highScore", label: "High Scores" },
  { value: "birds", label: "Most Played Bird" },
];

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

export interface AchieverDetail {
  name: string;
  date: string | number;
}

export interface RecordHighScore {
  name: string;
  score: number;
  achievers: AchieverDetail[];
}

export interface HighScoreReturn {
  personal: PlayerHighScoreData[];
  overall: RecordHighScore[];
}

const ledgerCache = new Map<string, LedgerRecord[]>();
const highScoreCache = new Map<string, HighScoreReturn>();

function LedgerPage() {
  const [view, setView] = useState<View>("wins");
  const [sortKey, setSortKey] = useState<SortKey>("wins");

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
    setWinRatePlayerCount((prev) => (prev + 1) % 4);
    // If they click the win rate header, automatically sort by it
    handleSort("win_rate");
  };

  useEffect(() => {
    const fetchAllData = async () => {
      if (ledgerCache.has("ledgerData") && highScoreCache.has("highScoreData")) {
        setLedgerData(ledgerCache.get("ledgerData")!);
        setHighScoreData(highScoreCache.get("highScoreData")!);
        setIsLoading(false);
        setIsHighScoreLoading(false);
        return;
      }

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

        // Default sort is by wins
        const sortedLedger = ledgerDataRaw.sort((a, b) => b.wins - a.wins);
        setLedgerData(sortedLedger);
        ledgerCache.set("ledgerData", sortedLedger);

        highDataRaw.personal.sort((a, b) => b.score - a.score);
        setHighScoreData(highDataRaw);
        highScoreCache.set("highScoreData", highDataRaw);
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

  // Handle Sorting Logic
  const handleSort = (key: SortKey) => {
    setSortKey(key);

    // Create a new array to trigger a re-render
    const sorted = [...ledgerData].sort((a, b) => {
      // If we are sorting by win rate and viewing a specific player count, use that specific metric
      if (key === "win_rate") {
        const aRate = [a.win_rate, a.win_rate_2p ?? 0, a.win_rate_3p ?? 0, a.win_rate_4p ?? 0][
          winRatePlayerCount
        ];
        const bRate = [b.win_rate, b.win_rate_2p ?? 0, b.win_rate_3p ?? 0, b.win_rate_4p ?? 0][
          winRatePlayerCount
        ];
        return bRate - aRate;
      }
      return b[key] - a[key];
    });
    setLedgerData(sorted);
  };

  const formatDate = (dateVal: string | number | undefined) => {
    if (!dateVal) return "No date found";
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
                <tr className="border-b border-border bg-muted/60 text-xs font-bold uppercase tracking-widest text-muted-foreground [&>th]:px-4 [&>th]:py-4">
                  <th className="sm:px-6">Player</th>

                  {/* Wins Header */}
                  <th className="text-right">
                    <button
                      onClick={() => handleSort("wins")}
                      className={`inline-flex items-center gap-1 hover:text-primary transition-colors ${sortKey === "wins" ? "text-primary" : ""}`}
                    >
                      WINS {sortKey === "wins" && <ArrowDownWideNarrow className="h-3 w-3" />}
                    </button>
                  </th>

                  {/* Games Header */}
                  <th className="hidden text-right sm:table-cell">
                    <button
                      onClick={() => handleSort("games")}
                      className={`inline-flex items-center gap-1 hover:text-primary transition-colors ${sortKey === "games" ? "text-primary" : ""}`}
                    >
                      GAMES {sortKey === "games" && <ArrowDownWideNarrow className="h-3 w-3" />}
                    </button>
                  </th>

                  {/* Win Rate Header */}
                  <th className="text-right">
                    <button
                      onClick={win_rate_clicked}
                      className={`inline-flex items-center gap-1 hover:text-primary transition-colors ${sortKey === "win_rate" ? "text-primary" : ""}`}
                    >
                      {select_win_rate[winRatePlayerCount]} WIN RATE
                      {sortKey === "win_rate" && <ArrowDownWideNarrow className="h-3 w-3" />}
                    </button>
                  </th>

                  {/* Average Score Header */}
                  <th className="hidden text-right sm:table-cell">
                    <button
                      onClick={() => handleSort("average")}
                      className={`inline-flex items-center gap-1 hover:text-primary transition-colors ${sortKey === "average" ? "text-primary" : ""}`}
                    >
                      AVG SCORE{" "}
                      {sortKey === "average" && <ArrowDownWideNarrow className="h-3 w-3" />}
                    </button>
                  </th>

                  {/* Total Score Header */}
                  <th className="hidden text-right md:table-cell">
                    <button
                      onClick={() => handleSort("total")}
                      className={`inline-flex items-center gap-1 hover:text-primary transition-colors ${sortKey === "total" ? "text-primary" : ""}`}
                    >
                      TOTAL SCORE{" "}
                      {sortKey === "total" && <ArrowDownWideNarrow className="h-3 w-3" />}
                    </button>
                  </th>
                </tr>
              </thead>

              {/* Animated Table Body */}
              <motion.tbody layout>
                <AnimatePresence>
                  {ledgerData.map((s, i) => (
                    <motion.tr
                      layout
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ type: "spring", stiffness: 150, damping: 30 }}
                      key={s.username}
                      className="border-b border-border/60 last:border-0 [&>td]:px-4 [&>td]:py-4"
                    >
                      <td className="sm:px-6">
                        <span className="flex items-center gap-3 font-semibold">
                          <span
                            className="h-3 w-3 rounded-full shrink-0"
                            style={{ backgroundColor: playerColors[s.name] || "var(--chart-5)" }}
                          />
                          {s.name}
                          {i === 0 && <Trophy className="h-4 w-4 text-nectar shrink-0" />}
                        </span>
                      </td>
                      <td className="text-right font-serif text-lg font-semibold">{s.wins}</td>
                      <td className="hidden text-right text-muted-foreground sm:table-cell">
                        {s.games}
                      </td>
                      <td className="text-right">
                        {
                          [s.win_rate, s.win_rate_2p ?? 0, s.win_rate_3p ?? 0, s.win_rate_4p ?? 0][
                            winRatePlayerCount
                          ]
                        }
                        %
                      </td>
                      <td className="hidden text-right sm:table-cell">{s.average}</td>
                      <td className="hidden text-right md:table-cell">
                        {s.total.toLocaleString()}
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </motion.tbody>
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
          ) : (
            highScoreData && (
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
                      <p className="mt-4 text-sm font-semibold text-muted-foreground">
                        Highest Score
                      </p>
                      <p className="mt-1 font-serif text-4xl font-semibold">{s.score}</p>
                      <p className="mt-2 text-xs text-muted-foreground">{formatDate(s.date)}</p>
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
                      {/* Iterate over all tied players chronologically */}
                      <div className="mt-4 pt-4 border-t border-border/60 flex flex-col gap-3">
                        {s.achievers.map((achiever, idx) => (
                          <div key={idx}>
                            <p className="text-sm font-semibold flex items-center gap-2">
                              <span
                                className="h-2 w-2 rounded-full"
                                style={{
                                  backgroundColor: playerColors[achiever.name] || "var(--chart-5)",
                                }}
                              />
                              {achiever.name}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {formatDate(achiever.date)}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )
          )}
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
