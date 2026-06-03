import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { RegisterPage } from '@/pages/RegisterPage';
import { authApi } from '@/api/auth';

vi.mock('@/api/auth', () => ({
  authApi: { register: vi.fn() },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

describe('RegisterPage layout', () => {
  beforeEach(() => {
    vi.mocked(authApi.register).mockReset();
    mockNavigate.mockReset();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );
  });

  it('renders dual-panel layout with left brand section matching login page', () => {
    expect(screen.getByText('EasyBX')).toBeInTheDocument();
    expect(screen.getByText('智能发票报销助手')).toBeInTheDocument();
  });

  it('renders right side form with username, display name, and password inputs', () => {
    expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    expect(screen.getByLabelText('显示名称')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '注册' })).toBeInTheDocument();
  });

  it('register button has type submit', () => {
    const btn = screen.getByRole('button', { name: '注册' });
    expect(btn).toHaveAttribute('type', 'submit');
  });

  it('renders login link at the bottom', () => {
    expect(screen.getByText('已有账号？')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '登录' })).toBeInTheDocument();
  });
});

describe('RegisterPage frontend validation', () => {
  beforeEach(() => {
    vi.mocked(authApi.register).mockReset();
    mockNavigate.mockReset();
  });

  it('shows error on password when password is less than 6 characters and does not send request', async () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '测试' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '12345' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('密码至少需要 6 个字符')).toBeInTheDocument();
    });

    expect(vi.mocked(authApi.register)).not.toHaveBeenCalled();
  });

  it('sends request when all fields are valid and password is 6+ characters', async () => {
    vi.mocked(authApi.register).mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '测试' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(vi.mocked(authApi.register)).toHaveBeenCalledWith({
        username: 'testuser',
        password: '123456',
        display_name: '测试',
      });
    });
  });
});

describe('RegisterPage error mapping', () => {
  beforeEach(() => {
    vi.mocked(authApi.register).mockReset();
    mockNavigate.mockReset();
  });

  it('shows username exists error on 409 without clearing form fields', async () => {
    vi.mocked(authApi.register).mockRejectedValue({ response: { status: 409 } });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'existing' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '测试' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('用户名已存在')).toBeInTheDocument();
    });

    const usernameInput = screen.getByLabelText('用户名') as HTMLInputElement;
    const displayNameInput = screen.getByLabelText('显示名称') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('密码') as HTMLInputElement;
    expect(usernameInput.value).toBe('existing');
    expect(displayNameInput.value).toBe('测试');
    expect(passwordInput.value).toBe('123456');
  });

  it('shows network error when err.response is undefined', async () => {
    vi.mocked(authApi.register).mockRejectedValue({});

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '测试' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('网络连接失败，请稍后重试')).toBeInTheDocument();
    });
  });

  it('shows server error on 500 response', async () => {
    vi.mocked(authApi.register).mockRejectedValue({ response: { status: 500 } });

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '测试' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(screen.getByText('服务异常，请稍后重试')).toBeInTheDocument();
    });
  });
});

describe('RegisterPage success redirect', () => {
  beforeEach(() => {
    vi.mocked(authApi.register).mockReset();
    mockNavigate.mockReset();
  });

  it('navigates to /login with registeredUsername in state on success', async () => {
    vi.mocked(authApi.register).mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'zhangsan' } });
    fireEvent.change(screen.getByLabelText('显示名称'), { target: { value: '张三' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '注册' }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { registeredUsername: 'zhangsan' },
      });
    });
  });
});