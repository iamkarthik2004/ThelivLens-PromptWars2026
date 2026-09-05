import * as React from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from './hooks/useTheme';
import { analyzeMedia, analyzeUrl } from './services/api';
import Navbar from './components/Navbar'; import Footer from './components/Footer'; import Copilot from './components/Copilot';
import Home from './pages/Home'; import Analyze from './pages/Analyze'; import ResultsView from './components/ResultsView'; import { About, HowItWorks, Resources, SourcePage } from './pages/InfoPages';
export default function App(){const {theme,toggleTheme}=useTheme();const navigate=useNavigate(); const [analysis,setAnalysis]=React.useState(null); const run=async(payload)=>{const result=payload.url?await analyzeUrl(payload.url):await analyzeMedia(payload);setAnalysis(result);navigate('/results',{state:{media:result}})};return <><a href="#main-content" className="skip-link">Skip to main content</a><Navbar theme={theme} toggleTheme={toggleTheme}/><main id="main-content"><Routes><Route path="/" element={<Home onAnalyze={run}/>}/><Route path="/analyze" element={<Analyze onAnalyze={run}/>}/><Route path="/results" element={<ResultsRoute/>}/><Route path="/source-trace" element={<SourcePage/>}/><Route path="/how-it-works" element={<HowItWorks/>}/><Route path="/resources" element={<Resources/>}/><Route path="/about" element={<About/>}/></Routes></main><Footer/><Copilot analysis={analysis}/></>}
function ResultsRoute(){const {state}=useLocation();return <ResultsView media={state?.media}/>}
