import { useEffect, useState, type FormEvent } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  ArrowRight,
  BookOpen,
  Brain,
  Check,
  CheckCircle2,
  ChevronRight,
  Circle,
  Compass,
  Headphones,
  Heart,
  HelpCircle,
  Home as HomeIcon,
  Leaf,
  LifeBuoy,
  LockKeyhole,
  Menu,
  MessageCircle,
  Moon,
  Phone,
  Plus,
  RotateCcw,
  Send,
  ShieldCheck,
  Sparkles,
  Sun,
  Wind,
  X,
  type LucideIcon,
} from 'lucide-react';
import { ErrorBoundary } from '@/components/error-boundary';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';

const queryClient = new QueryClient();

type Section = 'home' | 'journey' | 'companion' | 'memory' | 'help';
type Mood = 'still' | 'tender' | 'tangled' | 'bright' | 'tired';

type NavItem = {
  id: Section;
  label: string;
  icon: LucideIcon;
};

const navItems: NavItem[] = [
  { id: 'home', label: 'Home', icon: HomeIcon },
  { id: 'journey', label: 'Journey', icon: Compass },
  { id: 'companion', label: 'AI Companion', icon: MessageCircle },
  { id: 'memory', label: 'Memory', icon: BookOpen },
  { id: 'help', label: 'Help & support', icon: LifeBuoy },
];

const moods: { id: Mood; label: string; icon: LucideIcon }[] = [
  { id: 'still', label: 'Still', icon: Moon },
  { id: 'tender', label: 'Tender', icon: Heart },
  { id: 'tangled', label: 'Tangled', icon: Wind },
  { id: 'bright', label: 'Bright', icon: Sun },
  { id: 'tired', label: 'Tired', icon: Leaf },
];

const initialMessages = [
  { from: 'companion', text: 'Good evening, Shri. I am here with you. There is nowhere else you need to be for this moment.', time: 'just now' },
  { from: 'you', text: 'I want to slow down, but my thoughts are moving quickly.', time: 'just now' },
  { from: 'companion', text: 'That makes sense. We can let them pass without chasing each one. What feels most present right now?', time: 'just now' },
];

const responseBank = [
  'You do not have to solve the whole evening. We can stay with one small, honest feeling.',
  'I hear the care underneath that. Let us make a little room for it, without asking it to change yet.',
  'Thank you for trusting this space with that thought. A gentle next step is enough for now.',
];

const initialMemories = [
  { id: 1, title: 'A quieter kind of morning', text: 'I noticed the light on the kitchen floor before reaching for my phone.', date: 'Today, 8:14 am', icon: Sun },
  { id: 2, title: 'What I am learning about rest', text: 'Rest is not a reward for finishing everything. It is part of how I continue.', date: 'Yesterday', icon: Leaf },
  { id: 3, title: 'A note to return to', text: 'I can be in progress and still be worthy of tenderness.', date: '12 Mar 2024', icon: Heart },
];

function Brand() {
  return (
    <div className="ds-brand" aria-label="DearShri Ai">
      <div className="ds-brand-mark"><Sparkles size={17} strokeWidth={2.2} /></div>
      <div>
        <div className="ds-brand-name">DearShri Ai</div>
        <span className="ds-brand-sub">a softer place to land</span>
      </div>
    </div>
  );
}

function Navigation({ active, onChange }: { active: Section; onChange: (section: Section) => void }) {
  return (
    <>
      <aside className="ds-sidebar">
        <Brand />
        <div className="ds-nav-label">Your space</div>
        <nav className="ds-nav" aria-label="Primary navigation">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              className={active === id ? 'active' : ''}
              onClick={() => onChange(id)}
              data-testid={`button-nav-${id}`}
              aria-current={active === id ? 'page' : undefined}
            >
              <Icon size={17} strokeWidth={1.7} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="ds-side-note">
          <p>“You can arrive exactly as you are.”</p>
          <small>DearShri note 04</small>
        </div>
      </aside>
      <nav className="ds-mobile-nav" aria-label="Mobile navigation">
        {navItems.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={active === id ? 'active' : ''}
            onClick={() => onChange(id)}
            data-testid={`button-mobile-nav-${id}`}
          >
            <Icon size={17} strokeWidth={1.8} />
            <span>{id === 'companion' ? 'Talk' : label.split(' ')[0]}</span>
          </button>
        ))}
      </nav>
    </>
  );
}

