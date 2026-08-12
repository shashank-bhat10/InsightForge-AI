import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './App.css'

const API_URL = 'https://insightforge-backend-6ldc.onrender.com'

type User = {
  id: number
  full_name: string
  email: string
}

type Dataset = {
  id: number
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  file_path: string
  user_id: number
  created_at: string
}

type Summary = {
  rows: number
  columns: number
  column_names: string[]
  data_types: Record<string, string>
  missing_values: Record<string, number>
}

type Statistics = {
  rows: number
  columns: number
  numeric_columns: Record<
    string,
    {
      count: number
      mean: number
      median: number
      min: number
      max: number
      std: number
    }
  >
}

type GroupedRecord = {
  category: string
  count: number
  average: number
  total: number
}

type GroupedAnalysis = Record<string, GroupedRecord[]>

type AdvancedAnalytics = {
  numeric_distributions: Record<string, {
    count: number
    mean: number | null
    median: number | null
    min: number | null
    max: number | null
    q1: number | null
    q3: number | null
    skewness: number | null
  }>
  correlations: {
    column_a: string
    column_b: string
    correlation: number
    absolute_correlation: number
  }[]
  strongest_correlations: {
    column_a: string
    column_b: string
    correlation: number
    absolute_correlation: number
  }[]
  categorical_distributions: Record<string, {
    category: string
    count: number
    percentage: number
  }[]>
}

type QualityReport = {
  quality_score: number
  quality_level: string
  rows: number
  columns: number
  total_missing_values: number
  duplicate_rows: number
  duplicate_percentage: number
  constant_columns: string[]
  column_details: Record<string, {
    data_type: string
    unique_values: number
    missing_values: number
    missing_percentage: number
    is_constant: boolean
  }>
  missing_values: Record<string, {
    count: number
    percentage: number
  }>
  categorical_inconsistencies: Record<string, {
    normalized_value: string
    variants: string[]
  }[]>
  outliers: Record<string, {
    count: number
    percentage: number
    lower_bound: number
    upper_bound: number
  }>
  recommendations: string[]
}

type Conversation = {
  id: number
  user_id: number
  title: string
  created_at: string
}

type ChatMessage = {
  id?: number
  prompt: string
  response: string
  created_at?: string
}

type Page =
  | 'overview'
  | 'datasets'
  | 'analytics'
  | 'ml'
  | 'forecast'
  | 'ai'
  | 'conversations'

