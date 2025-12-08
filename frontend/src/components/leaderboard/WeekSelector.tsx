import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface WeekSelectorProps {
  selectedWeek: number | null;
  onWeekChange: (week: number | null) => void;
  currentWeek?: number;
}

export function WeekSelector({
  selectedWeek,
  onWeekChange,
  currentWeek,
}: WeekSelectorProps) {
  const weeks = Array.from({ length: 18 }, (_, i) => i + 1);

  const handleValueChange = (value: string) => {
    if (value === "all") {
      onWeekChange(null);
    } else {
      onWeekChange(parseInt(value, 10));
    }
  };

  return (
    <Select
      value={selectedWeek === null ? "all" : selectedWeek.toString()}
      onValueChange={handleValueChange}
    >
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select week" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Weeks</SelectItem>
        {weeks.map((week) => (
          <SelectItem
            key={week}
            value={week.toString()}
            className={week === currentWeek ? "font-semibold" : ""}
          >
            Week {week}
            {week === currentWeek && " (Current)"}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
