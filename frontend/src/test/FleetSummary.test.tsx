import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { FleetSummary } from '../components/FleetSummary'

vi.mock('../hooks/useFleetState', () => ({
  useFleetState: vi.fn(),
}))

import { useFleetState } from '../hooks/useFleetState'

const mockUseFleetState = vi.mocked(useFleetState)

describe('FleetSummary', () => {
  it('renders loading state when data is not ready', () => {
    mockUseFleetState.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useFleetState>)
    render(<FleetSummary />)
    expect(screen.getByText(/loading fleet state/i)).toBeInTheDocument()
  })

  it('renders four status tiles with correct counts', () => {
    mockUseFleetState.mockReturnValue({
      data: { idle: 10, moving: 15, charging: 5, fault: 2, total: 32 },
      isLoading: false,
    } as ReturnType<typeof useFleetState>)
    render(<FleetSummary />)
    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('renders total vehicle count in the heading', () => {
    mockUseFleetState.mockReturnValue({
      data: { idle: 10, moving: 15, charging: 5, fault: 2, total: 32 },
      isLoading: false,
    } as ReturnType<typeof useFleetState>)
    render(<FleetSummary />)
    expect(screen.getByText(/32 vehicles/i)).toBeInTheDocument()
  })
})
