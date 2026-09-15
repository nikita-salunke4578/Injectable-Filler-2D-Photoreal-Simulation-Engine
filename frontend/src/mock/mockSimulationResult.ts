import type { ConfigurationState, SimulationRequestPayload, SimulationResult } from '../types/simulation'
import { ZONES } from './staticData'

function buildRequestPayload(config: ConfigurationState): SimulationRequestPayload[] {
  return ZONES.filter((zone) => config.enabledZones[zone.id]).map((zone) => {
    const params = config.parameters[zone.id]
    return {
      zone: zone.id,
      volume: params.volumeMl,
      intensity: params.volumeMl > 0 ? Number((params.volumeMl / volumeCeiling(zone.id)).toFixed(2)) : 0,
      meta: { ...params },
    }
  })
}

function volumeCeiling(zone: SimulationRequestPayload['zone']) {
  switch (zone) {
    case 'lips':
      return 2.0
    case 'cheeks':
      return 4.0
    case 'jaw':
      return 3.0
  }
}

/**
 * mockSimulationResult
 *
 * This is the ONLY function that needs to be replaced once the real
 * simulation engine exists. It currently resolves with the uploaded
 * photo as both "before" and "after" so the preview UI can be built
 * and tested end to end. Swap the body of this function for a call to
 * POST /api/simulations and keep the return type identical.
 */
export async function runSimulationApi(
  photoFile: File,
  config: ConfigurationState,
): Promise<SimulationResult> {
  const requestPayload = buildRequestPayload(config)

  const base64Data = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(photoFile)
  })

  const response = await fetch('http://localhost:8000/api/simulations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      image_url: '',
      image_base64: base64Data,
      zones: requestPayload,
    }),
  })

  if (!response.ok) {
    throw new Error('Simulation failed on server')
  }

  const result = await response.json()
  
  // Map backend response properties to frontend camelCase expectations
  return {
    id: result.id,
    beforeImageUrl: result.before_image_url === 'local_base64_used' ? base64Data : result.before_image_url,
    afterImageUrl: result.after_image_url,
    generatedAt: result.generated_at,
    requestPayload,
    estimatedCostUsd: result.estimated_cost_usd,
    totalVolumeMl: result.total_volume_ml,
    disclaimer: result.disclaimer,
  }
}
