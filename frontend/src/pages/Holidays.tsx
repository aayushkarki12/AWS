import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";

import { useAuth } from "@/auth/AuthContext";
import * as holidaysApi from "@/api/holidays";
import { getApiErrorMessage } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { formatDate } from "@/utils/format";

function CreateHolidayDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [date, setDate] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => holidaysApi.createHoliday({ name, holiday_date: date }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["holidays"] });
      setName("");
      setDate("");
      onClose();
    },
    onError: (e) => setError(getApiErrorMessage(e)),
  });

  return (
    <Dialog open={open} onClose={onClose} title="Add holiday">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
        className="flex flex-col gap-4"
      >
        {error && <p className="text-[13px] text-coral-glow">{error}</p>}
        <div className="flex flex-col gap-1.5">
          <Label>Name</Label>
          <Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="New Year's Day" />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Date</Label>
          <Input type="date" required value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        <div className="flex justify-end gap-2 pt-1">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Add holiday
          </Button>
        </div>
      </form>
    </Dialog>
  );
}

export default function Holidays() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin" || user?.role === "super_admin";
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["holidays"],
    queryFn: holidaysApi.listHolidays,
  });

  const today = new Date().toISOString().slice(0, 10);

  return (
    <div className="flex flex-col gap-4">
      {isAdmin && (
        <div className="flex justify-end">
          <Button onClick={() => setDialogOpen(true)}>
            <Plus className="h-4 w-4" /> Add holiday
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <p className="p-5 text-sm text-ink-500">Loading…</p>
          ) : !data || data.length === 0 ? (
            <p className="p-5 text-sm text-ink-500">No holidays scheduled.</p>
          ) : (
            <ul>
              {data.map((h) => (
                <li
                  key={h.id}
                  className="flex items-center justify-between border-b border-ink-800/60 px-5 py-3.5 text-sm last:border-0"
                >
                  <span className="text-ink-100">{h.name}</span>
                  <div className="flex items-center gap-2">
                    {h.is_optional && <Badge variant="neutral">Optional</Badge>}
                    {h.holiday_date >= today && <Badge variant="success">Upcoming</Badge>}
                    <span className="w-28 text-right text-ink-400">{formatDate(h.holiday_date)}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <CreateHolidayDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  );
}
