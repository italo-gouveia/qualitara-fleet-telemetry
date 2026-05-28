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

  it('battery fill is red when battery_pct is below 15', () => {
    const lowBattery: Vehicle = { ...baseVehicle, battery_pct: 10 }
    const { container } = render(
      <table><tbody>
        <VehicleRow vehicle={lowBattery} />
      </tbody></table>
    )
    const fill = container.querySelector('.battery-fill') as HTMLElement
    expect(fill).toHaveStyle('background-color: rgb(239, 68, 68)')
  })

  it('battery fill is green when battery_pct is 15 or above', () => {
    const okBattery: Vehicle = { ...baseVehicle, battery_pct: 50 }
    const { container } = render(
      <table><tbody>
        <VehicleRow vehicle={okBattery} />
      </tbody></table>
    )
    const fill = container.querySelector('.battery-fill') as HTMLElement
    expect(fill).toHaveStyle('background-color: rgb(34, 197, 94)')
  })

  it('shows anomaly badge when anomalies are present', () => {
    mockUseVehicleAnomalies.mockReturnValue({
      data: [
        {
          id: 1,
          vehicle_id: 'v-01',
          type: 'low_battery',
          detected_at: '2026-05-28T10:00:00Z',
          detail: {},
        },
      ],
    } as ReturnType<typeof useVehicleAnomalies>)
    render(
      <table><tbody>
        <VehicleRow vehicle={baseVehicle} />
      </tbody></table>
    )
    expect(screen.getByText('low_battery')).toBeInTheDocument()
  })

  it('does not show anomaly badge when anomaly list is empty', () => {
    mockUseVehicleAnomalies.mockReturnValue({
      data: [],
    } as ReturnType<typeof useVehicleAnomalies>)
    const { container } = render(
      <table><tbody>
        <VehicleRow vehicle={baseVehicle} />
      </tbody></table>
    )
    expect(container.querySelector('.badge-orange')).not.toBeInTheDocument()
  })
})
