import { ChevronDown } from "lucide-react";

interface MetricSelectProps {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  onChange: (value: string) => void;
}

export function MetricSelect({ label, value, options, onChange }: MetricSelectProps) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <span className="relative block w-full">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none rounded-full border border-border bg-card py-2.5 pl-5 pr-11 text-sm font-semibold text-card-foreground shadow-feather outline-none transition-colors focus:border-ring"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-primary" />
      </span>
    </label>
  );
}