function Topbar({ active }: { active: Section }) {
  const current = navItems.find((item) => item.id === active);
  return (
    <header className="ds-topbar">
      <div>
        <div className="ds-kicker">{current?.label ?? 'Home'}</div>
        <div className="ds-date" data-testid="text-date">Tuesday, 19 March 2024 · 8:42 pm</div>
      </div>
      <div className="ds-profile" title="Shri" data-testid="text-profile">S</div>
    </header>
  );
}

function HomeSection({
  mood,
  onMoodChange,
  onNavigate,
  onToast,
}: {
  mood: Mood | null;
  onMoodChange: (mood: Mood) => void;
  onNavigate: (section: Section) => void;
  onToast: (message: string) => void;
}) {
  return (
    <>
      <section className="ds-hero">
        <div className="ds-hero-copy">
          <div className="ds-kicker">A gentle check-in</div>
          <h1>How are you<br />holding <em>today?</em></h1>
          <p>This is your quiet corner of the day — a place to notice what is here, be met with care, and take one kind step forward.</p>
          <div className="ds-hero-actions">
            <button type="button" className="ds-btn" onClick={() => { onNavigate('journey'); onToast('Your evening check-in is ready.'); }} data-testid="button-begin-checkin">
              Begin check-in <ArrowRight size={15} />
            </button>
            <button type="button" className="ds-btn ds-btn-quiet" onClick={() => onNavigate('companion')} data-testid="button-talk-companion">
              <MessageCircle size={15} /> Talk with Shri
            </button>
          </div>
        </div>
        <div className="ds-glass ds-checkin">
          <div className="ds-checkin-head">
            <div>
              <div className="ds-checkin-label">Right now</div>
              <h2>Check in softly.</h2>
            </div>
            <div className="ds-moon"><Moon size={22} strokeWidth={1.5} /></div>
          </div>
          <div>
            <p className="ds-checkin-question">Which word feels nearest to you?</p>
            <div className="ds-moods" role="group" aria-label="Choose how you feel">
              {moods.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  type="button"
                  className={`ds-mood ${mood === id ? 'selected' : ''}`}
                  onClick={() => { onMoodChange(id); onToast(`Noted: ${label.toLowerCase()}.`); }}
                  data-testid={`button-mood-${id}`}
                  aria-pressed={mood === id}
                >
                  <Icon className="ds-mood-icon" size={17} strokeWidth={1.7} />
                  <span className="ds-mood-word">{label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="ds-section-head">
        <div>
          <h2>A little room to breathe</h2>
          <p>Small invitations for wherever you are starting from.</p>
        </div>
        <button type="button" className="ds-link" onClick={() => onNavigate('journey')} data-testid="button-view-journey">
          View journey <ChevronRight size={14} />
        </button>
      </div>
      <section className="ds-ritual-grid">
        <button type="button" className="ds-glass ds-ritual" onClick={() => onNavigate('journey')} data-testid="button-ritual-checkin">
          <span className="ds-ritual-arrow"><ArrowRight size={16} /></span>
          <div className="ds-icon-box"><Wind size={17} /></div>
          <h3>Evening check-in</h3>
          <p>Three minutes to notice, name, and gently set down what the day carried.</p>
        </button>
        <button type="button" className="ds-glass ds-ritual" onClick={() => onNavigate('companion')} data-testid="button-ritual-talk">
          <div className="ds-icon-box"><MessageCircle size={17} /></div>
          <h3>Open a conversation</h3>
          <p>Say the thing that has been circling.</p>
        </button>
        <button type="button" className="ds-glass ds-ritual" onClick={() => onNavigate('memory')} data-testid="button-ritual-memory">
          <div className="ds-icon-box"><BookOpen size={17} /></div>
          <h3>Revisit a memory</h3>
          <p>Return to the words you left for yourself.</p>
        </button>
      </section>
      <section className="ds-lower-grid">
        <div className="ds-glass ds-lower-card">
          <h3>Your unfolding journey</h3>
          <p>You have made a little space for yourself on 4 of the last 7 evenings.</p>
          <div className="ds-progress"><i /></div>
          <div className="ds-progress-meta"><span>Week 02 · Returning</span><span>68%</span></div>
        </div>
        <div className="ds-glass ds-lower-card">
          <div className="ds-quote"><span className="ds-quote-mark">“</span> Nothing needs to be rushed tonight.</div>
        </div>
      </section>
    </>
  );
}

function JourneySection({ completed, onComplete, onNavigate, onToast }: { completed: number[]; onComplete: (index: number) => void; onNavigate: (section: Section) => void; onToast: (message: string) => void }) {
  const steps = [
    { title: 'Arrive in the room', text: 'Notice five things that tell your body it is safe enough to pause.' },
    { title: 'Name what is here', text: 'Give the strongest feeling a little language, without judging it.' },
    { title: 'Meet yourself kindly', text: 'Offer the part of you that is trying its best a sentence of care.' },
    { title: 'Choose one small thing', text: 'Close with a next step that feels possible, not perfect.' },
  ];
  return (
    <>
      <div className="ds-page-title">
        <div className="ds-kicker">Guided journey · 02</div>
        <h1>Returning to<br /><em>yourself.</em></h1>
        <p>A gentle sequence for evenings when the inside of your mind feels louder than the world outside. Move at your own pace.</p>
      </div>
      <div className="ds-journey">
        <div className="ds-journey-intro">
          <div className="ds-glass">
            <div className="ds-icon-box"><Compass size={18} /></div>
            <h3 style={{ margin: '0 0 8px', fontSize: 15 }}>Tonight’s intention</h3>
            <p style={{ margin: 0, color: 'hsl(var(--muted-foreground))', font: 'italic 21px/1.2 var(--app-font-serif)' }}>To leave a little more room for what is true.</p>
            <div className="ds-progress"><i style={{ width: `${(completed.length / steps.length) * 100}%` }} /></div>
            <div className="ds-progress-meta"><span>{completed.length} of {steps.length} complete</span><span>{completed.length === steps.length ? 'Complete' : 'In progress'}</span></div>
          </div>
          <button type="button" className="ds-btn ds-btn-quiet" style={{ marginTop: 12, width: '100%' }} onClick={() => onNavigate('companion')} data-testid="button-journey-companion">
            Need a little company <MessageCircle size={15} />
          </button>
        </div>
        <div className="ds-sequence">
          {steps.map((step, index) => {
            const done = completed.includes(index);
            return (
              <div className={`ds-step ${done ? 'done' : ''}`} key={step.title} data-testid={`card-journey-step-${index}`}>
                <div className="ds-step-index">{done ? <Check size={14} /> : `0${index + 1}`}</div>
                <div><h3>{step.title}</h3><p>{step.text}</p></div>
                <button type="button" onClick={() => { onComplete(index); onToast(done ? 'Step reopened.' : 'A small step, kept.'); }} data-testid={`button-complete-step-${index}`}>
                  {done ? 'Reopen' : index === completed.length ? 'Start' : 'Later'}
                </button>
              </div>
            );
          })}
          <button type="button" className="ds-btn" style={{ marginTop: 8, justifySelf: 'start' }} onClick={() => onToast('You have given yourself enough for tonight.')} data-testid="button-finish-journey">
            Finish for tonight <CheckCircle2 size={15} />
          </button>
        </div>
      </div>
    </>
  );
}

function CompanionSection({ messages, onSend, onToast }: { messages: typeof initialMessages; onSend: (text: string) => void; onToast: (message: string) => void }) {
  const [draft, setDraft] = useState('');
  const suggestions = [
    ['I feel a bit overwhelmed', 'We can slow the edges down together.'],
    ['Help me find perspective', 'Let us look at this from a kinder distance.'],
    ['I want to celebrate something', 'There is room for joy here too.'],
  ];
  const send = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.trim()) return;
    onSend(draft.trim());
    setDraft('');
  };
  return (
    <>
      <div className="ds-page-title">
        <div className="ds-kicker">Your companion · always private</div>
        <h1>A conversation<br />with <em>care.</em></h1>
        <p>Shri listens without rushing to fix. Start anywhere — a thought, a feeling, or even just a pause.</p>
      </div>
      <div className="ds-companion">
        <div className="ds-glass ds-chat">
          <div className="ds-chat-head">
            <div className="ds-companion-orb"><Sparkles size={20} /></div>
            <div><h2>Shri</h2><div className="ds-online"><i /> present with you</div></div>
            <button type="button" className="ds-link" style={{ marginLeft: 'auto' }} onClick={() => onToast('This conversation is already private to you.')} data-testid="button-chat-privacy"><LockKeyhole size={14} /> Private</button>
          </div>
          <div className="ds-messages" aria-live="polite">
            {messages.map((message, index) => (
              <div key={`${message.time}-${index}`} className={`ds-message ${message.from === 'you' ? 'you' : ''}`} data-testid={`message-chat-${index}`}>
                <small>{message.from === 'you' ? 'You' : 'Shri'} · {message.time}</small>{message.text}
              </div>
            ))}
          </div>
          <form className="ds-chat-form" onSubmit={send}>
            <input className="ds-input" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Write what is on your mind…" aria-label="Message Shri" data-testid="input-chat-message" />
            <button className="ds-send" type="submit" aria-label="Send message" data-testid="button-send-message"><Send size={16} /></button>
          </form>
        </div>
        <div className="ds-suggestions">
          <div className="ds-kicker" style={{ margin: '3px 0 2px' }}>Try beginning with</div>
          {suggestions.map(([title, copy], index) => (
            <button type="button" className="ds-suggestion" key={title} onClick={() => { onSend(title); onToast('A gentle beginning.'); }} data-testid={`button-suggestion-${index}`}>
              <strong>{title}</strong><span>{copy}</span>
            </button>
          ))}
          <button type="button" className="ds-suggestion" onClick={() => onToast('Take three slow breaths before you write.')} data-testid="button-breathing-pause">
            <strong><Wind size={14} style={{ verticalAlign: -3, marginRight: 5 }} /> Take a breathing pause</strong><span>There is no need to find the right words yet.</span>
          </button>
        </div>
      </div>
    </>
  );
}

