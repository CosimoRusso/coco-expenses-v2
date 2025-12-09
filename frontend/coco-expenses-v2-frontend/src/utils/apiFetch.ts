/**
 * apiFetch - A wrapper around the native fetch function that:
 * 1. Adds the 'Content-Type': 'application/json' header to the request
 * 2. Prefixes the URL with '/api/'
 */
export const apiFetch = async (
  url: string,
  options: RequestInit = {},
  omitContentType = false,
): Promise<Response> => {
  // Ensure the URL starts with '/api/'
  const apiUrl = url.startsWith('/') ? url : `/${url}`

  // Merge the provided headers with our Content-Type header
  const headers = {
    ...(omitContentType ? {} : { 'Content-Type': 'application/json' }),
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.headers || {}),
  }
  // Return the fetch call with the modified URL and headers
  return fetch(apiUrl, {
    ...options,
    headers,
  })
}

export default apiFetch
