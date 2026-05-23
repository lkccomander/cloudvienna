import type { SVGProps } from "react";

export type IconName =
  | "activity"
  | "calendar"
  | "check"
  | "chevronRight"
  | "edit"
  | "fileText"
  | "globe"
  | "home"
  | "layers"
  | "logOut"
  | "mapPin"
  | "menu"
  | "moon"
  | "newspaper"
  | "plus"
  | "save"
  | "search"
  | "sun"
  | "users";

const paths: Record<IconName, string[]> = {
  activity: ["M3 12h4l3 7 4-14 3 7h4"],
  calendar: ["M7 3v4M17 3v4", "M4 8h16", "M5 5h14a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z"],
  check: ["m5 12 4 4L19 6"],
  chevronRight: ["m9 18 6-6-6-6"],
  edit: ["M12 20h9", "M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4 11.5-11.5Z"],
  fileText: ["M14 3v5h5", "M6 3h8l5 5v13H6V3Z", "M9 13h6M9 17h6"],
  globe: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M3.6 9h16.8M3.6 15h16.8", "M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"],
  home: ["M3 11.5 12 4l9 7.5", "M5 10.5V20h5v-5h4v5h5v-9.5"],
  layers: ["m12 3 9 5-9 5-9-5 9-5Z", "m3 12 9 5 9-5", "m3 16 9 5 9-5"],
  logOut: ["M10 17l5-5-5-5", "M15 12H3", "M14 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5"],
  mapPin: ["M12 21s7-5.2 7-11a7 7 0 1 0-14 0c0 5.8 7 11 7 11Z", "M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"],
  menu: ["M4 7h16", "M4 12h16", "M4 17h16"],
  moon: ["M20 15.5A8.5 8.5 0 0 1 8.5 4 9 9 0 1 0 20 15.5Z"],
  newspaper: ["M4 5h13a3 3 0 0 1 3 3v11H6a2 2 0 0 1-2-2V5Z", "M8 9h5M8 13h8M8 17h5", "M17 8h3"],
  plus: ["M12 5v14M5 12h14"],
  save: ["M5 3h12l2 2v16H5V3Z", "M8 3v6h8V3", "M8 21v-7h8v7"],
  search: ["M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z", "m16 16 4 4"],
  sun: [
    "M12 2.5v2.2M12 19.3v2.2M21.5 12h-2.2M4.7 12H2.5",
    "M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6M18.7 18.7l-1.6-1.6M6.9 6.9 5.3 5.3",
    "M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z",
  ],
  users: ["M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2", "M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z", "M22 21v-2a4 4 0 0 0-3-3.9", "M16 3.1a4 4 0 0 1 0 7.8"],
};

export function Icon({ name, className, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
      aria-hidden="true"
      {...props}
    >
      {paths[name].map((path) => (
        <path key={path} d={path} />
      ))}
    </svg>
  );
}
