import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatPrice(price?: number, currency = 'CAD'): string {
  if (!price) return 'Prix non disponible';
  
  return new Intl.NumberFormat('fr-CA', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0,
  }).format(price);
}

export function formatArea(area?: number): string | null {
  if (!area) return null;
  return `${area.toFixed(0)} m²`;
}

export function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-CA', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Récemment';
  }
}

export function getPropertyTypeIcon(type?: string): string {
  switch (type?.toLowerCase()) {
    case 'house': return '🏠';
    case 'condo': return '🏢';
    case 'apartment': return '🏠';
    case 'townhouse': return '🏘️';
    default: return '🏠';
  }
}

export function getPropertyTypeLabel(type?: string): string {
  switch (type?.toLowerCase()) {
    case 'house': return 'Maison';
    case 'condo': return 'Condo';
    case 'apartment': return 'Appartement';
    case 'townhouse': return 'Maison de ville';
    default: return type || 'Inconnu';
  }
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}
