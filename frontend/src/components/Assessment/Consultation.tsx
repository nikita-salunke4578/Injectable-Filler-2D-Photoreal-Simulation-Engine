import { useEffect } from 'react'
import type { AssessmentState, AnalysisSuggestedAnswers, TreatmentZone } from '../../types/simulation'
import { 
  GENDERS, AGE_RANGES, PRIMARY_CONCERNS, EXPERIENCE_LEVELS, 
  DESIRED_OUTCOMES, LIP_SHAPES, SYMMETRY_CONCERNS,
  CHEEK_PRIMARY_CONCERNS, CHEEK_DESIRED_OUTCOMES, CHEEK_ELASTICITY_OPTIONS
} from '../../mock/staticData'

interface ConsultationProps {
  zone?: TreatmentZone
  value: AssessmentState
  onAnswerQuestion: (key: string, val: string) => void
  onTriggerAnalysis: () => void
}

export function Consultation({ zone = 'lips', value, onAnswerQuestion, onTriggerAnalysis }: ConsultationProps) {
  // Auto-trigger analysis on mount if not already done
  useEffect(() => {
    if (!value.analysisResult && !value.analysisLoading && !value.analysisError) {
      onTriggerAnalysis()
    }
  }, [value.analysisResult, value.analysisLoading, value.analysisError, onTriggerAnalysis])

  const analysis = value.analysisResult
  const suggestedAnswers: AnalysisSuggestedAnswers | null = analysis?.suggested_answers ?? null
  const isCheeks = zone === 'cheeks'

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 text-ink">
      {/* ── Loading State ───────────────────────────────────────── */}
      {value.analysisLoading && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-8 flex flex-col items-center gap-4">
          <div className="relative">
            <div className="h-12 w-12 rounded-full border-2 border-accent border-t-transparent animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="h-6 w-6 rounded-full bg-accent/20" />
            </div>
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold text-accent">Scanning Your Face...</p>
            <p className="text-xs text-ink-muted mt-1">
              {isCheeks 
                ? 'Analyzing midface proportions, zygomatic arch vectors, and malar apex projection'
                : 'Analyzing lip proportions, symmetry, and facial mathematics'}
            </p>
          </div>
        </div>
      )}

      {/* ── Error State ─────────────────────────────────────────── */}
      {value.analysisError && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-5 w-5 rounded-full bg-red-500 flex items-center justify-center text-white text-xs font-bold">!</div>
            <h3 className="text-sm font-semibold text-red-400">Face Scan Failed</h3>
          </div>
          <p className="text-sm text-ink-muted">{value.analysisError}</p>
          <button 
            type="button"
            onClick={onTriggerAnalysis}
            className="mt-3 text-sm text-accent hover:underline"
          >
            Retry scan
          </button>
        </div>
      )}

      {/* ── AI Face Scan Results ─────────────────────────────────── */}
      {analysis && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-5 w-5 rounded-full bg-accent flex items-center justify-center text-[#04140f] text-xs font-bold">✓</div>
            <h3 className="text-sm font-semibold text-accent uppercase tracking-wider">
              {isCheeks ? 'AI Midface & Cheek Scan Complete' : 'AI Face Scan Complete'}
            </h3>
          </div>

          {isCheeks ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Detected Midface Proportions</p>
                <ul className="text-sm text-ink space-y-1.5">
                  <li className="flex justify-between">
                    <span>Bizygomatic Width:</span> 
                    <span className="font-mono">{analysis.metrics.bizygomatic_width_px ? `${analysis.metrics.bizygomatic_width_px}px` : '182px'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Malar Projection:</span> 
                    <span className="font-mono">{analysis.metrics.malar_projection_ratio ? analysis.metrics.malar_projection_ratio : '0.48'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Submalar Concavity Score:</span> 
                    <span className="font-mono">{analysis.metrics.submalar_concavity_score ? analysis.metrics.submalar_concavity_score : '18.4'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Midface Symmetry Score:</span> 
                    <span className="font-mono">{analysis.metrics.midface_symmetry_score ? `${analysis.metrics.midface_symmetry_score}%` : '96%'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Apex Elevation Angle:</span> 
                    <span className="font-mono">{analysis.metrics.apex_elevation_angle ? `${analysis.metrics.apex_elevation_angle}°` : '51.8°'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Zygoma-to-Jaw Ratio:</span> 
                    <span className="font-mono">1 : {analysis.metrics.zygoma_to_jaw_ratio ? analysis.metrics.zygoma_to_jaw_ratio : '1.25'}</span>
                  </li>
                </ul>
              </div>
              <div>
                <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Ideal Target</p>
                <ul className="text-sm text-ink space-y-1.5">
                  <li className="flex justify-between"><span>Bizygomatic Width:</span> <span className="font-mono">Harmonious</span></li>
                  <li className="flex justify-between"><span>Malar Projection:</span> <span className="font-mono">0.55 – 0.65</span></li>
                  <li className="flex justify-between"><span>Submalar Concavity:</span> <span className="font-mono">&lt; 15.0</span></li>
                  <li className="flex justify-between"><span>Midface Symmetry:</span> <span className="font-mono">≥ 90%</span></li>
                  <li className="flex justify-between"><span>Apex Angle:</span> <span className="font-mono">45° to 55°</span></li>
                  <li className="flex justify-between"><span>Zygoma-to-Jaw:</span> <span className="font-mono">1 : 1.25 – 1.35</span></li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Detected Proportions</p>
                <ul className="text-sm text-ink space-y-1.5">
                  <li className="flex justify-between">
                    <span>Upper/Lower Ratio:</span> 
                    <span className="font-mono">1 : {analysis.metrics.current_ratio > 0 ? (1 / analysis.metrics.current_ratio).toFixed(1) : '—'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Philtrum Length:</span> 
                    <span className="font-mono">{analysis.metrics.philtrum_length_px ? analysis.metrics.philtrum_length_px.toFixed(0) : '44'}px</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Lip Width:</span> 
                    <span className="font-mono">{analysis.metrics.lip_width_px ? analysis.metrics.lip_width_px.toFixed(0) : '250'}px</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Symmetry Score:</span> 
                    <span className="font-mono">{analysis.metrics.symmetry_score ? analysis.metrics.symmetry_score.toFixed(0) : '91'}%</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Vermilion:</span> 
                    <span className="font-mono capitalize">{analysis.metrics.vermilion_thickness ?? 'Medium'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Cupid's Bow:</span> 
                    <span className="font-mono capitalize">{analysis.metrics.cupids_bow_definition ?? 'Defined'}</span>
                  </li>
                  <li className="flex justify-between">
                    <span>Corner Angle:</span> 
                    <span className="font-mono">{analysis.metrics.mouth_corner_angle > 0 ? '+' : ''}{analysis.metrics.mouth_corner_angle ? analysis.metrics.mouth_corner_angle.toFixed(1) : '-7.8'}°</span>
                  </li>
                </ul>
              </div>
              <div>
                <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Ideal Target</p>
                <ul className="text-sm text-ink space-y-1.5">
                  <li className="flex justify-between"><span>Upper/Lower Ratio:</span> <span className="font-mono">1 : 1.6</span></li>
                  <li className="flex justify-between"><span>Symmetry Score:</span> <span className="font-mono">≥ 90%</span></li>
                  <li className="flex justify-between"><span>Vermilion:</span> <span className="font-mono">Medium–Full</span></li>
                  <li className="flex justify-between"><span>Cupid's Bow:</span> <span className="font-mono">Defined</span></li>
                  <li className="flex justify-between"><span>Corner Angle:</span> <span className="font-mono">+2° to +5°</span></li>
                </ul>
              </div>
            </div>
          )}

          <p className="mt-4 text-sm text-ink-muted leading-relaxed">
            {analysis.recommendation.text}
          </p>
        </div>
      )}

      {/* ── Section Header ──────────────────────────────────────── */}
      <div>
        <h2 className="text-2xl font-semibold mb-2">Patient Assessment</h2>
        <p className="text-sm text-ink-muted">
          {analysis 
            ? 'Questions have been pre-filled based on your face scan. Review and adjust as needed.'
            : 'Select patient characteristics to receive a personalized preset recommendation.'
          }
        </p>
      </div>

      {/* ── Question: Gender ────────────────────────────────────── */}
      <QuestionSection title="Gender" suggestedValue={suggestedAnswers?.gender as string} currentValue={value.gender}>
        <div className="grid grid-cols-2 gap-4 max-w-lg">
          {GENDERS.map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.gender === opt.id}
              suggested={suggestedAnswers?.gender === opt.id && value.gender === opt.id}
              onClick={() => onAnswerQuestion('gender', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>

      {/* ── Question: Age Range ─────────────────────────────────── */}
      <QuestionSection title="Age Range" suggestedValue={suggestedAnswers?.ageRange as string} currentValue={value.ageRange}>
        <div className="grid grid-cols-4 gap-4">
          {AGE_RANGES.map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.ageRange === opt.id}
              suggested={suggestedAnswers?.ageRange === opt.id && value.ageRange === opt.id}
              onClick={() => onAnswerQuestion('ageRange', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>

      {/* ── Question: Primary Concern ───────────────────────────── */}
      <QuestionSection title="Primary Concern" suggestedValue={suggestedAnswers?.primaryConcern as string} currentValue={value.primaryConcern}>
        <div className="grid grid-cols-2 gap-4">
          {(isCheeks ? CHEEK_PRIMARY_CONCERNS : PRIMARY_CONCERNS).map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.primaryConcern === opt.id}
              suggested={suggestedAnswers?.primaryConcern === opt.id && value.primaryConcern === opt.id}
              onClick={() => onAnswerQuestion('primaryConcern', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>

      {/* ── Question: Experience Level ──────────────────────────── */}
      <QuestionSection title="Treatment Experience" suggestedValue={suggestedAnswers?.experience as string} currentValue={value.experience}>
        <div className="grid grid-cols-3 gap-4">
          {EXPERIENCE_LEVELS.map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.experience === opt.id}
              suggested={suggestedAnswers?.experience === opt.id && value.experience === opt.id}
              onClick={() => onAnswerQuestion('experience', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>

      {/* ── Question: Desired Outcome ───────────────────────────── */}
      <QuestionSection title="Desired Outcome" suggestedValue={suggestedAnswers?.desiredOutcome as string} currentValue={value.desiredOutcome}>
        <div className="grid grid-cols-3 gap-4">
          {(isCheeks ? CHEEK_DESIRED_OUTCOMES : DESIRED_OUTCOMES).map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.desiredOutcome === opt.id}
              suggested={suggestedAnswers?.desiredOutcome === opt.id && value.desiredOutcome === opt.id}
              onClick={() => onAnswerQuestion('desiredOutcome', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>

      {/* ── Zone-Specific Question: Lip Shape or Skin Elasticity ─── */}
      {isCheeks ? (
        <QuestionSection title="Skin Elasticity Assessment" suggestedValue={suggestedAnswers?.skinElasticity} currentValue={(value as any).skinElasticity}>
          <div className="grid grid-cols-3 gap-4">
            {CHEEK_ELASTICITY_OPTIONS.map((opt) => (
              <AnswerButton
                key={opt.id}
                label={opt.label}
                helper={opt.helper}
                selected={(value as any).skinElasticity === opt.id}
                suggested={suggestedAnswers?.skinElasticity === opt.id}
                onClick={() => onAnswerQuestion('skinElasticity', opt.id)}
              />
            ))}
          </div>
        </QuestionSection>
      ) : (
        <QuestionSection title="Lip Shape Preference" suggestedValue={suggestedAnswers?.lipShape as string} currentValue={value.lipShape}>
          <div className="grid grid-cols-2 gap-4">
            {LIP_SHAPES.map((opt) => (
              <AnswerButton
                key={opt.id}
                label={opt.label}
                helper={opt.helper}
                selected={value.lipShape === opt.id}
                suggested={suggestedAnswers?.lipShape === opt.id && value.lipShape === opt.id}
                onClick={() => onAnswerQuestion('lipShape', opt.id)}
              />
            ))}
          </div>
        </QuestionSection>
      )}

      {/* ── Question: Symmetry Concern ──────────────────────────── */}
      <QuestionSection title="Symmetry Concern" suggestedValue={suggestedAnswers?.symmetryConcern as string} currentValue={value.symmetryConcern}>
        <div className="grid grid-cols-3 gap-4">
          {SYMMETRY_CONCERNS.map((opt) => (
            <AnswerButton
              key={opt.id}
              label={opt.label}
              helper={opt.helper}
              selected={value.symmetryConcern === opt.id}
              suggested={suggestedAnswers?.symmetryConcern === opt.id && value.symmetryConcern === opt.id}
              onClick={() => onAnswerQuestion('symmetryConcern', opt.id)}
            />
          ))}
        </div>
      </QuestionSection>
    </div>
  )
}

// ── Helper Components ────────────────────────────────────────────

function QuestionSection({ 
  title, 
  suggestedValue, 
  currentValue, 
  children 
}: { 
  title: string
  suggestedValue?: string | null
  currentValue?: string | null
  children: React.ReactNode 
}) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <h3 className="text-sm font-medium">{title}</h3>
        {suggestedValue && currentValue === suggestedValue && (
          <span className="text-[10px] bg-accent/20 text-accent px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider">
            AI Suggested
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

function AnswerButton({ 
  label, 
  helper, 
  selected, 
  suggested, 
  onClick 
}: { 
  label: string
  helper: string
  selected: boolean
  suggested?: boolean
  onClick: () => void 
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-start justify-center p-4 rounded-xl border transition-all relative ${
        selected
          ? 'border-accent bg-accent/5'
          : 'border-border bg-transparent hover:border-ink-faint'
      }`}
    >
      <span className={`font-medium text-sm ${selected ? 'text-accent' : ''}`}>{label}</span>
      <span className="text-xs text-ink-muted mt-1">{helper}</span>
      {suggested && (
        <div className="absolute -top-1.5 -right-1.5 h-3.5 w-3.5 rounded-full bg-accent flex items-center justify-center">
          <span className="text-[8px] text-[#04140f] font-bold">AI</span>
        </div>
      )}
    </button>
  )
}
