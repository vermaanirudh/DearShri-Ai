import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import {
  ArrowUp,
  Bell,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  ChevronLeft,
  Clock3,
  HelpCircle,
  History,
  Heart,
  KeyRound,
  Leaf,
  LockKeyhole,
  GraduationCap,
  LogOut,
  Menu,
  MessageSquare,
  MoreHorizontal,
  PanelLeft,
  Phone,
  Plus,
  Send,
  Settings2,
  Shield,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserRound,
  X,
} from 'lucide-react';
import { journeyStories } from './journey-data';

type Screen = 'login' | 'intro' | 'app';
type View = 'chat' | 'companion' | 'journey' | 'history' | 'settings' | 'admin';
type Role = 'user' | 'assistant';
type CompanionMode = 'friend' | 'tutor' | 'guardian' | 'admin';

type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  time: string;
};

const defaultMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    content:
      'Hello, Shri. I’m here with you. You can bring me a thought, a question, or simply a quiet moment.',
    time: 'Now',
  },
];

const suggestions = [
  { title: 'Help me clear my head', copy: 'Sort through what feels tangled.' },
  { title: 'I need a small plan', copy: 'Find one gentle next step.' },
  { title: 'Something is on my mind', copy: 'Start wherever the feeling begins.' },
];

const modeDetails: Record<CompanionMode, { label: string; icon: typeof Heart; description: string }> = {
  friend: { label: 'Friend', icon: Heart, description: 'Warm and supportive' },
  tutor: { label: 'Tutor', icon: GraduationCap, description: 'Clear and practical' },
  guardian: { label: 'Guardian', icon: ShieldCheck, description: 'Grounded and protective' },
  admin: { label: 'Admin', icon: Shield, description: 'Direct human channel' },
};

function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`ds-logo ${compact ? 'compact' : ''}`} aria-label="DearShri Ai">
      <div className="ds-logo-mark"><Sparkles size={17} strokeWidth={2.2} /></div>
      {!compact && (
        <div>
          <strong>DearShri <span>Ai</span></strong>
          <small>Your private companion</small>
        </div>
      )}
    </div>
  );
}

function LoginScreen({ onLogin, externalError }: { onLogin: (phone: string, code: string) => Promise<void>; externalError?: string }) {
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (phone.replace(/\D/g, '').length < 8) {
      setError('Please enter a valid phone number.');
      return;
    }
    if (code.trim().length < 4) {
      setError('Enter the access code to continue.');
      return;
    }
    setError('');
    void onLogin(phone, code);
  };

  return (
    <div className="ds-auth-page">
      <div className="ds-auth-glow glow-left" />
      <div className="ds-auth-glow glow-right" />
      <header className="ds-auth-top"><Logo /></header>
      <main className="ds-auth-card">
        <div className="ds-auth-icon"><LockKeyhole size={21} /></div>
        <div className="ds-eyebrow">A private place to land</div>
        <h1>Welcome back,<br /><em>Shri.</em></h1>
        <p className="ds-auth-copy">
          Sign in to continue your conversations and return to the thoughts you’ve chosen to keep close.
        </p>
        <form className="ds-auth-form" onSubmit={submit}>
          <label>
            <span>Phone number</span>
            <div className="ds-field">
              <Phone size={16} />
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="+91 00000 00000"
                inputMode="tel"
                autoComplete="tel"
                aria-label="Phone number"
                data-testid="input-phone"
              />
            </div>
          </label>
          <label>
            <span>Access code</span>
            <div className="ds-field">
              <KeyRound size={16} />
              <input
                value={code}
                onChange={(event) => setCode(event.target.value)}
                placeholder="Enter your 4-digit code"
                type="password"
                inputMode="numeric"
                autoComplete="one-time-code"
                aria-label="Access code"
                data-testid="input-access-code"
              />
            </div>
          </label>
          {(error || externalError) && <div className="ds-form-error" role="alert">{error || externalError}</div>}
          <button className="ds-primary-button" type="submit" data-testid="button-login">
            Continue <ArrowUp size={16} />
          </button>
        </form>
        <div className="ds-auth-foot"><Shield size={13} /> Your conversations are private to you.</div>
      </main>
      <footer className="ds-auth-footer">DearShri Ai · Built for honest moments</footer>
    </div>
  );
}

