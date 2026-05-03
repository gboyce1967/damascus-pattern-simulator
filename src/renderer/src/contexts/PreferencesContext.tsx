import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { UnitSystem } from '../lib/units'

type PreferencesCtx = {
  unitSystem: UnitSystem
  setUnitSystem: (u: UnitSystem) => void
}

const PreferencesContext = createContext<PreferencesCtx>({
  unitSystem: 'metric',
  setUnitSystem: () => {}
})

export function PreferencesProvider({ children }: { children: ReactNode }) {
  const [unitSystem, setUnitSystemLocal] = useState<UnitSystem>('metric')

  // Load persisted preference on mount
  useEffect(() => {
    window.damascus.prefsGet().then((p) => {
      if (p?.unitSystem) setUnitSystemLocal(p.unitSystem)
    })
  }, [])

  function setUnitSystem(u: UnitSystem) {
    setUnitSystemLocal(u)
    window.damascus.prefsSet({ unitSystem: u })
  }

  return (
    <PreferencesContext.Provider value={{ unitSystem, setUnitSystem }}>
      {children}
    </PreferencesContext.Provider>
  )
}

export function usePreferences() {
  return useContext(PreferencesContext)
}
