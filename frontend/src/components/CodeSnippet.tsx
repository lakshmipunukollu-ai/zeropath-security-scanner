import React from 'react';

interface Props {
  code: string;
  filePath?: string;
  lineNumber?: number;
}

export default function CodeSnippet({ code, filePath, lineNumber }: Props) {
  return (
    <div className="code-snippet">
      {filePath && (
        <div className="code-header">
          <span className="code-filepath">{filePath}</span>
          {lineNumber !== undefined && lineNumber > 0 && (
            <span className="code-line">Line {lineNumber}</span>
          )}
        </div>
      )}
      <pre className="code-block">
        <code>{code}</code>
      </pre>
    </div>
  );
}
