import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  FileCheck, 
  Database, 
  HelpCircle, 
  TrendingUp, 
  CheckCircle, 
  AlertTriangle,
  Send,
  Loader,
  Upload,
  ArrowRight,
  ShieldAlert
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [brands, setBrands] = useState([]);
  const [products, setProducts] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  
  // Ask Think9 / Investigation States
  const [query, setQuery] = useState('Why has customer satisfaction declined over the last 30 days and what should we do?');
  const [investigating, setInvestigating] = useState(false);
  const [investigationResult, setInvestigationResult] = useState(null);
  
  // Historical Decision Memory States
  const [decisions, setDecisions] = useState([]);
  const [memorySearch, setMemorySearch] = useState('');

  // Dynamic Dashboard Metrics
  const [metrics, setMetrics] = useState({
    brands: 0,
    products: 0,
    documents: 0,
    decisions: 0,
    investigations: 0
  });

  // HITL Recommendation Edit state
  const [recommendationText, setRecommendationText] = useState('');
  const [approvalOwner, setApprovalOwner] = useState('John Doe (Product Lead)');
  
  // Fetch Brands
  useEffect(() => {
    fetch(`${API_BASE}/api/brands`)
      .then(res => res.json())
      .then(data => {
        setBrands(data);
        if (data.length > 0) {
          setSelectedBrand(data[0].name);
        }
      })
      .catch(err => console.error("Error fetching brands:", err));
  }, []);

  // Fetch Products when Brand changes
  useEffect(() => {
    if (!selectedBrand) return;
    const brand = brands.find(b => b.name === selectedBrand);
    if (!brand) return;

    fetch(`${API_BASE}/api/brands/${brand.id}/products`)
      .then(res => res.json())
      .then(data => {
        setProducts(data);
        if (data.length > 0) {
          setSelectedProduct(data[0].name);
        } else {
          setSelectedProduct('');
        }
      })
      .catch(err => console.error("Error fetching products:", err));
  }, [selectedBrand, brands]);

  // Fetch Decisions
  const fetchDecisions = (searchVal = '') => {
    fetch(`${API_BASE}/api/decisions?query=${searchVal}`)
      .then(res => res.json())
      .then(data => setDecisions(data))
      .catch(err => console.error("Error fetching decisions:", err));
  };

  const fetchMetrics = () => {
    fetch(`${API_BASE}/api/metrics`)
      .then(res => res.json())
      .then(data => setMetrics(data))
      .catch(err => console.error("Error fetching metrics:", err));
  };

  useEffect(() => {
    fetchDecisions();
    fetchMetrics();
  }, [activeTab]);

  // Trigger Investigation
  const handleInvestigate = (e) => {
    if (e) e.preventDefault();
    setInvestigating(true);
    setInvestigationResult(null);

    fetch(`${API_BASE}/api/investigate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        brand_name: selectedBrand,
        product_name: selectedProduct
      })
    })
      .then(res => res.json())
      .then(data => {
        setInvestigationResult(data);
        if (data.status === 'success') {
          setRecommendationText(data.recommendation_text || '');
        } else {
          setRecommendationText('');
        }
        setInvestigating(false);
        fetchMetrics();
      })
      .catch(err => {
        console.error("Error during investigation:", err);
        setInvestigating(false);
      });
  };

  // Submit Human Decision
  const handleDecisionSubmit = (status) => {
    if (!investigationResult) return;
    
    const decisionPayload = {
      brand_id: investigationResult.brand_id,
      product_id: investigationResult.product_id,
      problem: investigationResult.query,
      evidence: JSON.stringify(investigationResult.evidence),
      analysis: investigationResult.findings,
      recommendation: recommendationText,
      human_decision: status,
      owner: approvalOwner,
      status: "RESOLVED",
      outcome: status === 'APPROVED' ? "Approved — execution pending." :
               status === 'MODIFIED' ? "Decision approved with modifications." : "Decision rejected.",
      investigation_id: investigationResult.investigation_id,
      priority: "HIGH",
      decision_type: "QUALITY_CONTROL"
    };

    fetch(`${API_BASE}/api/decisions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(decisionPayload)
    })
      .then(res => res.json())
      .then(() => {
        alert(`Decision successfully recorded in Institutional Memory as: ${status}`);
        fetchDecisions();
        setActiveTab('memory');
      })
      .catch(err => console.error("Error saving decision:", err));
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="logo-container">
          <TrendingUp size={24} color="#3B82F6" />
          <span className="logo-text">THINK9 HUB</span>
        </div>
        <ul className="nav-links">
          <li>
            <div 
              className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <LayoutDashboard size={18} />
              <span>Dashboard</span>
            </div>
          </li>
          <li>
            <div 
              className={`nav-item ${activeTab === 'ask' ? 'active' : ''}`}
              onClick={() => setActiveTab('ask')}
            >
              <Search size={18} />
              <span>Ask Think9</span>
            </div>
          </li>
          <li>
            <div 
              className={`nav-item ${activeTab === 'recommendation' ? 'active' : ''}`}
              onClick={() => setActiveTab('recommendation')}
            >
              <FileCheck size={18} />
              <span>Review Panel</span>
            </div>
          </li>
          <li>
            <div 
              className={`nav-item ${activeTab === 'memory' ? 'active' : ''}`}
              onClick={() => setActiveTab('memory')}
            >
              <Database size={18} />
              <span>Decision Memory</span>
            </div>
          </li>
        </ul>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="header">
          <div>
            <h1>Think9 Intelligence Hub</h1>
            <p className="title-desc">"Every decision makes Think9 smarter."</p>
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            {/* Brand Dropdown Selector */}
            <select 
              className="search-input" 
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              value={selectedBrand} 
              onChange={(e) => setSelectedBrand(e.target.value)}
            >
              {brands.map(b => <option key={b.id} value={b.name}>{b.name}</option>)}
            </select>

            <select 
              className="search-input" 
              style={{ padding: '8px 16px', fontSize: '0.85rem' }}
              value={selectedProduct} 
              onChange={(e) => setSelectedProduct(e.target.value)}
            >
              {products.map(p => <option key={p.id} value={p.name}>{p.name}</option>)}
            </select>
          </div>
        </header>

        {/* Tab 1: Dashboard */}
        {activeTab === 'dashboard' && (
          <div>
            <div className="metrics-grid">
              <div className="metric-card">
                <div className="metric-header">
                  <span>ACTIVE BRANDS</span>
                  <TrendingUp size={16} color="#3B82F6" />
                </div>
                <div className="metric-value">{metrics.brands}</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span>RESOLVED DECISIONS</span>
                  <CheckCircle size={16} color="#10B981" />
                </div>
                <div className="metric-value">{metrics.decisions}</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span>INVESTIGATIONS RUN</span>
                  <TrendingUp size={16} color="#F59E0B" />
                </div>
                <div className="metric-value">{metrics.investigations}</div>
              </div>
              <div className="metric-card">
                <div className="metric-header">
                  <span>KNOWLEDGE SOURCES</span>
                  <Database size={16} color="#3B82F6" />
                </div>
                <div className="metric-value">{metrics.documents}</div>
              </div>
            </div>

            <div className="dashboard-grid">
              <div className="dashboard-card">
                <h3 className="card-title">Institutional Decisions Memory Log</h3>
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Brand</th>
                      <th>Problem Context</th>
                      <th>Human Decision</th>
                      <th>Owner</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.slice(0, 5).map(dec => (
                      <tr key={dec.id}>
                        <td>{dec.brand_name}</td>
                        <td>{dec.problem}</td>
                        <td>
                          <span className={`status-badge status-${dec.human_decision.toLowerCase()}`}>
                            {dec.human_decision}
                          </span>
                        </td>
                        <td>{dec.owner}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div>
                <div className="dashboard-card">
                  <h3 className="card-title"><ShieldAlert size={18} color="#EF4444" /> System Core Info</h3>
                  <p style={{ color: '#9CA3AF', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    Centralized platform managing multi-agent insights. Serves product quality records, SOP documents, and customer tickets globally across all 30+ brands.
                  </p>
                  <hr style={{ border: 'none', borderBottom: '1px solid var(--border-color)', margin: '16px 0' }} />
                  <p style={{ fontSize: '0.8rem', color: '#6B7280' }}>
                    Deterministic offline demo mode active when API keys are empty. Adjust keys in backend `.env` file to connect to live provider models.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Ask Think9 */}
        {activeTab === 'ask' && (
          <div>
            <div className="dashboard-card">
              <h3 className="card-title"><HelpCircle size={18} color="#3B82F6" /> Multi-Agent Investigation Console</h3>
              <form onSubmit={handleInvestigate} className="search-container">
                <input 
                  type="text" 
                  className="search-input" 
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about sales decline, product issue, reviews..."
                />
                <button type="submit" className="btn" disabled={investigating}>
                  {investigating ? <Loader className="animate-spin" size={18} /> : <Send size={18} />}
                  <span>{investigating ? 'Investigating...' : 'Investigate'}</span>
                </button>
              </form>
            </div>

            {investigating && (
              <div className="dashboard-card">
                <h3 className="card-title">Agent Workflow Executing...</h3>
                <div className="timeline">
                  <div className="timeline-item">
                    <div>
                      <div className="timeline-title">Research Agent</div>
                      <div className="timeline-desc">Retrieving customer support complaints, reviews, and documents...</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {investigationResult && (investigationResult.status === 'needs_context' || investigationResult.status === 'insufficient_evidence') && (
              <div className="dashboard-card" style={{ borderLeft: `4px solid ${investigationResult.status === 'needs_context' ? 'var(--color-warning)' : 'var(--color-danger)'}` }}>
                <h3 className="card-title">
                  {investigationResult.status === 'needs_context' ? (
                    <><AlertTriangle size={18} color="var(--color-warning)" /> Clarification Required</>
                  ) : (
                    <><ShieldAlert size={18} color="var(--color-danger)" /> Insufficient Knowledge Evidence</>
                  )}
                </h3>
                <p style={{ color: '#9CA3AF', fontSize: '0.95rem', lineHeight: '1.6' }}>
                  {investigationResult.message}
                </p>
              </div>
            )}

            {investigationResult && investigationResult.status === 'success' && (
              <div className="investigation-panel">
                <div className="dashboard-card">
                  <h3 className="card-title">Agent Activities</h3>
                  <div className="timeline">
                    {investigationResult.logs.map((log, index) => (
                      <div key={index} className="timeline-item completed">
                        <div>
                          <div className="timeline-title">{log.agent}</div>
                          <div className="timeline-desc">{log.message}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <div className="dashboard-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                      <span className="confidence-indicator" style={{ margin: 0 }}>
                        Evidence Strength: {investigationResult.confidence.score}% ({investigationResult.confidence.level})
                      </span>
                      <span style={{ fontSize: '0.8rem', color: '#6B7280' }}>
                        ID: {investigationResult.investigation_id}
                      </span>
                    </div>
                    
                    <h3 className="card-title" style={{ fontSize: '1.4rem' }}>{investigationResult.findings}</h3>

                    {/* Trend Box */}
                    <div style={{ margin: '16px 0', padding: '14px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                      <h4 style={{ fontSize: '0.9rem', color: 'var(--color-warning)', marginBottom: '8px' }}>
                        Trend Analysis: {investigationResult.trend_data.trend}
                      </h4>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', fontSize: '0.8rem' }}>
                        <div>
                          <span style={{ color: 'var(--text-secondary)' }}>Current 30 Days:</span>
                          <div>Neg Rate: {investigationResult.trend_data.current_period.negative_rate}% ({investigationResult.trend_data.current_period.negative} / {investigationResult.trend_data.current_period.total} reports)</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-secondary)' }}>Previous 30 Days:</span>
                          <div>Neg Rate: {investigationResult.trend_data.previous_period.negative_rate}% ({investigationResult.trend_data.previous_period.negative} / {investigationResult.trend_data.previous_period.total} reports)</div>
                        </div>
                      </div>
                      <div style={{ marginTop: '8px', fontSize: '0.8rem', color: investigationResult.trend_data.change_percentage_points > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                        Net Change: {investigationResult.trend_data.change_percentage_points > 0 ? '+' : ''}{investigationResult.trend_data.change_percentage_points} percentage points
                      </div>
                    </div>
                    
                    {/* Evidence Box with Citations */}
                    <div className="evidence-box">
                      <h4 style={{ fontSize: '0.9rem', marginBottom: '8px' }}>Supporting Evidence & Citations</h4>
                      <p style={{ fontSize: '0.85rem', color: '#9CA3AF' }}>
                        - Negative feedback matches: {investigationResult.evidence.negative_feedbacks_count} / {investigationResult.evidence.total_feedbacks_count} reports.
                      </p>
                      {investigationResult.evidence.documents_details && investigationResult.evidence.documents_details.length > 0 ? (
                        <div style={{ marginTop: '12px' }}>
                          <h5 style={{ fontSize: '0.8rem', color: '#E5E7EB', marginBottom: '6px' }}>Document Sources:</h5>
                          {investigationResult.evidence.documents_details.map((doc, idx) => (
                            <div key={idx} style={{ padding: '8px', background: 'rgba(255,255,255,0.04)', borderRadius: '4px', marginBottom: '6px', fontSize: '0.8rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#60A5FA', fontWeight: 'bold' }}>
                                <span>📄 {doc.filename} (ID: {doc.id})</span>
                                <span>Similarity: {Math.round(doc.score * 100)}%</span>
                              </div>
                              <p style={{ color: '#9CA3AF', margin: '4px 0 0 0', fontStyle: 'italic', fontSize: '0.75rem' }}>
                                "...{doc.content}..."
                              </p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={{ fontSize: '0.8rem', color: '#6B7280', marginTop: '6px' }}>
                          - No document chunks retrieved in RAG.
                        </p>
                      )}
                    </div>

                    <div style={{ marginTop: '24px' }}>
                      <button className="btn" onClick={() => setActiveTab('recommendation')}>
                        <span>Review Action Recommendations</span>
                        <ArrowRight size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Recommendation HITL */}
        {activeTab === 'recommendation' && (
          <div>
            {!investigationResult ? (
              <div className="dashboard-card" style={{ textAlign: 'center', padding: '60px' }}>
                <AlertTriangle size={48} color="#F59E0B" style={{ margin: '0 auto 16px' }} />
                <h3>No Active Investigation</h3>
                <p style={{ color: '#9CA3AF', marginTop: '8px' }}>
                  Please run an investigation from the "Ask Think9" page before reviewing recommendations.
                </p>
              </div>
            ) : (
              <div className="dashboard-card">
                <h3 className="card-title">Human-In-The-Loop Control Panel</h3>
                <p style={{ color: '#9CA3AF', fontSize: '0.9rem', marginBottom: '24px' }}>
                  You are reviewing proposed mitigation actions for <strong>{selectedBrand} {selectedProduct}</strong>. You can modify these recommendations below before storing.
                </p>

                <div className="confidence-indicator">
                  Evidence Strength: {investigationResult.confidence.score}% ({investigationResult.confidence.level})
                </div>

                {investigationResult.confidence.reasons && (
                  <div style={{ marginBottom: '24px', fontSize: '0.8rem', color: '#9CA3AF' }}>
                    <h5 style={{ color: '#E5E7EB', marginBottom: '6px' }}>Strength Factors:</h5>
                    <ul style={{ paddingLeft: '16px', margin: 0 }}>
                      {investigationResult.confidence.reasons.map((reason, idx) => (
                        <li key={idx} style={{ marginBottom: '4px' }}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div>
                  <label style={{ fontSize: '0.9rem', fontWeight: '600' }}>Reviewer Name / Owner</label>
                  <input 
                    type="text" 
                    className="input-field" 
                    value={approvalOwner} 
                    onChange={(e) => setApprovalOwner(e.target.value)} 
                  />

                  <label style={{ fontSize: '0.9rem', fontWeight: '600' }}>Edit Action Proposal</label>
                  <textarea 
                    className="input-field" 
                    rows={8}
                    value={recommendationText} 
                    onChange={(e) => setRecommendationText(e.target.value)}
                  />
                </div>

                <div className="action-row">
                  <button className="btn btn-success" onClick={() => handleDecisionSubmit('APPROVED')}>
                    APPROVE DECISION
                  </button>
                  <button className="btn btn-secondary" onClick={() => handleDecisionSubmit('MODIFIED')}>
                    MODIFY PROPOSAL
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDecisionSubmit('REJECTED')}>
                    REJECT PROPOSAL
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Decision Memory */}
        {activeTab === 'memory' && (
          <div>
            <div className="dashboard-card">
              <h3 className="card-title"><Database size={18} color="#10B981" /> Search Institutional Memory</h3>
              <div className="search-container">
                <input 
                  type="text" 
                  className="search-input" 
                  placeholder="Query packaging, shaker cup leakage, supplier name..."
                  value={memorySearch}
                  onChange={(e) => {
                    setMemorySearch(e.target.value);
                    fetchDecisions(e.target.value);
                  }}
                />
              </div>

              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Brand</th>
                    <th>Problem Context</th>
                    <th>Evidence</th>
                    <th>Mitigation Recommendation</th>
                    <th>Decision</th>
                    <th>Resolution Outcome</th>
                  </tr>
                </thead>
                <tbody>
                  {decisions.map(dec => (
                    <tr key={dec.id}>
                      <td><strong>{dec.brand_name}</strong></td>
                      <td>{dec.problem}</td>
                      <td style={{ fontSize: '0.8rem', color: '#9CA3AF' }}>
                        {dec.analysis}
                      </td>
                      <td>
                        <div style={{ whiteSpace: 'pre-line', fontSize: '0.85rem' }}>{dec.recommendation}</div>
                      </td>
                      <td>
                        <span className={`status-badge status-${dec.human_decision.toLowerCase()}`}>
                          {dec.human_decision}
                        </span>
                      </td>
                      <td style={{ color: '#10B981', fontSize: '0.85rem' }}>{dec.outcome}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
