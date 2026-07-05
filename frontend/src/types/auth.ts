export type Role = "super_admin" | "admin" | "employee";

export interface UserPublic {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  is_email_verified: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface RegisterPayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserPublic;
}