function MemorySection({ memories, onAdd, onToast }: { memories: typeof initialMemories; onAdd: (title: string, text: string) => void; onToast: (message: string) => void }) {
  const [adding, setAdding] = useState(false);
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const save = (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !text.trim()) return;
    onAdd(title.trim(), text.trim());
    setTitle('');
    setText('');
    setAdding(false);
    onToast('Saved to your memory garden.');
  };
  return (
    <>
      <div className="ds-page-title">
        <div className="ds-kicker">Your memory garden</div>
        <h1>Keep the words<br />that <em>warm you.</em></h1>
        <p>A private shelf for observations, promises, and moments you may want to remember on a harder day.</p>
      </div>
      <div className="ds-memory-layout">
        <section className="ds-glass ds-memory-main">
          <h2>Small things, held close.</h2>
          <p>There are no rules for what belongs here. A sentence is enough.</p>
          {!adding ? (
            <button type="button" className="ds-btn ds-btn-quiet" onClick={() => setAdding(true)} data-testid="button-add-memory"><Plus size={15} /> Add a memory</button>
          ) : (
            <form className="ds-memory-form" onSubmit={save}>
              <input className="ds-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Give this memory a name" aria-label="Memory title" data-testid="input-memory-title" />
              <textarea className="ds-textarea" value={text} onChange={(event) => setText(event.target.value)} placeholder="What would you like to remember?" aria-label="Memory text" data-testid="input-memory-text" />
              <div style={{ display: 'flex', gap: 8 }}>
                <button type="submit" className="ds-btn" data-testid="button-save-memory"><Check size={15} /> Keep this</button>
                <button type="button" className="ds-btn ds-btn-quiet" onClick={() => setAdding(false)} data-testid="button-cancel-memory"><X size={15} /> Cancel</button>
              </div>
            </form>
          )}
          <div className="ds-memory-list" style={{ marginTop: 22 }}>
            {memories.length === 0 ? <div className="ds-empty">Your garden is waiting for its first little note.</div> : memories.map(({ id, title: memoryTitle, text: memoryText, date, icon: Icon }) => (
              <article className="ds-memory-card" key={id} data-testid={`card-memory-${id}`}>
                <div className="ds-icon-box" style={{ margin: 0 }}><Icon size={15} /></div>
                <div><h3>{memoryTitle}</h3><p>{memoryText}</p></div>
                <div className="ds-memory-date">{date}</div>
              </article>
            ))}
          </div>
        </section>
        <aside className="ds-glass ds-memory-side">
          <div className="ds-icon-box"><Brain size={17} /></div>
          <h2>A kinder archive</h2>
          <p>When you return here, notice what your past self was already learning. You do not have to start from zero.</p>
          <div style={{ paddingTop: 18, borderTop: '1px solid hsl(var(--border) / .5)' }}>
            <div className="ds-kicker">A prompt for you</div>
            <p style={{ marginTop: 9, color: 'hsl(var(--foreground))', font: 'italic 22px/1.2 var(--app-font-serif)' }}>What did you do today that your future self might thank you for?</p>
            <button type="button" className="ds-link" onClick={() => { setAdding(true); onToast('A blank page is open for you.'); }} data-testid="button-prompt-memory">Write it down <ArrowRight size={14} /></button>
          </div>
        </aside>
      </div>
    </>
  );
}

