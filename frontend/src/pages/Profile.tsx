import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, Loader2 } from "lucide-react";

import * as employeesApi from "@/api/employees";
import { getApiErrorMessage, resolveUploadUrl } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";
import { formatDate, statusLabel } from "@/utils/format";

const MAX_AVATAR_MB = 3;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default function Profile() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    data: profile,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["employees", "me"],
    queryFn: employeesApi.fetchMyProfile,
    retry: false,
  });

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");

  useEffect(() => {
    if (!profile) return;
    setFirstName(profile.first_name);
    setLastName(profile.last_name);
    setPhone(profile.phone ?? "");
  }, [profile]);

  const updateMutation = useMutation({
    mutationFn: () =>
      employeesApi.updateMyProfile({
        first_name: firstName,
        last_name: lastName,
        phone: phone || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees", "me"] });
      showToast({ variant: "success", title: "Profile updated" });
    },
    onError: (e) =>
      showToast({ variant: "error", title: "Update failed", description: getApiErrorMessage(e) }),
  });

  const avatarMutation = useMutation({
    mutationFn: (file: File) => employeesApi.uploadMyAvatar(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["employees", "me"] });
      showToast({ variant: "success", title: "Profile picture updated" });
    },
    onError: (e) =>
      showToast({ variant: "error", title: "Upload failed", description: getApiErrorMessage(e) }),
  });

  function handleFileSelected(file: File | undefined) {
    if (!file) return;
    if (!ACCEPTED_TYPES.includes(file.type)) {
      showToast({
        variant: "error",
        title: "Unsupported file type",
        description: "Please upload a JPEG, PNG, or WebP image.",
      });
      return;
    }
    if (file.size > MAX_AVATAR_MB * 1024 * 1024) {
      showToast({
        variant: "error",
        title: "File too large",
        description: `Please upload an image smaller than ${MAX_AVATAR_MB}MB.`,
      });
      return;
    }
    avatarMutation.mutate(file);
  }

  if (isError) {
    return (
      <p className="text-sm text-ink-500">
        No employee profile is associated with this account.
      </p>
    );
  }

  if (isLoading || !profile) {
    return <p className="text-sm text-ink-500">Loading profile…</p>;
  }

  const avatarUrl = resolveUploadUrl(profile.profile_picture_url);
  const initials = `${profile.first_name[0] ?? ""}${profile.last_name[0] ?? ""}`.toUpperCase();

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardContent className="flex flex-wrap items-center gap-6">
          <div className="relative">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="group relative flex h-24 w-24 items-center justify-center overflow-hidden rounded-full border border-ink-600 bg-ink-800"
              aria-label="Change profile picture"
            >
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="h-full w-full object-cover" />
              ) : (
                <span className="font-display text-2xl text-amber-glow">{initials}</span>
              )}
              <div className="absolute inset-0 flex items-center justify-center bg-ink-950/60 opacity-0 transition-opacity group-hover:opacity-100">
                {avatarMutation.isPending ? (
                  <Loader2 className="h-5 w-5 animate-spin text-ink-100" />
                ) : (
                  <Camera className="h-5 w-5 text-ink-100" />
                )}
              </div>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES.join(",")}
              className="hidden"
              onChange={(e) => handleFileSelected(e.target.files?.[0])}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <h2 className="font-display text-xl text-ink-50">
              {profile.first_name} {profile.last_name}
            </h2>
            <p className="text-sm text-ink-400">{profile.email}</p>
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="neutral">{profile.employee_code}</Badge>
              <Badge variant={profile.role_name === "employee" ? "neutral" : "warning"}>
                {statusLabel(profile.role_name)}
              </Badge>
              {profile.job_title && <Badge variant="neutral">{profile.job_title}</Badge>}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Edit Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateMutation.mutate();
            }}
            className="flex flex-col gap-4"
          >
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-1.5">
                <Label>First name</Label>
                <Input required value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label>Last name</Label>
                <Input required value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>
            </div>

            <div className="flex flex-col gap-1.5 sm:w-1/2">
              <Label>Phone</Label>
              <Input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="e.g. +1 555 123 4567"
              />
            </div>

            <div className="flex justify-end">
              <Button type="submit" disabled={updateMutation.isPending}>
                Save changes
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Details</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div className="flex justify-between border-b border-ink-800/60 py-1.5">
            <span className="text-ink-500">Employee code</span>
            <span className="text-ink-200">{profile.employee_code}</span>
          </div>
          <div className="flex justify-between border-b border-ink-800/60 py-1.5">
            <span className="text-ink-500">Department</span>
            <span className="text-ink-200">{profile.department_name ?? "—"}</span>
          </div>
          <div className="flex justify-between border-b border-ink-800/60 py-1.5">
            <span className="text-ink-500">Manager</span>
            <span className="text-ink-200">{profile.manager_name ?? "—"}</span>
          </div>
          <div className="flex justify-between border-b border-ink-800/60 py-1.5">
            <span className="text-ink-500">Joined</span>
            <span className="text-ink-200">
              {profile.date_of_joining ? formatDate(profile.date_of_joining) : "—"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
