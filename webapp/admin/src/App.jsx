import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AdminLayout from "./layouts/AdminLayout";
import Dashboard from "./pages/Dashboard";
import Devices from "./pages/Devices";
import Users from "./pages/Users";
import Cards from "./pages/Cards";
import Logs from "./pages/Logs";
import Notifications from "./pages/Notifications";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<AdminLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="devices" element={<Devices />} />
          <Route path="users" element={<Users />} />
          <Route path="cards" element={<Cards />} />
          <Route path="logs" element={<Logs />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
