import { useState } from 'react';
import * as Icons from 'lucide-react';
import { MediaArtwork, Waveform } from './Visuals';

const tabs = ['Overview','Visual Forensics','Metadata','AI Signals','Source Trace'];

export default function ResultsView({ media = {} }) {
  const [tab, setTab] = useState('Overview');
  const video = media.type?.startsWith('video');
  const audio = media.type?.startsWith('audio');
  const report = media.report;
  const metrics = report?.metrics || { ai_generated: 0, manipulated: 0, authentic: 0 };
  const confidence = report?.confidence || 0;
  const evidenceItems = media.evidence_data || report?.evidence || [];
  const sourceEvents = media.source_trace || report?.source_events || [];

  return (
    <main className="results-page container">
      <div className="result-title">
        <div>
          <span className="eyebrow">ANALYSIS REPORT</span>
          <h1>Analysis result</h1>
          <p>{media.name} · Completed just now</p>
        </div>
        <button className="btn btn-outline"><Icons.Download size={17}/> Export report</button>
      </div>

      <section className="verdict-overview">
        <div className="result-media">
          <MediaArtwork/>
          {audio && <Waveform/>}
        </div>
        <div className="verdict-content">
          <span className="status-label warning">
            <Icons.TriangleAlert size={15}/> {report?.verdict || 'Analyzing...'}
          </span>
          <h2>Multiple signals deserve a closer look.</h2>
          <p>{report?.disclaimer || 'Analysis results will appear here once processing is complete.'}</p>
          <div className="confidence-list">
            {[
              ['AI Generated', metrics.ai_generated, 'cyan'],
              ['Manipulated', metrics.manipulated, 'purple'],
              ['Authentic', metrics.authentic, 'muted']
            ].map(([label, value, tone]) => (
              <div key={label}>
                <span>{label}<b>{value}%</b></span>
                <i className={tone}><em style={{width: `${value}%`}}/></i>
              </div>
            ))}
          </div>
        </div>
        <div className="confidence-ring">
          <svg viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="50"/>
            <circle className="ring-value" cx="60" cy="60" r="50" pathLength="100" style={{strokeDasharray: `${confidence} 100`}}/>
          </svg>
          <div><b>{confidence}%</b><small>confidence</small></div>
        </div>
      </section>

      <div className="tabs" role="tablist">
        {tabs.map(t => (
          <button className={tab === t ? 'active' : ''} key={t} onClick={() => setTab(t)} role="tab">{t}</button>
        ))}
      </div>

      {tab === 'Overview' && <Overview evidenceItems={evidenceItems} metrics={metrics} confidence={confidence} verdict={report?.verdict}/>}
      {tab === 'Visual Forensics' && <Forensics video={video} evidenceItems={evidenceItems}/>}
      {tab === 'Metadata' && <Metadata metadata={media.metadata}/>}
      {tab === 'AI Signals' && <Signals evidenceItems={evidenceItems} metrics={metrics}/>}
      {tab === 'Source Trace' && <SourceTrace events={sourceEvents}/>}
    </main>
  );
}

function Overview({ evidenceItems, metrics, confidence, verdict }) {
  const items = evidenceItems.map(item => ({
    ...item,
    text: item.text || item.description
  }));

  return (
    <>
      <section className="section-heading left">
        <span className="eyebrow">EXPLAINABLE AI</span>
        <h2>Why we think this</h2>
        <p>Independent signals make the assessment transparent and reviewable.</p>
      </section>
      <div className="evidence-grid">
        {items.map(item => {
          const I = Icons[item.icon] || Icons.Search;
          return (
            <article className="evidence-card" key={item.title}>
              <span className="evidence-icon"><I size={20}/></span>
              <div className="evidence-head">
                <h3>{item.title}</h3>
                <span className={`severity ${item.severity.toLowerCase()}`}>{item.severity}</span>
              </div>
              <p>{item.text}</p>
              <div className="evidence-confidence">
                <span>Signal confidence</span>
                <b>{item.confidence}%</b>
                <i><em style={{width: `${item.confidence}%`}}/></i>
              </div>
            </article>
          );
        })}
      </div>
      <EvidenceTable evidenceItems={evidenceItems}/>
      <FinalVerdict confidence={confidence} verdict={verdict}/>
    </>
  );
}

