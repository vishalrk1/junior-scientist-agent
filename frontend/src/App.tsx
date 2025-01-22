import { ThemeProvider } from './contexts/theme-provider'
import Dashboard from './pages/Dashboard/dashboard'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <Dashboard />
    </ThemeProvider>
  )
}

export default App
