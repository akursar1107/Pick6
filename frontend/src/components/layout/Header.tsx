import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

export function Header() {
  const location = useLocation();
  const isAuthenticated = localStorage.getItem("access_token") !== null;

  const navLinks = [
    { path: "/", label: "Home" },
    { path: "/picks", label: "My Picks", protected: true },
    { path: "/leaderboard", label: "Leaderboard" },
  ];

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link
            to="/"
            className="text-2xl font-bold hover:opacity-80 transition-opacity"
          >
            First6
          </Link>
          <nav className="flex items-center gap-6">
            {navLinks.map((link) => {
              // Skip protected routes if not authenticated
              if (link.protected && !isAuthenticated) return null;

              const isActive = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={cn(
                    "text-sm font-medium transition-colors hover:text-primary",
                    isActive ? "text-primary" : "text-muted-foreground"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
            {!isAuthenticated && (
              <Link
                to="/login"
                className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
              >
                Login
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
