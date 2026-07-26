import { Navigate, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LoginPage } from "@/features/auth/LoginPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { EndpointsPage } from "@/features/endpoints/EndpointsPage";
import { EndpointDetailPage } from "@/features/endpoints/EndpointDetailPage";
import { BlueprintPage } from "@/features/blueprint/BlueprintPage";
import { ChatPage } from "@/features/chat/ChatPage";
import { ReportsPage } from "@/features/reports/ReportsPage";
import { NotFoundPage } from "@/features/misc/NotFoundPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/endpoints"
        element={
          <ProtectedRoute>
            <EndpointsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/endpoints/:hostname"
        element={
          <ProtectedRoute>
            <EndpointDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/blueprint"
        element={
          <ProtectedRoute>
            <BlueprintPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <ChatPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="*"
        element={
          <ProtectedRoute>
            <NotFoundPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
