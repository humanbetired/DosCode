import { useState, useRef } from 'react'
import { Upload, GitPullRequest, CheckCircle, XCircle,
         AlertTriangle, Loader2, ChevronRight, Shield,
         Code2, Zap, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

// ── Severity config ────────────────────────────────────────────────────
const SEVERITY = {
  critical: { color: '#EF4444', bg: 'rgba(239,68,68,0.1)', label: 'Critical' },
  high:     { color: '#F97316', bg: 'rgba(249,115,22,0.1)', label: 'High' },
  medium:   { color: '#EAB308', bg: 'rgba(234,179,8,0.1)',  label: 'Medium' },
  low:      { color: '#22C55E', bg: 'rgba(34,197,94,0.1)',  label: 'Low' },
  unknown:  { color: '#8A8F98', bg: 'rgba(138,143,152,0.1)', label: 'Unknown' },
}

const NODE_ICONS = {
  classify_code:           <Code2 size={14} />,
  run_tools:               <Zap size={14} />,
  findings_evaluator:      <Shield size={14} />,
  style_rag:               <BookOpen size={14} />,
  generate_summary:        <CheckCircle size={14} />,
  request_human_approval:  <AlertTriangle size={14} />,
}

// ── Sub-components ─────────────────────────────────────────────────────
function AgentStep({ step }) {
  const isActive   = step.status === 'active'
  const isComplete = step.status === 'complete'

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '12px',
      padding: '10px 0',
      borderBottom: '1px solid rgba(255,255,255,0.04)',
      opacity: step.status === 'pending' ? 0.35 : 1,
      transition: 'opacity 0.3s ease',
    }}>
      {/* Icon */}
      <div style={{
        width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: isActive  ? 'rgba(94,106,210,0.15)'
                  : isComplete ? 'rgba(34,197,94,0.1)'
                  : 'rgba(255,255,255,0.04)',
        border: `1px solid ${
          isActive   ? 'rgba(94,106,210,0.4)'
        : isComplete ? 'rgba(34,197,94,0.3)'
        : 'rgba(255,255,255,0.06)'}`,
        color: isActive  ? '#828FFF'
             : isComplete ? '#22C55E'
             : '#8A8F98',
        transition: 'all 0.3s ease',
      }}>
        {isActive ? <Loader2 size={13} style={{animation:'spin 1s linear infinite'}} />
                  : (NODE_ICONS[step.node] || <ChevronRight size={13} />)}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 500,
          color: isComplete ? '#F7F8F8' : isActive ? '#F7F8F8' : '#62666D',
        }}>
          {step.message}
        </div>
        {step.detail && (
          <div style={{ fontSize: 12, color: '#62666D', marginTop: 3 }}>
            {step.detail}
          </div>
        )}
      </div>

      {/* Status badge */}
      {isComplete && (
        <div style={{ fontSize: 11, color: '#22C55E', flexShrink: 0, marginTop: 2 }}>
          done
        </div>
      )}
    </div>
  )
}

function SeverityBadge({ level }) {
  const s = SEVERITY[level] || SEVERITY.unknown
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      padding: '3px 10px', borderRadius: 9999,
      background: s.bg, border: `1px solid ${s.color}33`,
      color: s.color, fontSize: 12, fontWeight: 510,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: '50%',
        background: s.color,
      }}/>
      {s.label}
    </span>
  )
}

