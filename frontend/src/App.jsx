import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import RoleRoute from './components/RoleRoute'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import KioskView from './pages/KioskView'
import Dashboard from './pages/Dashboard'
import LiveQueueBoard from './pages/LiveQueueBoard'
import PatientIntake from './pages/PatientIntake'
import DepartmentManagement from './pages/DepartmentManagement'
import StaffManagement from './pages/StaffManagement'
import AIPredictions from './pages/AIPredictions'
import AnalyticsReports from './pages/AnalyticsReports'
import AlertsLog from './pages/AlertsLog'
import Profile from './pages/Profile'
import AdminPanel from './pages/AdminPanel'

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/kiosk" element={<KioskView />} />

      {/* Authenticated (any staff role) */}
      <Route element={<Layout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/queue" element={<LiveQueueBoard />} />
        <Route path="/predictions" element={<AIPredictions />} />
        <Route path="/alerts" element={<AlertsLog />} />
        <Route path="/profile" element={<Profile />} />

        {/* Analytics: Admin, Doctor, Nurse, Hospital Administrator */}
        <Route element={<RoleRoute roles={['ADMIN', 'DOCTOR', 'NURSE', 'HOSPITAL_ADMINISTRATOR']} />}>
          <Route path="/analytics" element={<AnalyticsReports />} />
        </Route>

        {/* Nurse/Admin only */}
        <Route element={<RoleRoute roles={['ADMIN', 'NURSE']} />}>
          <Route path="/intake" element={<PatientIntake />} />
        </Route>

        {/* Admin only — registration is admin-gated per spec, not public */}
        <Route element={<RoleRoute roles={['ADMIN']} />}>
          <Route path="/register" element={<Register />} />
          <Route path="/departments" element={<DepartmentManagement />} />
          <Route path="/staff" element={<StaffManagement />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
