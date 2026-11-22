const PATHS = {
  plus: "M12 5v14M5 12h14",
  edit: "M4 20h4l10-10-4-4L4 16v4zM14 6l4 4",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3",
  copy: "M9 9h10v11H9zM5 15V4h10",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM21 21l-5-5",
  menu: "M4 6h16M4 12h16M4 18h16",
  x: "M6 6l12 12M18 6L6 18",
  logout: "M10 4H5v16h5M15 8l4 4-4 4M19 12H9",
  check: "M5 12l5 5 9-10",
  draft: "M5 4h10l4 4v12H5zM9 13h6M9 17h4",
  sun: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M5 19l1.5-1.5M17.5 6.5L19 5",
  moon: "M20 14A8 8 0 0 1 10 4a8 8 0 1 0 10 10z",
} as const;

export type AdminIconName = keyof typeof PATHS;

export function AdminIcon({ name, size = 18 }: { name: AdminIconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={PATHS[name]} />
    </svg>
  );
}