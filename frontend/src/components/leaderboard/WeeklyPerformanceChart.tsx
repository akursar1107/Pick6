import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { WeekPerformance } from "@/types/leaderboard";
import {
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Line,
  ComposedChart,
} from "recharts";

interface WeeklyPerformanceChartProps {
  weeklyData: WeekPerformance[];
  bestWeek?: number;
  worstWeek?: number;
}

export function WeeklyPerformanceChart({
  weeklyData,
  bestWeek,
  worstWeek,
}: WeeklyPerformanceChartProps) {
  // Sort by week number
  const sortedData = [...weeklyData].sort((a, b) => a.week - b.week);

  // Determine bar colors based on best/worst weeks
  const getBarColor = (week: number) => {
    if (week === bestWeek) {
      return "hsl(142, 76%, 36%)"; // Green for best week
    }
    if (week === worstWeek) {
      return "hsl(0, 84%, 60%)"; // Red for worst week
    }
    return "hsl(217, 91%, 60%)"; // Default blue
  };

  // Custom tooltip
  const CustomTooltip = ({
    active,
    payload,
  }: {
    active?: boolean;
    payload?: Array<{ payload: WeekPerformance }>;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-semibold mb-1">Week {data.week}</p>
          <p className="text-sm">Points: {data.points}</p>
          <p className="text-sm">
            Record: {data.wins}-{data.losses}
          </p>
          <p className="text-sm">Rank: #{data.rank}</p>
          {data.week === bestWeek && (
            <p className="text-sm text-green-600 dark:text-green-400 font-semibold mt-1">
              Best Week 🏆
            </p>
          )}
          {data.week === worstWeek && (
            <p className="text-sm text-red-600 dark:text-red-400 font-semibold mt-1">
              Worst Week
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Weekly Performance</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart
            data={sortedData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="week"
              label={{ value: "Week", position: "insideBottom", offset: -5 }}
              className="text-xs"
            />
            <YAxis
              label={{ value: "Points", angle: -90, position: "insideLeft" }}
              className="text-xs"
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="points" radius={[4, 4, 0, 0]}>
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.week)} />
              ))}
            </Bar>
            {/* Trend line */}
            <Line
              type="monotone"
              dataKey="points"
              stroke="hsl(280, 100%, 70%)"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 5"
            />
          </ComposedChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex flex-wrap gap-4 mt-4 justify-center text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[hsl(217,91%,60%)]" />
            <span>Regular Week</span>
          </div>
          {bestWeek && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-[hsl(142,76%,36%)]" />
              <span>Best Week</span>
            </div>
          )}
          {worstWeek && (
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded bg-[hsl(0,84%,60%)]" />
              <span>Worst Week</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <div className="w-8 h-0.5 bg-[hsl(280,100%,70%)]" />
            <span>Trend</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
