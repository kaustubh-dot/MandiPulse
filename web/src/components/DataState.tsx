interface LoadingStateProps {
  label: string;
}

export function LoadingState({ label }: LoadingStateProps) {
  return (
    <div
      className="rounded border border-blue-200 bg-blue-50 px-4 py-5 text-sm text-blue-800"
      role="status"
      aria-live="polite"
    >
      {label}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded border border-red-200 bg-red-50 px-4 py-4 text-sm text-red-800" role="alert">
      <p className="font-semibold">Data could not be loaded.</p>
      <p className="mt-1 break-words">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded bg-red-700 px-3 py-1.5 font-medium text-white hover:bg-red-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
      >
        Retry
      </button>
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  detail: string;
}

export function EmptyState({ title, detail }: EmptyStateProps) {
  return (
    <div className="rounded border border-gray-200 bg-white px-4 py-5 text-sm text-gray-600" role="status">
      <p className="font-semibold text-gray-800">{title}</p>
      <p className="mt-1">{detail}</p>
    </div>
  );
}
