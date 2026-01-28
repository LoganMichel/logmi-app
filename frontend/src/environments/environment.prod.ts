export const environment = {
  production: true,
  apiUrl: (window as any).__env?.apiUrl || '/api',
  linktreeUrl: (window as any).__env?.linktreeUrl || 'http://localhost:8000',
};
