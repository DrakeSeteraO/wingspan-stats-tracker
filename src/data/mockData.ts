// Mock Wingspan game history — replace with your real SQL data later.
// Shapes are kept flat & simple so swapping in a real API is painless.

export interface PlayerGameResult {
  player: string;
  totalPoints: number;
  nectarPoints: number;
  eggs: number;
  birdsPlayed: number;
  bonusCards: number;
}

export interface GameRecord {
  id: number;
  date: string; // ISO date
  winner: string;
  results: PlayerGameResult[];
}

export const players = ["Robin", "Wren", "Finch", "Jay"] as const;
export type PlayerName = (typeof players)[number];

export const playerColors: Record<string, string> = {
  Robin: "var(--chart-3)",
  Wren: "var(--chart-1)",
  Finch: "var(--chart-4)",
  Jay: "var(--chart-2)",
};

// Define the parameters your Python backend expects
export interface TrendRequestParams {
  score: string;
  interval: string;
  handler: string;
  players: string[];
}

export const fetchTrendData = async (params: TrendRequestParams): Promise<GameRecord[]> => {
  try {
    const response = await fetch("http://localhost:8000/api/trend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      // Pass the dynamic parameters to the backend
      body: JSON.stringify(params), 
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to fetch trend data");
    }

    // The backend returns the exact GameRecord[] structure!
    const data: GameRecord[] = await response.json();
    return data;
    
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
};

export const games: GameRecord[] = [
  {
    id: 1,
    date: "2026-04-04",
    winner: "Wren",
    results: [
      { player: "Robin", totalPoints: 72, nectarPoints: 6, eggs: 14, birdsPlayed: 12, bonusCards: 9 },
      { player: "Wren", totalPoints: 84, nectarPoints: 9, eggs: 18, birdsPlayed: 14, bonusCards: 11 },
      { player: "Finch", totalPoints: 65, nectarPoints: 4, eggs: 11, birdsPlayed: 11, bonusCards: 7 },
      { player: "Jay", totalPoints: 70, nectarPoints: 7, eggs: 13, birdsPlayed: 12, bonusCards: 8 },
    ],
  },
  {
    id: 2,
    date: "2026-04-11",
    winner: "Robin",
    results: [
      { player: "Robin", totalPoints: 88, nectarPoints: 10, eggs: 19, birdsPlayed: 15, bonusCards: 12 },
      { player: "Wren", totalPoints: 79, nectarPoints: 8, eggs: 15, birdsPlayed: 13, bonusCards: 10 },
      { player: "Finch", totalPoints: 71, nectarPoints: 5, eggs: 13, birdsPlayed: 12, bonusCards: 9 },
      { player: "Jay", totalPoints: 62, nectarPoints: 3, eggs: 10, birdsPlayed: 10, bonusCards: 6 },
    ],
  },
  {
    id: 3,
    date: "2026-04-18",
    winner: "Wren",
    results: [
      { player: "Robin", totalPoints: 75, nectarPoints: 7, eggs: 15, birdsPlayed: 13, bonusCards: 8 },
      { player: "Wren", totalPoints: 91, nectarPoints: 11, eggs: 20, birdsPlayed: 15, bonusCards: 13 },
      { player: "Finch", totalPoints: 68, nectarPoints: 6, eggs: 12, birdsPlayed: 11, bonusCards: 8 },
      { player: "Jay", totalPoints: 74, nectarPoints: 8, eggs: 14, birdsPlayed: 12, bonusCards: 9 },
    ],
  },
  {
    id: 4,
    date: "2026-05-02",
    winner: "Jay",
    results: [
      { player: "Robin", totalPoints: 69, nectarPoints: 5, eggs: 12, birdsPlayed: 11, bonusCards: 7 },
      { player: "Wren", totalPoints: 77, nectarPoints: 7, eggs: 14, birdsPlayed: 13, bonusCards: 9 },
      { player: "Finch", totalPoints: 73, nectarPoints: 8, eggs: 15, birdsPlayed: 12, bonusCards: 10 },
      { player: "Jay", totalPoints: 86, nectarPoints: 12, eggs: 17, birdsPlayed: 14, bonusCards: 11 },
    ],
  },
  {
    id: 5,
    date: "2026-05-09",
    winner: "Robin",
    results: [
      { player: "Robin", totalPoints: 93, nectarPoints: 11, eggs: 21, birdsPlayed: 16, bonusCards: 13 },
      { player: "Wren", totalPoints: 81, nectarPoints: 9, eggs: 16, birdsPlayed: 13, bonusCards: 10 },
      { player: "Finch", totalPoints: 70, nectarPoints: 6, eggs: 13, birdsPlayed: 12, bonusCards: 8 },
      { player: "Jay", totalPoints: 78, nectarPoints: 9, eggs: 15, birdsPlayed: 13, bonusCards: 9 },
    ],
  },
  {
    id: 6,
    date: "2026-05-23",
    winner: "Finch",
    results: [
      { player: "Robin", totalPoints: 76, nectarPoints: 8, eggs: 14, birdsPlayed: 13, bonusCards: 9 },
      { player: "Wren", totalPoints: 74, nectarPoints: 6, eggs: 13, birdsPlayed: 12, bonusCards: 8 },
      { player: "Finch", totalPoints: 89, nectarPoints: 10, eggs: 19, birdsPlayed: 15, bonusCards: 12 },
      { player: "Jay", totalPoints: 71, nectarPoints: 7, eggs: 13, birdsPlayed: 12, bonusCards: 8 },
    ],
  },
  {
    id: 7,
    date: "2026-06-06",
    winner: "Wren",
    results: [
      { player: "Robin", totalPoints: 82, nectarPoints: 9, eggs: 17, birdsPlayed: 14, bonusCards: 10 },
      { player: "Wren", totalPoints: 95, nectarPoints: 13, eggs: 22, birdsPlayed: 16, bonusCards: 14 },
      { player: "Finch", totalPoints: 77, nectarPoints: 7, eggs: 15, birdsPlayed: 13, bonusCards: 9 },
      { player: "Jay", totalPoints: 80, nectarPoints: 10, eggs: 16, birdsPlayed: 13, bonusCards: 10 },
    ],
  },
  {
    id: 8,
    date: "2026-06-20",
    winner: "Robin",
    results: [
      { player: "Robin", totalPoints: 90, nectarPoints: 12, eggs: 20, birdsPlayed: 15, bonusCards: 12 },
      { player: "Wren", totalPoints: 83, nectarPoints: 8, eggs: 16, birdsPlayed: 14, bonusCards: 11 },
      { player: "Finch", totalPoints: 74, nectarPoints: 6, eggs: 14, birdsPlayed: 12, bonusCards: 9 },
      { player: "Jay", totalPoints: 85, nectarPoints: 11, eggs: 18, birdsPlayed: 14, bonusCards: 11 },
    ],
  },
  {
    id: 9,
    date: "2026-07-04",
    winner: "Jay",
    results: [
      { player: "Robin", totalPoints: 79, nectarPoints: 8, eggs: 15, birdsPlayed: 13, bonusCards: 10 },
      { player: "Wren", totalPoints: 86, nectarPoints: 10, eggs: 18, birdsPlayed: 14, bonusCards: 11 },
      { player: "Finch", totalPoints: 81, nectarPoints: 9, eggs: 16, birdsPlayed: 14, bonusCards: 10 },
      { player: "Jay", totalPoints: 92, nectarPoints: 13, eggs: 21, birdsPlayed: 16, bonusCards: 13 },
    ],
  },
];

export const mostPlayedBirds = [
  { bird: "American Robin", habitat: "Grassland", timesPlayed: 14, avgPoints: 4.2 },
  { bird: "Barn Owl", habitat: "Forest", timesPlayed: 12, avgPoints: 5.1 },
  { bird: "Ruby-throated Hummingbird", habitat: "Wetland", timesPlayed: 11, avgPoints: 3.8 },
  { bird: "Great Blue Heron", habitat: "Wetland", timesPlayed: 9, avgPoints: 6.4 },
  { bird: "Cedar Waxwing", habitat: "Forest", timesPlayed: 8, avgPoints: 4.9 },
  { bird: "Killdeer", habitat: "Grassland", timesPlayed: 7, avgPoints: 3.5 },
];

export interface Prediction {
  title: string;
  player: string;
  value: string;
  confidence: number; // 0-100
  note: string;
}

export const predictions: Record<string, Prediction[]> = {
  nextGamePoints: [
    { title: "Estimated Points Next Game", player: "Robin", value: "84 pts", confidence: 78, note: "Trending upward over last 3 games" },
    { title: "Estimated Points Next Game", player: "Wren", value: "87 pts", confidence: 82, note: "Most consistent scorer in the flock" },
    { title: "Estimated Points Next Game", player: "Finch", value: "77 pts", confidence: 71, note: "Steady climb since late May" },
    { title: "Estimated Points Next Game", player: "Jay", value: "88 pts", confidence: 75, note: "Hot streak: two wins in last three" },
  ],
  nextWinner: [
    { title: "Predicted Winner", player: "Jay", value: "36%", confidence: 36, note: "Momentum from the July 4th victory" },
    { title: "Predicted Winner", player: "Wren", value: "31%", confidence: 31, note: "Highest average score overall" },
    { title: "Predicted Winner", player: "Robin", value: "22%", confidence: 22, note: "Dangerous when the bonus cards align" },
    { title: "Predicted Winner", player: "Finch", value: "11%", confidence: 11, note: "The quiet underdog — watch the wetlands" },
  ],
  eggCount: [
    { title: "Expected Egg Count", player: "Robin", value: "17 eggs", confidence: 74, note: "Loves a full grassland row" },
    { title: "Expected Egg Count", player: "Wren", value: "19 eggs", confidence: 80, note: "Egg-laying engine builder supreme" },
    { title: "Expected Egg Count", player: "Finch", value: "15 eggs", confidence: 69, note: "Improving clutch sizes each week" },
    { title: "Expected Egg Count", player: "Jay", value: "18 eggs", confidence: 73, note: "Consistent round-4 egg sprints" },
  ],
};