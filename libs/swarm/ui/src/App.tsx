import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { 
  Activity, 
  ShieldCheck, 
  RefreshCcw, 
  Database, 
  Cpu, 
  Eye, 
  AlertTriangle,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types
interface Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  status: 'pending' | 'approved' | 'rejected' | 'overridden' | 'completed';
  agent: string;
  timestamp: string;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
}

const MOCK_DATA = {
  nodes: [
    { id: '1', label: 'Market Research', status: 'completed', agent: 'researcher', timestamp: '2026-04-26T16:00:00' },
    { id: '2', label: 'Risk Analysis', status: 'approved', agent: 'validator', timestamp: '2026-04-26T16:05:00' },
    { id: '3', label: 'Transaction Execution', status: 'overridden', agent: 'executor', timestamp: '2026-04-26T16:10:00' },
    { id: '4', label: 'Ledger Audit', status: 'pending', agent: 'curator', timestamp: '2026-04-26T16:12:00' },
    { id: '5', label: 'Compliance Report', status: 'pending', agent: 'curator', timestamp: '2026-04-26T16:15:00' },
  ],
  links: [
    { source: '1', target: '2' },
    { source: '2', target: '3' },
    { source: '3', target: '4' },
    { source: '3', target: '5' },
  ]
};

const App: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [entropy, setEntropy] = useState(0.42);
  const [coherence, setCoherence] = useState(0.89);

  useEffect(() => {
    if (!svgRef.current) return;

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    const simulation = d3.forceSimulation<Node>(MOCK_DATA.nodes as any)
      .force("link", d3.forceLink<Node, Link>(MOCK_DATA.links as any).id(d(d as any).id).distance(150))
      .force("charge", d3.forceManyBody().strength(-500))
      .force("center", d3.forceCenter(width / 2, height / 2));

    const link = g.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(MOCK_DATA.links)
      .enter().append("line")
      .attr("class", "link causal");

    const node = g.append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(MOCK_DATA.nodes)
      .enter().append("circle")
      .attr("class", d => `node status-${d.status}`)
      .attr("r", 12)
      .on("click", (event, d) => setSelectedNode(d as any))
      .call(d3.drag<SVGCircleElement, any>()
        .on("start", (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on("drag", (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on("end", (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any);

    const labels = g.append("g")
      .selectAll("text")
      .data(MOCK_DATA.nodes)
      .enter().append("text")
      .attr("class", "mono")
      .attr("dy", 30)
      .attr("text-anchor", "middle")
      .attr("fill", "rgba(255,255,255,0.6)")
      .text(d => d.label);

    simulation.on("tick", () => {
      link
        .attr("x1", d => (d.source as any).x)
        .attr("y1", d => (d.source as any).y)
        .attr("x2", d => (d.target as any).x)
        .attr("y2", d => (d.target as any).y);

      node
        .attr("cx", d => d.x!)
        .attr("cy", d => d.y!);
      
      labels
        .attr("x", d => d.x!)
        .attr("y", d => d.y!);
    });

    return () => simulation.stop();
  }, []);

  return (
    <div className="dashboard-grid">
      {/* Left Sidebar: Observability Plane */}
      <aside className="glass p-6 flex flex-col gap-8">
        <div>
          <h2 className="text-2xl font-bold gradient-text mb-2 flex items-center gap-2">
            <Activity className="text-primary" /> Observability Plane
          </h2>
          <p className="text-sm opacity-60">Real-time OpenTelemetry semantic metrics</p>
        </div>

        <div className="space-y-6">
          <MetricCard 
            label="Epistemic Entropy" 
            value={`${entropy.toFixed(3)} bits`} 
            icon={<Cpu size={18} />} 
            progress={entropy}
          />
          <MetricCard 
            label="Swarm Coherence" 
            value={`${(coherence * 100).toFixed(0)}%`} 
            icon={<ShieldCheck size={18} />} 
            progress={coherence}
          />
          <div className="p-4 glass bg-primary/5 border-primary/20">
            <div className="flex items-center gap-2 text-primary mb-2">
              <Database size={16} /> 
              <span className="text-xs font-bold uppercase tracking-wider">Provenance Engine</span>
            </div>
            <p className="text-xs opacity-80 leading-relaxed">
              Every execution path is logged as an immutable record with SHA-256 integrity validation.
            </p>
          </div>
        </div>

        <div className="mt-auto">
          <div className="flex items-center gap-2 text-xs opacity-50 mb-4 uppercase tracking-[0.2em]">
            Recent Logs
          </div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="flex gap-3 text-xs mono opacity-70">
                <span className="text-primary">{'>'}</span>
                <span>Agent.v{i} registered transition</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content: Causal Visualization */}
      <main className="relative glass overflow-hidden">
        <div className="absolute top-6 left-6 z-10">
          <div className="flex items-center gap-3 px-4 py-2 glass bg-white/5">
            <Eye size={16} className="text-accent" />
            <span className="text-sm font-semibold uppercase tracking-widest">Causal DAG Visualization</span>
          </div>
        </div>
        <svg ref={svgRef} className="w-full h-full" />
      </main>

      {/* Right Sidebar: Human-in-the-loop Control */}
      <aside className="glass p-6">
        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
          <RefreshCcw size={20} className="text-secondary" /> Governance
        </h2>

        <AnimatePresence mode="wait">
          {selectedNode ? (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div className="p-4 glass bg-white/5 border-white/10">
                <div className="text-[10px] uppercase tracking-widest opacity-40 mb-1">Node Detail</div>
                <div className="text-lg font-semibold">{selectedNode.label}</div>
                <div className="text-xs mono opacity-60 mt-1">{selectedNode.id}</div>
              </div>

              <div className="space-y-4">
                <DetailRow label="Agent" value={selectedNode.agent} />
                <DetailRow label="Status" value={selectedNode.status.toUpperCase()} />
                <DetailRow label="Checksum" value="SHA-256: 8a4c...f2e" />
              </div>

              <div className="pt-6 border-t border-white/10 space-y-4">
                <button 
                  className="w-full py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 transition-colors flex items-center justify-center gap-2 text-sm font-bold shadow-lg shadow-indigo-500/20"
                  onClick={() => alert('Triggering immediate subgraph re-computation...')}
                >
                  <AlertTriangle size={16} /> ONE-CLICK OVERRIDE
                </button>
                <p className="text-[10px] text-center opacity-40 leading-relaxed italic">
                  Overrides trigger an immediate subgraph re-computation across the neural fabric.
                </p>
              </div>
            </motion.div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-30">
              <div className="p-6 rounded-full border-2 border-dashed border-white/20 mb-4">
                <ChevronRight size={32} />
              </div>
              <p className="text-sm">Select a node to intervene in the swarm execution path</p>
            </div>
          )}
        </AnimatePresence>

        <div className="absolute bottom-6 left-6 right-6 p-4 glass bg-secondary/5 border-secondary/20">
          <div className="text-[10px] font-bold uppercase text-secondary mb-2">Self-Distillation Loop</div>
          <div className="flex justify-between items-end">
            <span className="text-xs opacity-60">LoRA Updates</span>
            <span className="text-lg font-bold mono">14.2K</span>
          </div>
        </div>
      </aside>
    </div>
  );
};

const MetricCard: React.FC<{ label: string, value: string, icon: React.ReactNode, progress: number }> = ({ label, value, icon, progress }) => (
  <div className="space-y-2">
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-2 opacity-70">
        {icon}
        <span className="text-xs font-medium">{label}</span>
      </div>
      <span className="text-sm font-bold mono">{value}</span>
    </div>
    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: `${progress * 100}%` }}
        className="h-full bg-primary"
      />
    </div>
  </div>
);

const DetailRow: React.FC<{ label: string, value: string }> = ({ label, value }) => (
  <div className="flex justify-between items-center text-sm">
    <span className="opacity-50">{label}</span>
    <span className="font-medium">{value}</span>
  </div>
);

export default App;
