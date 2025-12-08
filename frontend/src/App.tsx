import { useEffect, Suspense } from "react";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { queryClient } from "@/lib/query-client";
import { routes } from "./routes";
import { useAuthStore } from "@/stores/authStore";
import { Spinner } from "@/components/ui/spinner";

// Create router with Suspense wrapper and future flags to suppress v7 warnings
const router = createBrowserRouter(
  routes.map((route) => ({
    ...route,
    element: (
      <Suspense
        fallback={
          <div className="flex items-center justify-center min-h-screen">
            <Spinner size="lg" />
          </div>
        }
      >
        {route.element}
      </Suspense>
    ),
  })),
  {
    future: {
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    },
  }
);

function App() {
  const loadUserFromToken = useAuthStore((state) => state.loadUserFromToken);

  // Validate stored token on app load
  useEffect(() => {
    loadUserFromToken();
  }, [loadUserFromToken]);

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
