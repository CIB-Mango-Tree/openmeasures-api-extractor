export type ExportFormat = 'csv' | 'excel' | 'json';

type SaveResult = {
  status: 'saved' | 'cancelled' | 'error';
  path?: string;
  message?: string;
};

type PyWebView = {
  api?: {
    save_export?: (queryId: string, format: ExportFormat) => Promise<SaveResult>;
  };
};

declare global {
  interface Window {
    pywebview?: PyWebView;
  }
}

/** True inside the desktop app, false when the page is opened in a browser during development. */
export function hasNativeSave(): boolean {
  return typeof window.pywebview?.api?.save_export === 'function';
}

/**
 * Saves an export.
 *
 * In the desktop app this hands off to Python, which generates the file and opens a native save
 * dialog. The webview has no download manager, so a plain link to the download endpoint just
 * renders the file in the window instead of saving it.
 *
 * In a browser the same endpoint responds with Content-Disposition: attachment, so a link works.
 */
export async function saveExport(queryId: string, format: ExportFormat): Promise<SaveResult> {
  const save = window.pywebview?.api?.save_export;

  if (save == null) {
    const link: HTMLAnchorElement = document.createElement('a');

    link.href = `/api/queries/${queryId}/download/${format}`;
    link.download = '';

    document.body.appendChild(link);
    link.click();
    link.remove();

    return { status: 'saved' };
  }

  return await save(queryId, format);
}
