import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Menu, Moon, ShieldCheck, Sun, X } from 'lucide-react';

const links = [['Home','/'], ['Analyze','/analyze'], ['How It Works','/how-it-works'], ['Resources','/resources'], ['About','/about']];
export default function Navbar({ theme, toggleTheme }) {
  const [open, setOpen] = useState(false);
  return <header className="nav-wrap"><nav className="navbar container" aria-label="Main navigation">
    <Link className="brand" to="/"><span className="brand-mark"><ShieldCheck size={21}/></span><span><strong>ThelivLens</strong><small>Detect. Explain. Verify.</small></span></Link>
    <div className={`nav-links ${open ? 'open' : ''}`}>{links.map(([name, path]) => <NavLink key={path} onClick={() => setOpen(false)} to={path} end={path === '/'}>{name}</NavLink>)}</div>
    <div className="nav-actions"><button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle colour theme">{theme === 'dark' ? <Sun size={17}/> : <Moon size={17}/>}</button><Link className="btn btn-small" to="/analyze">Get Started</Link><button className="menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">{open ? <X/> : <Menu/>}</button></div>
  </nav></header>;
}
