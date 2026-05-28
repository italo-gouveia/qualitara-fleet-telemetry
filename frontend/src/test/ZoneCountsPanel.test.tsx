import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ZoneCountsPanel } from '../components/ZoneCountsPanel'

vi.mock('../hooks/useZoneCounts', () => ({
  useZoneCounts: vi.fn(),
}))

import { useZoneCounts } from '../hooks/useZoneCounts'

const mockUseZoneCounts = vi.mocked(useZoneCounts)

describe('ZoneCountsPanel', () => {
  it('renders a row for each zone', () => {
    mockUseZoneCounts.mockReturnValue({
      data: { aisle_a: 3, charging_bay_1: 7, pack_station: 1 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useZoneCounts>)
    render(<ZoneCountsPanel />)
    expect(screen.getByText('aisle a')).toBeInTheDocument()
    expect(screen.getByText('charging bay 1')).toBeInTheDocument()
    expect(screen.getByText('pack station')).toBeInTheDocument()
  })

  it('renders zones sorted descending by count', () => {
    mockUseZoneCounts.mockReturnValue({
      data: { aisle_a: 3, charging_bay_1: 20, pack_station: 1 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useZoneCounts>)
    render(<ZoneCountsPanel />)
    const rows = screen.getAllByRole('row').slice(1) // skip header
    expect(rows[0]).toHaveTextContent('charging bay 1')
    expect(rows[1]).toHaveTextContent('aisle a')
    expect(rows[2]).toHaveTextContent('pack station')
  })

  it('applies highlight class to zones with count above threshold', () => {
    mockUseZoneCounts.mockReturnValue({
      data: { high_zone: 15, low_zone: 3 },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useZoneCounts>)
    render(<ZoneCountsPanel />)
    const rows = screen.getAllByRole('row').slice(1)
    expect(rows[0]).toHaveClass('zone-high')
    expect(rows[1]).not.toHaveClass('zone-high')
  })
})
