export const getApiUrl = (path: string) => {
  // If VITE_API_URL is defined in Vercel or your local .env, use it.
  // Otherwise, default to an empty string (meaning relative path).
  const baseUrl = import.meta.env.VITE_LOCAL_API_URL || "";
  console.log('calling API: ', `${baseUrl}${path}`)
  return `${baseUrl}${path}`;
};