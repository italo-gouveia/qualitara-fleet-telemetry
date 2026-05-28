import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiFetch } from '../api/client'

describe('apiFetch', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  function mockOk(data: unknown) {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify(data), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
  }

  function mockStatus(status: number) {
    vi.mocked(fetch).mockResolvedValue(new Response('error', { status }))
  }

  it('calls fetch with the correct base URL and path', async () => {
    mockOk({})
    await apiFetch('/fleet/state')
    expect(vi.mocked(fetch)).toHaveBeenCalledWith('http://localhost:8000/fleet/state')
  })

  it('appends multiple query params to the URL', async () => {
    mockOk([])
    await apiFetch('/anomalies', { vehicle_id: 'v-01', limit: '10' })
    const called = vi.mocked(fetch).mock.calls[0][0] as string
    const url = new URL(called)
    expect(url.searchParams.get('vehicle_id')).toBe('v-01')
    expect(url.searchParams.get('limit')).toBe('10')
  })

  it('returns parsed JSON on a successful response', async () => {
    const payload = { idle: 5, moving: 3, charging: 2, fault: 1, total: 11 }
    mockOk(payload)
    const result = await apiFetch('/fleet/state')
    expect(result).toEqual(payload)
  })

  it('throws with status code on a 404 response', async () => {
    mockStatus(404)
    await expect(apiFetch('/fleet/state')).rejects.toThrow('API error 404')
  })

  it('throws with status code on a 500 response', async () => {
    mockStatus(500)
    await expect(apiFetch('/vehicles')).rejects.toThrow('API error 500')
  })
})
