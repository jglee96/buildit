import MapboxDraw from '@mapbox/mapbox-gl-draw'
import maplibregl, { Map as MapLibreMap } from 'maplibre-gl'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Button, StatusChip } from '@/shared/ui'

;(MapboxDraw as unknown as { constants?: { classes?: Record<string, string> } }).constants = {
  ...(MapboxDraw as unknown as { constants?: { classes?: Record<string, string> } }).constants,
  classes: {
    ...((MapboxDraw as unknown as { constants?: { classes?: Record<string, string> } }).constants?.classes ?? {}),
    CANVAS: 'maplibregl-canvas',
    CONTROL_BASE: 'maplibregl-ctrl',
    CONTROL_PREFIX: 'maplibregl-ctrl-',
    CONTROL_GROUP: 'maplibregl-ctrl-group',
    ATTRIBUTION: 'maplibregl-ctrl-attrib'
  }
}

type SiteMapProps = {
  polygon: number[][][]
  onPolygonChange: (polygon: number[][][]) => void
}

const osmStyle: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap Contributors'
    }
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
}

export function SiteMap({ polygon, onPolygonChange }: SiteMapProps): JSX.Element {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const drawRef = useRef<MapboxDraw | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) {
      return
    }

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: osmStyle,
      center: [126.978, 37.5665],
      zoom: 14
    })

    const draw = new MapboxDraw({
      displayControlsDefault: false,
      defaultMode: 'simple_select'
    })

    map.addControl(draw as unknown as maplibregl.IControl, 'top-left')
    mapRef.current = map
    drawRef.current = draw

    const syncPolygon = (): void => {
      const featureCollection = draw.getAll()
      const firstPolygon = featureCollection.features.find((feature) => feature.geometry.type === 'Polygon')
      if (!firstPolygon || firstPolygon.geometry.type !== 'Polygon') {
        onPolygonChange([])
        return
      }
      onPolygonChange(firstPolygon.geometry.coordinates as number[][][])
    }

    map.on('load', () => setStatus('ready'))
    map.on('error', () => setStatus('error'))
    map.on('draw.create', syncPolygon)
    map.on('draw.update', syncPolygon)
    map.on('draw.delete', () => onPolygonChange([]))

    return () => {
      map.remove()
      mapRef.current = null
      drawRef.current = null
    }
  }, [onPolygonChange])

  const helpText = useMemo(() => {
    if (status === 'loading') {
      return '지도 로딩 중...'
    }
    if (status === 'error') {
      return '지도 로딩에 실패했습니다. 네트워크 연결 후 새로고침해주세요.'
    }
    return polygon.length > 0 ? '대지 폴리곤이 선택되었습니다.' : '폴리곤 그리기 버튼을 눌러 대지를 지정하세요.'
  }, [polygon.length, status])

  const polygonMeta = useMemo(() => {
    if (polygon.length === 0 || polygon[0].length < 4) {
      return { vertices: 0, areaM2: 0 }
    }
    const ring = polygon[0]
    const projected = ring.map(([lng, lat]) => {
      const x = (lng * 111320) * Math.cos((lat * Math.PI) / 180)
      const y = lat * 110540
      return [x, y] as const
    })
    let twiceArea = 0
    for (let i = 0; i < projected.length - 1; i += 1) {
      const [x1, y1] = projected[i]
      const [x2, y2] = projected[i + 1]
      twiceArea += x1 * y2 - x2 * y1
    }
    return {
      vertices: Math.max(0, ring.length - 1),
      areaM2: Math.abs(twiceArea) / 2
    }
  }, [polygon])

  const startDraw = (): void => {
    drawRef.current?.changeMode('draw_polygon')
  }

  const clearDraw = (): void => {
    drawRef.current?.deleteAll()
    onPolygonChange([])
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="secondary" onClick={startDraw} disabled={status !== 'ready'}>
          폴리곤 그리기
        </Button>
        <Button variant="ghost" onClick={clearDraw} disabled={status !== 'ready'}>
          초기화
        </Button>
        <StatusChip tone={polygon.length > 0 ? 'good' : 'neutral'}>{helpText}</StatusChip>
        {polygonMeta.vertices > 0 ? <StatusChip tone="good">정점 {polygonMeta.vertices}개</StatusChip> : null}
        {polygonMeta.areaM2 > 0 ? <StatusChip tone="good">약 {Math.round(polygonMeta.areaM2)}㎡</StatusChip> : null}
      </div>
      <div className="h-[480px] overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
        <div ref={mapContainerRef} className="h-full w-full" />
      </div>
    </div>
  )
}
