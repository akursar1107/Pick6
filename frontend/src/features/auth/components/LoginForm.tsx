import { useState, FormEvent } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "sonner";
import { handleAuthError } from "@/lib/auth-errors";

interface LoginFormProps {
  onSuccess?: () => void;
}

interface LocationState {
  from?: {
    pathname: string;
  };
}

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isLoading } = useAuthStore();

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
    general?: string;
  }>({});

  // Validate email format
  const validateEmail = (email: string): boolean => {
    if (!email) {
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Validate form fields
  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!email) {
      newErrors.email = "Email is required";
    } else if (!validateEmail(email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!password) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});

    // Validate form
    if (!validateForm()) {
      return;
    }

    try {
      // Call login from auth store
      await login(email, password);

      // Show success toast
      toast.success("Login successful! Welcome back.");

      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }

      // Get intended destination from location state
      const state = location.state as LocationState;
      const from = state?.from?.pathname || "/picks";

      // Redirect to intended destination
      navigate(from, { replace: true });
    } catch (error) {
      // Parse error and get user-friendly message
      const errorMessage = handleAuthError(error);

      // Show error toast
      toast.error(errorMessage);

      // Also set inline error for form display
      setErrors({
        general: errorMessage,
      });
    }
  };

  // Clear errors when user starts typing
  const handleEmailChange = (value: string) => {
    setEmail(value);
    if (errors.email || errors.general) {
      setErrors({ ...errors, email: undefined, general: undefined });
    }
  };

  const handlePasswordChange = (value: string) => {
    setPassword(value);
    if (errors.password || errors.general) {
      setErrors({ ...errors, password: undefined, general: undefined });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="w-full max-w-md p-8 space-y-8 border rounded-lg shadow-sm">
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-center">First6 Login</h1>
          <p className="text-sm text-center text-muted-foreground">
            Enter your credentials to access your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* General error message */}
          {errors.general && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md">
              {errors.general}
            </div>
          )}

          {/* Email field */}
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => handleEmailChange(e.target.value)}
              disabled={isLoading}
              className={errors.email ? "border-destructive" : ""}
              autoComplete="email"
              autoFocus
            />
            {errors.email && (
              <p className="text-sm text-destructive">{errors.email}</p>
            )}
          </div>

          {/* Password field */}
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => handlePasswordChange(e.target.value)}
              disabled={isLoading}
              className={errors.password ? "border-destructive" : ""}
              autoComplete="current-password"
            />
            {errors.password && (
              <p className="text-sm text-destructive">{errors.password}</p>
            )}
          </div>

          {/* Submit button */}
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Logging in...
              </>
            ) : (
              "Log in"
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
