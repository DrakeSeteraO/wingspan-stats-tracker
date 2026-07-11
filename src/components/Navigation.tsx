import { Link } from "@tanstack/react-router";
import { Bird } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

const navLinks = [
  { to: "/", label: "Trends" },
  { to: "/ledger", label: "Ledger" },
  { to: "/oracle", label: "Aviary Oracle" },
] as const;

export function Navigation() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-3">
          {/* Wingspan logo placeholder — drop your logo asset here */}
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-dashed border-primary/50 bg-primary/10 text-primary">
            <Bird className="h-5 w-5" />
          </span>
          <span className="font-serif text-lg font-semibold tracking-wide sm:text-xl">
            Wingspan <span className="italic text-muted-foreground">Field Notes</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              activeOptions={{ exact: link.to === "/" }}
              activeProps={{
                className: "bg-primary/15 text-primary",
              }}
              inactiveProps={{
                className: "text-muted-foreground hover:bg-muted hover:text-foreground",
              }}
              className="rounded-full px-3 py-2 text-sm font-semibold transition-colors sm:px-4"
            >
              {link.label}
            </Link>
          ))}
          <div className="ml-1 sm:ml-3">
            <ThemeToggle />
          </div>
        </nav>
      </div>
    </header>
  );
}