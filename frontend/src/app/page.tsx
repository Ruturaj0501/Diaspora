import UploadSection from '@/components/UploadSection';
import CopilotChat from '@/components/CopilotChat';

export default function Home() {
  const pillars = [
    { title: "Plantation Archive Recovery", desc: "Digitization and indexing of labor rosters, birth registries, and housing records from major colonial zones." },
    { title: "Slave Trade Port Intelligence", desc: "Integration of transatlantic voyage manifests and auction house ledgers to track identity linkage." },
    { title: "Probate & Estate Forensics", desc: "Tracing ancestry through wills and estate divisions where enslaved persons were listed by name." },
    { title: "Corporate & Insurance Documentation", desc: "Analysis of mortality claims and insurance policies identifying enslaved individuals as assets." },
    { title: "Reconstruction Identity Systems", desc: "Post-emancipation documentation including Freedmen’s Bureau records and marriage registrations." },
    { title: "Genetic Genealogy Integration", desc: "DNA dataset integration to confirm lineage hypotheses and regional African origins." }
  ];

  const impacts = [
    { title: "Restored Registries", desc: "Comprehensive databases of names once lost to time, now reclaimed for history." },
    { title: "Ancestral Maps", desc: "Geospatial mapping of migration corridors and community clusters." },
    { title: "Lineage Reconnection", desc: "Bridging the gap between modern descendants and pre-emancipation kinship networks." }
  ];

  return (
    <main className="min-h-screen bg-background text-foreground selection:bg-accent/30 overflow-x-hidden scroll-smooth">
      {/* Background Ambience */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none opacity-20">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent/10 rounded-full blur-[120px]" />
      </div>

      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-white/5 glass-dark px-8 py-4 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center font-serif text-accent-foreground font-bold text-xl shadow-[0_0_15px_rgba(212,175,55,0.4)]">D</div>
          <span className="font-serif text-xl tracking-tight font-bold">DIRP <span className="text-accent">Archival Intelligence</span></span>
        </div>
        <div className="hidden lg:flex items-center space-x-6 text-[10px] uppercase tracking-[0.2em] font-bold text-muted-foreground transition-all">
          <a href="#pillars" className="hover:text-accent transition-colors">Pillars</a>
          <a href="#pipeline" className="hover:text-accent transition-colors">Pipeline</a>
          <a href="#copilot" className="hover:text-accent transition-colors">Research Copilot</a>
          <a href="#impact" className="hover:text-accent transition-colors">Impact</a>
          <a href="#governance" className="hover:text-accent transition-colors">Governance</a>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="relative z-10 container mx-auto px-8 pt-24 pb-16 text-center max-w-4xl">
        <div className="inline-block px-4 py-1 border border-accent/30 rounded-full text-[10px] uppercase tracking-[0.3em] text-accent font-bold mb-6">Transnational Archival Initiative</div>
        <h1 className="text-5xl md:text-7xl font-serif mb-6 leading-tight text-white font-bold tracking-tight">
          Reconstructing the <span className="text-accent text-glow">Diaspora Identity Gap</span>
        </h1>
        <p className="text-xl text-muted-foreground font-serif italic mb-8 max-w-2xl mx-auto leading-relaxed">
          Establishing the first unified identity restoration framework for populations historically documented as property rather than persons.
        </p>
      </header>

      {/* Research Pillars Section */}
      <section id="pillars" className="relative z-10 container mx-auto px-8 pb-32 scroll-mt-24">
        <div className="mb-12 text-center lg:text-left">
          <h2 className="text-3xl font-serif font-bold text-white mb-2">Research Pillars</h2>
          <div className="h-1 w-20 bg-accent mx-auto lg:mx-0" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((p, idx) => (
            <div key={idx} className="glass p-6 rounded-2xl border-white/5 hover:border-accent/30 transition-all group">
              <div className="text-accent font-serif font-bold text-2xl mb-4 opacity-50 group-hover:opacity-100 transition-opacity">0{idx + 1}</div>
              <h3 className="text-lg font-bold text-white mb-2">{p.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline & Copilot Grid */}
      <section className="relative z-10 container mx-auto px-8 pb-32 grid grid-cols-1 lg:grid-cols-2 gap-12">
        <div className="space-y-12">
          <div id="pipeline" className="scroll-mt-24">
            <div className="mb-8">
              <h2 className="text-3xl font-serif font-bold text-white mb-2">Ingestion Pipeline</h2>
              <p className="text-sm text-muted-foreground italic font-serif">Convert manuscripts into structured identity nodes.</p>
            </div>
            <UploadSection />
          </div>

          <div className="glass p-8 rounded-2xl border-white/5 opacity-60">
            <h3 className="text-xl font-serif font-bold text-white mb-4">Archival Protocol</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Every document uploaded undergoes multi-phase AI analysis including OCR, entity extraction, and biometric phonetic normalization to bridge the diaspora gap.
            </p>
          </div>
        </div>

        <div id="copilot" className="lg:pt-0 scroll-mt-24">
          <div className="mb-8 lg:text-right">
            <h2 className="text-3xl font-serif font-bold text-white mb-2">Archival Copilot</h2>
            <p className="text-sm text-muted-foreground italic font-serif">Query ancestral lineages using natural language.</p>
          </div>
          <CopilotChat />
        </div>
      </section>

      {/* Historical Impact Section */}
      <section id="impact" className="relative z-10 container mx-auto px-8 pb-32 scroll-mt-24">
        <div className="mb-12 text-center lg:text-right">
          <h2 className="text-3xl font-serif font-bold text-white mb-2">Historical Impact</h2>
          <div className="h-1 w-20 bg-accent ml-auto mr-auto lg:ml-auto lg:mr-0" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {impacts.map((item, idx) => (
            <div key={idx} className="glass p-8 rounded-2xl border-white/5 text-center space-y-4 hover:border-accent/20 transition-all">
              <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center mx-auto border border-accent/20">
                <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
              </div>
              <h4 className="text-white font-bold">{item.title}</h4>
              <p className="text-xs text-muted-foreground leading-relaxed italic">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Governance Section */}
      <section id="governance" className="relative z-10 container mx-auto px-8 pb-32 scroll-mt-24">
        <div className="glass p-8 rounded-2xl border-white/5 bg-accent/5">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <div className="lg:col-span-1">
              <h2 className="text-3xl font-serif font-bold text-white mb-4">Governance & Ethics</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                DIRP operates under strict archival ethics. Our system ensures immutable audit logging and descendant consent enforcement across all reconstruction phases.
              </p>
            </div>
            <div className="lg:col-span-2 flex items-center">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-accent rounded-full" />
                  <h4 className="text-accent text-[10px] uppercase tracking-widest font-bold">Consent Registry Active</h4>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Decedents and descendants retain the right to revoke archival visibility via the Forensic Consent Block. Every reconstruction phase is logged with AI provenance for institutional accountability.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stakeholder Ecosystem */}
      <section className="relative z-10 container mx-auto px-8 pb-24 border-t border-white/5 pt-16">
        <div className="text-center mb-12">
          <p className="text-[10px] uppercase tracking-[0.3em] font-bold text-muted-foreground">Institutional Stakeholders</p>
        </div>
        <div className="flex flex-wrap justify-center gap-8 opacity-40 grayscale hover:grayscale-0 transition-all duration-700">
          {["National Archives", "United Universities", "Cultural Museums", "Genealogical Societies", "Reparative Justice Bodies"].map((s) => (
            <span key={s} className="font-serif text-sm italic py-2 px-4 border border-white/10 rounded-full">{s}</span>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-12 bg-black/50">
        <div className="container mx-auto px-8 flex flex-col md:flex-row justify-between items-center opacity-50 space-y-4 md:space-y-0 text-[10px] uppercase tracking-widest font-bold">
          <p>© 2026 Diaspora Identity Reconstruction Program™</p>
          <div className="flex space-x-8">
            <a href="#" className="hover:text-white transition-colors">Privacy Protocol</a>
            <a href="#" className="hover:text-white transition-colors">Retention Ethics</a>
            <a href="#" className="hover:text-white transition-colors">API Documentation</a>
          </div>
        </div>
      </footer>
    </main>
  );
}
