/**
 * Route-level error boundary.
 *
 * Without one, a single render-time exception unmounts the whole React tree
 * and the user gets a blank page with no explanation. This catches the throw,
 * keeps the app shell (and therefore the navigation) alive, and shows what
 * went wrong with a way out.
 *
 * Error boundaries must be class components — there is no hook equivalent.
 */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { RefreshCw } from "lucide-react";
import { ErrorState } from "@/components/common";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Keep the stack in the console for debugging; the UI stays friendly.
    console.error("Unhandled render error:", error, info.componentStack);
  }

  private reset = () => this.setState({ error: null });

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="mx-auto max-w-2xl py-8">
        <ErrorState message="Something went wrong on this page." />
        <div className="mt-4 rounded-lg border bg-muted/40 p-4">
          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Details
          </div>
          <p className="mt-1.5 break-words font-mono text-xs text-foreground/80">{error.message}</p>
          <p className="mt-3 text-xs text-muted-foreground">
            The rest of the app is still available — use the navigation to move elsewhere, or try
            this page again.
          </p>
        </div>
        <div className="mt-4 flex gap-2">
          <Button onClick={this.reset}>
            <RefreshCw /> Try again
          </Button>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Reload page
          </Button>
        </div>
      </div>
    );
  }
}
