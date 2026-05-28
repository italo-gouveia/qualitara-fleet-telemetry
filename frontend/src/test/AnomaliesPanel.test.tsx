import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import { AnomaliesPanel } from '../components/AnomaliesPanel'
import type { Anomaly } from '../types'

vi.mock('../hooks/useAnomalies')
import { useAnomalies } from '../hooks/useAnomalies'

const mockUseAnomalies = vi.mocked(useAnomalies)

const ANOMALIES: Anomaly[] = [
  {
    id: 1,
    vehicle_id: 'v-02',
    type: 'fault_entered',
    detected_at: new Date(Date.now() - 30_000).toISOString(),
    detail: {},
  },
  {
    id: 2,
    vehicle_id: 'v-01',
    type: 'low_battery',
    detected_at: new Date(Date.now() - 120_000).toISOString(),
    detail: { battery_pct: 12 },
  },
]

describe('AnomaliesPanel', () => {
  it('shows loading state', () => {
    mockUseAnomalies.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useAnomalies>)

    render(<AnomaliesPanel />)
    expect(screen.getByText('Loading anomalies…')).toBeInTheDocument()
  })

  it('shows error state', () => {
    mockUseAnomalies.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
    } as ReturnType<typeof useAnomalies>)

    const { container } = render(<AnomaliesPanel />)
    expect(container.querySelector('.error')).toBeInTheDocument()
  })

  it('shows empty state when no anomalies', () => {
    mockUseAnomalies.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useAnomalies>)

    render(<AnomaliesPanel />)
    expect(screen.getByText('No anomalies detected.')).toBeInTheDocument()
  })

  it('renders one row per anomaly with vehicle id and type badge', () => {
    mockUseAnomalies.mockReturnValue({
      data: ANOMALIES,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useAnomalies>)

    render(<AnomaliesPanel />)
    expect(screen.getByText('v-02')).toBeInTheDocument()
    expect(screen.getByText('v-01')).toBeInTheDocument()
    expect(screen.getByText('fault entered')).toBeInTheDocument()
    expect(screen.getByText('low battery')).toBeInTheDocument()
  })

  it('shows count badge when anomalies are present', () => {
    mockUseAnomalies.mockReturnValue({
      data: ANOMALIES,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useAnomalies>)

    const { container } = render(<AnomaliesPanel />)
    expect(container.querySelector('.panel-count')).toHaveTextContent('2')
  })

  it('applies red badge to critical anomaly types', () => {
    mockUseAnomalies.mockReturnValue({
      data: [{ ...ANOMALIES[0], type: 'critical_battery' }],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useAnomalies>)

    render(<AnomaliesPanel />)
    const badge = screen.getByText('critical battery')
    expect(badge).toHaveClass('badge-red')
  })
})
