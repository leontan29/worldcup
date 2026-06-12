// API returns naive ISO strings (no Z). Append Z so JS treats them as UTC
// and toLocaleString() converts to the browser's local timezone.
export const parseDate = (s) => s ? new Date(s + 'Z') : null