function IntroScreen({ onStart, name }: { onStart: () => void; name: string }) {
  return (
    <div className="ds-intro-page">
      <div className="ds-intro-wash" />
      <header className="ds-intro-top"><Logo /></header>
      <main className="ds-intro-content">
        <div className="ds-intro-mark"><Sparkles size={25} /></div>
        <div className="ds-eyebrow">A warm welcome</div>
        <h1>There’s room for<br /><em>you</em> here, {name}.</h1>
        <p className="ds-intro-lead">
          DearShri Ai is a calm, private companion for thinking out loud, finding perspective, and keeping the small things that matter.
        </p>
        <div className="ds-special-note">
          <Leaf size={17} />
          <span>This is a special place designed just for you.</span>
        </div>
        <div className="ds-capability-grid">
          <div><MessageSquare size={17} /><strong>Talk freely</strong><span>Start wherever you are.</span></div>
          <div><History size={17} /><strong>Keep context</strong><span>Return to what matters.</span></div>
          <div><LockKeyhole size={17} /><strong>Stay private</strong><span>Your space is yours.</span></div>
        </div>
        <button className="ds-primary-button intro-cta" type="button" onClick={onStart} data-testid="button-start-chatting">
          Start chatting <ArrowUp size={16} />
        </button>
        <small className="ds-intro-disclaimer">DearShri Ai is a reflection companion, not a replacement for professional care.</small>
      </main>
    </div>
  );
}

