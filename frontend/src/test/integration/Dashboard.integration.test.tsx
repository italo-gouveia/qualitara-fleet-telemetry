import { type ReactNode } from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { http, HttpResponse } from 'msw'
import { describe, it, expect } from 'vitest'
import { server } from '../mocks/server'
import { FleetSummary } from '../../components/FleetSummary'
import { VehicleList } from '../../components/VehicleList'
import { ZoneCountsPanel } from '../../components/ZoneCountsPanel'
import { AnomaliesPanel } from '../../components/AnomaliesPanel'

/** Fresh QueryClient per test — no shared cache, no retries, no polling */
function makeClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchInterval: false as const },
    },
  })
}

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={makeClient()}>
      {children}
    </QueryClientProvider>
  )
}

// ─── FleetSummary ───────────────────────────────────────────────────────────

describe('FleetSummary (integration)', () => {
  it('shows loading state initially then renders fleet counts from the API', async () => {
    render(<Wrapper><FleetSummary /></Wrapper>)

    expect(screen.getByText(/loading fleet state/i)).toBeInTheDocument()

    await waitFor(() =>
      expect(screen.getByText(/19 vehicles/i)).toBeInTheDocument(),
    )
    expect(screen.getByText('10')).toBeInTheDocument() // idle
    expect(screen.getByText('5')).toBeInTheDocument()  // moving
    expect(screen.getByText('3')).toBeInTheDocument()  // charging
    expect(screen.getByText('1')).toBeInTheDocument()  // fault
  })
})

// ─── VehicleList ─────────────────────────────────────────────────────────────

describe('VehicleList (integration)', () => {
  it('loads and renders all vehicles from the API', async () => {
    render(<Wrapper><VehicleList /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText('v-01')).toBeInTheDocument(),
    )
    expect(screen.getByText('v-02')).toBeInTheDocument()
    expect(screen.getByText(/vehicles \(2\)/i)).toBeInTheDocument()
  })

  it('renders error state when the API returns 500', async () => {
    server.use(
      http.get('http://localhost:8000/vehicles', () =>
        HttpResponse.json({ detail: 'Internal Server Error' }, { status: 500 }),
      ),
    )
    render(<Wrapper><VehicleList /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText(/failed to load vehicles/i)).toBeInTheDocument(),
    )
  })
})

// ─── ZoneCountsPanel ────────────────────────────────────────────────────────

describe('ZoneCountsPanel (integration)', () => {
  it('loads zone counts and displays them sorted descending', async () => {
    render(<Wrapper><ZoneCountsPanel /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText('charging bay 1')).toBeInTheDocument(),
    )

    const rows = screen.getAllByRole('row').slice(1) // skip header
    expect(rows[0]).toHaveTextContent('charging bay 1') // 12
    expect(rows[1]).toHaveTextContent('aisle a')        // 5
    expect(rows[2]).toHaveTextContent('pack station')   // 3
  })

  it('renders error state when the API returns 500', async () => {
    server.use(
      http.get('http://localhost:8000/zones/counts', () =>
        HttpResponse.json({ detail: 'error' }, { status: 500 }),
      ),
    )
    render(<Wrapper><ZoneCountsPanel /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText(/failed to load zone counts/i)).toBeInTheDocument(),
    )
  })
})

// ─── AnomaliesPanel ─────────────────────────────────────────────────────────

describe('AnomaliesPanel (integration)', () => {
  it('shows loading state then renders anomaly rows from the API', async () => {
    render(<Wrapper><AnomaliesPanel /></Wrapper>)

    expect(screen.getByText(/loading anomalies/i)).toBeInTheDocument()

    await waitFor(() =>
      expect(screen.getByText('v-02')).toBeInTheDocument(),
    )
    expect(screen.getByText('v-01')).toBeInTheDocument()
    // type rendered with underscores replaced by spaces
    expect(screen.getByText('fault entered')).toBeInTheDocument()
    expect(screen.getByText('low battery')).toBeInTheDocument()
  })

  it('shows count badge matching the number of anomalies returned', async () => {
    const { container } = render(<Wrapper><AnomaliesPanel /></Wrapper>)

    await waitFor(() =>
      // handlers.ts returns 3 anomalies
      expect(container.querySelector('.panel-count')).toHaveTextContent('3'),
    )
  })

  it('shows empty state when the API returns an empty list', async () => {
    server.use(
      http.get('http://localhost:8000/anomalies', () =>
        HttpResponse.json([]),
      ),
    )
    render(<Wrapper><AnomaliesPanel /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText(/no anomalies detected/i)).toBeInTheDocument(),
    )
  })

  it('renders error state when the API returns 500', async () => {
    server.use(
      http.get('http://localhost:8000/anomalies', () =>
        HttpResponse.json({ detail: 'error' }, { status: 500 }),
      ),
    )
    render(<Wrapper><AnomaliesPanel /></Wrapper>)

    await waitFor(() =>
      expect(screen.getByText(/failed to load anomalies/i)).toBeInTheDocument(),
    )
  })
})
