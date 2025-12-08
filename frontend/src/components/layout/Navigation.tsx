import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";

export function Navigation() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-background border-b">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          {/* Left side - Main navigation */}
          <div className="flex items-center space-x-6">
            <Link
              to="/standings"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Standings
            </Link>
            <Link
              to="/best-bets"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Best Bets
            </Link>
            <Link
              to="/analysis"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Analysis
            </Link>
            <Link
              to="/weekly-games"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              Weekly Games
            </Link>
            <Link
              to="/new-pick"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              New Pick
            </Link>
            <Link
              to="/picks"
              className="text-sm font-medium hover:text-primary transition-colors"
            >
              All Picks
            </Link>
            {user && (
              <Link
                to="/admin/scoring"
                className="text-sm font-medium hover:text-primary transition-colors"
              >
                Admin
              </Link>
            )}
          </div>

          {/* Right side - User actions */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link
                  to="/profile"
                  className="text-sm font-medium hover:text-primary transition-colors"
                >
                  Profile
                </Link>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-sm"
                >
                  Logout
                </Button>
              </>
            ) : (
              <Link
                to="/login"
                className="text-sm font-medium hover:text-primary transition-colors"
              >
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
