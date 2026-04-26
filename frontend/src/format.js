const DATE_OPTS      = { day: "numeric", month: "short", year: "numeric" };
const DATETIME_OPTS  = { day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" };
const TIME_OPTS      = { hour: "numeric", minute: "2-digit" };

export function fmtDate(value) {
  if (!value) return "";
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("en-US", DATE_OPTS);
}

export function fmtDateTime(value) {
  if (!value) return "";
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("en-US", DATETIME_OPTS);
}

export function fmtTime(value) {
  if (!value) return "";
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("en-US", TIME_OPTS);
}
