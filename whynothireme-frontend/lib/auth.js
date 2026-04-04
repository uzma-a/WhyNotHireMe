// Token management — localStorage based

export function saveAuth(data) {
  localStorage.setItem("wnhm_token",    data.access_token);
  localStorage.setItem("wnhm_company",  data.company_name);
  localStorage.setItem("wnhm_id",       data.company_id);
  localStorage.setItem("wnhm_api_key",  data.api_key);
}

export function getToken() {
  return localStorage.getItem("wnhm_token");
}

export function getCompanyName() {
  return localStorage.getItem("wnhm_company");
}

export function getApiKey() {
  return localStorage.getItem("wnhm_api_key");
}

export function isLoggedIn() {
  return !!localStorage.getItem("wnhm_token");
}

export function logout() {
  localStorage.removeItem("wnhm_token");
  localStorage.removeItem("wnhm_company");
  localStorage.removeItem("wnhm_id");
  localStorage.removeItem("wnhm_api_key");
}