function App() {
  const [token, setToken] = useState(
    localStorage.getItem('access_token') || ''
  )

  const [user, setUser] = useState<User | null>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  const [page, setPage] = useState<Page>('overview')

  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(
    null
  )

  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const [preview, setPreview] = useState<Record<string, unknown>[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [insights, setInsights] = useState<string[]>([])

  const [groupedAnalysis, setGroupedAnalysis] =
    useState<GroupedAnalysis>({})
  const [qualityReport, setQualityReport] = useState<QualityReport | null>(null)
  const [advancedAnalytics, setAdvancedAnalytics] =
    useState<AdvancedAnalytics | null>(null)
  const [chartMetric, setChartMetric] = useState<'total' | 'average'>('total')

  const [mlTarget, setMlTarget] = useState('')
  const [mlProblemType, setMlProblemType] = useState<'auto' | 'classification' | 'regression'>('auto')
  const [mlResult, setMlResult] = useState<any | null>(null)
  const [mlLoading, setMlLoading] = useState(false)
  const [mlError, setMlError] = useState('')

  const [forecastDateColumn, setForecastDateColumn] = useState('')
  const [forecastTargetColumn, setForecastTargetColumn] = useState('')
  const [forecastPeriods, setForecastPeriods] = useState(12)
  const [forecastFrequency, setForecastFrequency] = useState('auto')
  const [forecastResult, setForecastResult] = useState<any | null>(null)
  const [forecastLoading, setForecastLoading] = useState(false)
  const [forecastError, setForecastError] = useState('')
  const [forecastColumns, setForecastColumns] = useState<{
    date_columns: string[]
    numeric_columns: string[]
  }>({ date_columns: [], numeric_columns: [] })

  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [analyticsError, setAnalyticsError] = useState('')

  const [prompt, setPrompt] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null)

  const [conversationMessages, setConversationMessages] = useState<
    ChatMessage[]
  >([])

  const [editingConversation, setEditingConversation] = useState<
    number | null
  >(null)

  const [editingTitle, setEditingTitle] = useState('')

  const authHeaders = {
    Authorization: `Bearer ${token}`,
  }

  useEffect(() => {
    if (!token) {
      return
    }

    loadCurrentUser()
  }, [token])

  useEffect(() => {
    if (user) {
      loadDatasets()
      loadConversations()
    }
  }, [user])

  const loadCurrentUser = async () => {
    try {
      const response = await fetch(`${API_URL}/me`, {
        headers: authHeaders,
      })

      if (!response.ok) {
        localStorage.removeItem('access_token')
        setToken('')
        setUser(null)
        return
      }

      const data = await response.json()
      setUser(data)
    } catch {
      localStorage.removeItem('access_token')
      setToken('')
      setUser(null)
    }
  }

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    setLoginError('')
    setLoginLoading(true)

    try {
      const formData = new URLSearchParams()

      formData.append('username', email)
      formData.append('password', password)

      const response = await fetch(`${API_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Invalid email or password')
      }

      localStorage.setItem('access_token', data.access_token)
      setToken(data.access_token)
      setPassword('')
    } catch (error) {
      if (error instanceof TypeError) {
        setLoginError(
          'Unable to connect to the backend. Make sure FastAPI is running.'
        )
      } else {
        setLoginError(
          error instanceof Error ? error.message : 'Login failed'
        )
      }
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')

    setToken('')
    setUser(null)

    setDatasets([])
    setSelectedDataset(null)
    setConversations([])
    setSelectedConversation(null)
    setChatMessages([])
  }

  const loadDatasets = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/datasets/`, {
        headers: authHeaders,
      })

      if (!response.ok) {
        return
      }

      const data = await response.json()
      setDatasets(data)
    } catch {
      setDatasets([])
    }
  }

  const uploadDataset = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setUploading(true)
    setUploadError('')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API_URL}/api/v1/datasets/`, {
        method: 'POST',
        headers: authHeaders,
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Dataset upload failed')
      }

      setDatasets((current) => [data, ...current])
      setSelectedDataset(data)
      setPage('analytics')
      await loadAnalytics(data.id)
    } catch (error) {
      setUploadError(
        error instanceof Error
          ? error.message
          : 'Dataset upload failed'
      )
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const deleteDataset = async (datasetId: number) => {
    const confirmed = window.confirm(
      'Are you sure you want to delete this dataset?'
    )

    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(
        `${API_URL}/api/v1/datasets/${datasetId}`,
        {
          method: 'DELETE',
          headers: authHeaders,
        }
      )

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Unable to delete dataset')
      }

      setDatasets((current) =>
        current.filter((dataset) => dataset.id !== datasetId)
      )

      if (selectedDataset?.id === datasetId) {
        setSelectedDataset(null)
        setPreview([])
        setSummary(null)
        setStatistics(null)
        setInsights([])
        setGroupedAnalysis({})
        setQualityReport(null)
        setAdvancedAnalytics(null)
        setMlTarget('')
        setMlResult(null)
        setMlError('')
        setForecastDateColumn('')
        setForecastTargetColumn('')
        setForecastResult(null)
        setForecastError('')
        setForecastColumns({ date_columns: [], numeric_columns: [] })
      }
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : 'Unable to delete dataset'
      )
    }
  }

  const loadAnalytics = async (datasetId: number) => {
    setAnalyticsLoading(true)
    setAnalyticsError('')

    try {
      const headers = authHeaders

      const [
        previewResponse,
        summaryResponse,
        statisticsResponse,
        insightsResponse,
        groupedAnalysisResponse,
        qualityResponse,
        advancedAnalyticsResponse,
      ] = await Promise.all([
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/preview`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/summary`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/statistics`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/insights`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/grouped-analysis`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/quality`,
          { headers }
        ),
        fetch(
          `${API_URL}/api/v1/analytics/${datasetId}/advanced`,
          { headers }
        ),
      ])

      if (
        !previewResponse.ok ||
        !summaryResponse.ok ||
        !statisticsResponse.ok ||
        !insightsResponse.ok ||
        !groupedAnalysisResponse.ok ||
        !qualityResponse.ok ||
        !advancedAnalyticsResponse.ok
      ) {
        throw new Error('Unable to load dataset analytics')
      }

      const previewData = await previewResponse.json()
      const summaryData = await summaryResponse.json()
      const statisticsData = await statisticsResponse.json()
      const insightsData = await insightsResponse.json()
      const groupedAnalysisData = await groupedAnalysisResponse.json()
      const qualityData = await qualityResponse.json()
      const advancedAnalyticsData =
        await advancedAnalyticsResponse.json()

      setPreview(previewData)
      setSummary(summaryData)
      setStatistics(statisticsData)
      setInsights(insightsData.insights || [])
      setGroupedAnalysis(groupedAnalysisData || {})
      setQualityReport(qualityData)
      setAdvancedAnalytics(advancedAnalyticsData)
    } catch (error) {
      setAnalyticsError(
        error instanceof Error
          ? error.message
          : 'Unable to load analytics'
      )
    } finally {
      setAnalyticsLoading(false)
    }
  }

  const selectDataset = async (dataset: Dataset) => {
    setSelectedDataset(dataset)
    setChatMessages([])
    setChatError('')
    setPrompt('')
    setPage('analytics')
    await loadAnalytics(dataset.id)
  }

  const loadForecastColumns = async (datasetId: number) => {
    setForecastError('')

    try {
      const response = await fetch(
        `${API_URL}/api/v1/forecast/${datasetId}/columns`,
        { headers: authHeaders }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to detect forecast columns')
      }

      setForecastColumns(data)

      if (data.date_columns?.length > 0) {
        setForecastDateColumn(data.date_columns[0])
      } else {
        setForecastDateColumn('')
      }

      if (data.numeric_columns?.length > 0) {
        setForecastTargetColumn(data.numeric_columns[0])
      } else {
        setForecastTargetColumn('')
      }
    } catch (error) {
      setForecastColumns({ date_columns: [], numeric_columns: [] })
      setForecastError(
        error instanceof Error
          ? error.message
          : 'Unable to detect forecast columns'
      )
    }
  }

  const generateForecast = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!selectedDataset || !forecastDateColumn || !forecastTargetColumn) {
      return
    }

    setForecastLoading(true)
    setForecastError('')
    setForecastResult(null)

    try {
      const response = await fetch(
        `${API_URL}/api/v1/forecast/${selectedDataset.id}/predict`,
        {
          method: 'POST',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            date_column: forecastDateColumn,
            target_column: forecastTargetColumn,
            periods: forecastPeriods,
            frequency: forecastFrequency,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Forecast generation failed')
      }

      setForecastResult(data)
    } catch (error) {
      setForecastError(
        error instanceof Error
          ? error.message
          : 'Forecast generation failed'
      )
    } finally {
      setForecastLoading(false)
    }
  }

  const sendChat = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!prompt.trim()) {
      return
    }

    if (!selectedDataset) {
      setChatError('Select a dataset before asking a data question.')
      return
    }

    const currentPrompt = prompt.trim()

    setPrompt('')
    setChatError('')
    setChatLoading(true)

    try {
      const response = await fetch(`${API_URL}/api/v1/ai/chat`, {
        method: 'POST',
        headers: {
          ...authHeaders,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: currentPrompt,
          dataset_id: selectedDataset.id,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'AI request failed')
      }

      const message: ChatMessage = {
        prompt: currentPrompt,
        response: data.response,
      }

      setChatMessages((current) => [...current, message])

      await loadConversations()
    } catch (error) {
      setChatError(
        error instanceof Error
          ? error.message
          : 'AI request failed'
      )
    } finally {
      setChatLoading(false)
    }
  }

  const trainModels = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!selectedDataset) {
      setMlError('Select a dataset before training a model.')
      return
    }

    if (!mlTarget.trim()) {
      setMlError('Select a target column.')
      return
    }

    setMlLoading(true)
    setMlError('')
    setMlResult(null)

    try {
      const response = await fetch(
        `${API_URL}/api/v1/ml/${selectedDataset.id}/train`,
        {
          method: 'POST',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            target_column: mlTarget.trim(),
            problem_type: mlProblemType,
          }),
        }
      )

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || 'Model training failed')
      }

      setMlResult(data)
    } catch (error) {
      setMlError(
        error instanceof Error ? error.message : 'Model training failed'
      )
    } finally {
      setMlLoading(false)
    }
  }

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_URL}/api/v1/conversations/`, {
        headers: authHeaders,
      })

      if (!response.ok) {
        return
      }

      const data = await response.json()
      setConversations(data)
    } catch {
      setConversations([])
    }
  }

  const loadConversationHistory = async (
    conversation: Conversation
  ) => {
    setSelectedConversation(conversation)
    setPage('conversations')

    try {
      const response = await fetch(
        `${API_URL}/api/v1/ai/history/${conversation.id}?skip=0&limit=100`,
        {
          headers: authHeaders,
        }
      )

      if (!response.ok) {
        throw new Error('Unable to load conversation history')
      }

      const data = await response.json()

      setConversationMessages(data)
    } catch {
      setConversationMessages([])
    }
  }

  const renameConversation = async (conversationId: number) => {
    if (!editingTitle.trim()) {
      return
    }

    try {
      const response = await fetch(
        `${API_URL}/api/v1/conversations/${conversationId}`,
        {
          method: 'PUT',
          headers: {
            ...authHeaders,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            title: editingTitle.trim(),
          }),
        }
      )

      if (!response.ok) {
        throw new Error('Unable to rename conversation')
      }

      const updated = await response.json()

      setConversations((current) =>
        current.map((conversation) =>
          conversation.id === conversationId
            ? updated
            : conversation
        )
      )

      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(updated)
      }

      setEditingConversation(null)
      setEditingTitle('')
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : 'Unable to rename conversation'
      )
    }
  }

  const deleteConversation = async (conversationId: number) => {
    const confirmed = window.confirm(
      'Are you sure you want to delete this conversation?'
    )

    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(
        `${API_URL}/api/v1/conversations/${conversationId}`,
        {
          method: 'DELETE',
          headers: authHeaders,
        }
      )

      if (!response.ok) {
        throw new Error('Unable to delete conversation')
      }

      setConversations((current) =>
        current.filter(
          (conversation) => conversation.id !== conversationId
        )
      )

      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null)
        setConversationMessages([])
      }
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : 'Unable to delete conversation'
      )
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) {
      return `${bytes} B`
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString()
  }

  const formatAIResponse = (response: string): ReactNode => {
    const lines = response.split(/\r?\n/)

    const renderInline = (text: string) => {
      const parts = text.split(/(\*\*.*?\*\*)/g)

      return parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={index}>
              {part.slice(2, -2)}
            </strong>
          )
        }

        return <span key={index}>{part}</span>
      })
    }

    return lines.map((line, index) => {
      const trimmed = line.trim()

      if (!trimmed) {
        return <div key={index} style={{ height: 8 }} />
      }

      const headingMatch = trimmed.match(/^#{1,3}\s+(.*)$/)
      if (headingMatch) {
        return (
          <div
            key={index}
            style={{
              fontWeight: 700,
              fontSize: 15,
              margin: '10px 0 6px',
            }}
          >
            {renderInline(headingMatch[1])}
          </div>
        )
      }

      const numberedMatch = trimmed.match(/^(\d+)\.\s+(.*)$/)
      if (numberedMatch) {
        return (
          <div
            key={index}
            style={{
              display: 'flex',
              gap: 8,
              margin: '5px 0',
              lineHeight: 1.6,
            }}
          >
            <strong>{numberedMatch[1]}.</strong>
            <span>{renderInline(numberedMatch[2])}</span>
          </div>
        )
      }

      const bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/)
      if (bulletMatch) {
        return (
          <div
            key={index}
            style={{
              display: 'flex',
              gap: 8,
              margin: '5px 0',
              lineHeight: 1.6,
            }}
          >
            <span>•</span>
            <span>{renderInline(bulletMatch[1])}</span>
          </div>
        )
      }

      return (
        <div
          key={index}
          style={{
            margin: '4px 0',
            lineHeight: 1.65,
          }}
        >
          {renderInline(trimmed)}
        </div>
      )
    })
  }

  const salesChartEntries = Object.entries(groupedAnalysis)
    .filter(([key, records]) => key.endsWith('_by_Sales') && records.length > 0)
    .sort(([keyA], [keyB]) => {
      const priority = (key: string) => {
        if (key.startsWith('Item Type_')) return 0
        if (key.startsWith('Outlet Location Type_')) return 1
        if (key.startsWith('Outlet Type_')) return 2
        return 3
      }

      return priority(keyA) - priority(keyB)
    })
    .slice(0, 2)

  const formatChartTitle = (key: string) => {
    const category = key.replace(/_by_Sales$/, '')
    return `${category} by Sales`
  }

  const exportAnalyticsReport = () => {
    if (!selectedDataset || !summary) {
      window.alert('Select a dataset and wait for its analytics to load before exporting.')
      return
    }

    const escapeHtml = (value: unknown) =>
      String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')

    const numericRows = statistics
      ? Object.entries(statistics.numeric_columns)
          .map(
            ([column, stats]) => `
              <tr>
                <td>${escapeHtml(column)}</td>
                <td>${stats.count}</td>
                <td>${stats.mean.toFixed(2)}</td>
                <td>${stats.median}</td>
                <td>${stats.min}</td>
                <td>${stats.max}</td>
                <td>${stats.std.toFixed(2)}</td>
              </tr>
            `
          )
          .join('')
      : ''

    const qualityRecommendations = qualityReport
      ? qualityReport.recommendations
          .map((item) => `<li>${escapeHtml(item)}</li>`)
          .join('')
      : '<li>No quality recommendations available.</li>'

    const correlationRows = advancedAnalytics
      ? advancedAnalytics.strongest_correlations
          .slice(0, 10)
          .map(
            (item) => `
              <tr>
                <td>${escapeHtml(item.column_a)}</td>
                <td>${escapeHtml(item.column_b)}</td>
                <td>${item.correlation.toFixed(3)}</td>
              </tr>
            `
          )
          .join('')
      : ''

    const insightRows = insights
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join('')

    const missingRows = Object.entries(summary.missing_values)
      .filter(([, count]) => count > 0)
      .map(
        ([column, count]) =>
          `<tr><td>${escapeHtml(column)}</td><td>${count}</td></tr>`
      )
      .join('')

    const reportHtml = `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>InsightForge AI Report - ${escapeHtml(selectedDataset.original_filename)}</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px;
      color: #202124;
      line-height: 1.5;
    }
    h1 { margin-bottom: 4px; }
    h2 { margin-top: 32px; border-bottom: 1px solid #ddd; padding-bottom: 8px; }
    .muted { color: #666; }
    .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin: 20px 0; }
    .card { border: 1px solid #ddd; border-radius: 10px; padding: 16px; }
    .card strong { display: block; font-size: 22px; margin-top: 4px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; }
    th, td { border: 1px solid #ddd; padding: 8px 10px; text-align: left; }
    th { background: #f5f5f5; }
    li { margin: 6px 0; }
    .quality { font-size: 20px; font-weight: 700; }
    @media print {
      body { padding: 20px; }
      .no-print { display: none; }
      .card { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <p class="muted">INSIGHTFORGE AI · ANALYTICS REPORT</p>
  <h1>${escapeHtml(selectedDataset.original_filename)}</h1>
  <p class="muted">Dataset #${selectedDataset.id} · Generated ${escapeHtml(new Date().toLocaleString())}</p>

  <div class="cards">
    <div class="card">Rows<strong>${summary.rows}</strong></div>
    <div class="card">Columns<strong>${summary.columns}</strong></div>
    <div class="card">Missing values<strong>${Object.values(summary.missing_values).reduce((a, b) => a + b, 0)}</strong></div>
    <div class="card">Data quality<strong>${qualityReport ? `${qualityReport.quality_score.toFixed(2)}%` : 'N/A'}</strong></div>
  </div>

  <h2>AI-Generated Insights</h2>
  <ul>${insightRows || '<li>No insights available.</li>'}</ul>

  <h2>Data Quality</h2>
  ${
    qualityReport
      ? `<p class="quality">${escapeHtml(qualityReport.quality_level)} · ${qualityReport.quality_score.toFixed(2)}%</p>
         <p>Duplicate rows: ${qualityReport.duplicate_rows} (${qualityReport.duplicate_percentage}%)</p>
         <h3>Recommendations</h3>
         <ul>${qualityRecommendations}</ul>`
      : '<p>Quality analysis was not available.</p>'
  }

  <h2>Missing Values</h2>
  ${
    missingRows
      ? `<table><thead><tr><th>Column</th><th>Missing values</th></tr></thead><tbody>${missingRows}</tbody></table>`
      : '<p>No missing values detected.</p>'
  }

  <h2>Numeric Statistics</h2>
  ${
    numericRows
      ? `<table>
          <thead><tr><th>Column</th><th>Count</th><th>Mean</th><th>Median</th><th>Minimum</th><th>Maximum</th><th>Std Dev</th></tr></thead>
          <tbody>${numericRows}</tbody>
        </table>`
      : '<p>No numeric statistics available.</p>'
  }

  <h2>Advanced Analytics</h2>
  ${
    correlationRows
      ? `<table>
          <thead><tr><th>Column A</th><th>Column B</th><th>Correlation</th></tr></thead>
          <tbody>${correlationRows}</tbody>
        </table>`
      : '<p>No correlation analysis available.</p>'
  }

  <p class="muted" style="margin-top:40px">
    Generated by InsightForge AI. Open this file in a browser and use Print → Save as PDF if a PDF copy is required.
  </p>
</body>
</html>`

    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `InsightForge_Report_${selectedDataset.id}.html`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  if (!user) {
    return (
      <div className="app">
        <div className="background-glow background-glow-one"></div>
        <div className="background-glow background-glow-two"></div>

        <main className="login-page">
          <section className="brand-section">
            <div className="brand-mark">IF</div>

            <h1>InsightForge AI</h1>

            <p className="brand-tagline">
              Turn your data into insights.
            </p>

            <p className="brand-description">
              Upload datasets, explore analytics, and ask AI-powered
              questions about your data — all in one place.
            </p>

            <div className="feature-list">
              <div className="feature-item">
                <span className="feature-icon">◈</span>
                <div>
                  <strong>Smart Analytics</strong>
                  <span>Understand your datasets instantly.</span>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">✦</span>
                <div>
                  <strong>AI Data Assistant</strong>
                  <span>Ask questions and get meaningful answers.</span>
                </div>
              </div>

              <div className="feature-item">
                <span className="feature-icon">↗</span>
                <div>
                  <strong>Actionable Insights</strong>
                  <span>Discover patterns hidden in your data.</span>
                </div>
              </div>
            </div>
          </section>

          <section className="login-card">
            <div className="login-header">
              <span className="welcome-label">WELCOME BACK</span>

              <h2>Sign in to InsightForge</h2>

              <p>
                Access your datasets, analytics, and AI conversations.
              </p>
            </div>

            <form
              className="login-form"
              onSubmit={handleLogin}
            >
              <div className="form-group">
                <label htmlFor="email">Email address</label>

                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) =>
                    setEmail(event.target.value)
                  }
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="password">Password</label>

                <input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  required
                />
              </div>

              {loginError && (
                <div className="login-error">
                  {loginError}
                </div>
              )}

              <button
                type="submit"
                className="login-button"
                disabled={loginLoading}
              >
                {loginLoading ? 'Signing in...' : 'Sign in'}

                {!loginLoading && <span>→</span>}
              </button>
            </form>

            <p className="signup-text">
              InsightForge AI · Intelligent analytics powered by AI
            </p>
          </section>
        </main>
      </div>
    )
  }

  return (
    <div className="dashboard-app">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-logo">IF</div>

          <div>
            <strong>InsightForge</strong>
            <span>AI Analytics</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={page === 'overview' ? 'active' : ''}
            onClick={() => setPage('overview')}
          >
            <span>⌂</span>
            Dashboard
          </button>

          <button
            className={page === 'datasets' ? 'active' : ''}
            onClick={() => setPage('datasets')}
          >
            <span>▣</span>
            Datasets
          </button>

          <button
            className={page === 'analytics' ? 'active' : ''}
            onClick={() => setPage('analytics')}
          >
            <span>▥</span>
            Analytics
          </button>

          <button
            className={page === 'ml' ? 'active' : ''}
            onClick={() => setPage('ml')}
          >
            <span>⌁</span>
            AutoML
          </button>

          <button
            className={page === 'forecast' ? 'active' : ''}
            onClick={() => {
              setPage('forecast')
              if (selectedDataset) {
                loadForecastColumns(selectedDataset.id)
              }
            }}
          >
            <span>↗</span>
            Forecasting
          </button>

          <button
            className={page === 'ai' ? 'active' : ''}
            onClick={() => setPage('ai')}
          >
            <span>✦</span>
            AI Assistant
          </button>

          <button
            className={page === 'conversations' ? 'active' : ''}
            onClick={() => setPage('conversations')}
          >
            <span>◌</span>
            Conversations
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="user-mini">
            <div className="avatar">
              {user.full_name.charAt(0).toUpperCase()}
            </div>

            <div>
              <strong>{user.full_name}</strong>
              <span>{user.email}</span>
            </div>
          </div>

          <button
            className="logout-sidebar"
            onClick={handleLogout}
          >
            ↪ Sign out
          </button>
        </div>
      </aside>

      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <span className="header-label">
              INSIGHTFORGE AI
            </span>

            <h1>
              {page === 'overview' && 'Dashboard'}
              {page === 'datasets' && 'Your Datasets'}
              {page === 'analytics' && 'Analytics'}
              {page === 'ml' && 'AutoML / ML Models'}
              {page === 'forecast' && 'Forecasting'}
              {page === 'ai' && 'AI Data Assistant'}
              {page === 'conversations' && 'Conversations'}
            </h1>
          </div>

          <div className="header-user">
            <div className="header-avatar">
              {user.full_name.charAt(0).toUpperCase()}
            </div>

            <div>
              <strong>{user.full_name}</strong>
              <span>Data Analyst</span>
            </div>
          </div>
        </header>

        {page === 'overview' && (
          <section className="content">
            <div className="hero-card">
              <div>
                <span className="hero-label">
                  WELCOME BACK
                </span>

                <h2>
                  Turn your data into
                  <span> meaningful insights.</span>
                </h2>

                <p>
                  Upload a dataset, explore its analytics, and
                  ask InsightForge AI questions about your data.
                </p>

                <button
                  className="primary-button"
                  onClick={() => setPage('datasets')}
                >
                  Explore datasets →
                </button>
              </div>

              <div className="hero-icon">✦</div>
            </div>

            <div className="stat-grid">
              <div className="stat-card">
                <span className="stat-icon">▣</span>
                <div>
                  <span>Datasets</span>
                  <strong>{datasets.length}</strong>
                </div>
              </div>

              <div className="stat-card">
                <span className="stat-icon">▥</span>
                <div>
                  <span>Selected dataset</span>
                  <strong>
                    {selectedDataset ? selectedDataset.id : '—'}
                  </strong>
                </div>
              </div>

              <div className="stat-card">
                <span className="stat-icon">◌</span>
                <div>
                  <span>Conversations</span>
                  <strong>{conversations.length}</strong>
                </div>
              </div>

              <div className="stat-card">
                <span className="stat-icon">✦</span>
                <div>
                  <span>AI Assistant</span>
                  <strong>Ready</strong>
                </div>
              </div>
            </div>

            <div className="section-card">
              <div className="section-heading">
                <div>
                  <span className="section-kicker">
                    RECENT DATA
                  </span>
                  <h2>Datasets</h2>
                </div>

                <button
                  className="text-button"
                  onClick={() => setPage('datasets')}
                >
                  View all →
                </button>
              </div>

              {datasets.length === 0 ? (
                <div className="empty-state">
                  <div>▣</div>
                  <h3>No datasets yet</h3>
                  <p>
                    Upload your first CSV or Excel dataset to
                    get started.
                  </p>
                </div>
              ) : (
                <div className="dataset-list">
                  {datasets.slice(0, 4).map((dataset) => (
                    <div
                      className="dataset-row"
                      key={dataset.id}
                    >
                      <div className="file-icon">
                        {dataset.file_type
                          .replace('.', '')
                          .toUpperCase()}
                      </div>

                      <div className="dataset-info">
                        <strong>
                          {dataset.original_filename}
                        </strong>

                        <span>
                          Dataset #{dataset.id} ·{' '}
                          {formatFileSize(dataset.file_size)}
                        </span>
                      </div>

                      <button
                        className="small-button"
                        onClick={() =>
                          selectDataset(dataset)
                        }
                      >
                        Open
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {page === 'datasets' && (
          <section className="content">
            <div className="upload-card">
              <div className="upload-icon">↑</div>

              <div>
                <h2>Upload a dataset</h2>
                <p>
                  CSV and Excel files are supported.
                </p>
              </div>

              <label className="upload-button">
                {uploading ? 'Uploading...' : 'Choose file'}
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={uploadDataset}
                  disabled={uploading}
                  hidden
                />
              </label>
            </div>

            {uploadError && (
              <div className="page-error">
                {uploadError}
              </div>
            )}

            <div className="section-card">
              <div className="section-heading">
                <div>
                  <span className="section-kicker">
                    DATA LIBRARY
                  </span>
                  <h2>Your datasets</h2>
                </div>

                <span className="count-badge">
                  {datasets.length}
                </span>
              </div>

              {datasets.length === 0 ? (
                <div className="empty-state">
                  <div>▣</div>
                  <h3>Your dataset library is empty</h3>
                  <p>
                    Upload a dataset to begin analyzing your
                    data.
                  </p>
                </div>
              ) : (
                <div className="dataset-grid">
                  {datasets.map((dataset) => (
                    <div
                      className="dataset-card"
                      key={dataset.id}
                    >
                      <div className="dataset-card-top">
                        <div className="file-icon large">
                          {dataset.file_type
                            .replace('.', '')
                            .toUpperCase()}
                        </div>

                        <span className="dataset-id">
                          #{dataset.id}
                        </span>
                      </div>

                      <h3>{dataset.original_filename}</h3>

                      <p>
                        {dataset.file_type.toUpperCase().replace(
                          '.',
                          ''
                        )}{' '}
                        · {formatFileSize(dataset.file_size)}
                      </p>

                      <span className="dataset-date">
                        Uploaded {formatDate(dataset.created_at)}
                      </span>

                      <div className="dataset-actions">
                        <button
                          className="primary-small-button"
                          onClick={() =>
                            selectDataset(dataset)
                          }
                        >
                          Analyze
                        </button>

                        <button
                          className="delete-button"
                          onClick={() =>
                            deleteDataset(dataset.id)
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {page === 'analytics' && (
          <section className="content">
            {!selectedDataset ? (
              <div className="section-card">
                <div className="empty-state">
                  <div>▥</div>
                  <h3>Select a dataset</h3>
                  <p>
                    Choose a dataset from your library to view
                    its analytics.
                  </p>

                  <button
                    className="primary-button"
                    onClick={() => setPage('datasets')}
                  >
                    Browse datasets
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="dataset-header-card">
                  <div className="file-icon large">
                    {selectedDataset.file_type
                      .replace('.', '')
                      .toUpperCase()}
                  </div>

                  <div>
                    <span className="section-kicker">
                      DATASET #{selectedDataset.id}
                    </span>

                    <h2>
                      {selectedDataset.original_filename}
                    </h2>

                    <p>
                      {formatFileSize(
                        selectedDataset.file_size
                      )}{' '}
                      · Uploaded{' '}
                      {formatDate(
                        selectedDataset.created_at
                      )}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    <button
                      className="secondary-button"
                      onClick={exportAnalyticsReport}
                      disabled={!summary || analyticsLoading}
                    >
                      Export report ↓
                    </button>
                    <button
                      className="secondary-button"
                      onClick={() => setPage('ai')}
                    >
                      Ask AI ✦
                    </button>
                  </div>
                </div>

                {analyticsError && (
                  <div className="page-error">
                    {analyticsError}
                  </div>
                )}

                {analyticsLoading ? (
                  <div className="loading-card">
                    <div className="spinner"></div>
                    <p>Analyzing your dataset...</p>
                  </div>
                ) : (
                  <>
                    {summary && (
                      <div className="analytics-stat-grid">
                        <div>
                          <span>Rows</span>
                          <strong>{summary.rows}</strong>
                        </div>

                        <div>
                          <span>Columns</span>
                          <strong>{summary.columns}</strong>
                        </div>

                        <div>
                          <span>Numeric columns</span>
                          <strong>
                            {statistics
                              ? Object.keys(
                                  statistics.numeric_columns
                                ).length
                              : 0}
                          </strong>
                        </div>

                        <div>
                          <span>Missing values</span>
                          <strong>
                            {Object.values(
                              summary.missing_values
                            ).reduce(
                              (total, value) =>
                                total + value,
                              0
                            )}
                          </strong>
                        </div>
                      </div>
                    )}

                    {qualityReport && (
                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              DATA QUALITY
                            </span>
                            <h2>Dataset health</h2>
                          </div>
                          <span className="count-badge">
                            {qualityReport.quality_level}
                          </span>
                        </div>

                        <div className="analytics-stat-grid">
                          <div>
                            <span>Quality score</span>
                            <strong>
                              {qualityReport.quality_score.toFixed(2)}%
                            </strong>
                          </div>
                          <div>
                            <span>Missing values</span>
                            <strong>{qualityReport.total_missing_values}</strong>
                          </div>
                          <div>
                            <span>Duplicate rows</span>
                            <strong>{qualityReport.duplicate_rows}</strong>
                          </div>
                          <div>
                            <span>Outlier fields</span>
                            <strong>
                              {Object.values(qualityReport.outliers).filter(
                                (item) => item.count > 0
                              ).length}
                            </strong>
                          </div>
                        </div>

                        <div style={{ marginTop: 20 }}>
                          <strong style={{ display: 'block', marginBottom: 10 }}>
                            Recommendations
                          </strong>
                          <div className="insight-list">
                            {qualityReport.recommendations.map(
                              (recommendation, index) => (
                                <div className="insight-item" key={index}>
                                  <span>!</span>
                                  <p>{recommendation}</p>
                                </div>
                              )
                            )}
                          </div>
                        </div>

                        {Object.keys(
                          qualityReport.categorical_inconsistencies
                        ).length > 0 && (
                          <div style={{ marginTop: 20 }}>
                            <strong style={{ display: 'block', marginBottom: 10 }}>
                              Categorical inconsistencies
                            </strong>
                            {Object.entries(
                              qualityReport.categorical_inconsistencies
                            ).map(([column, issues]) => (
                              <div key={column} style={{ marginBottom: 8 }}>
                                <strong>{column}:</strong>{' '}
                                {issues
                                  .map(
                                    (issue) =>
                                      `${issue.variants.join(', ')} → ${issue.normalized_value}`
                                  )
                                  .join('; ')}
                              </div>
                            ))}
                          </div>
                        )}

                        {Object.values(qualityReport.outliers).some(
                          (item) => item.count > 0
                        ) && (
                          <div style={{ marginTop: 20 }}>
                            <strong style={{ display: 'block', marginBottom: 10 }}>
                              Detected outliers
                            </strong>
                            <div className="statistics-grid">
                              {Object.entries(qualityReport.outliers)
                                .filter(([, item]) => item.count > 0)
                                .map(([column, item]) => (
                                  <div className="statistics-card" key={column}>
                                    <h3>{column}</h3>
                                    <div className="statistics-values">
                                      <div>
                                        <span>Count</span>
                                        <strong>{item.count}</strong>
                                      </div>
                                      <div>
                                        <span>Percentage</span>
                                        <strong>
                                          {item.percentage.toFixed(2)}%
                                        </strong>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="analytics-columns">
                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              DATA PREVIEW
                            </span>
                            <h2>First rows</h2>
                          </div>
                        </div>

                        <div className="table-wrapper">
                          <table>
                            <thead>
                              <tr>
                                {preview.length > 0 &&
                                  Object.keys(
                                    preview[0]
                                  ).map((column) => (
                                    <th key={column}>
                                      {column}
                                    </th>
                                  ))}
                              </tr>
                            </thead>

                            <tbody>
                              {preview.map(
                                (row, rowIndex) => (
                                  <tr key={rowIndex}>
                                    {Object.values(row).map(
                                      (value, index) => (
                                        <td key={index}>
                                          {String(value)}
                                        </td>
                                      )
                                    )}
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              AI-GENERATED
                            </span>
                            <h2>Insights</h2>
                          </div>
                        </div>

                        <div className="insight-list">
                          {insights.map(
                            (insight, index) => (
                              <div
                                className="insight-item"
                                key={index}
                              >
                                <span>✓</span>
                                <p>{insight}</p>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    </div>

                    {salesChartEntries.length > 0 && (
                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              VISUAL ANALYTICS
                            </span>
                            <h2>Sales performance</h2>
                          </div>

                          <div style={{ display: 'flex', gap: 8 }}>
                            <button
                              className={`small-button ${chartMetric === 'total' ? 'active' : ''}`}
                              onClick={() => setChartMetric('total')}
                            >
                              Total sales
                            </button>
                            <button
                              className={`small-button ${chartMetric === 'average' ? 'active' : ''}`}
                              onClick={() => setChartMetric('average')}
                            >
                              Average sales
                            </button>
                          </div>
                        </div>

                        <div className="analytics-columns">
                          {salesChartEntries.map(([key, records]) => (
                            <div key={key} style={{ minWidth: 0 }}>
                              <h3 style={{ margin: '0 0 18px' }}>
                                {formatChartTitle(key)}
                              </h3>

                              <div style={{ width: '100%', height: 340 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                  <BarChart
                                    data={records}
                                    margin={{ top: 8, right: 12, left: 8, bottom: 70 }}
                                  >
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                    <XAxis
                                      dataKey="category"
                                      angle={-35}
                                      textAnchor="end"
                                      interval={0}
                                      height={90}
                                      tick={{ fontSize: 11 }}
                                    />
                                    <YAxis
                                      tick={{ fontSize: 11 }}
                                      width={55}
                                    />
                                    <Tooltip
                                      formatter={(value) => [
                                        Number(value).toLocaleString(undefined, {
                                          maximumFractionDigits: 2,
                                        }),
                                        chartMetric === 'total' ? 'Total sales' : 'Average sales',
                                      ]}
                                    />
                                    <Bar
                                      dataKey={chartMetric}
                                      name={chartMetric === 'total' ? 'Total sales' : 'Average sales'}
                                      fill="#5b54e8"
                                      radius={[6, 6, 0, 0]}
                                    />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {advancedAnalytics && (
                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              ADVANCED ANALYTICS
                            </span>
                            <h2>Deeper patterns</h2>
                          </div>
                          <span className="count-badge">
                            {advancedAnalytics.strongest_correlations.length} correlations
                          </span>
                        </div>

                        {advancedAnalytics.strongest_correlations.length > 0 ? (
                          <div>
                            <h3 style={{ marginBottom: 14 }}>
                              Strongest relationships
                            </h3>

                            <div className="table-wrapper">
                              <table>
                                <thead>
                                  <tr>
                                    <th>Column A</th>
                                    <th>Column B</th>
                                    <th>Correlation</th>
                                    <th>Relationship</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {advancedAnalytics.strongest_correlations
                                    .slice(0, 10)
                                    .map((item) => (
                                      <tr
                                        key={`${item.column_a}-${item.column_b}`}
                                      >
                                        <td>{item.column_a}</td>
                                        <td>{item.column_b}</td>
                                        <td>
                                          {item.correlation.toFixed(3)}
                                        </td>
                                        <td>
                                          {item.correlation >= 0.7
                                            ? 'Strong positive'
                                            : item.correlation >= 0.3
                                              ? 'Moderate positive'
                                              : item.correlation <= -0.7
                                                ? 'Strong negative'
                                                : item.correlation <= -0.3
                                                  ? 'Moderate negative'
                                                  : 'Weak'}
                                        </td>
                                      </tr>
                                    ))}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        ) : (
                          <p>
                            At least two numeric columns are required to
                            calculate correlations.
                          </p>
                        )}

                        {Object.keys(
                          advancedAnalytics.numeric_distributions
                        ).length > 0 && (
                          <div style={{ marginTop: 24 }}>
                            <h3 style={{ marginBottom: 14 }}>
                              Numeric distributions
                            </h3>

                            <div className="statistics-grid">
                              {Object.entries(
                                advancedAnalytics.numeric_distributions
                              ).map(([column, stats]) => (
                                <div
                                  className="statistics-card"
                                  key={column}
                                >
                                  <h3>{column}</h3>

                                  <div className="statistics-values">
                                    <div>
                                      <span>Mean</span>
                                      <strong>
                                        {stats.mean !== null
                                          ? stats.mean.toFixed(2)
                                          : '—'}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Median</span>
                                      <strong>
                                        {stats.median !== null
                                          ? stats.median.toFixed(2)
                                          : '—'}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Q1</span>
                                      <strong>
                                        {stats.q1 !== null
                                          ? stats.q1.toFixed(2)
                                          : '—'}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Q3</span>
                                      <strong>
                                        {stats.q3 !== null
                                          ? stats.q3.toFixed(2)
                                          : '—'}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Skewness</span>
                                      <strong>
                                        {stats.skewness !== null
                                          ? stats.skewness.toFixed(2)
                                          : '—'}
                                      </strong>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {Object.keys(
                          advancedAnalytics.categorical_distributions
                        ).length > 0 && (
                          <div style={{ marginTop: 24 }}>
                            <h3 style={{ marginBottom: 14 }}>
                              Category distributions
                            </h3>

                            <div className="statistics-grid">
                              {Object.entries(
                                advancedAnalytics.categorical_distributions
                              )
                                .slice(0, 6)
                                .map(([column, records]) => (
                                  <div
                                    className="statistics-card"
                                    key={column}
                                  >
                                    <h3>{column}</h3>

                                    <div className="table-wrapper">
                                      <table>
                                        <thead>
                                          <tr>
                                            <th>Category</th>
                                            <th>Count</th>
                                            <th>%</th>
                                          </tr>
                                        </thead>

                                        <tbody>
                                          {records
                                            .slice(0, 5)
                                            .map((record) => (
                                              <tr
                                                key={`${column}-${record.category}`}
                                              >
                                                <td>
                                                  {record.category}
                                                </td>
                                                <td>
                                                  {record.count}
                                                </td>
                                                <td>
                                                  {record.percentage.toFixed(
                                                    2
                                                  )}%
                                                </td>
                                              </tr>
                                            ))}
                                        </tbody>
                                      </table>
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {statistics &&
                      Object.keys(
                        statistics.numeric_columns
                      ).length > 0 && (
                        <div className="section-card">
                          <div className="section-heading">
                            <div>
                              <span className="section-kicker">
                                STATISTICS
                              </span>
                              <h2>Numeric analysis</h2>
                            </div>
                          </div>

                          <div className="statistics-grid">
                            {Object.entries(
                              statistics.numeric_columns
                            ).map(
                              ([column, stats]) => (
                                <div
                                  className="statistics-card"
                                  key={column}
                                >
                                  <h3>{column}</h3>

                                  <div className="statistics-values">
                                    <div>
                                      <span>Mean</span>
                                      <strong>
                                        {stats.mean.toFixed(2)}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Median</span>
                                      <strong>
                                        {stats.median}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Minimum</span>
                                      <strong>
                                        {stats.min}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Maximum</span>
                                      <strong>
                                        {stats.max}
                                      </strong>
                                    </div>

                                    <div>
                                      <span>Std Dev</span>
                                      <strong>
                                        {stats.std.toFixed(2)}
                                      </strong>
                                    </div>
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        </div>
                      )}
                  </>
                )}
              </>
            )}
          </section>
        )}

        {page === 'ml' && (
          <section className="content">
            {!selectedDataset ? (
              <div className="section-card">
                <div className="empty-state">
                  <div>⌁</div>
                  <h3>Select a dataset first</h3>
                  <p>Choose a dataset before training machine-learning models.</p>
                  <button className="primary-button" onClick={() => setPage('datasets')}>
                    Select dataset
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="dataset-header-card">
                  <div className="file-icon large">
                    {selectedDataset.file_type.replace('.', '').toUpperCase()}
                  </div>
                  <div>
                    <span className="section-kicker">MACHINE LEARNING</span>
                    <h2>{selectedDataset.original_filename}</h2>
                    <p>Train and compare multiple models automatically.</p>
                  </div>
                </div>

                <div className="section-card">
                  <div className="section-heading">
                    <div>
                      <span className="section-kicker">AUTOML</span>
                      <h2>Model comparison</h2>
                    </div>
                  </div>

                  <form onSubmit={trainModels}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 220px) auto', gap: 12, alignItems: 'end' }}>
                      <div className="form-group">
                        <label htmlFor="ml-target">Target column</label>
                        <select
                          id="ml-target"
                          value={mlTarget}
                          onChange={(event) => setMlTarget(event.target.value)}
                          style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid #ddd' }}
                        >
                          <option value="">Select target column</option>
                          {summary?.column_names.map((column) => (
                            <option key={column} value={column}>{column}</option>
                          ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label htmlFor="ml-problem">Problem type</label>
                        <select
                          id="ml-problem"
                          value={mlProblemType}
                          onChange={(event) => setMlProblemType(event.target.value as 'auto' | 'classification' | 'regression')}
                          style={{ width: '100%', padding: '12px 14px', borderRadius: 10, border: '1px solid #ddd' }}
                        >
                          <option value="auto">Auto detect</option>
                          <option value="regression">Regression</option>
                          <option value="classification">Classification</option>
                        </select>
                      </div>

                      <button type="submit" className="primary-small-button" disabled={mlLoading || !mlTarget} style={{ minHeight: 46 }}>
                        {mlLoading ? 'Training...' : 'Train & Compare'}
                      </button>
                    </div>
                  </form>

                  {mlError && <div className="page-error" style={{ marginTop: 16 }}>{mlError}</div>}
                </div>

                {mlResult && (
                  <>
                    <div className="analytics-stat-grid">
                      <div><span>Problem type</span><strong>{mlResult.problem_type}</strong></div>
                      <div><span>Training rows</span><strong>{mlResult.train_rows}</strong></div>
                      <div><span>Test rows</span><strong>{mlResult.test_rows}</strong></div>
                      <div><span>Best model</span><strong>{mlResult.best_model}</strong></div>
                    </div>

                    <div className="section-card">
                      <div className="section-heading">
                        <div>
                          <span className="section-kicker">RESULTS</span>
                          <h2>Model comparison</h2>
                        </div>
                        <span className="count-badge">Best: {mlResult.best_model}</span>
                      </div>

                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Model</th>
                              {mlResult.problem_type === 'classification' ? (
                                <><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th></>
                              ) : (
                                <><th>MAE</th><th>RMSE</th><th>R²</th></>
                              )}
                            </tr>
                          </thead>
                          <tbody>
                            {mlResult.models.map((model: any) => (
                              <tr key={model.model}>
                                <td><strong>{model.model}</strong></td>
                                {model.error ? (
                                  <td colSpan={mlResult.problem_type === 'classification' ? 4 : 3}>{model.error}</td>
                                ) : mlResult.problem_type === 'classification' ? (
                                  <><td>{model.accuracy}</td><td>{model.precision}</td><td>{model.recall}</td><td>{model.f1_score}</td></>
                                ) : (
                                  <><td>{model.mae}</td><td>{model.rmse}</td><td>{model.r2_score}</td></>
                                )}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {mlResult.explainability && (
                      <div className="section-card">
                        <div className="section-heading">
                          <div>
                            <span className="section-kicker">
                              EXPLAINABLE AI
                            </span>
                            <h2>Feature importance</h2>
                          </div>

                          <span className="count-badge">
                            {mlResult.explainability.method}
                          </span>
                        </div>

                        <p style={{ marginTop: 0, marginBottom: 18 }}>
                          These features had the greatest influence on the
                          selected {mlResult.best_model} model.
                        </p>

                        <div className="table-wrapper">
                          <table>
                            <thead>
                              <tr>
                                <th>Rank</th>
                                <th>Feature</th>
                                <th>Importance</th>
                                <th>Variation</th>
                              </tr>
                            </thead>

                            <tbody>
                              {mlResult.explainability.features.map(
                                (feature: any, index: number) => (
                                  <tr key={feature.feature}>
                                    <td>
                                      <strong>{index + 1}</strong>
                                    </td>

                                    <td>
                                      <strong>{feature.feature}</strong>
                                    </td>

                                    <td>
                                      {Number(feature.importance).toFixed(6)}
                                    </td>

                                    <td>
                                      ± {Number(feature.std).toFixed(6)}
                                    </td>
                                  </tr>
                                )
                              )}
                            </tbody>
                          </table>
                        </div>

                        <div
                          style={{
                            marginTop: 20,
                            padding: 16,
                            borderRadius: 12,
                            background: 'rgba(91, 84, 232, 0.06)',
                          }}
                        >
                          <strong>How to read this:</strong>
                          <p style={{ margin: '6px 0 0', lineHeight: 1.6 }}>
                            Higher permutation importance means the model's
                            performance changed more when that feature was
                            shuffled. This indicates a greater contribution
                            to the model's predictions.
                          </p>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </section>
        )}

        {page === 'forecast' && (
          <section className="content">
            {!selectedDataset ? (
              <div className="section-card">
                <div className="empty-state">
                  <div>↗</div>
                  <h3>Select a dataset first</h3>
                  <p>Select a dataset before generating a forecast.</p>
                  <button
                    className="primary-button"
                    onClick={() => setPage('datasets')}
                  >
                    Select dataset
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="dataset-header-card">
                  <div className="file-icon large">
                    {selectedDataset.file_type.replace('.', '').toUpperCase()}
                  </div>
                  <div>
                    <span className="section-kicker">TIME SERIES</span>
                    <h2>{selectedDataset.original_filename}</h2>
                    <p>Generate future values from historical time-based data.</p>
                  </div>
                </div>

                <div className="section-card">
                  <div className="section-heading">
                    <div>
                      <span className="section-kicker">FORECASTING</span>
                      <h2>Forecast future values</h2>
                    </div>
                  </div>

                  {forecastColumns.date_columns.length === 0 ? (
                    <div
                      style={{
                        padding: 20,
                        borderRadius: 12,
                        background: 'rgba(91, 84, 232, 0.06)',
                        lineHeight: 1.6,
                      }}
                    >
                      <strong>No date/time column detected.</strong>
                      <p style={{ marginBottom: 0 }}>
  Forecasting requires a dataset containing a date or time
  column and at least one numeric value to forecast.
  Upload a time-series dataset to use this feature.
</p>
                    </div>
                  ) : (
                    <form onSubmit={generateForecast}>
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns:
                            'minmax(0, 1fr) minmax(0, 1fr) 160px 180px auto',
                          gap: 12,
                          alignItems: 'end',
                        }}
                      >
                        <div className="form-group">
                          <label htmlFor="forecast-date">Date column</label>
                          <select
                            id="forecast-date"
                            value={forecastDateColumn}
                            onChange={(event) =>
                              setForecastDateColumn(event.target.value)
                            }
                            style={{
                              width: '100%',
                              padding: '12px 14px',
                              borderRadius: 10,
                              border: '1px solid #ddd',
                            }}
                          >
                            {forecastColumns.date_columns.map((column) => (
                              <option key={column} value={column}>
                                {column}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label htmlFor="forecast-target">Target column</label>
                          <select
                            id="forecast-target"
                            value={forecastTargetColumn}
                            onChange={(event) =>
                              setForecastTargetColumn(event.target.value)
                            }
                            style={{
                              width: '100%',
                              padding: '12px 14px',
                              borderRadius: 10,
                              border: '1px solid #ddd',
                            }}
                          >
                            {forecastColumns.numeric_columns.map((column) => (
                              <option key={column} value={column}>
                                {column}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="form-group">
                          <label htmlFor="forecast-periods">Periods</label>
                          <input
                            id="forecast-periods"
                            type="number"
                            min="1"
                            max="60"
                            value={forecastPeriods}
                            onChange={(event) =>
                              setForecastPeriods(Number(event.target.value))
                            }
                            style={{
                              width: '100%',
                              padding: '12px 14px',
                              borderRadius: 10,
                              border: '1px solid #ddd',
                            }}
                          />
                        </div>

                        <div className="form-group">
                          <label htmlFor="forecast-frequency">Frequency</label>
                          <select
                            id="forecast-frequency"
                            value={forecastFrequency}
                            onChange={(event) =>
                              setForecastFrequency(event.target.value)
                            }
                            style={{
                              width: '100%',
                              padding: '12px 14px',
                              borderRadius: 10,
                              border: '1px solid #ddd',
                            }}
                          >
                            <option value="auto">Auto detect</option>
                            <option value="D">Daily</option>
                            <option value="W">Weekly</option>
                            <option value="MS">Monthly</option>
                            <option value="QS">Quarterly</option>
                            <option value="YS">Yearly</option>
                          </select>
                        </div>

                        <button
                          type="submit"
                          className="primary-small-button"
                          disabled={
                            forecastLoading ||
                            !forecastDateColumn ||
                            !forecastTargetColumn
                          }
                          style={{ minHeight: 46 }}
                        >
                          {forecastLoading
                            ? 'Forecasting...'
                            : 'Generate forecast'}
                        </button>
                      </div>
                    </form>
                  )}

                  {forecastError && (
                    <div className="page-error" style={{ marginTop: 16 }}>
                      {forecastError}
                    </div>
                  )}
                </div>

                {forecastResult && (
                  <>
                    <div className="analytics-stat-grid">
                      <div>
                        <span>Model</span>
                        <strong>{forecastResult.model}</strong>
                      </div>
                      <div>
                        <span>Frequency</span>
                        <strong>{forecastResult.frequency}</strong>
                      </div>
                      <div>
                        <span>Historical periods</span>
                        <strong>{forecastResult.historical_periods}</strong>
                      </div>
                      <div>
                        <span>Forecast periods</span>
                        <strong>{forecastResult.forecast_periods}</strong>
                      </div>
                    </div>

                    <div className="section-card">
                      <div className="section-heading">
                        <div>
                          <span className="section-kicker">FORECAST</span>
                          <h2>Predicted values</h2>
                        </div>
                      </div>

                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Prediction</th>
                              <th>Lower bound</th>
                              <th>Upper bound</th>
                            </tr>
                          </thead>
                          <tbody>
                            {forecastResult.forecast.map((row: any) => (
                              <tr key={row.date}>
                                <td><strong>{row.date}</strong></td>
                                <td>{row.predicted}</td>
                                <td>{row.lower_bound}</td>
                                <td>{row.upper_bound}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    <div className="section-card">
                      <div className="section-heading">
                        <div>
                          <span className="section-kicker">TREND</span>
                          <h2>Forecast summary</h2>
                        </div>
                      </div>

                      <p style={{ margin: 0, lineHeight: 1.7 }}>
                        The estimated trend slope is{' '}
                        <strong>{forecastResult.trend_slope}</strong> per
                        time period. Forecast intervals are based on the
                        historical residual variation of the linear trend
                        model.
                      </p>
                    </div>
                  </>
                )}
              </>
            )}
          </section>
        )}

        {page === 'ai' && (
          <section className="content">
            {!selectedDataset ? (
              <div className="section-card">
                <div className="empty-state">
                  <div>✦</div>
                  <h3>Select a dataset first</h3>
                  <p>
                    InsightForge AI needs a dataset to answer
                    questions about your data.
                  </p>

                  <button
                    className="primary-button"
                    onClick={() => setPage('datasets')}
                  >
                    Select dataset
                  </button>
                </div>
              </div>
            ) : (
              <div className="ai-layout">
                <div className="ai-card">
                  <div className="ai-header">
                    <div>
                      <span className="section-kicker">
                        AI DATA ASSISTANT
                      </span>

                      <h2>Ask questions about your data</h2>

                      <p>
                        Currently analyzing{' '}
                        <strong>
                          {selectedDataset.original_filename}
                        </strong>
                      </p>
                    </div>

                    <div className="ai-status">
                      <span></span>
                      AI ready
                    </div>
                  </div>

                  <div className="chat-area">
                    {chatMessages.length === 0 ? (
                      <div className="chat-empty">
                        <div className="ai-big-icon">✦</div>

                        <h3>
                          What would you like to know?
                        </h3>

                        <p>
                          Ask questions about the rows,
                          columns, patterns, or statistics in
                          your dataset.
                        </p>

                        <div className="suggestion-list">
                          <button
                            onClick={() =>
                              setPrompt(
                                'What is the average value in this dataset?'
                              )
                            }
                          >
                            What is the average value?
                          </button>

                          <button
                            onClick={() =>
                              setPrompt(
                                'Which person is the oldest in this dataset?'
                              )
                            }
                          >
                            Which person is the oldest?
                          </button>

                          <button
                            onClick={() =>
                              setPrompt(
                                'Give me the most important insights from this dataset.'
                              )
                            }
                          >
                            Give me the key insights.
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="message-list">
                        {chatMessages.map(
                          (message, index) => (
                            <div
                              className="message-group"
                              key={index}
                            >
                              <div className="user-message">
                                <div className="message-avatar">
                                  {user.full_name
                                    .charAt(0)
                                    .toUpperCase()}
                                </div>

                                <div>
                                  <span className="message-label">
                                    You
                                  </span>

                                  <p>
                                    {message.prompt}
                                  </p>
                                </div>
                              </div>

                              <div className="ai-message">
                                <div className="ai-message-avatar">
                                  ✦
                                </div>

                                <div>
                                  <span className="message-label">
                                    InsightForge AI
                                  </span>

                                  <div className="ai-response-content">
                                    {formatAIResponse(message.response)}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )
                        )}

                        {chatLoading && (
                          <div className="ai-message">
                            <div className="ai-message-avatar">
                              ✦
                            </div>

                            <div>
                              <span className="message-label">
                                InsightForge AI
                              </span>

                              <p className="ai-thinking">
                                Thinking about your data...
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {chatError && (
                    <div className="chat-error">
                      {chatError}
                    </div>
                  )}

                  <form
                    className="chat-input"
                    onSubmit={sendChat}
                  >
                    <input
                      value={prompt}
                      onChange={(event) =>
                        setPrompt(event.target.value)
                      }
                      placeholder="Ask something about your data..."
                      disabled={chatLoading}
                    />

                    <button
                      type="submit"
                      disabled={chatLoading || !prompt.trim()}
                    >
                      {chatLoading ? '...' : '→'}
                    </button>
                  </form>
                </div>
              </div>
            )}
          </section>
        )}

        {page === 'conversations' && (
          <section className="content">
            <div className="conversation-layout">
              <div className="section-card conversation-list-card">
                <div className="section-heading">
                  <div>
                    <span className="section-kicker">
                      CHAT HISTORY
                    </span>
                    <h2>Your conversations</h2>
                  </div>

                  <span className="count-badge">
                    {conversations.length}
                  </span>
                </div>

                {conversations.length === 0 ? (
                  <div className="empty-state">
                    <div>◌</div>
                    <h3>No conversations yet</h3>
                    <p>
                      Your AI conversations will appear here.
                    </p>
                  </div>
                ) : (
                  <div className="conversation-list">
                    {conversations.map(
                      (conversation) => (
                        <div
                          className={`conversation-row ${
                            selectedConversation?.id ===
                            conversation.id
                              ? 'selected'
                              : ''
                          }`}
                          key={conversation.id}
                        >
                          {editingConversation ===
                          conversation.id ? (
                            <div className="rename-area">
                              <input
                                value={editingTitle}
                                onChange={(event) =>
                                  setEditingTitle(
                                    event.target.value
                                  )
                                }
                                autoFocus
                              />

                              <div>
                                <button
                                  className="primary-small-button"
                                  onClick={() =>
                                    renameConversation(
                                      conversation.id
                                    )
                                  }
                                >
                                  Save
                                </button>

                                <button
                                  className="delete-button"
                                  onClick={() => {
                                    setEditingConversation(
                                      null
                                    )
                                    setEditingTitle('')
                                  }}
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <>
                              <button
                                className="conversation-main"
                                onClick={() =>
                                  loadConversationHistory(
                                    conversation
                                  )
                                }
                              >
                                <span className="conversation-icon">
                                  ✦
                                </span>

                                <div>
                                  <strong>
                                    {conversation.title}
                                  </strong>

                                  <span>
                                    {formatDate(
                                      conversation.created_at
                                    )}
                                  </span>
                                </div>
                              </button>

                              <button
                                className="icon-button"
                                title="Rename"
                                onClick={() => {
                                  setEditingConversation(
                                    conversation.id
                                  )
                                  setEditingTitle(
                                    conversation.title
                                  )
                                }}
                              >
                                ✎
                              </button>

                              <button
                                className="icon-button danger"
                                title="Delete"
                                onClick={() =>
                                  deleteConversation(
                                    conversation.id
                                  )
                                }
                              >
                                ×
                              </button>
                            </>
                          )}
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>

              <div className="section-card conversation-detail">
                {selectedConversation ? (
                  <>
                    <div className="section-heading">
                      <div>
                        <span className="section-kicker">
                          CONVERSATION #{selectedConversation.id}
                        </span>

                        <h2>
                          {selectedConversation.title}
                        </h2>
                      </div>
                    </div>

                    <div className="history-messages">
                      {conversationMessages.length === 0 ? (
                        <div className="empty-state">
                          <p>No messages found.</p>
                        </div>
                      ) : (
                        conversationMessages.map(
                          (message, index) => (
                            <div
                              className="history-group"
                              key={message.id || index}
                            >
                              <div className="history-prompt">
                                <span>You</span>
                                <p>
                                  {message.prompt}
                                </p>
                              </div>

                              <div className="history-response">
                                <span>
                                  InsightForge AI
                                </span>
                                <div className="ai-response-content">
                                  {formatAIResponse(message.response)}
                                </div>
                              </div>
                            </div>
                          )
                        )
                      )}
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <div>◌</div>
                    <h3>Select a conversation</h3>
                    <p>
                      Choose a conversation from the list to
                      view its history.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App