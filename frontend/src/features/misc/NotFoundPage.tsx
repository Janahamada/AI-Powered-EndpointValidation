import { Link } from "react-router-dom";
import { buttonVariants } from "@/components/ui/button";

export function NotFoundPage() {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-24 text-center">
      <div className="text-5xl font-bold text-primary">404</div>
      <p className="text-muted-foreground">This page could not be found.</p>
      <Link to="/dashboard" className={buttonVariants()}>
        Back to dashboard
      </Link>
    </div>
  );
}
