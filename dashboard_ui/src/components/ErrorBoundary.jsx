import React from 'react';

export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error', error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 p-8 text-center">
          <div className="max-w-2xl w-full bg-surface-base border border-red-500/20 rounded-xl p-8 shadow-lg">
            <h1 className="text-2xl font-bold text-red-500 mb-4">Something went wrong</h1>
            <p className="text-text-secondary mb-6">An unexpected error occurred while rendering this page.</p>
            <div className="text-left bg-slate-900 rounded p-4 overflow-x-auto">
              <pre className="text-sm text-red-400">{this.state.error?.toString()}</pre>
              <pre className="text-xs text-text-muted mt-4">{this.state.errorInfo?.componentStack}</pre>
            </div>
            <button 
              onClick={() => window.location.reload()}
              className="mt-8 px-6 py-2 bg-brand-primary text-white rounded-lg hover:bg-brand-primary-dark transition-colors"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
