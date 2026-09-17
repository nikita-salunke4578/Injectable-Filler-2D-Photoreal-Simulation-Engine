import { useState } from 'react'
import { ParameterSlider } from './ParameterSlider'
import type {
  ConfigurationState,
  TreatmentZone,
} from '../../types/simulation'

interface ZoneParameterPanelProps {
  zone: TreatmentZone
  configuration: ConfigurationState
  disabled: boolean
  onUpdate: (zone: TreatmentZone, patch: Record<string, unknown>) => void
  onReset: (zone: TreatmentZone) => void
}

const PRESETS = [
  { id: 'youthful', label: 'Youthful Rejuvenation', desc: 'Balanced shortening + vermilion show for anti-aging' },
  { id: 'korean', label: 'Korean Cherry Lips', desc: 'Defined cupid\'s bow, plump vermilion show' },
  { id: 'feminizing', label: 'Feminizing Lip Lift', desc: 'Aggressive shortening + vermilion for feminization', rec: true },
  { id: 'subtle', label: 'Subtle Enhancement', desc: 'Conservative approach, minimal visible change' },
  { id: 'corner', label: 'Corner Mouth Lift', desc: 'Targets downturned mouth corners' },
]

const TECHNIQUES = [
  { id: 'bullhorn', label: 'Bullhorn', desc: 'Uniform philtral shortening from nose base' },
  { id: 'direct', label: 'Direct', desc: 'Primarily at vermilion border' },
  { id: 'corner', label: 'Corner', desc: 'Elevates mouth corners' },
]

export function ZoneParameterPanel({ zone, configuration, disabled, onUpdate, onReset }: ZoneParameterPanelProps) {
  const [activePreset, setActivePreset] = useState<string | null>(null)
  const [activeTechnique, setActiveTechnique] = useState<string | null>('bullhorn')

  if (zone === 'lips') {
    const params = configuration.parameters.lips
    return (
      <div className="flex flex-col gap-8">
        
        <div className="flex flex-col gap-3">
          <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 rounded-full bg-accent flex items-center justify-center text-[#04140f] text-xs font-bold">✓</div>
              <h3 className="text-sm font-semibold text-accent">AI Assessment Complete</h3>
            </div>
            <p className="text-xs text-ink-muted ml-6">Smart suggestions applied based on your facial analysis. Adjust if needed.</p>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wider text-ink-faint mb-3 uppercase">Lip Lift Presets</h3>
          <div className="grid grid-cols-2 gap-3">
            {PRESETS.map(p => (
              <button 
                key={p.id}
                type="button"
                className={`p-4 rounded-xl border text-left transition-all ${activePreset === p.id ? 'border-accent bg-accent/20' : (p.rec ? 'border-accent bg-accent/5' : 'border-border hover:border-ink-faint')}`}
                onClick={() => {
                   setActivePreset(p.id)
                   if (p.id === 'youthful') onUpdate('lips', { philtralShortening: 50, vermilionShow: 40, cupidsBow: 30, philtralColumn: 20, dentalShow: 30 })
                   if (p.id === 'feminizing') onUpdate('lips', { philtralShortening: 80, vermilionShow: 60, cupidsBow: 70, philtralColumn: 50, dentalShow: 50 })
                   if (p.id === 'korean') onUpdate('lips', { philtralShortening: 20, vermilionShow: 70, cupidsBow: 90, philtralColumn: 60, dentalShow: 10 })
                   if (p.id === 'subtle') onUpdate('lips', { philtralShortening: 20, vermilionShow: 15, cupidsBow: 10, philtralColumn: 0, dentalShow: 0 })
                   if (p.id === 'corner') onUpdate('lips', { philtralShortening: 10, vermilionShow: 20, cupidsBow: 10, philtralColumn: 0, dentalShow: 10 })
                }}
              >
                <div className="flex justify-between items-center mb-1">
                  <span className="font-medium text-sm text-ink">{p.label}</span>
                  {p.rec && <span className="text-[10px] bg-accent text-[#04140f] px-1.5 py-0.5 rounded font-bold">REC</span>}
                </div>
                <span className="text-xs text-ink-muted leading-tight block">{p.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wider text-ink-faint mb-3 uppercase">Technique</h3>
          <div className="grid grid-cols-3 gap-3">
            {TECHNIQUES.map(t => (
              <button 
                key={t.id} 
                onClick={() => setActiveTechnique(t.id)}
                className={`p-3 rounded-xl border transition-all text-center ${activeTechnique === t.id ? 'border-accent bg-accent/20' : 'border-border hover:border-ink-faint'}`}
              >
                <span className="font-medium text-sm text-ink block mb-1">{t.label}</span>
                <span className="text-[10px] text-ink-muted leading-tight block">{t.desc}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-semibold tracking-wider text-ink-faint uppercase">Parameters</h3>
            <button onClick={() => { setActivePreset(null); onReset('lips') }} className="text-xs text-accent hover:underline">Reset</button>
          </div>
          
          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Philtral Shortening"
                value={params.philtralShortening}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => { setActivePreset(null); onUpdate('lips', { philtralShortening: v }) }}
              />
              <p className="text-[10px] text-ink-muted">Reduces the distance between nose base and upper lip, creating a youthful lift.</p>
            </div>
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Vermilion Show"
                value={params.vermilionShow}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => { setActivePreset(null); onUpdate('lips', { vermilionShow: v }) }}
              />
              <p className="text-[10px] text-ink-muted">Rolls the pink part of the lip outward for a fuller, plumper appearance.</p>
            </div>
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Cupid's Bow Definition"
                value={params.cupidsBow}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => { setActivePreset(null); onUpdate('lips', { cupidsBow: v }) }}
              />
              <p className="text-[10px] text-ink-muted">Sharpens and elevates the two central peaks of the upper lip.</p>
            </div>
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Philtral Column Enhancement"
                value={params.philtralColumn}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => { setActivePreset(null); onUpdate('lips', { philtralColumn: v }) }}
              />
              <p className="text-[10px] text-ink-muted">Adds structural definition to the two vertical lines above the lip.</p>
            </div>
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Dental Show"
                value={params.dentalShow}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => { setActivePreset(null); onUpdate('lips', { dentalShow: v }) }}
              />
              <p className="text-[10px] text-ink-muted">Slightly parts the center of the lip to reveal more teeth at rest.</p>
            </div>
          </div>
        </div>

      </div>
    )
  }

  return (
    <div className="text-sm text-ink-muted p-4">Zone not supported in Lip Lift simulator.</div>
  )
}

