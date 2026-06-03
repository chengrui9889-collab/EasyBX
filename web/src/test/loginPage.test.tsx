import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '@/pages/LoginPage';
import { authApi } from '@/api/auth';

vi.mock('@/api/auth', () => ({
  authApi: { login: vi.fn() },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

describe('LoginPage layout', () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'token', token_type: 'bearer' });
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );
  });

  it('renders dual-panel layout with left brand section', () => {
    expect(screen.getByText('EasyBX')).toBeInTheDocument();
    expect(screen.getByText('智能发票报销助手')).toBeInTheDocument();
  });

  it('renders right side form with username and password inputs', () => {
    expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    expect(screen.getByLabelText('密码')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument();
  });

  it('renders register link', () => {
    expect(screen.getByText('还没有账号？')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '注册' })).toBeInTheDocument();
  });

  it('login button has type submit for Enter key support', () => {
    const btn = screen.getByRole('button', { name: '登录' });
    expect(btn).toHaveAttribute('type', 'submit');
  });
});

describe('LoginPage frontend validation', () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
  });

  it('shows error on username input when username is empty and does not send request', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'token', token_type: 'bearer' });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument();
    });

    expect(vi.mocked(authApi.login)).not.toHaveBeenCalled();
  });

  it('shows error on password input when password is empty and does not send request', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'token', token_type: 'bearer' });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('请输入密码')).toBeInTheDocument();
    });

    expect(vi.mocked(authApi.login)).not.toHaveBeenCalled();
  });

  it('sends request when both username and password are non-empty', async () => {
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'token', token_type: 'bearer' });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(vi.mocked(authApi.login)).toHaveBeenCalledWith({
        username: 'testuser',
        password: '123456',
      });
    });
  });
});

describe('LoginPage error mapping', () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
  });

  it('shows credentials error, clears password, and focuses password field on 401', async () => {
    vi.mocked(authApi.login).mockRejectedValue({ response: { status: 401 } });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'wrongpass' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('用户名或密码错误')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText('密码') as HTMLInputElement;
    expect(passwordInput.value).toBe('');
    expect(document.activeElement).toBe(passwordInput);
  });

  it('shows network error when err.response is undefined', async () => {
    vi.mocked(authApi.login).mockRejectedValue({});

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('网络连接失败，请稍后重试')).toBeInTheDocument();
    });
  });

  it('shows server error on 500 response', async () => {
    vi.mocked(authApi.login).mockRejectedValue({ response: { status: 500 } });

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'testuser' } });
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: '123456' } });
    fireEvent.click(screen.getByRole('button', { name: '登录' }));

    await waitFor(() => {
      expect(screen.getByText('服务异常，请稍后重试')).toBeInTheDocument();
    });
  });
});

describe('LoginPage registration success handoff', () => {
  beforeEach(() => {
    vi.mocked(authApi.login).mockReset();
    mockNavigate.mockReset();
  });

  it('shows green success banner and fills username when registeredUsername is in location state', () => {
    render(
      <MemoryRouter initialEntries={[{ pathname: '/login', state: { registeredUsername: 'zhangsan' } }]}>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText('注册成功，请登录')).toBeInTheDocument();

    const usernameInput = screen.getByLabelText('用户名') as HTMLInputElement;
    expect(usernameInput.value).toBe('zhangsan');
  });

  it('clears location state after rendering success banner', () => {
    render(
      <MemoryRouter initialEntries={[{ pathname: '/login', state: { registeredUsername: 'zhangsan' } }]}>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true, state: {} });
  });

  it('does not show green banner when no location state', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.queryByText('注册成功，请登录')).not.toBeInTheDocument();

    const usernameInput = screen.getByLabelText('用户名') as HTMLInputElement;
    expect(usernameInput.value).toBe('');
  });
});