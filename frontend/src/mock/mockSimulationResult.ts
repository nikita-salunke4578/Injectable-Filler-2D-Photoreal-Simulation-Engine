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
export async function mockSimulationResult(
  photoUrl: string,
  config: ConfigurationState,
): Promise<SimulationResult> {
  const requestPayload = buildRequestPayload(config)
  const totalVolumeMl = requestPayload.reduce((sum, p) => sum + p.volume, 0)

  // Simulate network + processing latency.
  await new Promise((resolve) => setTimeout(resolve, 1600))

  return {
    id: `sim_${Date.now()}`,
    beforeImageUrl: photoUrl,
    afterImageUrl: photoUrl,
    generatedAt: new Date().toISOString(),
    requestPayload,
    estimatedCostUsd: [totalVolumeMl * 650, totalVolumeMl * 950],
    totalVolumeMl: Number(totalVolumeMl.toFixed(2)),
    disclaimer:
      'This is a simulated preview for planning and educational purposes only. Actual results vary by anatomy, product and injector technique.',
  }
}
