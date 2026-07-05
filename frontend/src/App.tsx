import { Route, Routes } from "react-router-dom";

import { PrivateRoute } from "@/components/common/PrivateRoute";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import Attendance from "@/pages/Attendance";
import Dashboard from "@/pages/Dashboard";
import Employees from "@/pages/Employees";
import Holidays from "@/pages/Holidays";
import Login from "@/pages/Login";
import Profile from "@/pages/Profile";
import Register from "@/pages/Register";
import Reports from "@/pages/Reports";
import Shifts from "@/pages/Shifts";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<PrivateRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/attendance" element={<Attendance />} />
          <Route path="/holidays" element={<Holidays />} />
          <Route path="/profile" element={<Profile />} />

          <Route element={<PrivateRoute allowedRoles={["admin", "super_admin"]} />}>
            <Route path="/employees" element={<Employees />} />
            <Route path="/shifts" element={<Shifts />} />
            <Route path="/reports" element={<Reports />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