function HelpSection({ onToast }: { onToast: (message: string) => void }) {
  return (
    <>
      <div className="ds-page-title">
        <div className="ds-kicker">You do not have to carry it alone</div>
        <h1>Support for<br /><em>this moment.</em></h1>
        <p>Gentle tools and clear next steps, whether you need grounding, a human voice, or a little more information.</p>
      </div>
      <div className="ds-help-grid">
        <section className="ds-glass ds-help-card featured">
          <div>
            <h2>Are you safe right now?</h2>
            <p>If you feel at immediate risk or might hurt yourself, please contact your local emergency service or go to the nearest emergency department.</p>
          </div>
          <div className="ds-help-actions">
            <button type="button" className="ds-btn" onClick={() => onToast('Please call your local emergency service now.')} data-testid="button-emergency-help"><Phone size={15} /> Get immediate help</button>
            <button type="button" className="ds-btn ds-btn-quiet" onClick={() => onToast('You are not alone in asking for support.')} data-testid="button-trusted-person"><Heart size={15} /> Tell someone trusted</button>
          </div>
        </section>
        <section className="ds-glass ds-help-card">
          <ShieldCheck className="ds-resource-icon" size={19} />
          <h3 style={{ marginTop: 17 }}>Ground yourself</h3>
          <p>A two-minute reset for when everything feels too much.</p>
          <div className="ds-resource"><Wind size={17} className="ds-resource-icon" /><div><strong>Five gentle senses</strong><span>Name what you can see, hear, feel, smell, and taste.</span></div></div>
          <button type="button" className="ds-link" onClick={() => onToast('Grounding practice opened. Look for one blue thing near you.')} data-testid="button-grounding">Begin grounding <ArrowRight size={14} /></button>
        </section>
        <section className="ds-glass ds-help-card">
          <Headphones className="ds-resource-icon" size={19} />
          <h3 style={{ marginTop: 17 }}>Find a human voice</h3>
          <p>Reaching out is a form of care, not an interruption.</p>
          <div className="ds-resource"><LifeBuoy size={17} className="ds-resource-icon" /><div><strong>Talk to someone you trust</strong><span>Consider texting: “I could use some company tonight.”</span></div></div>
          <button type="button" className="ds-link" onClick={() => onToast('A message prompt is ready to copy.')} data-testid="button-message-prompt">See a message prompt <ArrowRight size={14} /></button>
        </section>
        <section className="ds-glass ds-help-card">
          <RotateCcw className="ds-resource-icon" size={19} />
          <h3 style={{ marginTop: 17 }}>Come back to the room</h3>
          <p>Small facts can help your mind find the present again.</p>
          <div className="ds-resource"><Circle size={17} className="ds-resource-icon" /><div><strong>Notice your surroundings</strong><span>Feel your feet on the floor. Let your shoulders drop by one degree.</span></div></div>
          <button type="button" className="ds-link" onClick={() => onToast('You are here. The next breath is enough.')} data-testid="button-return-room">Try it now <ArrowRight size={14} /></button>
        </section>
        <section className="ds-glass ds-help-card">
          <HelpCircle className="ds-resource-icon" size={19} />
          <h3 style={{ marginTop: 17 }}>About this space</h3>
          <p>DearShri is a reflection companion, not a replacement for professional care. Your reflections stay yours.</p>
          <button type="button" className="ds-link" onClick={() => onToast('DearShri keeps this space private to you.')} data-testid="button-about-privacy">Read privacy promise <LockKeyhole size={14} /></button>
        </section>
      </div>
    </>
  );
}

