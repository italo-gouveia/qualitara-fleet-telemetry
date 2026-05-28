import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { VehicleList } from '../components/VehicleList'
import type { Vehicle } from '../types'

vi.mock('../hooks/useVehicles', () => ({
  useVehicles: vi.fn(),
}))

vi.mock('../hooks/useVehicleAnomalies', () => ({
  useVehicleAnomalies: vi.fn().mockReturnValue({ data: undefined }),
}))

import { useVehicles } from '../hooks/useVehicles'

const mockUseVehicles = vi.mocked(useVehicles)

function makeVehicle(id: string, status: Vehicle['status'] = 'idle'): Vehicle {
  return {
    vehicle_id: id,
    status,
    battery_pct: 80,
    lat: 51.505,
    lon: -0.09,
    updated_at: '2026-05-28T10:00:00Z',
  }
}

describe('VehicleList', () => {
  beforeEach(() => {
    mockUseVehicles.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useVehicles>)
  })

  it('renders loading state while data is being fetched', () => {
    mockUseVehicles.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useVehicles>)
    render(<VehicleList />)
    expect(screen.getByText(/loading vehicles/i)).toBeInTheDocument()
  })

  it('renders error state when the request fails', () => {
    mockUseVehicles.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useVehicles>)
    render(<VehicleList />)
    const msg = screen.getByText(/failed to load vehicles/i)
    expect(msg).toBeInTheDocument()
    expect(msg).toHaveClass('error')
  })

  it('renders empty state when no vehicles are reporting', () => {
    mockUseVehicles.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useVehicles>)
    render(<VehicleList />)
    expect(screen.getByText(/no vehicles reporting yet/i)).toBeInTheDocument()
  })

  it('renders one row per vehicle and shows count in the heading', () => {
    mockUseVehicles.mockReturnValue({
      data: [makeVehicle('v-01'), makeVehicle('v-02'), makeVehicle('v-03')],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useVehicles>)
    render(<VehicleList />)
    expect(screen.getByText(/vehicles \(3\)/i)).toBeInTheDocument()
    expect(screen.getByText('v-01')).toBeInTheDocument()
    expect(screen.getByText('v-02')).toBeInTheDocument()
    expect(screen.getByText('v-03')).toBeInTheDocument()
  })
})
