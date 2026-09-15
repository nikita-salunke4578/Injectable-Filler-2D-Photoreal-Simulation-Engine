import { useState, useEffect } from 'react'
import { CheckCircle2, UserSquare2, ScanFace, Calculator } from 'lucide-react'
import { Card } from '../common/Card'
import type { AssessmentState } from '../../types/simulation'

interface ConsultationProps {
  value: AssessmentState
  onAnswerQuestion: (key: string, val: string) => void
  onRunAnalysis: () => void
}

export function Consultation({ value, onAnswerQuestion, onRunAnalysis }: ConsultationProps) {
  const [isScanning, setIsScanning] = useState(false)

  // Run analysis when component mounts if not already done
  useEffect(() => {
    if (!value.analysisResult && !isScanning) {
      setIsScanning(true)
      onRunAnalysis()
    }
  }, [value.analysisResult, isScanning, onRunAnalysis])

  useEffect(() => {
    if (value.analysisResult) {
      setIsScanning(false)
    }
  }, [value.analysisResult])

  return (
    <div className="flex w-full flex-col gap-6">
      {/* 1. Facial Scan Section */}
      <Card>
        <div className="flex items-center gap-3 border-b border-border pb-4">
          <ScanFace className="text-accent" />
          <h2 className="text-lg font-semibold text-ink">Mathematical Facial Scan</h2>
        </div>
        
        <div className="pt-4">
          {isScanning || !value.analysisResult ? (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-border-strong border-t-accent" />
              <p className="mt-4 text-sm text-ink-muted">Scanning anatomical landmarks...</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2 rounded-lg bg-accent-soft p-4 text-sm text-ink">
                <Calculator className="text-accent" size={20} />
                <p>{value.analysisResult.recommendation.text}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 rounded-lg border border-border p-4">
                <div>
                  <p className="text-xs font-semibold tracking-wide text-ink-faint">YOUR RATIO</p>
                  <p className="text-lg font-medium text-ink">
                    1 : {(1 / value.analysisResult.metrics.current_ratio).toFixed(2)}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold tracking-wide text-ink-faint">GOLDEN RATIO</p>
                  <p className="text-lg font-medium text-ink">1 : 1.61</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* 2. Surgical Consultation Questions */}
      <Card>
        <div className="flex items-center gap-3 border-b border-border pb-4">
          <UserSquare2 className="text-ink" />
          <h2 className="text-lg font-semibold text-ink">Surgical Consultation</h2>
        </div>
        
        <div className="flex flex-col gap-8 pt-6">
          <div className="flex flex-col gap-3">
            <label className="font-medium text-ink flex items-center gap-2">
              Focus Area 
              <span className="text-xs font-normal text-ink-faint">
                (Vermilion Border vs Body)
              </span>
            </label>
            <p className="text-xs text-ink-muted leading-relaxed">
              Do you want to define the crisp outer edge of the lip (the Vermilion Border) to prevent filler migration and improve shape, or do you want to focus on the fleshy body of the lip for overall volume?
            </p>
            <div className="grid grid-cols-2 gap-3">
              {(['Define Border', 'Volume Body'] as const).map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => onAnswerQuestion('focus', opt)}
                  className={`flex h-12 items-center justify-center rounded-lg border text-sm transition-all ${
                    value.consultationAnswers.focus === opt
                      ? 'border-accent bg-accent/5 text-accent font-medium'
                      : 'border-border bg-surface text-ink hover:bg-surface-raised'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <label className="font-medium text-ink flex items-center gap-2">
              Projection vs Vertical Height
            </label>
            <p className="text-xs text-ink-muted leading-relaxed">
              Are you looking for increased projection (the lips stick out more from the side profile, like a "Russian Lip" technique) or increased vertical height (showing more pink tissue from the front)?
            </p>
            <div className="grid grid-cols-2 gap-3">
              {(['Increase Projection', 'Vertical Height'] as const).map((opt) => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => onAnswerQuestion('projection', opt)}
                  className={`flex h-12 items-center justify-center rounded-lg border text-sm transition-all ${
                    value.consultationAnswers.projection === opt
                      ? 'border-accent bg-accent/5 text-accent font-medium'
                      : 'border-border bg-surface text-ink hover:bg-surface-raised'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center gap-2 rounded-lg bg-surface-sunken p-3 text-xs text-ink-muted">
            <CheckCircle2 size={14} className="text-accent" />
            Your settings will automatically initialize with our mathematical recommendations, but your answers will help us fine-tune the final preview.
          </div>
        </div>
      </Card>
    </div>
  )
}
