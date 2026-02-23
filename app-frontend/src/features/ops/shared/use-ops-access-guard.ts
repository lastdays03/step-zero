"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/providers/AuthProvider";

export function useOpsAccessGuard() {
  const router = useRouter();
  const { isLoggedIn, isAuthReady, canAccessOps } = useAuth();

  useEffect(() => {
    if (!isAuthReady) return;
    if (!isLoggedIn || !canAccessOps) {
      router.replace("/dashboard");
    }
  }, [canAccessOps, isAuthReady, isLoggedIn, router]);

  const canRender = isAuthReady && isLoggedIn && canAccessOps;
  return { canRender, isAuthReady };
}
