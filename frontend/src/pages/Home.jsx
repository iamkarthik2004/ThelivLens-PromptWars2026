import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, AudioLines, BrainCircuit, CheckCircle2, Eye, FileSearch, Fingerprint, Image, LocateFixed, ShieldCheck, Sparkles, Video } from 'lucide-react';
import AnalysisWorkspace from '../components/AnalysisWorkspace';
import { MediaArtwork, Waveform } from '../components/Visuals';
import { getRecentAnalyses } from '../services/api';
const features=[['BrainCircuit','AI Detection','Advanced forensic models detect AI-generated or manipulated content by analyzing pixel patterns, noise signatures, and compression artifacts.'],['Eye','Explainable Results','Understand exactly why the system reached its assessment. Every signal comes with confidence levels and plain-language explanations.'],['LocateFixed','Source Tracing','Find original sources and understand how content spread. Trace the provenance chain and detect context changes across the web.'],['AudioLines','Multi-Format Support','Analyze images, videos, and audio in all major formats. Each media type receives specialized forensic analysis.'],['Fingerprint','Evidence-Based Analysis','Combine multiple independent signals instead of a single prediction. Cross-reference visual, metadata, and frequency domain indicators.'],['ShieldCheck','Built for Impact','Designed for journalists, researchers, fact-checkers, and everyday citizens who need to verify media before sharing.']];
function formatTimeAgo(dateStr) {
  if (!dateStr) return 'Unknown';
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}
function getVerdictTone(verdict) {
  if (!verdict) return 'neutral';
  const v = verdict.toLowerCase();
  if (v.includes('likely_ai') || v.includes('ai_generated')) return 'warning';
  if (v.includes('manipulated')) return 'danger';
  if (v.includes('authentic') || v.includes('probably')) return 'success';
  return 'neutral';
}
function getVerdictLabel(verdict) {
  if (!verdict) return 'Unknown';
  return verdict.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
export default function Home({onAnalyze}){return <><main><section className="hero container"><div className="hero-copy"><span className="eyebrow">TRUTH IN A SYNTHETIC WORLD</span><h1>Detect.<br/>Explain.<br/><span>Verify.</span></h1><p className="hero-lead">AI-generated media is everywhere. ThelivLens helps you see through it.</p><p className="hero-description">Deepfakes, synthetic images, and manipulated audio are becoming indistinguishable from reality. ThelivLens analyzes visual forensics, metadata authenticity, and source provenance to help you make informed decisions about the media you encounter — before you trust or share.</p><div className="hero-buttons"><Link className="btn" to="/analyze">Start Verifying <ArrowRight size={17} aria-hidden="true"/></Link><a className="btn btn-outline" href="#how">Learn More</a></div></div><HeroVisual/></section><section className="container hero-stats" aria-label="Key statistics">{[['3+','Media Types','Image, Video, Audio'],['AI','Powered Analysis','Advanced media intelligence'],['Trusted','For Journalists & Researchers','and everyday users']].map(s=><div key={s[0]}><b>{s[0]}</b><span>{s[1]}</span><small>{s[2]}</small></div>)}</section><section className="container" id="analyze"><AnalysisWorkspace onAnalyze={onAnalyze}/></section><section className="container features" id="how"><div className="section-heading"><span className="eyebrow">BUILT FOR CLARITY</span><h2>Evidence, not empty verdicts.</h2><p>Every assessment is designed to help you make a more informed next decision.</p></div><div className="feature-grid" role="list" aria-label="Platform features">{features.map(([icon,title,text])=>{const I={BrainCircuit,Eye,LocateFixed,AudioLines,Fingerprint,ShieldCheck}[icon];return <article className="feature-card" key={title} role="listitem"><span aria-hidden="true"><I size={21}/></span><h3>{title}</h3><p>{text}</p><ArrowRight size={17} aria-hidden="true"/></article>})}</div></section><Recent/><Extension/></main></>}
function HeroVisual(){return <div className="hero-visual" aria-hidden="true"><div className="orb orb-one"/><div className="orb orb-two"/><div className="hero-main-card"><div className="card-top"><span><Sparkles size={14}/> Live signal scan</span><i/></div><MediaArtwork/><div className="card-caption"><span><Image size={15}/> image_01.jpg</span><b>87% synthetic likelihood</b></div></div><div className="floating-card video-card"><span className="mini-icon"><Video size={16}/></span><div><b>Video frames</b><small>12 signals analyzed</small></div><CheckCircle2 size={18}/></div><div className="floating-card audio-card"><span className="mini-icon purple"><AudioLines size={16}/></span><div><b>Voice analysis</b><Waveform/></div></div><span className="signal-badge ai">✦ AI Generated?</span><span className="signal-badge deepfake">◉ Deepfake?</span><span className="signal-badge authentic">✓ Authentic?</span></div>}
function Recent(){
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getRecentAnalyses()
      .then(data => setAnalyses(Array.isArray(data) ? data.slice(0, 4) : []))
      .catch(() => setAnalyses([]))
      .finally(() => setLoading(false));
  }, []);
  return <section className="container recent" aria-label="Recent analyses"><div className="section-heading left"><span className="eyebrow">YOUR WORKSPACE</span><h2>Recent analyses</h2><p>{loading ? 'Loading analyses...' : analyses.length === 0 ? 'No analyses yet. Upload media to get started.' : 'Your recent verification results.'}</p></div><div className="recent-grid" role="list">{loading ? <p style={{gridColumn:'1/-1',opacity:0.6}} aria-live="polite">Loading...</p> : analyses.length === 0 ? <p style={{gridColumn:'1/-1',opacity:0.6}}>No analyses found. Start by uploading a file.</p> : analyses.map((x,i) => <article key={x.id || i} role="listitem"><div className={`recent-thumb t${i}`} aria-hidden="true"><FileSearch size={22}/></div><div><h3>{x.name || 'Untitled'}</h3><p>{formatTimeAgo(x.created_at)}</p></div><span className={`status-label ${getVerdictTone(x.overall_verdict)}`}>{getVerdictLabel(x.overall_verdict)}</span><b>{x.confidence || 0}%</b></article>)}</div></section>}
function Extension(){return <section className="container extension" aria-label="Browser extension"><div><span className="eyebrow">TRUTHLENS EXTENSION</span><h2>Verify what you see, anywhere.</h2><p>See suspicious media while browsing? Verify it instantly with the ThelivLens browser extension.</p><button className="btn" aria-label="Add ThelivLens browser extension">Add to Browser <ArrowRight size={17} aria-hidden="true"/></button></div><div className="extension-popup" aria-label="Extension preview popup"><header><ShieldCheck size={18} aria-hidden="true"/> <b>ThelivLens</b><span>•••</span></header><div className="popup-warning">⚠ <b>Potentially<br/>Manipulated</b></div><p>Confidence: <strong>86%</strong></p><hr/><small>Why?</small><ul><li>Synthetic artifacts</li><li>Missing metadata</li><li>Source uncertain</li></ul><button aria-label="View full analysis from extension">View Full Analysis <ArrowRight size={15} aria-hidden="true"/></button></div></section>}