function Sidebar({
  view,
  collapsed,
  mobileOpen,
  journeyAvailable,
  isAdmin,
  onView,
  onNewChat,
  onClose,
}: {
  view: View;
  collapsed: boolean;
  mobileOpen: boolean;
  journeyAvailable: boolean;
  isAdmin: boolean;
  onView: (view: View) => void;
  onNewChat: () => void;
  onClose: () => void;
}) {
  const links: { id: View; label: string; icon: typeof MessageSquare }[] = [
    { id: 'chat', label: 'New chat', icon: MessageSquare },
    ...(journeyAvailable ? [{ id: 'journey' as View, label: 'Journey', icon: BookOpen }] : []),
    { id: 'companion', label: 'Companion', icon: Sparkles },
    { id: 'history', label: 'History', icon: History },
    { id: 'settings', label: 'Settings', icon: Settings2 },
    ...(isAdmin ? [{ id: 'admin' as View, label: 'Admin inbox', icon: Shield }] : []),
  ];
  return (
    <>
      {mobileOpen && <button className="ds-drawer-scrim" type="button" onClick={onClose} aria-label="Close menu" />}
      <aside className={`ds-sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="ds-sidebar-top">
          <Logo compact={collapsed} />
          <button className="ds-icon-button ds-sidebar-close" type="button" onClick={onClose} aria-label="Close menu"><X size={17} /></button>
        </div>
        <button className="ds-new-chat" type="button" onClick={onNewChat} data-testid="button-new-chat">
          <Plus size={17} /><span>New conversation</span>
        </button>
        <div className="ds-nav-section-label">Workspace</div>
        <nav className="ds-workspace-nav" aria-label="Workspace navigation">
          {links.map(({ id, label, icon: Icon }) => (
            <button
              type="button"
              key={id}
              className={view === id ? 'active' : ''}
              onClick={() => { onView(id); onClose(); }}
              title={collapsed ? label : undefined}
              data-testid={`button-nav-${id}`}
            >
              <Icon size={17} />
              <span>{label}</span>
              {id === 'admin' && <i className="ds-admin-dot" />}
            </button>
          ))}
        </nav>
        {!collapsed && (
          <div className="ds-sidebar-tip">
            <Sparkles size={15} />
            <div><strong>A quiet reminder</strong><span>You don’t have to have the right words.</span></div>
          </div>
        )}
        <div className="ds-sidebar-bottom">
          <div className="ds-private-label"><LockKeyhole size={13} /> <span>Private workspace</span></div>
          <div className="ds-sidebar-user"><div className="ds-avatar">S</div>{!collapsed && <div><strong>Shri</strong><span>Personal space</span></div>}</div>
        </div>
      </aside>
    </>
  );
}

function ChatView({
  messages,
  onSend,
  onClear,
  mode,
  onModeChange,
}: {
  messages: ChatMessage[];
  onSend: (text: string) => void;
  onClear: () => void;
  mode: CompanionMode;
  onModeChange: (mode: CompanionMode) => void;
}) {
  const [draft, setDraft] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages.length]);

  const send = () => {
    const text = draft.trim();
    if (!text) return;
    onSend(text);
    setDraft('');
  };

  return (
    <section className="ds-chat-view">
      <div className="ds-chat-titlebar">
        <div className="ds-chat-identity">
          <div className="ds-orb"><Sparkles size={17} /></div>
          <div><strong>{modeDetails[mode].label} · DearShri Ai</strong><span><i /> {modeDetails[mode].description}</span></div>
        </div>
        <div className="ds-chat-actions">
          <div className="ds-mode-switcher" aria-label="Companion mode">
            {(Object.keys(modeDetails) as CompanionMode[]).map((key) => {
              const Icon = modeDetails[key].icon;
              return <button key={key} type="button" className={mode === key ? 'active' : ''} onClick={() => onModeChange(key)} title={modeDetails[key].description}><Icon size={13} /><span>{modeDetails[key].label}</span></button>;
            })}
          </div>
          <button className="ds-icon-button" type="button" onClick={onClear} title="Clear conversation" aria-label="Clear conversation"><Trash2 size={16} /></button>
        </div>
      </div>
      <div className="ds-chat-scroll" ref={scrollRef} aria-live="polite">
        <div className="ds-chat-inner">
          {messages.length === 1 && (
            <div className="ds-chat-welcome">
              <div className="ds-welcome-spark"><Sparkles size={18} /></div>
              <h1>What would you like<br /><em>to explore?</em></h1>
              <p>Take your time. There’s no perfect way to begin.</p>
              <div className="ds-suggestion-grid">
                {suggestions.map((item) => (
                  <button type="button" className="ds-suggestion-card" key={item.title} onClick={() => onSend(item.title)}>
                    <strong>{item.title}</strong><span>{item.copy}</span><ChevronRight size={14} />
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((message) => (
            <div className={`ds-message-row ${message.role}`} key={message.id}>
              {message.role === 'assistant' && <div className="ds-message-avatar"><Sparkles size={13} /></div>}
              <div className="ds-bubble-wrap">
                <span className="ds-message-name">{message.role === 'assistant' ? 'DearShri Ai' : 'You'} · {message.time}</span>
                <div className="ds-bubble">{message.content}</div>
              </div>
              {message.role === 'user' && <div className="ds-message-avatar user"><UserRound size={13} /></div>}
            </div>
          ))}
        </div>
      </div>
      <div className="ds-composer-area">
        <div className="ds-composer">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(); } }}
            placeholder="Message DearShri Ai..."
            rows={1}
            aria-label="Message DearShri Ai"
            data-testid="input-chat-message"
          />
          <button className="ds-send-button" type="button" onClick={send} disabled={!draft.trim()} aria-label="Send message" data-testid="button-send-message"><ArrowUp size={17} /></button>
        </div>
        <div className="ds-composer-meta"><span><LockKeyhole size={11} /> Private conversation</span><span>Enter to send · Shift + Enter for a new line</span></div>
      </div>
    </section>
  );
}

function JourneyView({
  answers,
  onAnswer,
}: {
  answers: Record<string, string>;
  onAnswer: (storyIndex: number, questionIndex: number, answer: string) => void;
}) {
  const [selectedStory, setSelectedStory] = useState(0);
  const story = journeyStories[selectedStory];
  const completedForStory = story.questions.filter((_, index) => answers[`${story.storyId}-${index}`]).length;
  const previousComplete = selectedStory === 0 || journeyStories[selectedStory - 1].questions.every((_, index) => answers[`${journeyStories[selectedStory - 1].storyId}-${index}`]);
  const unlocked = selectedStory === 0 || previousComplete;
  const questionIndex = story.questions.findIndex((_, index) => !answers[`${story.storyId}-${index}`]);
  const activeQuestion = questionIndex === -1 ? story.questions.length - 1 : questionIndex;
  const [draft, setDraft] = useState(answers[`${story.storyId}-${activeQuestion}`] ?? '');
  useEffect(() => {
    setDraft(answers[`${story.storyId}-${activeQuestion}`] ?? '');
  }, [selectedStory, answers, activeQuestion, story.storyId]);
  const completedTotal = Object.keys(answers).length;

  const submit = () => {
    if (!draft.trim() || !unlocked || completedForStory >= 10) return;
    onAnswer(selectedStory, activeQuestion, draft.trim());
    setDraft('');
  };

  return (
    <section className="ds-journey-view">
      <div className="ds-page-heading">
        <div><div className="ds-eyebrow">Your private reflection path</div><h1>The Journey</h1><p>Ten stories. One gentle question at a time. Your answers save automatically.</p></div>
        <div className="ds-journey-total"><strong>{completedTotal}<span>/100</span></strong><small>questions explored</small></div>
      </div>
      <div className="ds-story-grid">
        {journeyStories.map((item, index) => {
          const count = item.questions.filter((_, question) => answers[`${item.storyId}-${question}`]).length;
          const isUnlocked = index === 0 || journeyStories[index - 1].questions.every((_, question) => answers[`${journeyStories[index - 1].storyId}-${question}`]);
          return <button key={item.storyId} type="button" className={`ds-story-card ${selectedStory === index ? 'selected' : ''} ${!isUnlocked ? 'locked' : ''}`} onClick={() => isUnlocked && setSelectedStory(index)} disabled={!isUnlocked}>
            <div className="ds-story-top"><span className="ds-story-emoji">{item.emoji}</span>{isUnlocked ? <ChevronRight size={15} /> : <LockKeyhole size={14} />}</div>
            <strong>Story {item.storyNum}</strong><h3>{item.title}</h3>
            <div className="ds-story-progress"><i style={{ width: `${count * 10}%` }} /></div><small>{count === 10 ? 'Complete' : `${count}/10 explored`}</small>
          </button>;
        })}
      </div>
      <div className={`ds-journey-question ${!unlocked ? 'is-locked' : ''}`}>
        <div className="ds-journey-question-top"><span>{story.emoji} Story {story.storyNum} · Question {activeQuestion + 1} of 10</span>{completedForStory === 10 && <span className="ds-complete-pill"><Check size={12} /> Complete</span>}</div>
        <h2>{completedForStory === 10 ? 'This story is complete.' : story.questions[activeQuestion]}</h2>
        {unlocked && completedForStory < 10 ? <><textarea value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Take your time. There is no perfect answer." rows={4} aria-label="Journey answer" /><button className="ds-primary-button small" type="button" onClick={submit} disabled={!draft.trim()}><Check size={14} /> Save & continue</button></> : <p>{completedForStory === 10 ? 'Choose another story, or keep this reflection close.' : 'Complete the previous story to gently unlock this one.'}</p>}
      </div>
    </section>
  );
}

function HistoryView({ onOpenChat }: { onOpenChat: () => void }) {
  return (
    <section className="ds-page-view">
      <div className="ds-page-heading"><div><div className="ds-eyebrow">Your conversations</div><h1>History</h1><p>Return to a thought whenever you need to.</p></div><button className="ds-primary-button small" type="button" onClick={onOpenChat}><Plus size={15} /> New chat</button></div>
      <div className="ds-history-list">
        <button className="ds-history-row" type="button" onClick={onOpenChat}><div className="ds-history-icon"><MessageSquare size={16} /></div><div><strong>A quiet place to begin</strong><span>Today · Just now</span></div><ChevronRight size={16} /></button>
        <div className="ds-empty-state"><Clock3 size={20} /><strong>Your older conversations will appear here.</strong><span>Each conversation stays private to your workspace.</span></div>
      </div>
    </section>
  );
}

function SettingsView({ notifications, onNotifications }: { notifications: boolean; onNotifications: () => void }) {
  return (
    <section className="ds-page-view narrow">
      <div className="ds-page-heading"><div><div className="ds-eyebrow">Make it yours</div><h1>Settings</h1><p>Simple controls for your private space.</p></div></div>
      <div className="ds-settings-card">
        <div className="ds-settings-profile"><div className="ds-large-avatar">S</div><div><strong>Shri</strong><span>Signed in with your private access</span></div><button className="ds-icon-button" type="button" aria-label="Edit profile"><MoreHorizontal size={17} /></button></div>
        <div className="ds-setting-row"><div><Bell size={17} /><div><strong>System notices</strong><span>Receive important updates from DearShri Ai.</span></div></div><button className={`ds-toggle ${notifications ? 'on' : ''}`} type="button" onClick={onNotifications} aria-label="Toggle system notices"><i /></button></div>
        <div className="ds-setting-row"><div><LockKeyhole size={17} /><div><strong>Privacy</strong><span>Your conversations are isolated to this account.</span></div></div><Check size={17} className="ds-setting-check" /></div>
        <div className="ds-setting-row"><div><HelpCircle size={17} /><div><strong>Need support?</strong><span>Reach out if you need a human voice.</span></div></div><ChevronRight size={17} /></div>
      </div>
    </section>
  );
}

function AdminView({ onNotice }: { onNotice: (message: string) => void }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !body.trim()) return;
    onNotice('Notice broadcast to the workspace.');
    setTitle('');
    setBody('');
  };
  return (
    <section className="ds-page-view narrow">
      <div className="ds-page-heading"><div><div className="ds-eyebrow">Workspace controls</div><h1>Admin inbox</h1><p>Share a clear system notice with signed-in users.</p></div><div className="ds-admin-badge"><Shield size={14} /> Admin only</div></div>
      <form className="ds-admin-card" onSubmit={submit}>
        <div className="ds-admin-card-heading"><div className="ds-admin-icon"><Shield size={17} /></div><div><strong>Broadcast a notice</strong><span>Keep it short, kind, and useful.</span></div></div>
        <label><span>Notice title</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="A small update" /></label>
        <label><span>Message</span><textarea value={body} onChange={(event) => setBody(event.target.value)} placeholder="Write the message for the workspace..." rows={5} /></label>
        <button className="ds-primary-button small" type="submit"><Send size={14} /> Broadcast notice</button>
      </form>
    </section>
  );
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

async function apiRequest(path: string, options: RequestInit = {}, sessionToken?: string) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(sessionToken ? { 'X-Session-Token': sessionToken } : {}),
      ...(options.headers ?? {}),
    },
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed (${response.status})`);
  }
  return response.status === 204 ? null : response.json();
}

