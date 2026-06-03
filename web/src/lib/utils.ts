import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function getDaysLeft(deletedAt: string): number {
  const deleted = new Date(deletedAt);
  const expiry = new Date(deleted.getTime() + 30 * 24 * 60 * 60 * 1000);
  const now = new Date();
  return Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

export function getInvoiceTypeIcon(type: string | null): string {
  const icons: Record<string, string> = {
    '增值税': 'Receipt',
    '高铁': 'Train',
    '滴滴': 'Car',
    '飞机': 'Plane',
  };
  return icons[type || ''] || 'FileText';
}

export function getInvoiceTypeColor(type: string | null): string {
  const colors: Record<string, string> = {
    '增值税': 'text-red-600',
    '高铁': 'text-blue-600',
    '滴滴': 'text-green-600',
    '飞机': 'text-purple-600',
  };
  return colors[type || ''] || 'text-gray-500';
}

export function splitAmountToDigits(amount: number): (string | null)[] {
  const totalFen = Math.round(amount * 100);
  const yuan = Math.floor(totalFen / 100);
  const jiao = Math.floor((totalFen % 100) / 10);
  const fen = totalFen % 10;

  const digits: (string | null)[] = [
    yuan >= 1000000 ? String(Math.floor(yuan / 1000000) % 10) : null,
    yuan >= 100000 ? String(Math.floor(yuan / 100000) % 10) : null,
    yuan >= 10000 ? String(Math.floor(yuan / 10000) % 10) : null,
    yuan >= 1000 ? String(Math.floor(yuan / 1000) % 10) : null,
    yuan >= 100 ? String(Math.floor(yuan / 100) % 10) : null,
    yuan >= 10 ? String(Math.floor(yuan / 10) % 10) : null,
    String(yuan % 10),
    String(jiao),
    String(fen),
  ];

  return digits;
}

export function amountToChinese(amount: number): string {
  const digitsCn = '零壹贰叁肆伍陆柒捌玖';
  const unitsInt = ['', '拾', '佰', '仟'];
  const unitsSection = ['', '万', '亿'];

  const totalFen = Math.round(amount * 100);
  const yuan = Math.floor(totalFen / 100);
  const jiao = Math.floor((totalFen % 100) / 10);
  const fen = totalFen % 10;

  if (yuan === 0 && jiao === 0 && fen === 0) {
    return '零元整';
  }

  const _convertSection = (n: number): string => {
    if (n === 0) return '';
    let result = '';
    let zero = false;
    const positions = [
      Math.floor(n / 1000) % 10,
      Math.floor(n / 100) % 10,
      Math.floor(n / 10) % 10,
      n % 10,
    ];
    for (let i = 0; i < 4; i++) {
      const d = positions[i];
      if (d === 0) {
        zero = true;
      } else {
        if (zero) {
          result += '零';
          zero = false;
        }
        result += digitsCn[d] + unitsInt[3 - i];
      }
    }
    return result;
  };

  let n = yuan;
  let intPart = '';
  let sectionIdx = 0;
  let lowerSectionVal = 0;
  while (n > 0) {
    const section = n % 10000;
    n = Math.floor(n / 10000);
    if (section > 0) {
      let sectionStr = _convertSection(section);
      if (sectionIdx > 0) {
        if (section < 1000 && lowerSectionVal < 1000) {
          intPart = '零' + intPart;
        }
        sectionStr += unitsSection[sectionIdx];
      }
      intPart = sectionStr + intPart;
    }
    lowerSectionVal = section;
    sectionIdx++;
  }
  if (!intPart) intPart = '零';

  let decimalPart = '';
  if (jiao === 0 && fen === 0) {
    decimalPart = '整';
  } else {
    if (jiao > 0) {
      decimalPart += digitsCn[jiao] + '角';
    }
    if (fen > 0) {
      decimalPart += digitsCn[fen] + '分';
    }
  }

  return intPart + '元' + decimalPart;
}