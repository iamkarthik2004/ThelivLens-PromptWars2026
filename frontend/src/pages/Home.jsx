import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, AudioLines, BrainCircuit, CheckCircle2, Eye, FileSearch, Fingerprint, Image, LocateFixed, ShieldCheck, Sparkles, Video } from 'lucide-react';
import AnalysisWorkspace from '../components/AnalysisWorkspace';
import { MediaArtwork, Waveform } from '../components/Visuals';
import { getRecentAnalyses } from '../services/api';
const features=[['BrainCircuit','AI Detection','Advanced models detect AI-generated or manipulated content.'],['Eye','Explainable Results','Understand exactly why the system reached its assessment.'],['LocateFixed','Source Tracing','Find original sources and understand how content spread.'],['AudioLines','Multi-Format Support','Analyze images, videos, audio, and more.'],['Fingerprint','Evidence-Based Analysis','Combine multiple signals instead of a single prediction.'],['ShieldCheck','Built for Impact','Designed for journalists, researchers, and everyday citizens.']];
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
export default function Home({onAnalyze}){return <><main><section className="hero container"><div className="hero-copy"><span className="eyebrow">TRUTH IN A SYNTHETIC WORLD</span><h1>Detect.<br/>Explain.<br/><span>Verify.</span></h1><p className="hero-lead">AI-powered media verification for a more trustworthy internet.</p><p className="hero-description">Analyze images, audio, and video to detect potential AI generation or manipulation, understand the reasoning, and trace the original source — before you trust or share.</p><div className="hero-buttons"><Link className="btn" to="/analyze">Start Verifying <ArrowRight size={17}/></Link><a className="btn btn-outline" href="#how">Learn More</a></div></div><HeroVisual/></section><section className="container hero-stats">{[['3+','Media Types','Image, Video, Audio'],['AI','Powered Analysis','Advanced media intelligence'],['Trusted','For Journalists & Researchers','and everyday users']].map(s=><div key={s[0]}><b>{s[0]}</b><span>{s[1]}</span><small>{s[2]}</small></div>)}</section><section className="container" id="analyze"><AnalysisWorkspace onAnalyze={onAnalyze}/></section><section className="container features" id="how"><div className="section-heading"><span className="eyebrow">BUILT FOR CLARITY</span><h2>Evidence, not empty verdicts.</h2><p>Every assessment is designed to help you make a more informed next decision.</p></div><div className="feature-grid">{features.map(([icon,title,text])=>{const I={BrainCircuit,Eye,LocateFixed,AudioLines,Fingerprint,ShieldCheck}[icon];return <article className="feature-card" key={title}><span><I size={21}/></span><h3>{title}</h3><p>{text}</p><ArrowRight size={17}/></article>})}</div></section><Recent/><Extension/></main></>}
function HeroVisual(){return <div className="hero-visual"><div className="orb orb-one"/><div className="orb orb-two"/><div className="hero-main-card"><div className="card-top"><span><Sparkles size={14}/> Live signal scan</span><i/></div><MediaArtwork/><div className="card-caption"><span><Image size={15}/> image_01.jpg</span><b>87% synthetic likelihood</b></div></div><div className="floating-card video-card"><span className="mini-icon"><Video size={16}/></span><div><b>Video frames</b><small>12 signals analyzed</small></div><CheckCircle2 size={18}/></div><div className="floating-card audio-card"><span className="mini-icon purple"><AudioLines size={16}/></span><div><b>Voice analysis</b><Waveform/></div></div><span className="signal-badge ai">✦ AI Generated?</span><span className="signal-badge deepfake">◉ Deepfake?</span><span className="signal-badge authentic">✓ Authentic?</span></div>}
function Recent(){
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    getRecentAnalyses()
      .then(data => setAnalyses(Array.isArray(data) ? data.slice(0, 4) : []))
      .catch(() => setAnalyses([]))
      .finally(() => setLoading(false));
  }, []);
  return <section className="container recent"><div className="section-heading left"><span className="eyebrow">YOUR WORKSPACE</span><h2>Recent analyses</h2><p>{loading ? 'Loading analyses...' : analyses.length === 0 ? 'No analyses yet. Upload media to get started.' : 'Your recent verification results.'}</p></div><div className="recent-grid">{loading ? <p style={{gridColumn:'1/-1',opacity:0.6}}>Loading...</p> : analyses.length === 0 ? <p style={{gridColumn:'1/-1',opacity:0.6}}>No analyses found. Start by uploading a file.</p> : analyses.map((x,i) => <article key={x.id || i}><div className={`recent-thumb t${i}`}><FileSearch size={22}/></div><div><h3>{x.name || 'Untitled'}</h3><p>{formatTimeAgo(x.created_at)}</p></div><span className={`status-label ${getVerdictTone(x.overall_verdict)}`}>{getVerdictLabel(x.overall_verdict)}</span><b>{x.confidence || 0}%</b></article>)}</div></section>}
function Extension(){return <section className="container extension"><div><span className="eyebrow">TRUTHLENS EXTENSION</span><h2>Verify what you see, anywhere.</h2><p>See suspicious media while browsing? Verify it instantly with the TruthLens browser extension.</p><button className="btn">Add to Browser <ArrowRight size={17}/></button></div><div className="extension-popup"><header><ShieldCheck size={18}/> <b>TruthLens</b><span>•••</span></header><div className="popup-warning">⚠ <b>Potentially<br/>Manipulated</b></div><p>Confidence: <strong>86%</strong></p><hr/><small>Why?</small><ul><li>Synthetic artifacts</li><li>Missing metadata</li><li>Source uncertain</li></ul><button>View Full Analysis <ArrowRight size={15}/></button></div></section>}
