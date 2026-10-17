import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Store } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by DukaanFlow ErrorBoundary:', error, errorInfo)
  }

  public handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#F7F8FA] flex flex-col justify-center items-center px-4 py-12 text-center">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 border border-amber-200">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-[#17191C]">Something interrupted your session</h1>
          <p className="mt-2 text-sm text-[#737780] max-w-md">
            Don't worry — your khata records and cash calculations are safe on the server.
          </p>
          <div className="mt-6 flex items-center gap-3">
            <button
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-[#16A36A] hover:bg-[#138A5A] rounded-lg transition-colors cursor-pointer"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reload DukaanFlow</span>
            </button>
            <a
              href="/"
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-[#737780] hover:text-[#17191C] bg-white border border-[#D0D5DD] rounded-lg transition-colors"
            >
              <Store className="w-4 h-4" />
              <span>Back to Overview</span>
            </a>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
