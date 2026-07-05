import { describe, expect, it } from "vitest";

import { formatMinutes, formatTime, statusLabel } from "@/utils/format";

describe("formatTime", () => {
  it("returns an em dash for null", () => {
    expect(formatTime(null)).toBe("—");
  });

  it("formats an ISO timestamp as a local time string", () => {
    const result = formatTime("2026-07-05T09:30:00Z");
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });
});

describe("formatMinutes", () => {
  it("returns an em dash for null", () => {
    expect(formatMinutes(null)).toBe("—");
  });

  it("formats minutes as hours and minutes", () => {
    expect(formatMinutes(0)).toBe("0h 0m");
    expect(formatMinutes(90)).toBe("1h 30m");
    expect(formatMinutes(125)).toBe("2h 5m");
  });
});

describe("statusLabel", () => {
  it("replaces underscores with spaces and title-cases", () => {
    expect(statusLabel("half_day")).toBe("Half Day");
    expect(statusLabel("present")).toBe("Present");
    expect(statusLabel("wfh")).toBe("Wfh");
  });
});