function AppContent() {
  const [activeSection, setActiveSection] = useState<Section>('home');
  const [mood, setMood] = useState<Mood | null>(null);
  const [completed, setCompleted] = useState<number[]>([0]);
  const [messages, setMessages] = useState(initialMessages);
  const [memories, setMemories] = useState(initialMemories);
  const [toast, setToast] = useState('');

  useEffect(() => {
    if (!toast) return;
    const timer = window.setTimeout(() => setToast(''), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  const notify = (message: string) => setToast(message);
  const toggleStep = (index: number) => setCompleted((current) => current.includes(index) ? current.filter((step) => step !== index) : [...current, index].sort());
  const sendMessage = (text: string) => {
    setMessages((current) => [...current, { from: 'you', text, time: 'just now' }]);
    window.setTimeout(() => {
      setMessages((current) => [...current, { from: 'companion', text: responseBank[current.length % responseBank.length], time: 'just now' }]);
    }, 550);
  };
  const addMemory = (title: string, text: string) => {
    setMemories((current) => [{ id: Date.now(), title, text, date: 'Just now', icon: Heart }, ...current]);
  };

  return (
    <div className="ds-app">
      <div className="ds-orb ds-orb-one" /><div className="ds-orb ds-orb-two" />
      <div className="ds-shell">
        <Navigation active={activeSection} onChange={setActiveSection} />
        <main className="ds-main">
          <div className="ds-content">
            <Topbar active={activeSection} />
            {activeSection === 'home' && <HomeSection mood={mood} onMoodChange={setMood} onNavigate={setActiveSection} onToast={notify} />}
            {activeSection === 'journey' && <JourneySection completed={completed} onComplete={toggleStep} onNavigate={setActiveSection} onToast={notify} />}
            {activeSection === 'companion' && <CompanionSection messages={messages} onSend={sendMessage} onToast={notify} />}
            {activeSection === 'memory' && <MemorySection memories={memories} onAdd={addMemory} onToast={notify} />}
            {activeSection === 'help' && <HelpSection onToast={notify} />}
          </div>
        </main>
      </div>
      {toast && <div className="ds-toast" role="status" data-testid="status-toast">{toast}</div>}
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ErrorBoundary resetKey="dearshri">
          <AppContent />
        </ErrorBoundary>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;