function activeRowClass(isActive: boolean): string {
  return isActive ? 'bg-success/10' : 'bg-base-200 text-base-content/50'
}

function activeBorderClass(isActive: boolean): string {
  return isActive ? 'border-l-success' : 'border-l-base-300'
}

function activeBadgeClass(isActive: boolean): string {
  return isActive ? 'badge-success' : 'badge-neutral'
}

function activeLabel(isActive: boolean): string {
  return isActive ? 'Active' : 'Inactive'
}

export { activeRowClass, activeBorderClass, activeBadgeClass, activeLabel }
