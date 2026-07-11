import { Feather } from "lucide-react";

interface ArtPlaceholderProps {
  label: string;
  className?: string;
}

/** Drop-in slot for real Wingspan bird card art / background assets. */
export function ArtPlaceholder({ label, className = "" }: ArtPlaceholderProps) {
  return (
    <div
      className={`watercolor-wash flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-primary/40 text-center ${className}`}
    >
      <Feather className="h-5 w-5 text-primary/60" />
      <span className="px-3 text-xs font-semibold text-muted-foreground">{label}</span>
    </div>
  );
}