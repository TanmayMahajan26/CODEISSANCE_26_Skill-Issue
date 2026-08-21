"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

// The backend expects x-www-form-urlencoded
const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [error, setError] = useState<string | null>(null);
  const login = useAuthStore((state) => state.login);
  const router = useRouter();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const fillCredentials = (role: string) => {
    setValue("username", `${role}@kovi.in`);
    setValue("password", "strongpassword");
  };

    const onSubmit = async (data: LoginForm) => {
    setError(null);
    try {
      const formData = new URLSearchParams();
      formData.append("username", data.username.trim());
      formData.append("password", data.password);

      const response = await api.post("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      // Assuming backend returns { access_token: "...", token_type: "bearer" }
      const token = response.data.access_token;

      if (typeof window !== "undefined") {
        localStorage.setItem("accessToken", token);
      }

      // Fetch user profile
      const userResponse = await api.get("/auth/me");

      login(userResponse.data, token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Invalid credentials");
    }
  };

  return (
    <div className="w-full h-screen flex items-center justify-center bg-[#EAEAEA]">
      <div className="glass-panel w-full max-w-md p-10 flex flex-col items-center">
        <div className="w-16 h-16 bg-black text-white rounded-full flex items-center justify-center font-bold text-3xl mb-6">
          Nº
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome Back</h2>
        <p className="text-sm text-gray-500 mb-8">Sign in to Kovi</p>

        <form onSubmit={handleSubmit(onSubmit)} className="w-full flex flex-col gap-5">
          {error && (
            <div className="bg-red-50 text-red-500 text-sm p-3 rounded-xl text-center font-medium">
              {error}
            </div>
          )}
          
          <div>
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2 block">
              Username
            </label>
            <input
              {...register("username")}
              type="text"
              className="w-full px-4 py-3 rounded-2xl border-none bg-gray-50 focus:ring-2 focus:ring-[#E2604B] text-gray-900 text-sm"
              placeholder="e.g. admin"
            />
            {errors.username && <p className="text-red-500 text-xs mt-1">{errors.username.message}</p>}
          </div>

          <div>
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2 block">
              Password
            </label>
            <input
              {...register("password")}
              type="password"
              className="w-full px-4 py-3 rounded-2xl border-none bg-gray-50 focus:ring-2 focus:ring-[#E2604B] text-gray-900 text-sm"
              placeholder="••••••••"
            />
            {errors.password && <p className="text-red-500 text-xs mt-1">{errors.password.message}</p>}
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full accent-coral text-white font-semibold py-3 rounded-2xl mt-4 shadow-lg hover:opacity-90 transition-opacity flex justify-center items-center h-12"
          >
            {isSubmitting ? <Loader2 className="animate-spin" size={20} /> : "Sign In"}
          </button>
        </form>
        
        <div className="mt-8 pt-6 border-t border-gray-100 w-full flex flex-col gap-3">
          <p className="text-xs text-gray-500 text-center font-medium">Demo Quick Logins</p>
          <div className="flex justify-center gap-2 flex-wrap">
            <button
              type="button"
              onClick={() => fillCredentials("admin")}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("manager")}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
            >
              Manager
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("rm1")}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
            >
              RM 1
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("rm2")}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
            >
              RM 2
            </button>
            <button
              type="button"
              onClick={() => fillCredentials("manager")}
              className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs rounded-lg transition-colors"
              title="Reviewers are mapped to the Manager role"
            >
              Reviewer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
