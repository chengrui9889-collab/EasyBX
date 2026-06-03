import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

describe('apiClient 401 interceptor', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    delete (window as { location?: Window['location'] }).location;
    (window as { location?: Window['location'] }).location = {
      ...originalLocation,
      href: '',
    } as Window['location'];
  });

  afterEach(() => {
    window.location = originalLocation;
    localStorage.clear();
  });

  it('auth login 401 should NOT redirect (page handles error)', async () => {
    const { apiClient } = await import('@/api/client');

    const mock = new MockAdapter(apiClient);
    mock.onPost('/auth/login').reply(401, {
      detail: { code: 'INVALID_CREDENTIALS', message: '用户名或密码错误' },
    });

    try {
      await apiClient.post('/auth/login', { username: 'test', password: 'wrong' });
    } catch (_) {}

    expect(window.location.href).not.toBe('/login');
    mock.restore();
  });

  it('auth register 409 should NOT redirect (page handles error)', async () => {
    const { apiClient } = await import('@/api/client');

    const mock = new MockAdapter(apiClient);
    mock.onPost('/auth/register').reply(409, {
      detail: { code: 'USERNAME_EXISTS', message: '用户名已存在' },
    });

    try {
      await apiClient.post('/auth/register', { username: 'test', password: '123456' });
    } catch (_) {}

    expect(window.location.href).not.toBe('/login');
    mock.restore();
  });

  it('other endpoints 401 should redirect to /login', async () => {
    const { apiClient } = await import('@/api/client');

    const mock = new MockAdapter(apiClient);
    mock.onGet('/invoices').reply(401);

    try {
      await apiClient.get('/invoices');
    } catch (_) {}

    expect(window.location.href).toBe('/login');
    mock.restore();
  });
});