import { useState, useEffect, useCallback } from 'react'

function App() {
  // Config state (defaults to the deployed Cloud Run service URL)
  const defaultBackend = import.meta.env.VITE_BACKEND_URL || "https://intelligent-slack-knowledge-base-242431895873.asia-south1.run.app"
  const [backendUrl, setBackendUrl] = useState(defaultBackend)
  
  // Tab and filter states
  const [activeTab, setActiveTab] = useState('documents')
  const [scopeFilter, setScopeFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  
  // Data states
  const [stats, setStats] = useState({
    documents: 0,
    chunks: 0,
    scopes: {},
    ingestion_jobs: 0,
    failed_jobs: 0
  })
  const [documents, setDocuments] = useState([])
  const [jobs, setJobs] = useState([])
  
  // Selected Document details (Modal)
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [selectedDocChunks, setSelectedDocChunks] = useState([])
  const [loadingDocDetail, setLoadingDocDetail] = useState(false)
  
  // Status states
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [apiStatus, setApiStatus] = useState('loading') // 'ok' | 'error' | 'loading'
  const [dbStatus, setDbStatus] = useState('loading') // 'ok' | 'error' | 'loading'
  const [apiVersion, setApiVersion] = useState('Unknown')
  const [errorMessage, setErrorMessage] = useState('')

  // Check backend health & database readiness
  const checkHealth = useCallback(async (url) => {
    try {
      // 1. Fetch Root (check API + Version)
      const rootRes = await fetch(url)
      if (rootRes.ok) {
        const rootData = await rootRes.json()
        setApiStatus('ok')
        setApiVersion(rootData.version || '0.1.0')
      } else {
        setApiStatus('error')
      }

      // 2. Fetch /readyz (check Database)
      const readyRes = await fetch(`${url}/readyz`)
      if (readyRes.ok) {
        setDbStatus('ok')
      } else {
        setDbStatus('error')
      }
    } catch (err) {
      setApiStatus('error')
      setDbStatus('error')
      console.error("Health check failed:", err)
    }
  }, [])

  // Fetch Dashboard Stats
  const fetchStats = useCallback(async (url) => {
    try {
      const res = await fetch(`${url}/api/stats`)
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err)
    }
  }, [])

  // Fetch Documents
  const fetchDocuments = useCallback(async (url, scope) => {
    try {
      const queryParam = scope !== 'all' ? `?scope=${scope}` : ''
      const res = await fetch(`${url}/api/documents${queryParam}`)
      if (res.ok) {
        const data = await res.json()
        setDocuments(data.documents || [])
      }
    } catch (err) {
      console.error("Failed to fetch documents:", err)
    }
  }, [])

  // Fetch Ingestion Jobs
  const fetchJobs = useCallback(async (url) => {
    try {
      const res = await fetch(`${url}/api/ingestion-jobs`)
      if (res.ok) {
        const data = await res.json()
        setJobs(data.jobs || [])
      }
    } catch (err) {
      console.error("Failed to fetch jobs:", err)
    }
  }, [])

  // Master refresh function
  const refreshData = useCallback(async (targetUrl = backendUrl) => {
    setIsRefreshing(true)
    setErrorMessage('')
    
    // Clean trailing slash
    const cleanUrl = targetUrl.replace(/\/$/, '')
    
    try {
      await Promise.all([
        checkHealth(cleanUrl),
        fetchStats(cleanUrl),
        fetchDocuments(cleanUrl, scopeFilter),
        fetchJobs(cleanUrl)
      ])
    } catch (err) {
      setErrorMessage("Connection to backend API failed. Check VITE_BACKEND_URL or manual URL input.")
    } finally {
      setIsRefreshing(false)
    }
  }, [backendUrl, scopeFilter, checkHealth, fetchStats, fetchDocuments, fetchJobs])

  // Trigger load on backend URL or scope filter change
  useEffect(() => {
    refreshData(backendUrl)
  }, [backendUrl, scopeFilter])

  // Fetch specific document chunks for details view
  const handleViewDocDetails = async (docId) => {
    setLoadingDocDetail(true)
    setSelectedDoc(null)
    setSelectedDocChunks([])
    
    const cleanUrl = backendUrl.replace(/\/$/, '')
    try {
      const res = await fetch(`${cleanUrl}/api/documents/${docId}`)
      if (res.ok) {
        const data = await res.json()
        setSelectedDoc(data.document)
        setSelectedDocChunks(data.chunks || [])
      } else {
        alert("Failed to load document details.")
      }
    } catch (err) {
      console.error("Error fetching doc details:", err)
      alert("Error contacting server.")
    } finally {
      setLoadingDocDetail(false)
    }
  }

  // Filter documents by search query client-side
  const filteredDocuments = documents.filter(doc => {
    const query = searchQuery.toLowerCase()
    return (
      doc.title?.toLowerCase().includes(query) ||
      doc.id?.toLowerCase().includes(query) ||
      doc.source_type?.toLowerCase().includes(query) ||
      doc.tags?.some(tag => tag.toLowerCase().includes(query))
    )
  })

  // Format timestamp helper
  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A'
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="dashboard-container">
      <div className="noise"></div>
      
      {/* Top Header */}
      <header className="dashboard-header">
        <div className="header-title-area">
          <h1>Slack Knowledge Base</h1>
          <p>Admin Control Panel & Permission-Aware RAG Monitor</p>
        </div>
        <div className="header-actions">
          <span className="badge">Admin System</span>
          <button 
            className="btn-primary" 
            onClick={() => refreshData()}
            disabled={isRefreshing}
          >
            <span className={isRefreshing ? "refresh-spin" : ""}>🔄</span> Refresh
          </button>
        </div>
      </header>

      {/* Backend Settings Card */}
      <section className="glass-card">
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
            API Backend URL:
          </label>
          <input 
            type="text" 
            className="search-box" 
            style={{ flexGrow: 1, width: 'auto' }}
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            placeholder="https://your-cloud-run-url.run.app"
          />
          {backendUrl !== defaultBackend && (
            <button className="btn-primary" onClick={() => setBackendUrl(defaultBackend)} style={{ background: 'transparent', border: '1px solid var(--border-strong)' }}>
              Reset to Deployed URL
            </button>
          )}
        </div>
        {errorMessage && (
          <div style={{ color: 'var(--red)', fontSize: '0.85rem', marginTop: '12px' }}>
            ⚠️ {errorMessage}
          </div>
        )}
      </section>

      {/* System Stats Overview */}
      <section className="stats-grid">
        <div className="glass-card stat-card">
          <span className="stat-label">Total Documents</span>
          <span className="stat-value">{stats.documents}</span>
          <span className="stat-footer">
            <span className="stat-indicator green"></span>
            Permission-aware indexes
          </span>
        </div>
        
        <div className="glass-card stat-card">
          <span className="stat-label">Indexed Chunks</span>
          <span className="stat-value">{stats.chunks}</span>
          <span className="stat-footer">
            <span className="stat-indicator green"></span>
            pgvector dense embeddings
          </span>
        </div>

        <div className="glass-card stat-card">
          <span className="stat-label">Ingestion Jobs</span>
          <span className="stat-value">{stats.ingestion_jobs}</span>
          <span className="stat-footer">
            <span className="stat-indicator green"></span>
            Total trigger history
          </span>
        </div>

        <div className="glass-card stat-card">
          <span className="stat-label">Failed Ingests</span>
          <span className="stat-value" style={{ color: stats.failed_jobs > 0 ? 'var(--red)' : '#fff' }}>
            {stats.failed_jobs}
          </span>
          <span className="stat-footer">
            <span className={`stat-indicator ${stats.failed_jobs > 0 ? 'red' : 'green'}`}></span>
            Error rate: {stats.ingestion_jobs ? ((stats.failed_jobs / stats.ingestion_jobs) * 100).toFixed(1) : 0}%
          </span>
        </div>
      </section>

      {/* Two Column Section */}
      <div className="dashboard-grid">
        {/* Left Hand: System Status & Slack Quick Ref */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Status Panel */}
          <div className="glass-card">
            <h2 className="card-title">System Health</h2>
            <div className="status-list">
              <div className="status-row">
                <div className="status-info">
                  <span className="status-name">Cloud Run Service</span>
                  <span className="status-detail">FastAPI (v{apiVersion})</span>
                </div>
                <span className={`status-badge ${apiStatus}`}>
                  {apiStatus === 'ok' ? 'Online' : apiStatus === 'loading' ? 'Loading' : 'Offline'}
                </span>
              </div>
              
              <div className="status-row">
                <div className="status-info">
                  <span className="status-name">Supabase Connection</span>
                  <span className="status-detail">PostgreSQL + pgvector</span>
                </div>
                <span className={`status-badge ${dbStatus}`}>
                  {dbStatus === 'ok' ? 'Ready' : dbStatus === 'loading' ? 'Checking' : 'Disconnected'}
                </span>
              </div>

              <div className="status-row">
                <div className="status-info">
                  <span className="status-name">Slack Socket Mode</span>
                  <span className="status-detail">Listening to events</span>
                </div>
                <span className={`status-badge ${apiStatus}`}>
                  {apiStatus === 'ok' ? 'Active' : 'Offline'}
                </span>
              </div>
            </div>
          </div>

          {/* Slack Commands Reference */}
          <div className="glass-card">
            <h2 className="card-title">Slack Commands</h2>
            <div className="cmd-list">
              <div className="cmd-item">
                <span className="cmd-name">/knowledge add [url/text]</span>
                <span className="cmd-desc">Add a document to the knowledge base (auto-detects channel/personal scope).</span>
              </div>
              <div className="cmd-item">
                <span className="cmd-name">/knowledge ask [question]</span>
                <span className="cmd-desc">Ask a question with citation details matching your access scope.</span>
              </div>
              <div className="cmd-item">
                <span className="cmd-name">/knowledge search [query]</span>
                <span className="cmd-desc">Search indexed chunks with similarity score & source citation.</span>
              </div>
              <div className="cmd-item">
                <span className="cmd-name">/knowledge sync</span>
                <span className="cmd-desc">Synchronize Slack history for permissions mapping.</span>
              </div>
              <div className="cmd-item">
                <span className="cmd-name">/knowledge status</span>
                <span className="cmd-desc">View deployment metadata and database statistics.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Hand: Main Panel Tabs (Documents / Ingestion Jobs) */}
        <div className="glass-card" style={{ minHeight: '500px', display: 'flex', flexDirection: 'column' }}>
          <div className="card-title" style={{ borderBottom: 'none', marginBottom: '10px' }}>
            <div style={{ display: 'flex', gap: '16px' }}>
              <button 
                onClick={() => setActiveTab('documents')}
                className={`scope-tab ${activeTab === 'documents' ? 'active' : ''}`}
                style={{ fontSize: '0.95rem', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px' }}
              >
                📁 Documents
              </button>
              <button 
                onClick={() => setActiveTab('jobs')}
                className={`scope-tab ${activeTab === 'jobs' ? 'active' : ''}`}
                style={{ fontSize: '0.95rem', background: 'none', border: 'none', cursor: 'pointer', padding: '4px 8px' }}
              >
                ⚙️ Ingestion Jobs
              </button>
            </div>
          </div>

          {activeTab === 'documents' ? (
            <>
              {/* Documents Header Filter */}
              <div className="docs-header">
                <input 
                  type="text" 
                  placeholder="Search documents..."
                  className="search-box"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                
                <div className="scope-tabs">
                  {['all', 'org', 'team', 'personal'].map((scope) => (
                    <button 
                      key={scope}
                      className={`scope-tab ${scopeFilter === scope ? 'active' : ''}`}
                      onClick={() => setScopeFilter(scope)}
                    >
                      {scope}
                    </button>
                  ))}
                </div>
              </div>

              {/* Documents Table */}
              <div className="table-wrapper">
                {filteredDocuments.length > 0 ? (
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Title</th>
                        <th>Scope</th>
                        <th>Source</th>
                        <th>Created At</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredDocuments.map((doc) => (
                        <tr key={doc.id} onClick={() => handleViewDocDetails(doc.id)}>
                          <td className="doc-title-cell">{doc.title}</td>
                          <td>
                            <span className={`scope-badge ${doc.scope}`}>
                              {doc.scope}
                            </span>
                          </td>
                          <td>
                            {doc.source_type} 
                            {doc.tags && doc.tags.map((tag) => (
                              <span key={tag} className="tag-pill">{tag}</span>
                            ))}
                          </td>
                          <td>{formatDate(doc.created_at)}</td>
                          <td>
                            <button 
                              className="btn-primary" 
                              style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleViewDocDetails(doc.id);
                              }}
                            >
                              Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="empty-state">
                    No documents indexed yet. Try adding some documents in Slack via `/knowledge add`!
                  </div>
                )}
              </div>
            </>
          ) : (
            // Ingestion Jobs
            <div className="jobs-list">
              {jobs.length > 0 ? (
                jobs.map((job) => (
                  <div key={job.id} className="job-item">
                    <div className="job-header">
                      <span className="job-source">📄 {job.source_label}</span>
                      <span className={`status-badge ${job.status === 'ready' ? 'ok' : job.status === 'failed' ? 'error' : 'loading'}`}>
                        {job.status}
                      </span>
                    </div>
                    <div className="job-meta">
                      <span>Requested by: <code>{job.requested_by}</code></span>
                      <span className="job-time">Started: {formatDate(job.created_at)}</span>
                    </div>
                    {job.completed_at && (
                      <div className="job-meta" style={{ marginTop: '-4px' }}>
                        <span>Completed: {formatDate(job.completed_at)}</span>
                      </div>
                    )}
                    {job.error_message && (
                      <div className="job-error">
                        Error: {job.error_message}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  No ingestion jobs ran yet.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Document Detail Modal */}
      {selectedDoc && (
        <div className="detail-overlay" onClick={() => setSelectedDoc(null)}>
          <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-area">
                <h2>{selectedDoc.title}</h2>
                <span className={`scope-badge ${selectedDoc.scope}`}>
                  {selectedDoc.scope} Scope ({selectedDoc.scope_id || 'Global'})
                </span>
              </div>
              <button className="close-btn" onClick={() => setSelectedDoc(null)}>✖</button>
            </div>
            
            <div className="modal-body">
              {/* Meta Grid */}
              <div className="meta-grid">
                <div className="meta-item">
                  <span className="meta-label">Document ID</span>
                  <span className="meta-value">{selectedDoc.id}</span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Owner</span>
                  <span className="meta-value"><code>{selectedDoc.owner_user_id || 'N/A'}</code></span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Source URL</span>
                  <span className="meta-value">
                    {selectedDoc.source_url ? (
                      <a href={selectedDoc.source_url} target="_blank" rel="noopener noreferrer">
                        {selectedDoc.source_url}
                      </a>
                    ) : 'None'}
                  </span>
                </div>
                <div className="meta-item">
                  <span className="meta-label">Indexed On</span>
                  <span className="meta-value">{formatDate(selectedDoc.created_at)}</span>
                </div>
              </div>

              {/* Chunks Section */}
              <div className="chunks-section">
                <h3 className="chunks-title">Dense Embeddings ({selectedDocChunks.length} Chunks)</h3>
                
                {selectedDocChunks.map((chunk, idx) => (
                  <div key={chunk.id} className="chunk-card">
                    <div className="chunk-meta">
                      <span>Chunk Index #{chunk.chunk_index}</span>
                      <span>Token Estimate: {chunk.token_estimate}</span>
                    </div>
                    <pre className="chunk-text">{chunk.content}</pre>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Spinner Overlay for details loading */}
      {loadingDocDetail && (
        <div className="detail-overlay">
          <div style={{ fontSize: '1.2rem', color: '#fff', display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
            <span className="refresh-spin" style={{ fontSize: '2.5rem' }}>⏳</span>
            Fetching document chunks & metadata...
          </div>
        </div>
      )}
    </div>
  )
}

export default App
