"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body className="flex min-h-screen flex-col items-center justify-center gap-4 p-4 text-center">
        <h2 className="text-xl font-semibold">Erro crítico</h2>
        <p className="text-sm text-neutral-500">{error.message}</p>
        <button
          type="button"
          onClick={reset}
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm text-white"
        >
          Tentar novamente
        </button>
      </body>
    </html>
  );
}
