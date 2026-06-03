import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from '@testing-library/react';

vi.mock('@/api/dashboard', () => ({
  dashboardApi: {
    getStats: vi.fn(),
  },
}));

import { dashboardApi } from '@/api/dashboard';
import { useDashboardStore } from '@/stores/dashboardStore';

describe('dashboardStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    act(() => {
      useDashboardStore.setState({
        stats: null,
        loading: false,
        error: false,
      });
    });
  });

  it('fetchStats sets stats on success', async () => {
    const mockStats = {
      pending_invoice_count: 3,
      monthly_total_amount: 1500.50,
      active_batch_count: 2,
      recent_batches: [
        {
          id: 1,
          department: '研发部',
          period_start: '2025-12-01',
          period_end: '2025-12-31',
          report_date: '2025-12-15',
          reporter: '张三',
          total_amount: 1500.50,
          status: 'draft',
          invoice_count: 3,
          created_at: '2025-12-15T10:30:00',
        },
      ],
    };
    vi.mocked(dashboardApi.getStats).mockResolvedValue(mockStats);

    await act(async () => {
      await useDashboardStore.getState().fetchStats();
    });

    const state = useDashboardStore.getState();
    expect(state.stats).toEqual(mockStats);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(false);
  });

  it('fetchStats sets error on failure', async () => {
    vi.mocked(dashboardApi.getStats).mockRejectedValue(new Error('Network error'));

    await act(async () => {
      await useDashboardStore.getState().fetchStats();
    });

    const state = useDashboardStore.getState();
    expect(state.stats).toBeNull();
    expect(state.loading).toBe(false);
    expect(state.error).toBe(true);
  });

  it('fetchStats sets loading to true during request', async () => {
    let resolvePromise!: (value: unknown) => void;
    vi.mocked(dashboardApi.getStats).mockReturnValue(new Promise((resolve) => {
      resolvePromise = resolve;
    }));

    const fetchPromise = act(async () => {
      const p = useDashboardStore.getState().fetchStats();
      expect(useDashboardStore.getState().loading).toBe(true);
      resolvePromise({
        pending_invoice_count: 0,
        monthly_total_amount: 0,
        active_batch_count: 0,
        recent_batches: [],
      });
      await p;
    });

    await fetchPromise;
    expect(useDashboardStore.getState().loading).toBe(false);
  });
});