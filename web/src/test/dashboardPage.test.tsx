import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { act } from '@testing-library/react';

vi.mock('@/stores/dashboardStore', () => ({
  useDashboardStore: vi.fn(),
}));

import { useDashboardStore } from '@/stores/dashboardStore';
import { DashboardPage } from '@/pages/DashboardPage';

const mockStore = vi.mocked(useDashboardStore);

function renderDashboard() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  );
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockStore.mockReturnValue({
      stats: null,
      loading: true,
      error: false,
      fetchStats: vi.fn(),
    });
    renderDashboard();
    expect(screen.getByText('概览')).toBeInTheDocument();
  });

  it('renders stats cards with data', () => {
    mockStore.mockReturnValue({
      stats: {
        pending_invoice_count: 5,
        monthly_total_amount: 3200.50,
        active_batch_count: 3,
        recent_batches: [
          {
            id: 1,
            department: '研发部',
            period_start: '2025-12-01',
            period_end: '2025-12-31',
            report_date: '2025-12-15',
            reporter: '张三',
            total_amount: 3200.50,
            status: 'draft',
            invoice_count: 5,
            created_at: '2025-12-15T10:30:00',
          },
        ],
      },
      loading: false,
      error: false,
      fetchStats: vi.fn(),
    });
    renderDashboard();
    expect(screen.getByText('5')).toBeInTheDocument();
    const amountTexts = screen.getAllByText('¥3,200.50');
    expect(amountTexts.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('3')).toBeInTheDocument();
    expect(screen.getByText('研发部')).toBeInTheDocument();
    expect(screen.getByText('上传发票')).toBeInTheDocument();
    expect(screen.getByText('创建批次')).toBeInTheDocument();
    expect(screen.getByText('导出台账')).toBeInTheDocument();
  });

  it('renders error state with dashes', () => {
    mockStore.mockReturnValue({
      stats: null,
      loading: false,
      error: true,
      fetchStats: vi.fn(),
    });
    renderDashboard();
    const dashes = screen.getAllByText('——');
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('renders empty state for new user', () => {
    mockStore.mockReturnValue({
      stats: {
        pending_invoice_count: 0,
        monthly_total_amount: 0,
        active_batch_count: 0,
        recent_batches: [],
      },
      loading: false,
      error: false,
      fetchStats: vi.fn(),
    });
    renderDashboard();
    expect(screen.getByText(/欢迎使用 EasyBX/)).toBeInTheDocument();
    expect(screen.getByText('开始使用')).toBeInTheDocument();
  });
});