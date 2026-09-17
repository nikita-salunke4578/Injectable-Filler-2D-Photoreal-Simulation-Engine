import type { ConfigurationState } from '../types/simulation'
import { ZONES } from '../mock/staticData'

const COST_PER_ML_RANGE: [number, number] = [650, 950]

export function getActiveZones(config: ConfigurationState) {
  return ZONES.filter((zone) => config.enabledZones[zone.id])
}

export function getTotalVolume(config: ConfigurationState): number {
  return getActiveZones(config).reduce((sum, zone) => {
    const params = config.parameters[zone.id] as any
    return sum + (params.volumeMl || 0)
  }, 0)
}

export function getEstimatedCostRange(config: ConfigurationState): [number, number] {
  const totalVolume = getTotalVolume(config)
  return [totalVolume * COST_PER_ML_RANGE[0], totalVolume * COST_PER_ML_RANGE[1]]
}