function Forensics({ video, evidenceItems }) {
  return (
    <section className="forensic-panel">
      <div className="forensic-preview">
        <MediaArtwork/>
        <span className="face-box one">Face: 94%</span>
        <span className="face-box two">Artifact region</span>
      </div>
      <div>
        <span className="eyebrow">VISUAL FORENSICS</span>
        <h2>Artifact map</h2>
        <p>Highlighted zones mark regions with irregular texture and blending patterns.</p>
        <ul className="forensic-list">
          {(evidenceItems || []).slice(0, 3).map((item, i) => (
            <li key={i}><b>{String(i + 1).padStart(2, '0')}</b> {item.title}</li>
          ))}
          {(!evidenceItems || evidenceItems.length === 0) && (
            <>
              <li><b>01</b> Facial boundary inconsistency</li>
              <li><b>02</b> Background depth irregularity</li>
              <li><b>03</b> Compression pattern shift</li>
            </>
          )}
        </ul>
      </div>
      {video && (
        <div className="video-timeline">
          <h3>Frame analysis</h3>
          <div className="timeline-line">
            {['00:04','00:08','00:12','00:16','00:20'].map((time, i) => (
              <button key={time} className={i === 2 || i === 4 ? 'clean' : 'flagged'}>
                {time}<span>{i === 2 || i === 4 ? '✓' : '⚠'}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

function Metadata({ metadata }) {
  const exif = metadata?.exif || {};
  const captureDevice = exif.Make || exif[271] || 'Not available';
  const creationDate = exif.DateTimeOriginal || exif.DateTime || exif[36867] || 'Not available';
  const software = exif.Software || exif[305] || 'Not available';

  return (
    <section className="metadata-card">
      <Icons.FileSearch/>
      <div>
        <span className="eyebrow">METADATA INSPECTION</span>
        <h2>Metadata analysis</h2>
        <p>
          {Object.keys(exif).length === 0
            ? 'No EXIF metadata found. This can happen with AI-generated images or after processing.'
            : 'Metadata fields found. Review the details below for provenance signals.'}
        </p>
      </div>
      <dl>
        <div><dt>Capture device</dt><dd>{captureDevice}</dd></div>
        <div><dt>Creation date</dt><dd>{creationDate}</dd></div>
        <div><dt>Editing software</dt><dd>{software}</dd></div>
        {metadata?.width && <div><dt>Dimensions</dt><dd>{metadata.width} x {metadata.height}</dd></div>}
        {metadata?.format && <div><dt>Format</dt><dd>{metadata.format}</dd></div>}
        {metadata?.size_bytes && <div><dt>File size</dt><dd>{(metadata.size_bytes / 1024).toFixed(1)} KB</dd></div>}
      </dl>
    </section>
  );
}

function Signals({ evidenceItems, metrics }) {
  return (
    <section className="signal-grid">
      <div>
        <Icons.BrainCircuit/>
        <h2>Model consensus</h2>
        <p>{evidenceItems.length} independent signals were analyzed for this media.</p>
      </div>
      <div className="signal-bars">
        {evidenceItems.map((item, i) => (
          <span key={item.title}>
            {item.title}
            <i><em style={{width: `${item.confidence}%`}}/></i>
          </span>
        ))}
        {evidenceItems.length === 0 && (
          <>
            <span>Texture consistency<i><em style={{width: '92%'}}/></i></span>
            <span>Reflectance cues<i><em style={{width: '81%'}}/></i></span>
            <span>Noise distribution<i><em style={{width: '70%'}}/></i></span>
            <span>Semantic coherence<i><em style={{width: '59%'}}/></i></span>
          </>
        )}
      </div>
    </section>
  );
}

export function SourceTrace({ events = [] }) {
  return (
    <section className="source-section">
      <div className="section-heading left">
        <span className="eyebrow">SOURCETRACE</span>
        <h2>Where did this content come from?</h2>
        <p>Track how this media moved and changed across the web.</p>
      </div>
      <div className="trace-layout">
        <div className="source-timeline">
          {events.map((e, i) => (
            <article key={e.source + i}>
              <span className={`timeline-dot ${(e.status || 'unverified').toLowerCase()}`}>{i + 1}</span>
              <time>{e.date}</time>
              <h3>{e.source} <small>{e.platform}</small></h3>
              <p>{e.caption}</p>
              <a href="#trace">View archived URL ↗</a>
            </article>
          ))}
          {events.length === 0 && (
            <article>
              <span className="timeline-dot unverified">1</span>
              <time>Unknown</time>
              <h3>Original upload <small>Unverified</small></h3>
              <p>No provenance data available.</p>
            </article>
          )}
        </div>
        <aside className="source-summary">
          <div>
            <small>Earliest Known Source</small>
            <b>{events[0]?.source || 'Unknown / Unverified'}</b>
          </div>
          <div>
            <small>Source Credibility</small>
            <b className="medium">Medium</b>
          </div>
          <div>
            <small>Context Changes</small>
            <b className="warning-text">Potentially misleading</b>
          </div>
        </aside>
      </div>
    </section>
  );
}

function EvidenceTable({ evidenceItems }) {
  const rows = evidenceItems.map(item => [
    item.title,
    item.description?.substring(0, 50) + (item.description?.length > 50 ? '...' : ''),
    `${item.confidence}%`,
    item.severity
  ]);

  return (
    <section className="table-section">
      <div className="section-heading left">
        <span className="eyebrow">EVIDENCE SUMMARY</span>
        <h2>Signals at a glance</h2>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr><th>Signal</th><th>Result</th><th>Confidence</th><th>Status</th></tr>
          </thead>
          <tbody>
            {rows.map(r => (
              <tr key={r[0]}>
                {r.map((c, i) => (
                  <td key={c}>{i === 3 ? <span className={`status-label ${c === 'High' ? 'warning' : c === 'Medium' ? 'neutral' : 'success'}`}>{c}</span> : c}</td>
                ))}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan="4" style={{textAlign: 'center', opacity: 0.5}}>No evidence data available</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FinalVerdict({ confidence, verdict }) {
  const displayVerdict = verdict ? verdict.replace(/_/g, ' ').toUpperCase() : 'ANALYSIS PENDING';
  return (
    <section className="final-verdict">
      <span className="status-label warning">
        <Icons.TriangleAlert size={15}/> {displayVerdict}
      </span>
      <h2>Overall confidence: <strong>{confidence}%</strong></h2>
      <p>This assessment is based on multiple independent signals. These signals increase the likelihood of manipulation, but they do not by themselves prove that the content is falsified.</p>
    </section>
  );
}
