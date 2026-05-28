import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { VehicleRow } from '../components/VehicleRow'
import type { Vehicle } from '../types'

vi.mock('../hooks/useVehicleAnomalies', () => ({
  useVehicleAnomalies: vi.fn(),
}))

import { useVehicleAnomalies } from '../hooks/useVehicleAnomalies'

const mockUseVehicleAnomalies = vi.mocked(useVehicleAnomalies)

const baseVehicle: Vehicle = {
  vehicle_id: 'v-01',
  status: 'moving',
  battery_pct: 75,
  lat: 51.505,
  lon: -0.09,
  updated_at: '2026-05-28T10:00:00Z',
}

describe('VehicleRow', () => {
  beforeEach(() => {
    mockUseVehicleAnomalies.mockReturnValue({
      data: undefined,
    } as ReturnType<typeof useVehicleAnomalies>)
  })

  it('renders vehicle ID and status badge', () => {
    render(
      <table><tbody>
        <VehicleRow vehicle={baseVehicle} />
      </tbody></table>
    )
    expect(screen.getByText('v-01')).toBeInTheDocument()
    expect(screen.getByText('moving')).toBeInTheDocument()
  })

  it('renders battery percentage', () => {
    render(
      <table><tbody>
        <VehicleRow vehicle={baseVehicle} />
      </tbody></table>
    )
    expect(screen.getByText('75%')).toBeInTheDocument()
  })

  it('applies fault row class when vehicle status is fault', () => {
    const faultVehicle: Vehicle = { ...baseVehicle, status: 'fault' }
    render(
      <table><tbody>
        <VehicleRow vehicle={faultVehicle} />
      </tbody></table>
    )
    const row = screen.getByRole('row')
    expect(row).toHaveClass('row-fault')
  })
})
