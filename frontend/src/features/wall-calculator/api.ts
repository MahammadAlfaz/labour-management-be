import { apiFetch, apiUpload } from '../../lib/apiClient'

export type MeasurementConfidence = 'high' | 'low'

export interface MeasurementLine {
  raw_text: string
  length: string
  quantity: number
  confidence: MeasurementConfidence
  included: boolean
}

export interface ExtractedMeasurement {
  raw_text: string
  length: string
  quantity: number
  confidence: MeasurementConfidence
}

export interface ExtractionResult {
  source_image_path: string
  measurements: ExtractedMeasurement[]
  warnings: string[]
}

export interface LayerInput {
  label?: string | null
  height: string
  breadth: string
}

export interface LayerOut extends LayerInput {
  area: string
}

export interface WallCalculation {
  id: string
  site_id: string | null
  title: string | null
  source_image_path: string | null
  measurements: MeasurementLine[]
  total_measurement: string
  layers: LayerOut[]
  total_area: string
  rate_per_sqft: string
  total_cost: string
  created_by: string
  updated_by: string
  created_at: string
  updated_at: string
}

export interface WallCalculationInput {
  site_id?: string | null
  title?: string | null
  source_image_path?: string | null
  measurements: MeasurementLine[]
  total_measurement: string
  layers: LayerInput[]
  rate_per_sqft: string
}

export function extractMeasurements(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return apiUpload<ExtractionResult>('/wall-calculations/extract', formData)
}

export function listWallCalculations(params: { site_id?: string } = {}) {
  const query = new URLSearchParams()
  if (params.site_id) query.set('site_id', params.site_id)
  const qs = query.toString()
  return apiFetch<WallCalculation[]>(`/wall-calculations${qs ? `?${qs}` : ''}`)
}

export function getWallCalculation(id: string) {
  return apiFetch<WallCalculation>(`/wall-calculations/${id}`)
}

export function createWallCalculation(input: WallCalculationInput) {
  return apiFetch<WallCalculation>('/wall-calculations', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

export function updateWallCalculation(id: string, input: Partial<WallCalculationInput>) {
  return apiFetch<WallCalculation>(`/wall-calculations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
}

export function deleteWallCalculation(id: string) {
  return apiFetch<void>(`/wall-calculations/${id}`, { method: 'DELETE' })
}
