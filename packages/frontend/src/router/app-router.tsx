import { createBrowserRouter } from "react-router-dom";
import { LayoutShell } from "../common/components/layout/LayoutShell";
import { DashboardPage } from "../features/dashboard/pages/DashboardPage";
import { MaintenancePage } from "../features/maintenance/pages/MaintenancePage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <LayoutShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "maintenance", element: <MaintenancePage /> },
    ],
  },
]);
