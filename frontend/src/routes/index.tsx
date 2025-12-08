import { lazy } from "react";
import { RouteObject, Outlet } from "react-router-dom";
import { ProtectedRoute } from "./ProtectedRoute";
import { Layout } from "@/components/layout/Layout";

// Lazy load components for code splitting
const Home = lazy(() => import("@/features/games/components/Home"));
const Login = lazy(() => import("@/features/auth/components/LoginForm"));
const Leaderboard = lazy(
  () => import("@/features/picks/components/Leaderboard")
);
const PicksPage = lazy(() => import("@/features/picks/components/PicksPage"));
const AdminScoringPage = lazy(() => import("@/pages/AdminScoringPage"));
const AdminMonitoringPage = lazy(() => import("@/pages/AdminMonitoringPage"));

// New pages
const StandingsPage = lazy(() => import("@/pages/StandingsPage"));
const BestBetsPage = lazy(() => import("@/pages/BestBetsPage"));
const AnalysisPage = lazy(() => import("@/pages/AnalysisPage"));
const WeeklyGamesPage = lazy(() => import("@/pages/WeeklyGamesPage"));
const NewPickPage = lazy(() => import("@/pages/NewPickPage"));
const ProfilePage = lazy(() => import("@/pages/ProfilePage"));

export const routes: RouteObject[] = [
  {
    path: "/",
    element: (
      <Layout>
        <Outlet />
      </Layout>
    ),
    children: [
      {
        index: true,
        element: <Home />,
      },
      {
        path: "login",
        element: <Login />,
      },
      {
        path: "standings",
        element: <StandingsPage />,
      },
      {
        path: "best-bets",
        element: <BestBetsPage />,
      },
      {
        path: "analysis",
        element: <AnalysisPage />,
      },
      {
        path: "weekly-games",
        element: <WeeklyGamesPage />,
      },
      {
        path: "new-pick",
        element: (
          <ProtectedRoute>
            <NewPickPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "leaderboard",
        element: <Leaderboard />,
      },
      {
        path: "picks",
        element: (
          <ProtectedRoute>
            <PicksPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "profile",
        element: (
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        ),
      },
      {
        path: "admin/scoring",
        element: (
          <ProtectedRoute>
            <AdminScoringPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "admin/monitoring",
        element: (
          <ProtectedRoute>
            <AdminMonitoringPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
];
