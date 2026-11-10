/**
 * FinSight Currency and Date Formatters (en-IN Locale)
 */

export const formatINR = (value: number, includeDecimals = false): string => {
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0,
  });
  return formatter.format(value);
};

export const formatNumberINR = (value: number): string => {
  return new Intl.NumberFormat('en-IN').format(value);
};

export const getTodayFormatted = (): string => {
  const d = new Date();
  const dayName = d.toLocaleDateString('en-IN', { weekday: 'short' });
  const day = d.getDate();
  const month = d.toLocaleDateString('en-IN', { month: 'short' });
  const year = d.getFullYear();
  return `${dayName}, ${day} ${month}, ${year}`;
};
