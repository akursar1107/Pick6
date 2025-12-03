// TODO: Implement authentication hook
export function useAuth() {
  return {
    user: null,
    isAuthenticated: false,
    login: async () => {},
    logout: async () => {},
  }
}

