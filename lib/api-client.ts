import { apiConfig } from "@/lib/config";

/** Erreur remontée par la couche API. */
export class ApiError extends Error {
  status: number;
  body?: unknown;

  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

/** Construit une URL absolue à partir de NEXT_PUBLIC_API_BASE_URL. */
export function buildApiUrl(path: string): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${apiConfig.baseUrl.replace(/\/+$/, "")}${normalized}`;
}

/**
 * Appel HTTP générique vers le backend.
 * À n'utiliser que lorsque l'API est configurée (voir apiConfig.useMock) :
 * en mode mock, les services retournent directement les données locales.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    throw new ApiError(
      `Requête API échouée (${response.status})`,
      response.status,
      body,
    );
  }

  return (await response.json()) as T;
}
