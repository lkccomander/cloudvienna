import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { LoadingBlock } from "../components/feedback/LoadingBlock";
import { useAuth } from "./providers/AuthProvider";
import { LoginPage } from "../features/auth/LoginPage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { BirthdaysPage } from "../features/news/BirthdaysPage";
import { UsersPage } from "../features/users/UsersPage";
import { StudentsPage } from "../features/students/StudentsPage";
import { StudentDetailPage } from "../features/students/StudentDetailPage";
import { TeachersPage } from "../features/training/TeachersPage";
import { ClassesPage } from "../features/training/ClassesPage";
import { SessionsPage } from "../features/training/SessionsPage";
import { AttendancePage } from "../features/training/AttendancePage";
import { ReportsPage } from "../features/reports/ReportsPage";
import { AuditPage } from "../features/audit/AuditPage";
import type { UserRole } from "../lib/api/types";

function RequireAuth() {
  const { token, booting } = useAuth();
  if (booting) return <LoadingBlock label="Booting control center..." />;
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

function RequireRoles({ roles }: { roles: UserRole[] }) {
  const { user, booting } = useAuth();
  if (booting) return <LoadingBlock label="Resolving role access..." />;
  if (!user || !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <RequireAuth />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/news/birthdays", element: <BirthdaysPage /> },
          { path: "/students", element: <StudentsPage /> },
          { path: "/students/:studentId", element: <StudentDetailPage /> },
          { path: "/training/teachers", element: <TeachersPage /> },
          { path: "/training/classes", element: <ClassesPage /> },
          { path: "/training/sessions", element: <SessionsPage /> },
          { path: "/training/attendance", element: <AttendancePage /> },
          { path: "/profile/preferences", element: <Navigate to="/dashboard" replace /> },
          {
            element: <RequireRoles roles={["admin"]} />,
            children: [
              { path: "/users", element: <UsersPage /> },
              { path: "/audit", element: <AuditPage /> },
            ],
          },
          {
            element: <RequireRoles roles={["admin", "receptionist"]} />,
            children: [{ path: "/reports/students", element: <ReportsPage /> }],
          },
        ],
      },
    ],
  },
]);
