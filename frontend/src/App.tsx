import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { queryClient } from "@/lib/query-client";
import { routes } from "./routes";
import { useAuthStore } from "@/stores/authStore";

function App() {
  const loadUserFromToken = useAuthStore((state) => state.loadUserFromToken);

  // Validate stored token on app load
  useEffect(() => {
    loadUserFromToken();
  }, [loadUserFromToken]);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {routes.map((route) => (
            <Route key={route.path} path={route.path} element={route.element} />
          ))}
        </Routes>
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