function ReviewSummary({ summary, severity, loopCount, sessionId, onApprove }) {
  const [approving, setApproving] = useState(false)
  const [decision, setDecision] = useState(null)
  const [postResult, setPostResult] = useState(null)

  const handleApprove = async (approved) => {
    setApproving(true)
    try {
      const res = await fetch(
        `/api/review/approve?session_id=${sessionId}&approved=${approved}`,
        { method: 'POST' }
      )
      const data = await res.json()
      setDecision(approved ? 'approved' : 'rejected')
      setPostResult(data)
      onApprove?.(data)
    } catch (e) {
      setPostResult({ error: e.message })
    } finally {
      setApproving(false)
    }
  }

  return (
    <div style={{
      background: '#0F1011',
      border: '1px solid rgba(255,255,255,0.05)',
      borderRadius: 8, overflow: 'hidden',
      marginTop: 24,
    }}>
      {/* Header */}
      <div style={{
        padding: '14px 24px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 590, color: '#F7F8F8' }}>
            Review Summary
          </span>
          <SeverityBadge level={severity} />
        </div>
        {loopCount > 0 && (
          <span style={{ fontSize: 11, color: '#62666D' }}>
            {loopCount} RAG loop{loopCount > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {/* Summary — rendered markdown */}
      <div style={{ padding: '20px 24px' }}>
        <div style={{
          fontSize: 13, lineHeight: '22px', color: '#B4BCD0',
        }}>
          <ReactMarkdown
            components={{
              h1: ({children}) => (
                <h1 style={{
                  fontSize: 16, fontWeight: 590, color: '#F7F8F8',
                  marginBottom: 12, marginTop: 20,
                  paddingBottom: 8,
                  borderBottom: '1px solid rgba(255,255,255,0.06)'
                }}>{children}</h1>
              ),
              h2: ({children}) => (
                <h2 style={{
                  fontSize: 14, fontWeight: 590, color: '#F7F8F8',
                  marginBottom: 8, marginTop: 16,
                }}>{children}</h2>
              ),
              h3: ({children}) => (
                <h3 style={{
                  fontSize: 13, fontWeight: 510, color: '#D4D8E0',
                  marginBottom: 6, marginTop: 12,
                }}>{children}</h3>
              ),
              p: ({children}) => (
                <p style={{
                  marginBottom: 10, color: '#B4BCD0',
                  fontSize: 13, lineHeight: '22px',
                }}>{children}</p>
              ),
              ul: ({children}) => (
                <ul style={{
                  paddingLeft: 16, marginBottom: 10,
                  display: 'flex', flexDirection: 'column', gap: 4,
                }}>{children}</ul>
              ),
              li: ({children}) => (
                <li style={{
                  color: '#B4BCD0', fontSize: 13,
                  lineHeight: '20px', listStyleType: 'none',
                  paddingLeft: 12, position: 'relative',
                }}>
                  <span style={{
                    position: 'absolute', left: 0,
                    color: '#5E6AD2', fontSize: 10, top: 2,
                  }}>▸</span>
                  {children}
                </li>
              ),
              strong: ({children}) => (
                <strong style={{
                  fontWeight: 590, color: '#F7F8F8',
                }}>{children}</strong>
              ),
              code: ({children}) => (
                <code style={{
                  fontFamily: "'Berkeley Mono', 'SF Mono', monospace",
                  fontSize: 12, color: '#828FFF',
                  background: 'rgba(94,106,210,0.1)',
                  padding: '1px 6px', borderRadius: 4,
                }}>{children}</code>
              ),
              blockquote: ({children}) => (
                <blockquote style={{
                  borderLeft: '2px solid #5E6AD2',
                  paddingLeft: 12, marginLeft: 0,
                  color: '#8A8F98', fontStyle: 'italic',
                }}>{children}</blockquote>
              ),
            }}
          >
            {summary}
          </ReactMarkdown>
        </div>
      </div>

      {/* HITL approval */}
      {!decision && (
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', gap: 12,
        }}>
          <span style={{ fontSize: 12, color: '#62666D' }}>
            Post this review to GitHub PR?
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => handleApprove(false)}
              disabled={approving}
              style={{
                height: 32, padding: '0 12px', borderRadius: 9999,
                border: '1px solid rgba(255,255,255,0.08)',
                background: 'transparent', color: '#8A8F98',
                fontSize: 13, cursor: 'pointer',
              }}
            >
              Cancel
            </button>
            <button
              onClick={() => handleApprove(true)}
              disabled={approving}
              style={{
                height: 32, padding: '0 12px', borderRadius: 9999,
                border: '1px solid #E5E5E6',
                background: '#E5E5E6', color: '#08090A',
                fontSize: 13, fontWeight: 510, cursor: 'pointer',
                boxShadow: 'rgba(0,0,0,0.08) 0px 0px 1px 0px',
                display: 'flex', alignItems: 'center', gap: 6,
              }}
            >
              {approving
                ? <><Loader2 size={12} style={{animation:'spin 1s linear infinite'}}/> Posting...</>
                : <><GitPullRequest size={12}/> Post to GitHub</>
              }
            </button>
          </div>
        </div>
      )}

      {/* Decision result */}
      {decision && (
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.05)',
        }}>
          {/* Status bar */}
          <div style={{
            padding: '12px 24px',
            display: 'flex', alignItems: 'center', gap: 8,
            background: decision === 'approved'
              ? 'rgba(34,197,94,0.06)'
              : 'rgba(138,143,152,0.06)',
            borderBottom: postResult ? '1px solid rgba(255,255,255,0.05)' : 'none',
          }}>
            {decision === 'approved'
              ? <><CheckCircle size={14} color="#22C55E"/>
                  <span style={{fontSize:13, color:'#22C55E'}}>
                    Review posted to GitHub PR
                  </span>
                </>
              : <><XCircle size={14} color="#8A8F98"/>
                  <span style={{fontSize:13, color:'#8A8F98'}}>
                    Review cancelled — not posted
                  </span>
                </>
            }
          </div>

          {/* Post result detail */}
          {postResult && !postResult.error && decision === 'approved' && (
            <div style={{
              padding: '12px 24px',
              display: 'flex', flexDirection: 'column', gap: 6,
            }}>
              <div style={{fontSize:11, color:'#62666D', textTransform:'uppercase', letterSpacing:'0.05em', fontWeight:590}}>
                Result
              </div>
              <div style={{
                fontSize: 13, color: '#B4BCD0', lineHeight: '20px',
                fontFamily: "'Berkeley Mono', monospace",
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid rgba(255,255,255,0.06)',
                borderRadius: 6, padding: '10px 14px',
              }}>
                {postResult.message || JSON.stringify(postResult, null, 2)}
              </div>
            </div>
          )}

          {/* Error */}
          {postResult?.error && (
            <div style={{
              padding: '12px 24px',
              fontSize: 13, color: '#EF4444',
              fontFamily: "'Berkeley Mono', monospace",
            }}>
              Error: {postResult.error}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main App ───────────────────────────────────────────────────────────
export default function App() {
  const [file, setFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isReviewing, setIsReviewing] = useState(false)
  const [steps, setSteps] = useState([])
  const [toolResults, setToolResults] = useState([])
  const [reviewResult, setReviewResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)
  const sessionId = useRef(`session-${Date.now()}`)

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  const updateStep = (node, status, detail = null) => {
    setSteps(prev => {
      const existing = prev.find(s => s.node === node)
      if (existing) {
        return prev.map(s => s.node === node ? { ...s, status, detail } : s)
      }
      return prev
    })
  }

  const addStep = (node, message, icon) => {
    setSteps(prev => {
      if (prev.find(s => s.node === node)) return prev
      return [...prev, { node, message, icon, status: 'active', detail: null }]
    })
  }

  const startReview = async () => {
    if (!file) return
    setIsReviewing(true)
    setSteps([])
    setToolResults([])
    setReviewResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('session_id', sessionId.current)

    try {
      const res = await fetch('/api/review/stream', {
        method: 'POST', body: formData
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (line.startsWith('data:')) {
            try {
              const raw = line.slice(5).trim()
              const msg = JSON.parse(raw)

              // find event type from previous line — handled via EventSourceResponse
              if (msg.node) {
                // node_start
                addStep(msg.node, msg.message, msg.icon)
              } else if (msg.tools) {
                setToolResults(msg.tools)
                updateStep('run_tools', 'active', msg.tools.join(' · '))
              } else if (msg.level) {
                updateStep('findings_evaluator', 'active', `Severity: ${msg.level}`)
              } else if (msg.summary !== undefined) {
                // review_complete
                setReviewResult({
                  summary: msg.summary,
                  severity: msg.severity,
                  loopCount: msg.loop_count,
                })
                setSteps(prev => prev.map(s => ({ ...s, status: 'complete' })))
              }
            } catch (_) {}
          }

          if (line.startsWith('event:')) {
            const eventType = line.slice(6).trim()
            if (eventType === 'node_complete') {
              // will be handled in next data line — mark previous active as complete
            }
          }
        }
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setIsReviewing(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#08090A' }}>

      {/* Nav */}
      <nav style={{
        height: 72, borderBottom: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', alignItems: 'center',
        padding: '0 32px', gap: 12,
        boxShadow: 'rgba(0,0,0,0.4) 0px 1px 0px 0px',
        position: 'sticky', top: 0, zIndex: 10,
        background: '#0F1011',
      }}>
        <div style={{
          width: 24, height: 24, borderRadius: 6,
          background: '#5E6AD2',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <GitPullRequest size={13} color="#fff" />
        </div>
        <span style={{ fontSize: 14, fontWeight: 510, color: '#F7F8F8' }}>
          DosCode
        </span>
        <span style={{
          fontSize: 11, color: '#5E6AD2',
          background: 'rgba(94,106,210,0.1)',
          border: '1px solid rgba(94,106,210,0.2)',
          padding: '2px 8px', borderRadius: 9999,
          marginLeft: 4,
        }}>
          NgeReviewYuk
        </span>
      </nav>

      {/* Main content */}
      <main style={{ maxWidth: 760, margin: '0 auto', padding: '48px 24px' }}>

        {/* Hero */}
        <div style={{ marginBottom: 40 }}>
          <h1 style={{
            fontSize: 32, fontWeight: 510, color: '#F7F8F8',
            lineHeight: '40px', marginBottom: 10,
          }}>
            Code Review
          </h1>
          <p style={{ fontSize: 15, color: '#62666D', lineHeight: '24px' }}>
            Drop a Python file and let the agent analyze lint, security, 
            complexity, and cross-check your team's style guide.
          </p>
        </div>

        {/* Upload area */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `1px dashed ${isDragging ? '#5E6AD2' : 'rgba(255,255,255,0.1)'}`,
            borderRadius: 8, padding: '32px 24px',
            textAlign: 'center', cursor: 'pointer',
            background: isDragging ? 'rgba(94,106,210,0.05)' : 'rgba(255,255,255,0.02)',
            transition: 'all 0.2s ease',
            marginBottom: 24,
          }}
        >
          <input
            ref={fileInputRef}
            type="file" accept=".py,.js,.ts"
            style={{ display: 'none' }}
            onChange={(e) => setFile(e.target.files[0])}
          />
          <Upload size={20} color={file ? '#5E6AD2' : '#62666D'} style={{ margin: '0 auto 12px' }} />
          {file ? (
            <>
              <div style={{ fontSize: 14, fontWeight: 510, color: '#F7F8F8' }}>
                {file.name}
              </div>
              <div style={{ fontSize: 12, color: '#62666D', marginTop: 4 }}>
                {(file.size / 1024).toFixed(1)} KB · Click to change
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 14, color: '#8A8F98' }}>
                Drop a file or click to browse
              </div>
              <div style={{ fontSize: 12, color: '#62666D', marginTop: 4 }}>
                .py · .js · .ts
              </div>
            </>
          )}
        </div>

        {/* Start button */}
        <button
          onClick={startReview}
          disabled={!file || isReviewing}
          style={{
            height: 32, padding: '0 16px',
            borderRadius: 9999,
            background: (!file || isReviewing) ? 'rgba(229,229,230,0.3)' : '#E5E5E6',
            color: '#08090A',
            border: '1px solid #E5E5E6',
            fontSize: 13, fontWeight: 510,
            cursor: (!file || isReviewing) ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', gap: 6,
            boxShadow: 'rgba(0,0,0,0.08) 0px 0px 1px 0px',
            transition: 'all 0.2s ease',
            marginBottom: 32,
          }}
        >
          {isReviewing && <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />}
          {isReviewing ? 'Reviewing...' : 'Start Review'}
        </button>

        {/* Agent trace */}
        {steps.length > 0 && (
          <div style={{
            background: '#0F1011',
            border: '1px solid rgba(255,255,255,0.05)',
            borderRadius: 8, marginBottom: 24,
            overflow: 'hidden',
          }}>
            <div style={{
              padding: '12px 20px',
              borderBottom: '1px solid rgba(255,255,255,0.05)',
              fontSize: 11, fontWeight: 590,
              color: '#62666D', letterSpacing: '0.05em',
              textTransform: 'uppercase',
            }}>
              Agent Trace
            </div>
            <div style={{ padding: '4px 20px 8px' }}>
              {steps.map((step, i) => <AgentStep key={i} step={step} />)}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            padding: '14px 20px', borderRadius: 8,
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.2)',
            color: '#EF4444', fontSize: 13,
          }}>
            {error}
          </div>
        )}

        {/* Review result + HITL */}
        {reviewResult && (
          <ReviewSummary
            summary={reviewResult.summary}
            severity={reviewResult.severity}
            loopCount={reviewResult.loopCount}
            sessionId={sessionId.current}
            onApprove={(data) => console.log('Approval result:', data)}
          />
        )}
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        button:hover:not(:disabled) { opacity: 0.88; }
      `}</style>
    </div>
  )
}