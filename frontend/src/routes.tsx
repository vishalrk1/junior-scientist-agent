import { Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from '@/pages/Dashboard/dashboard'
import RagPage from '@/pages/Dashboard/ragPage'
import MainLayout from '@/layouts/MainLayout'

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/rag" element={<RagPage />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes
