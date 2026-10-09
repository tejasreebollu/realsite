// Remember the text search while a drawn area temporarily replaces it.
export function updateSearchFilters(filters, change) {
  const next = { ...filters, ...change };
  if (change.polygon) {
    next.boundary_q = filters.polygon ? (filters.boundary_q ?? '') : filters.q;
    next.q = '';
  } else if (change.q != null && change.q !== filters.q) {
    // An explicit new location starts a fresh search.
    next.polygon = '';
    next.boundary_q = '';
  } else if (change.polygon === '') {
    if (filters.polygon) next.q = filters.boundary_q ?? '';
    next.boundary_q = '';
  }
  return next;
}
