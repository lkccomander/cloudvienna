export function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export function formatDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(date);
}

export function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function formatBoolean(value?: boolean | null) {
  if (value === null || value === undefined) return "-";
  return value ? "Yes" : "No";
}

export function groupByAgeRange(birthdays: Array<string | null | undefined>) {
  const ranges = [
    { key: "<18", label: "Under 18", total: 0 },
    { key: "18-25", label: "18-25", total: 0 },
    { key: "26-35", label: "26-35", total: 0 },
    { key: "36-45", label: "36-45", total: 0 },
    { key: "46+", label: "46+", total: 0 },
    { key: "unknown", label: "Unknown", total: 0 },
  ];
  const now = new Date();
  birthdays.forEach((value) => {
    if (!value) {
      ranges[5].total += 1;
      return;
    }
    const birth = new Date(value);
    if (Number.isNaN(birth.getTime())) {
      ranges[5].total += 1;
      return;
    }
    let age = now.getFullYear() - birth.getFullYear();
    const monthDelta = now.getMonth() - birth.getMonth();
    if (monthDelta < 0 || (monthDelta === 0 && now.getDate() < birth.getDate())) {
      age -= 1;
    }
    if (age < 18) ranges[0].total += 1;
    else if (age <= 25) ranges[1].total += 1;
    else if (age <= 35) ranges[2].total += 1;
    else if (age <= 45) ranges[3].total += 1;
    else ranges[4].total += 1;
  });
  return ranges;
}

export function toPercentage(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}
