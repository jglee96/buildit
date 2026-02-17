export type SitePolygon = {
  type: 'Polygon'
  coordinates: number[][][]
}

export type UserRead = {
  id: string
  email: string
  name?: string
  created_at: string
}

export type ProjectRead = {
  id: string
  user_id: string
  name: string
  country_code: string
  jurisdiction_code: string
  occupancy_type: string
  site_geojson: SitePolygon
  created_at: string
}

export type ConstraintCheck = {
  rule_key: string
  rule_type: string
  passed: boolean
  detail: string
}

export type MeshPayload =
  | {
      type: 'box'
      width: number
      depth: number
      height: number
      origin?: [number, number, number]
    }
  | {
      type: 'stacked'
      segments: {
        width: number
        depth: number
        height: number
        base_y: number
      }[]
      origin: [number, number, number]
    }
  | {
      type: 'courtyard'
      outer_width: number
      outer_depth: number
      inner_width: number
      inner_depth: number
      height: number
      origin: [number, number, number]
    }
  | {
      type: 'multi_block'
      blocks: {
        x: number
        z: number
        width: number
        depth: number
        height: number
      }[]
      site_outline?: [number, number][]
      origin: [number, number, number]
    }

export type RunOption = {
  id: string
  rank: number
  option_type: string
  score: number
  parameters: {
    engine_version?: string
    far?: number
    height_m?: number
    coverage_percent?: number
    open_space_percent?: number
    qualitative_scores?: {
      skyline_harmony: number
      street_scale_fit: number
      open_space_quality: number
      reference_maturity: number
      market_fit?: number
      total: number
    }
    objective?: string
    feasible?: boolean
    legal_basis_tags?: string[]
    block_count?: number
    floors?: number
    building_spacing_m?: number
    max_block_length_m?: number
    plan_family?: string
    avg_unit_area_m2?: number
    unit_mix?: Record<string, number>
    runtime_profile?: {
      pipeline_ms?: Record<string, number>
      optimizer_ms?: Record<string, number>
    }
  }
  checks: ConstraintCheck[]
  mesh_payload: MeshPayload
}

export type SolarPoint = {
  timestamp_utc: string
  sun_altitude: number
  sun_azimuth: number
  insolation_kwh_m2: number
  shadow_ratio: number
}

export type RunRead = {
  id: string
  project_id: string
  snapshot_id: string
  objective: string
  status: string
  started_at?: string
  completed_at?: string
  error_message?: string
  options: RunOption[]
  solar: Record<string, SolarPoint[]>
}
