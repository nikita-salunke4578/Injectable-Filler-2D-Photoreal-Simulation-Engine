import { useState } from 'react'
import { AppHeader } from './components/layout/AppHeader'
import { OverviewDashboard } from './components/Dashboard/OverviewDashboard'
import { RegionDetailSection } from './components/Dashboard/RegionDetailSection'
import { DermalFillerSimulator } from './pages/DermalFillerSimulator/DermalFillerSimulator'
import type { DashboardSection } from './mock/dashboardData'
import type { TreatmentZone } from './types/simulation'

function App() {
  const [activeSection, setActiveSection] = useState<DashboardSection>('overview')
  const [showSimulator, setShowSimulator] = useState(false)

  const handleStartSimulation = () => {
    setShowSimulator(true)
  }

  const handleBackFromSimulator = () => {
    setShowSimulator(false)
  }

  const handleSectionChange = (section: DashboardSection) => {
    setActiveSection(section)
    // If switching sections while in the simulator, go back to dashboard
    setShowSimulator(false)
  }

  return (
    <div className="min-h-screen bg-base">
      <AppHeader
        activeSection={activeSection}
        onSectionChange={handleSectionChange}
      />

      {showSimulator ? (
        <DermalFillerSimulator
          initialZone={activeSection !== 'overview' ? activeSection : 'lips'}
          onBack={handleBackFromSimulator}
        />
      ) : activeSection === 'overview' ? (
        <OverviewDashboard onNavigateToRegion={(zone: TreatmentZone) => setActiveSection(zone)} />
      ) : (
        <RegionDetailSection
          zone={activeSection}
          onBack={() => setActiveSection('overview')}
          onStartSimulation={handleStartSimulation}
        />
      )}
    </div>
  )
}

export default App
