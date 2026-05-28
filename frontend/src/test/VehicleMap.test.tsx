import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { VehicleMap } from "../components/VehicleMap";

// ── react-leaflet stub ────────────────────────────────────────────────────────
// jsdom has no canvas / SVG rendering; stub the entire library so tests run
// without browser-specific APIs while still exercising the component logic.
vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => null,
  CircleMarker: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="circle-marker">{children}</div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="popup">{children}</div>
  ),
  Tooltip: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="tooltip">{children}</div>
  ),
}));

vi.mock("leaflet/dist/leaflet.css", () => ({}));

// ── data hooks ────────────────────────────────────────────────────────────────
vi.mock("../hooks/useVehicles");
vi.mock("../hooks/useAnomalies");

import { useVehicles } from "../hooks/useVehicles";
import { useAnomalies } from "../hooks/useAnomalies";

const mockUseVehicles = vi.mocked(useVehicles);
const mockUseAnomalies = vi.mocked(useAnomalies);

const VEHICLES = [
  { vehicle_id: "v-01", status: "moving",   battery_pct: 80, lat: 37.41, lon: -122.08, updated_at: new Date().toISOString() },
  { vehicle_id: "v-02", status: "fault",    battery_pct: 15, lat: 37.42, lon: -122.07, updated_at: new Date().toISOString() },
  { vehicle_id: "v-03", status: "charging", battery_pct: 50, lat: 37.40, lon: -122.09, updated_at: new Date().toISOString() },
] as const;

const ANOMALY = { id: 1, vehicle_id: "v-02", type: "fault_entered", detected_at: new Date().toISOString(), detail: {} };

beforeEach(() => {
  mockUseAnomalies.mockReturnValue({ data: [], isLoading: false, isError: false } as ReturnType<typeof useAnomalies>);
});

describe("VehicleMap", () => {
  it("renders loading state", () => {
    mockUseVehicles.mockReturnValue({ data: undefined, isLoading: true, isError: false } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    expect(screen.getByText(/loading map/i)).toBeInTheDocument();
  });

  it("renders error state", () => {
    mockUseVehicles.mockReturnValue({ data: undefined, isLoading: false, isError: true } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    expect(screen.getByText(/failed to load vehicle positions/i)).toBeInTheDocument();
  });

  it("renders map container with vehicles", () => {
    mockUseVehicles.mockReturnValue({ data: VEHICLES as never, isLoading: false, isError: false } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    expect(screen.getByTestId("map-container")).toBeInTheDocument();
    // 3 vehicles → at least 3 main markers (fault ring adds extra ones)
    expect(screen.getAllByTestId("circle-marker").length).toBeGreaterThanOrEqual(3);
  });

  it("shows vehicle count badge in heading", () => {
    mockUseVehicles.mockReturnValue({ data: VEHICLES as never, isLoading: false, isError: false } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders popup content for each vehicle", () => {
    mockUseVehicles.mockReturnValue({ data: VEHICLES as never, isLoading: false, isError: false } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    // vehicle id appears in both Tooltip and Popup — getAllByText handles duplicates
    expect(screen.getAllByText("v-01").length).toBeGreaterThanOrEqual(1);
    // battery shown in popup
    expect(screen.getAllByText(/80%/).length).toBeGreaterThanOrEqual(1);
  });

  it("shows anomaly alert in popup for vehicles with active anomalies", () => {
    mockUseVehicles.mockReturnValue({ data: VEHICLES as never, isLoading: false, isError: false } as ReturnType<typeof useVehicles>);
    mockUseAnomalies.mockReturnValue({ data: [ANOMALY], isLoading: false, isError: false } as ReturnType<typeof useAnomalies>);
    render(<VehicleMap />);
    expect(screen.getByText(/active anomaly/i)).toBeInTheDocument();
  });

  it("renders status legend with all four statuses and anomaly label", () => {
    mockUseVehicles.mockReturnValue({ data: VEHICLES as never, isLoading: false, isError: false } as ReturnType<typeof useVehicles>);
    render(<VehicleMap />);
    // status words appear in both Tooltips and the legend — getAllByText handles duplicates
    expect(screen.getAllByText("moving").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("charging").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("idle").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("fault").length).toBeGreaterThanOrEqual(1);
    // "anomaly" only appears in the legend
    expect(screen.getByText("anomaly")).toBeInTheDocument();
  });
});
