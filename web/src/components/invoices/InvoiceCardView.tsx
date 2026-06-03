import { InvoiceCard } from './InvoiceCard';
import type { Invoice } from '@/types/invoice';

interface InvoiceCardViewProps {
  invoices: Invoice[];
  onView: (id: number) => void;
  onDelete: (id: number) => void;
}

export function InvoiceCardView({ invoices, onView, onDelete }: InvoiceCardViewProps) {
  if (invoices.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {invoices.map((invoice) => (
        <InvoiceCard
          key={invoice.id}
          invoice={invoice}
          variant="card"
          onView={onView}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}