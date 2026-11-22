import { apiFetch } from "@/lib/api-client";
import { apiConfig } from "@/lib/config";
import { MOCK_PROGRAMMES } from "@/lib/mock-data";
import type { Programme } from "@/types";

/**
 * Récupère la liste des formations (consultation du catalogue).
 *
 * - API configurée : GET {API_BASE_URL}/api/catalogue/programmes
 * - sinon          : données mockées locales
 */
export async function getProgrammes(): Promise<Programme[]> {
  if (apiConfig.useMock) {
    return MOCK_PROGRAMMES;
  }
  return apiFetch<Programme[]>("/api/catalogue/programmes");
}

/**
 * Récupère une formation par son identifiant d'URL.
 *
 * - API configurée : GET {API_BASE_URL}/api/catalogue/programmes/{slug}
 * - sinon          : données mockées locales
 */
export async function getProgrammeBySlug(
  slug: string,
): Promise<Programme | undefined> {
  if (apiConfig.useMock) {
    return MOCK_PROGRAMMES.find((programme) => programme.slug === slug);
  }
  return apiFetch<Programme>(`/api/catalogue/programmes/${slug}`);
}
