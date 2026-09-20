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
  const [activePreset, setActivePreset] = useState<string | null>(() => {
    if (zone === 'cheeks') {
      const p = configuration.parameters.cheeks
      if (p.lateral_volume_ck1 === 1.8 && p.medial_volume_ck2 === 1.2) return 'contour'
    }
    return null
  })
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
                className={`p-4 rounded-xl border text-left transition-all ${activePreset === p.id ? 'border-accent bg-accent/20' : 'border-border hover:border-ink-faint'}`}
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

  if (zone === 'cheeks') {
    const params = configuration.parameters.cheeks
    const CHEEK_PRESETS = [
      {
        id: 'contour',
        label: 'High Cheekbone Contour',
        desc: 'Prominent lateral arch lift + malar apex projection',
        rec: true,
        params: { lateral_volume_ck1: 1.8, medial_volume_ck2: 1.2, submalar_volume_ck3: 0.2, skin_elasticity: 1.0, volumeMl: 3.2 },
      },
      {
        id: 'natural',
        label: 'Natural Midface Volume',
        desc: 'Harmonious, youthful anterior projection across midface',
        params: { lateral_volume_ck1: 1.0, medial_volume_ck2: 0.8, submalar_volume_ck3: 0.4, skin_elasticity: 1.0, volumeMl: 2.2 },
      },
      {
        id: 'model_lift',
        label: 'Model Zygomatic Lift',
        desc: 'Sculpted lateral elevation towards temporal hairline',
        params: { lateral_volume_ck1: 2.2, medial_volume_ck2: 0.6, submalar_volume_ck3: 0.0, skin_elasticity: 0.9, volumeMl: 2.8 },
      },
      {
        id: 'submalar',
        label: 'Gauntness Softening',
        desc: 'Fills lower cheek hollows beneath the bone',
        params: { lateral_volume_ck1: 0.5, medial_volume_ck2: 0.5, submalar_volume_ck3: 1.5, skin_elasticity: 1.1, volumeMl: 2.5 },
      },
      {
        id: 'subtle',
        label: 'Subtle Rejuvenation',
        desc: 'Conservative micro-enhancement for mature skin',
        params: { lateral_volume_ck1: 0.6, medial_volume_ck2: 0.4, submalar_volume_ck3: 0.2, skin_elasticity: 1.0, volumeMl: 1.2 },
      },
    ]

    return (
      <div className="flex flex-col gap-8">

        <div className="flex flex-col gap-3">
          <div className="rounded-lg border border-accent/30 bg-accent/5 p-4 flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 rounded-full bg-accent flex items-center justify-center text-[#04140f] text-xs font-bold">✓</div>
              <h3 className="text-sm font-semibold text-accent">Midface Contour Engine Active</h3>
            </div>
            <p className="text-xs text-ink-muted ml-6">
              Precision midface volumization using Gaussian RBF vectors, orbital safety caging, and physical LAB relighting.
            </p>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold tracking-wider text-ink-faint mb-3 uppercase">Cheek Enhancement Presets</h3>
          <div className="grid grid-cols-2 gap-3">
            {CHEEK_PRESETS.map((p) => (
              <button
                key={p.id}
                type="button"
                className={`p-4 rounded-xl border text-left transition-all ${activePreset === p.id
                    ? 'border-accent bg-accent/20'
                    : 'border-border hover:border-ink-faint'
                  }`}
                onClick={() => {
                  setActivePreset(p.id)
                  const total = Number(((p.params.lateral_volume_ck1 || 0) + (p.params.medial_volume_ck2 || 0) + (p.params.submalar_volume_ck3 || 0)).toFixed(1))
                  onUpdate('cheeks', { ...p.params, volumeMl: total })
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
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-semibold tracking-wider text-ink-faint uppercase">Anatomical Sub-Zones & Volume</h3>
            <button
              onClick={() => {
                setActivePreset(null)
                onReset('cheeks')
              }}
              className="text-xs text-accent hover:underline"
            >
              Reset
            </button>
          </div>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Lateral Cheek Volume (CK1)"
                value={params.lateral_volume_ck1}
                min={0}
                max={2.5}
                step={0.1}
                unit="mL"
                disabled={disabled}
                onChange={(v) => {
                  setActivePreset(null)
                  const total = Number((v + (params.medial_volume_ck2 || 0) + (params.submalar_volume_ck3 || 0)).toFixed(1))
                  onUpdate('cheeks', { lateral_volume_ck1: v, volumeMl: total })
                }}
              />
              <p className="text-[10px] text-ink-muted">
                Expands the outer zygomatic arch towards the hairline to create a lateral lift vector.
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Medial / Malar Cheek Volume (CK2)"
                value={params.medial_volume_ck2}
                min={0}
                max={2.5}
                step={0.1}
                unit="mL"
                disabled={disabled}
                onChange={(v) => {
                  setActivePreset(null)
                  const total = Number(((params.lateral_volume_ck1 || 0) + v + (params.submalar_volume_ck3 || 0)).toFixed(1))
                  onUpdate('cheeks', { medial_volume_ck2: v, volumeMl: total })
                }}
              />
              <p className="text-[10px] text-ink-muted">
                Increases forward (anterior) midface projection and sets the primary light-reflection highlight.
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Submalar Volume (CK3)"
                value={params.submalar_volume_ck3}
                min={0}
                max={2.0}
                step={0.1}
                unit="mL"
                disabled={disabled}
                onChange={(v) => {
                  setActivePreset(null)
                  const total = Number(((params.lateral_volume_ck1 || 0) + (params.medial_volume_ck2 || 0) + v).toFixed(1))
                  onUpdate('cheeks', { submalar_volume_ck3: v, volumeMl: total })
                }}
              />
              <p className="text-[10px] text-ink-muted">
                Softens gauntness in the lower midface hollow below the bone.
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Skin Elasticity Scale"
                value={params.skin_elasticity}
                min={0.8}
                max={1.2}
                step={0.05}
                unit="x"
                disabled={disabled}
                onChange={(v) => {
                  setActivePreset(null)
                  onUpdate('cheeks', { skin_elasticity: v })
                }}
              />
              <p className="text-[10px] text-ink-muted">
                Controls the kernel spread radius: 0.8 mimics tight youthful skin, 1.2 mimics mature lax skin.
              </p>
            </div>

            {/* Asymmetry Mode Toggle & Sliders */}
            <div className="rounded-xl border border-border bg-surface p-4 flex flex-col gap-4 mt-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-ink">Facial Asymmetry Correction</p>
                  <p className="text-xs text-ink-muted">Unlock independent left vs. right volume multipliers</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input
                    type="checkbox"
                    className="peer sr-only"
                    checked={params.asymmetry_mode}
                    onChange={(e) => onUpdate('cheeks', { asymmetry_mode: e.target.checked })}
                  />
                  <div className="peer h-6 w-11 rounded-full bg-border after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-accent peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none" />
                </label>
              </div>

              {params.asymmetry_mode && (
                <div className="flex flex-col gap-4 pt-3 border-t border-border/60">
                  <div className="flex flex-col gap-1">
                    <ParameterSlider
                      label="Left Cheek Multiplier"
                      value={params.left_cheek_multiplier}
                      min={0.0}
                      max={2.0}
                      step={0.05}
                      unit="x"
                      disabled={disabled}
                      onChange={(v) => onUpdate('cheeks', { left_cheek_multiplier: v })}
                    />
                    <p className="text-[10px] text-ink-muted">Scales volume applied to the patient's left cheek.</p>
                  </div>
                  <div className="flex flex-col gap-1">
                    <ParameterSlider
                      label="Right Cheek Multiplier"
                      value={params.right_cheek_multiplier}
                      min={0.0}
                      max={2.0}
                      step={0.05}
                      unit="x"
                      disabled={disabled}
                      onChange={(v) => onUpdate('cheeks', { right_cheek_multiplier: v })}
                    />
                    <p className="text-[10px] text-ink-muted">Scales volume applied to the patient's right cheek.</p>
                  </div>
                </div>
              )}
            </div>

          </div>
        </div>

      </div>
    )
  }

  if (zone === 'jaw') {
    const params = configuration.parameters.jaw
    return (
      <div className="flex flex-col gap-8">
        <div>
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xs font-semibold tracking-wider text-ink-faint uppercase">Parameters</h3>
            <button onClick={() => onReset('jaw')} className="text-xs text-accent hover:underline">Reset</button>
          </div>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Jaw Volume"
                value={params.volumeMl}
                min={0}
                max={3}
                unit="mL"
                disabled={disabled}
                onChange={(v) => onUpdate('jaw', { volumeMl: v })}
              />
              <p className="text-[10px] text-ink-muted">Controls the simulated filler volume along the jawline.</p>
            </div>
            <div className="flex flex-col gap-1">
              <ParameterSlider
                label="Jawline Definition"
                value={params.definition}
                min={0}
                max={100}
                unit="%"
                disabled={disabled}
                onChange={(v) => onUpdate('jaw', { definition: v })}
              />
              <p className="text-[10px] text-ink-muted">Sharpens the contour from soft and natural to more defined.</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="text-sm text-ink-muted p-4">Zone not supported.</div>
  )
}