function AppWorkspace({ onSignOut, phone, sessionToken, isAdmin }: { onSignOut: () => void; phone: string; sessionToken: string; isAdmin: boolean }) {
  const [view, setView] = useState<View>('chat');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notifications, setNotifications] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>(defaultMessages);
  const [toast, setToast] = useState('');
  const [mode, setMode] = useState<CompanionMode>('friend');
  const journeyKey = `dearshri-journey-${phone.replace(/\D/g, '')}`;
  const [journeyAnswers, setJourneyAnswers] = useState<Record<string, string>>(() => {
    try { return JSON.parse(sessionStorage.getItem(journeyKey) ?? '{}') as Record<string, string>; } catch { return {}; }
  });
  const [journeyComplete, setJourneyComplete] = useState(() => Object.keys(journeyAnswers).length >= 100);

  useEffect(() => {
    apiRequest('/api/chat/history', {}, sessionToken)
      .then((data) => {
        const loaded = (data.messages ?? []).map((message: { id: number; role: Role; content: string; created_at: string }) => ({
          id: String(message.id), role: message.role, content: message.content,
          time: new Intl.DateTimeFormat('en-IN', { hour: 'numeric', minute: '2-digit' }).format(new Date(message.created_at)),
        }));
        if (loaded.length) setMessages(loaded);
      })
      .catch(() => undefined);
    apiRequest('/journey/status', {}, sessionToken)
      .then((data) => {
        if (data.completed) setJourneyComplete(true);
      })
      .catch(() => undefined);
  }, [sessionToken]);

  useEffect(() => {
    if (!toast) return;
    const timeout = window.setTimeout(() => setToast(''), 2600);
    return () => window.clearTimeout(timeout);
  }, [toast]);

  const time = useMemo(() => new Intl.DateTimeFormat('en-IN', { hour: 'numeric', minute: '2-digit' }).format(new Date()), []);

  const sendMessage = async (content: string) => {
    const userMessage: ChatMessage = { id: `user-${Date.now()}`, role: 'user', content, time };
    setMessages((current) => [...current, userMessage]);
    try {
      const data = await apiRequest('/api/chat/message', { method: 'POST', body: JSON.stringify({ content, mode }) }, sessionToken);
      if (data.assistant_message) {
        setMessages((current) => [...current, { id: `assistant-${Date.now()}`, role: 'assistant', content: data.assistant_message.content, time: 'Now' }]);
      } else {
        setMessages((current) => [...current, { id: `admin-${Date.now()}`, role: 'assistant', content: 'Your message is in the Admin channel. AI replies are disabled here; a human can respond from the inbox.', time: 'Sent' }]);
      }
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Unable to send this message.');
    }
  };

  const newChat = () => {
    setMessages(defaultMessages);
    setView('chat');
    setToast('A fresh conversation is ready.');
  };

  const clearChat = () => {
    setMessages(defaultMessages);
    setToast('Conversation cleared.');
    apiRequest('/api/chat/history', { method: 'DELETE' }, sessionToken).catch(() => undefined);
  };

  const answerJourney = async (storyIndex: number, questionIndex: number, answer: string) => {
    const key = `${journeyStories[storyIndex].storyId}-${questionIndex}`;
    const next = { ...journeyAnswers, [key]: answer };
    setJourneyAnswers(next);
    sessionStorage.setItem(journeyKey, JSON.stringify(next));
    try {
      await apiRequest('/journey/start', { method: 'POST' }, sessionToken);
      const result = await apiRequest('/journey/answer', {
        method: 'POST',
        body: JSON.stringify({
          question_number: storyIndex * 10 + questionIndex + 1,
          story_id: journeyStories[storyIndex].storyId,
          answer,
        }),
      }, sessionToken);
      if (result.journey_completed) {
        setJourneyComplete(true);
        setView('chat');
        setToast('Your Journey is complete. Your reflection has been thoughtfully saved.');
      }
    } catch (error) {
      setToast(error instanceof Error ? error.message : 'Your answer could not be saved.');
    }
  };

  return (
    <div className="ds-workspace">
      <Sidebar view={view} collapsed={sidebarCollapsed} mobileOpen={mobileOpen} journeyAvailable={!journeyComplete} isAdmin={isAdmin} onView={setView} onNewChat={newChat} onClose={() => setMobileOpen(false)} />
      <main className="ds-workspace-main">
        <header className="ds-workspace-header">
          <div className="ds-header-left">
            <button className="ds-icon-button ds-menu-button" type="button" onClick={() => setMobileOpen(true)} aria-label="Open menu"><Menu size={19} /></button>
            <button className="ds-icon-button ds-collapse-button" type="button" onClick={() => setSidebarCollapsed((value) => !value)} aria-label="Toggle sidebar"><PanelLeft size={17} /></button>
            <span className="ds-header-title">{view === 'chat' ? 'New conversation' : view === 'companion' ? 'Companion' : view === 'admin' ? 'Admin inbox' : view[0].toUpperCase() + view.slice(1)}</span>
          </div>
          <div className="ds-profile-wrap">
            <button className="ds-profile-button" type="button" onClick={() => setProfileOpen((value) => !value)} aria-label="Open profile menu"><span>S</span><ChevronDown size={13} /></button>
            {profileOpen && <div className="ds-profile-menu"><div className="ds-profile-menu-head"><div className="ds-avatar">S</div><div><strong>Shri</strong><span>Private account</span></div></div><button type="button" onClick={onSignOut}><LogOut size={14} /> Sign out</button></div>}
          </div>
        </header>
        <div className="ds-workspace-content">
          {(view === 'chat' || view === 'companion') && <ChatView messages={messages} onSend={sendMessage} onClear={clearChat} mode={mode} onModeChange={setMode} />}
          {view === 'journey' && !journeyComplete && <JourneyView answers={journeyAnswers} onAnswer={answerJourney} />}
          {view === 'history' && <HistoryView onOpenChat={() => setView('chat')} />}
          {view === 'settings' && <SettingsView notifications={notifications} onNotifications={() => setNotifications((value) => !value)} />}
          {view === 'admin' && isAdmin && <AdminView onNotice={setToast} />}
        </div>
      </main>
      {toast && <div className="ds-toast" role="status">{toast}</div>}
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState<Screen>(() => sessionStorage.getItem('dearshri-screen') === 'app' ? 'app' : 'login');
  const [phone, setPhone] = useState(() => sessionStorage.getItem('dearshri-phone') ?? '');
  const [sessionToken, setSessionToken] = useState(() => sessionStorage.getItem('dearshri-session') ?? '');
  const [isAdmin, setIsAdmin] = useState(() => sessionStorage.getItem('dearshri-role') === 'admin');
  const [loginError, setLoginError] = useState('');

  const login = async (value: string, code: string) => {
    setLoginError('');
    try {
      const data = await apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ mobile_number: value, passcode: code }) });
      setPhone(data.profile.phone_number);
      setSessionToken(data.session_token);
      setIsAdmin(data.role === 'admin');
      sessionStorage.setItem('dearshri-phone', data.profile.phone_number);
      sessionStorage.setItem('dearshri-session', data.session_token);
      sessionStorage.setItem('dearshri-role', data.role);
      setScreen('intro');
      sessionStorage.setItem('dearshri-screen', 'intro');
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : 'Unable to sign in.');
    }
  };
  const start = () => {
    setScreen('app');
    sessionStorage.setItem('dearshri-screen', 'app');
  };
  const signOut = () => {
    if (sessionToken) apiRequest('/auth/logout', { method: 'POST' }, sessionToken).catch(() => undefined);
    sessionStorage.clear();
    setSessionToken('');
    setIsAdmin(false);
    setScreen('login');
  };

  if (screen === 'login') return <LoginScreen onLogin={login} externalError={loginError} />;
  if (screen === 'intro') return <IntroScreen name={phone ? 'Shri' : 'there'} onStart={start} />;
  return <AppWorkspace onSignOut={signOut} phone={phone} sessionToken={sessionToken} isAdmin={isAdmin} />;
}

export default App;