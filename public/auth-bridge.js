/**
 * Mindrian Auth Bridge
 *
 * Connects Supabase Auth to Chainlit by injecting the JWT token
 * into all HTTP requests (Authorization header).
 */
(function() {
  'use strict';

  const TOKEN_KEY = 'supabase_access_token';

  // Get token from localStorage
  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  // Check if token exists
  const token = getToken();

  if (!token) {
    // No token - redirect to login
    if (!window.location.pathname.includes('/public/login')) {
      console.log('[AuthBridge] No token found, redirecting to login');
      window.location.href = '/public/login.html';
    }
    return;
  }

  console.log('[AuthBridge] Token found, injecting into requests');

  // Inject token into fetch requests
  const originalFetch = window.fetch;
  window.fetch = function(url, options = {}) {
    const currentToken = getToken();

    if (currentToken) {
      options.headers = options.headers || {};

      // Handle Headers object
      if (options.headers instanceof Headers) {
        if (!options.headers.has('Authorization')) {
          options.headers.set('Authorization', `Bearer ${currentToken}`);
        }
      } else {
        // Handle plain object
        if (!options.headers['Authorization']) {
          options.headers['Authorization'] = `Bearer ${currentToken}`;
        }
      }
    }

    return originalFetch.call(this, url, options);
  };

  // Handle token refresh (Supabase client in login.html handles this)
  // But we listen for storage changes in case token is updated
  window.addEventListener('storage', (e) => {
    if (e.key === TOKEN_KEY && !e.newValue) {
      // Token was removed - redirect to login
      console.log('[AuthBridge] Token removed, redirecting to login');
      window.location.href = '/public/login.html';
    }
  });

  // Logout function (can be called from anywhere)
  window.mindrianLogout = async function() {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = '/public/login.html';
  };

  console.log('[AuthBridge] Initialized successfully');
})();
