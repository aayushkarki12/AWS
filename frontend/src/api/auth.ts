import { apiClient } from "@/api/client";
import type { LoginPayload, RegisterPayload, TokenResponse, UserPublic } from "@/types/auth";

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function register(payload: RegisterPayload): Promise<UserPublic> {
  const { data } = await apiClient.post<UserPublic>("/auth/register", payload);
  return data;
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}

export async function fetchCurrentUser(): Promise<UserPublic> {
  const { data } = await apiClient.get<UserPublic>("/auth/me");
  return data;
}
