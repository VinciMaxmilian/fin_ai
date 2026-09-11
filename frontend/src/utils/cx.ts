/** Junta class names, ignorando falsos. Evita uma dependência só para isso. */
export function cx(...values: Array<string | false | null | undefined>): string {
  return values.filter(Boolean).join(' ')
}
