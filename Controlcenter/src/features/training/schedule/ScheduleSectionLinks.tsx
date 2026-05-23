import { Link } from "react-router-dom";

export function ScheduleSectionLinks() {
  return (
    <div className="flex flex-wrap gap-3">
      <Link to="/training/teachers" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
        Teachers
      </Link>
      <Link to="/training/classes" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
        Classes
      </Link>
      <Link to="/training/sessions" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
        Sessions
      </Link>
      <Link to="/attendance" className="theme-secondary-button px-4 py-3 text-sm hover:bg-[var(--hover)]">
        Attendance
      </Link>
    </div>
  );
}
