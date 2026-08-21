import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: string;
  username: string;
  email: string;
  role: "ADMIN" | "MANAGER" | "RM" | "CREDIT_APPROVER";
}

interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: (user, token) => {
        // We sync the token to localStorage for the axios interceptor
        if (typeof window !== "undefined") {
          localStorage.setItem("accessToken", token);
        }
        const mappedUser = {
          ...user,
          username: user.username || user.email.split("@")[0],
        };
        set({ user: mappedUser, token });
      },
      logout: () => {
        if (typeof window !== "undefined") {
          localStorage.removeItem("accessToken");
        }
        set({ user: null, token: null });
      },
    }),
    {
      name: "auth-storage", // name of the item in the storage (must be unique)
    }
  )
);
