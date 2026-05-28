import { test, expect } from '@playwright/test'

const API = 'http://localhost:8000'

const FLEET_STATE = { idle: 10, moving: 5, charging: 3, fault: 2, total: 20 }

const VEHICLES = [
  {
    vehicle_id: 'v-01',
    status: 'moving',
    battery_pct: 75,
    lat: 51.505,
    lon: -0.09,
    updated_at: '2026-05-28T10:00:00Z',
  },
  {
    vehicle_id: 'v-02',
    status: 'fault',
    battery_pct: 8,
    lat: 51.506,
    lon: -0.091,
    updated_at: '2026-05-28T10:00:00Z',
  },
]

const ZONES = { aisle_a: 5, charging_bay_1: 20, pack_station: 2 }

test.beforeEach(async ({ page }) => {
  // Mock all API endpoints — no real backend required
  await page.route(`${API}/fleet/state`, route => route.fulfill({ json: FLEET_STATE }))
  await page.route(`${API}/vehicles`, route => route.fulfill({ json: VEHICLES }))
  await page.route(`${API}/zones/counts`, route => route.fulfill({ json: ZONES }))
  await page.route(`${API}/anomalies**`, route => route.fulfill({ json: [] }))
})

test('page title and LIVE badge are visible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /fleet telemetry monitor/i })).toBeVisible()
  await expect(page.getByText('● LIVE')).toBeVisible()
})

test('fleet summary renders correct total and all four status labels', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(/20 vehicles/i)).toBeVisible()
  const tiles = page.locator('.status-tiles')
  for (const label of ['idle', 'moving', 'charging', 'fault']) {
    await expect(tiles.getByText(label)).toBeVisible()
  }
})

test('vehicle list shows heading with count and both vehicle IDs', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('Vehicles (2)')).toBeVisible()
  await expect(page.getByText('v-01')).toBeVisible()
  await expect(page.getByText('v-02')).toBeVisible()
})

test('fault vehicle row has row-fault CSS class', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('tr.row-fault')).toBeVisible()
})

test('zone counts panel heading and high-count zone highlight are visible', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /zone counts/i })).toBeVisible()
  const highRow = page.locator('tr.zone-high')
  await expect(highRow).toBeVisible()
  await expect(highRow).toContainText('charging bay 1')
})

test('zones are sorted descending by count', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('charging bay 1')).toBeVisible()
  const rows = page.locator('.zone-table tbody tr')
  await expect(rows.nth(0)).toContainText('charging bay 1') // 20
  await expect(rows.nth(1)).toContainText('aisle a')        // 5
  await expect(rows.nth(2)).toContainText('pack station')   // 2
})

test('fleet summary status tile counts match mocked data', async ({ page }) => {
  await page.goto('/')
  // The tile counts are rendered as text nodes inside .status-tile
  const tiles = page.locator('.status-tile')
  await expect(tiles).toHaveCount(4)
  await expect(tiles.filter({ hasText: 'idle' })).toContainText('10')
  await expect(tiles.filter({ hasText: 'moving' })).toContainText('5')
  await expect(tiles.filter({ hasText: 'charging' })).toContainText('3')
  await expect(tiles.filter({ hasText: 'fault' })).toContainText('2')
})
