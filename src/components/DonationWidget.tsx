import { Coffee, X } from "lucide-react";
import { useState } from "react";

export function DonationWidget() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Support the site"
        className="fixed bottom-5 right-5 z-50 flex h-13 w-13 items-center justify-center rounded-full bg-primary p-4 text-primary-foreground shadow-nest transition-transform hover:scale-110"
      >
        <Coffee className="h-6 w-6" />
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-foreground/40 p-4 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Donation"
            className="field-card relative w-full max-w-sm p-8 text-center shadow-nest"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setOpen(false)}
              aria-label="Close"
              className="absolute right-4 top-4 rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
            <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
              <Coffee className="h-7 w-7" />
            </span>
            <h2 className="text-2xl font-semibold">A seed for the feeder?</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              If these field notes brighten your game nights, consider tossing a little birdseed our
              way to keep the site flying.
            </p>

            {/* Updated Button -> Anchor Tag */}
            <a
              href="https://buymeacoffee.com/DrakeSetera"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 block w-full rounded-full bg-primary px-6 py-3 text-sm font-bold text-primary-foreground transition-opacity hover:opacity-90"
              onClick={() => setOpen(false)}
            >
              Buy me a coffee
            </a>

            <button
              className="mt-3 text-xs font-semibold text-muted-foreground hover:text-foreground"
              onClick={() => setOpen(false)}
            >
              Maybe next migration
            </button>
          </div>
        </div>
      )}
    </>
  );
}
