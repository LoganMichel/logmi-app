export const environment = {
  production: false,
  apiUrl: (window as any).__env?.apiUrl || 'http://localhost:8000/api',
  linktreeUrl: (window as any).__env?.linktreeUrl || 'http://localhost:8000',
};
