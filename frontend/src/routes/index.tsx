import { lazy } from 'react'
import { RouteObject } from 'react-router-dom'

// Lazy load components for code splitting
const Home = lazy(() => import('@/features/games/components/Home'))
const Login = lazy(() => import('@/features/auth/components/LoginForm'))
const Leaderboard = lazy(() => import('@/features/picks/components/Leaderboard'))

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <Home />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/leaderboard',
    element: <Leaderboard />,
  },
]

