import type { AssessmentState } from '../../types/simulation'
import { GENDERS, AGE_RANGES, PRIMARY_CONCERNS } from '../../mock/staticData'

interface ConsultationProps {
  value: AssessmentState
  onAnswerQuestion: (key: string, val: string) => void
}

export function Consultation({ value, onAnswerQuestion }: ConsultationProps) {
  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-8 text-ink">
      {value.analysisResult && (
        <div className="rounded-xl border border-accent/20 bg-accent/5 p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="h-5 w-5 rounded-full bg-accent flex items-center justify-center text-[#04140f] text-xs font-bold">✓</div>
            <h3 className="text-sm font-semibold text-accent uppercase tracking-wider">AI Face Scan Complete</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Detected Proportions</p>
              <ul className="text-sm text-ink space-y-1">
                <li className="flex justify-between"><span>Upper/Lower Ratio:</span> <span className="font-mono">1 : 1.2</span></li>
                <li className="flex justify-between"><span>Philtrum Length:</span> <span className="font-mono">16mm (Long)</span></li>
                <li className="flex justify-between"><span>Symmetry Score:</span> <span className="font-mono">92%</span></li>
              </ul>
            </div>
            <div>
              <p className="text-xs text-ink-muted mb-2 uppercase tracking-wide">Ideal Target</p>
              <ul className="text-sm text-ink space-y-1">
                <li className="flex justify-between"><span>Upper/Lower Ratio:</span> <span className="font-mono">1 : 1.6</span></li>
                <li className="flex justify-between"><span>Philtrum Length:</span> <span className="font-mono">11-13mm</span></li>
              </ul>
            </div>
          </div>
          <p className="mt-4 text-sm text-ink-muted leading-relaxed">
            Based on the Golden Ratio (1:1.6), your upper lip is slightly long relative to the lower lip. We recommend a <strong>Feminizing Lip Lift</strong> to shorten the philtrum by 3-4mm and increase vermilion show, restoring youthful balance.
          </p>
        </div>
      )}

      <div>
        <h2 className="text-2xl font-semibold mb-2">Patient Assessment</h2>
        <p className="text-sm text-ink-muted">Select patient characteristics to receive a personalized preset recommendation.</p>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-medium">Gender</h3>
        <div className="grid grid-cols-2 gap-4 max-w-lg">
          {GENDERS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onAnswerQuestion('gender', opt.id)}
              className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${
                value.gender === opt.id
                  ? 'border-accent bg-accent/5'
                  : 'border-border bg-transparent hover:border-ink-faint'
              }`}
            >
              <span className={`font-medium ${value.gender === opt.id ? 'text-accent' : ''}`}>{opt.label}</span>
              <span className="text-xs text-ink-muted mt-1">{opt.helper}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-medium">Age Range</h3>
        <div className="grid grid-cols-4 gap-4">
          {AGE_RANGES.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onAnswerQuestion('ageRange', opt.id)}
              className={`flex flex-col items-center justify-center p-4 rounded-xl border transition-all ${
                value.ageRange === opt.id
                  ? 'border-accent bg-accent/5'
                  : 'border-border bg-transparent hover:border-ink-faint'
              }`}
            >
              <span className={`font-medium ${value.ageRange === opt.id ? 'text-accent' : ''}`}>{opt.label}</span>
              <span className="text-xs text-ink-muted mt-1 text-center">{opt.helper}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-medium">Primary Concern</h3>
        <div className="grid grid-cols-2 gap-4">
          {PRIMARY_CONCERNS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => onAnswerQuestion('primaryConcern', opt.id)}
              className={`flex flex-col items-start justify-center p-4 rounded-xl border transition-all ${
                value.primaryConcern === opt.id
                  ? 'border-accent bg-accent/5'
                  : 'border-border bg-transparent hover:border-ink-faint'
              }`}
            >
              <span className={`font-medium ${value.primaryConcern === opt.id ? 'text-accent' : ''}`}>{opt.label}</span>
              <span className="text-xs text-ink-muted mt-1">{opt.helper}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
