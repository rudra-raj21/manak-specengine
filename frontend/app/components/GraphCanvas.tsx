"use client";

import React, { useState, useMemo } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Info, Shield, CheckCircle, AlertTriangle } from "lucide-react";

export interface GraphNode {
  id: string;
  label: string;
  title?: string;
  type?: string; // 'Standard', 'QCO', 'TestStandard', 'Scheme', 'Ministry'
  status?: string;
  department?: string;
  year?: number;
  is_root?: boolean;
  hop?: number;
}

export interface GraphLink {
  source: string;
  target: string;
  relationship: string;
  description?: string;
}

export interface GraphData {
  root_id?: string;
  total_nodes?: number;
  total_links?: number;
  nodes: GraphNode[];
  links: GraphLink[];
}

interface GraphCanvasProps {
  data: GraphData;
  height?: number;
  onSelectNode?: (node: GraphNode) => void;
}

export default function GraphCanvas({ data, height = 450, onSelectNode }: GraphCanvasProps) {
  const [zoom, setZoom] = useState(1);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);

  // Compute radial/force positions deterministically based on nodes and hops
  const layout = useMemo(() => {
    const nodes = data.nodes || [];
    const links = data.links || [];

    if (nodes.length === 0) return { nodes: [], links: [] };

    const width = 800;
    const canvasHeight = height;
    const centerX = width / 2;
    const centerY = canvasHeight / 2;

    const rootNode = nodes.find(n => n.is_root) || nodes[0];
    const nodePositions: Record<string, { x: number; y: number }> = {};

    // Root at center
    nodePositions[rootNode.id] = { x: centerX, y: centerY };

    // Group other nodes by type / hop
    const otherNodes = nodes.filter(n => n.id !== rootNode.id);
    const qcoNodes = otherNodes.filter(n => n.type === "QCO");
    const testNodes = otherNodes.filter(n => n.type === "TestStandard" || n.label.toLowerCase().includes("test") || n.id.includes("1608") || n.id.includes("1599") || n.id.includes("1757") || n.id.includes("228"));
    const stdNodes = otherNodes.filter(n => !qcoNodes.includes(n) && !testNodes.includes(n));

    // Place QCOs in top arc
    qcoNodes.forEach((node, i) => {
      const angle = -Math.PI / 2 + (i - (qcoNodes.length - 1) / 2) * 0.6;
      const radius = 140;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    // Place Test Methods in bottom arc
    testNodes.forEach((node, i) => {
      const angle = Math.PI / 2 + (i - (testNodes.length - 1) / 2) * 0.5;
      const radius = 150;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    // Place Normative Standards in lateral arcs
    stdNodes.forEach((node, i) => {
      const isLeft = i % 2 === 0;
      const sideIndex = Math.floor(i / 2);
      const angle = isLeft ? Math.PI + (sideIndex - 1) * 0.45 : (sideIndex - 1) * 0.45;
      const radius = 175 + (i % 3) * 20;
      nodePositions[node.id] = {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });

    const positionedNodes = nodes.map(n => ({
      ...n,
      x: nodePositions[n.id]?.x || centerX + (Math.random() - 0.5) * 200,
      y: nodePositions[n.id]?.y || centerY + (Math.random() - 0.5) * 200
    }));

    const positionedLinks = links.map(l => {
      const srcPos = nodePositions[l.source] || { x: centerX, y: centerY };
      const tgtPos = nodePositions[l.target] || { x: centerX + 50, y: centerY + 50 };
      return {
        ...l,
        x1: srcPos.x,
        y1: srcPos.y,
        x2: tgtPos.x,
        y2: tgtPos.y
      };
    });

    return { nodes: positionedNodes, links: positionedLinks };
  }, [data, height]);

  const getNodeColor = (node: GraphNode) => {
    if (node.is_root) return "#00f2fe"; // Neon Cyan
    if (node.type === "QCO") return "#f59e0b"; // Amber Gold
    if (node.status === "SUPERSEDED") return "#f43f5e"; // Rose
    if (node.type === "TestStandard" || node.label.toLowerCase().includes("test") || node.id.includes("1608") || node.id.includes("1599") || node.id.includes("1757") || node.id.includes("228")) {
      return "#10b981"; // Emerald
    }
    return "#60a5fa"; // Blue
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    if (onSelectNode) onSelectNode(node);
  };

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>
        No graph relationship topology loaded.
      </div>
    );
  }

  return (
    <div style={{ position: "relative", width: "100%", height, background: "rgba(7, 11, 22, 0.8)", borderRadius: 16, overflow: "hidden", border: "1px solid rgba(255,255,255,0.06)" }}>
      {/* Controls Bar */}
      <div style={{ position: "absolute", top: 12, right: 12, zIndex: 10, display: "flex", gap: 6, background: "rgba(13, 20, 36, 0.85)", padding: 4, borderRadius: 10, border: "1px solid rgba(255,255,255,0.08)" }}>
        <button onClick={() => setZoom(z => Math.min(2, z + 0.2))} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", padding: 6 }}>
          <ZoomIn size={16} />
        </button>
        <button onClick={() => setZoom(z => Math.max(0.5, z - 0.2))} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", padding: 6 }}>
          <ZoomOut size={16} />
        </button>
        <button onClick={() => setZoom(1)} style={{ background: "transparent", border: "none", color: "#94a3b8", cursor: "pointer", padding: 6 }}>
          <RotateCcw size={16} />
        </button>
      </div>

      {/* Legend */}
      <div style={{ position: "absolute", bottom: 12, left: 12, zIndex: 10, display: "flex", gap: 12, background: "rgba(13, 20, 36, 0.85)", padding: "6px 14px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.08)", fontSize: 11 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#00f2fe" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#00f2fe", display: "inline-block" }}></span> Primary Standard
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#f59e0b" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", display: "inline-block" }}></span> Statutory QCO
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#10b981" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981", display: "inline-block" }}></span> Test Method
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 5, color: "#60a5fa" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#60a5fa", display: "inline-block" }}></span> Normative Ref
        </span>
      </div>

      {/* SVG Canvas */}
      <svg
        viewBox="0 0 800 450"
        style={{ width: "100%", height: "100%", transform: `scale(${zoom})`, transformOrigin: "center center", transition: "transform 0.2s ease" }}
      >
        <defs>
          <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="rgba(255,255,255,0.3)" />
          </marker>
        </defs>

        {/* Links */}
        {layout.links.map((link, i) => (
          <g key={`link-${i}`}>
            <line
              x1={link.x1}
              y1={link.y1}
              x2={link.x2}
              y2={link.y2}
              stroke="rgba(255, 255, 255, 0.15)"
              strokeWidth={1.5}
              strokeDasharray={link.relationship === "SUPERSEDES" ? "4,4" : undefined}
              markerEnd="url(#arrow)"
            />
            {/* Midpoint Label */}
            <text
              x={(link.x1 + link.x2) / 2}
              y={(link.y1 + link.y2) / 2 - 4}
              fill="rgba(148, 163, 184, 0.6)"
              fontSize={9}
              textAnchor="middle"
              fontFamily="monospace"
            >
              {link.relationship}
            </text>
          </g>
        ))}

        {/* Nodes */}
        {layout.nodes.map((node) => {
          const color = getNodeColor(node);
          const isSelected = selectedNode?.id === node.id;
          const isHovered = hoveredNode?.id === node.id;
          const radius = node.is_root ? 20 : node.type === "QCO" ? 17 : 14;

          return (
            <g
              key={node.id}
              transform={`translate(${node.x}, ${node.y})`}
              onClick={() => handleNodeClick(node)}
              onMouseEnter={() => setHoveredNode(node)}
              onMouseLeave={() => setHoveredNode(null)}
              style={{ cursor: "pointer" }}
            >
              {/* Glow for root or selected */}
              {(node.is_root || isSelected || isHovered) && (
                <circle
                  r={radius + 6}
                  fill="none"
                  stroke={color}
                  strokeWidth={2}
                  opacity={0.4}
                />
              )}
              {/* Node Body */}
              <circle
                r={radius}
                fill="#0d1424"
                stroke={color}
                strokeWidth={node.is_root ? 3 : 2}
              />
              {/* Node Label */}
              <text
                dy={radius + 14}
                textAnchor="middle"
                fill={isSelected ? "#ffffff" : "#cbd5e1"}
                fontSize={10}
                fontWeight={node.is_root ? 700 : 500}
                fontFamily="sans-serif"
              >
                {node.label.length > 20 ? node.label.slice(0, 18) + "..." : node.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Selected Node Drawer */}
      {selectedNode && (
        <div style={{ position: "absolute", top: 12, left: 12, width: 280, background: "rgba(14, 21, 37, 0.95)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 14, padding: 16, zIndex: 20, boxShadow: "0 10px 25px rgba(0,0,0,0.6)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
            <span style={{ fontSize: 11, textTransform: "uppercase", color: getNodeColor(selectedNode), fontWeight: 700, fontFamily: "monospace" }}>
              {selectedNode.type || "Standard"}
            </span>
            <button onClick={() => setSelectedNode(null)} style={{ background: "transparent", border: "none", color: "#64748b", cursor: "pointer", fontSize: 16 }}>×</button>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14, color: "#ffffff", marginBottom: 4 }}>
            {selectedNode.label}
          </div>
          {selectedNode.title && (
            <div style={{ fontSize: 12, color: "#94a3b8", lineHeight: 1.4, marginBottom: 8 }}>
              {selectedNode.title}
            </div>
          )}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 8 }}>
            {selectedNode.status && (
              <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: selectedNode.status === "ACTIVE" ? "rgba(16,185,129,0.15)" : "rgba(244,63,94,0.15)", color: selectedNode.status === "ACTIVE" ? "#10b981" : "#f43f5e", border: "1px solid rgba(255,255,255,0.08)" }}>
                {selectedNode.status}
              </span>
            )}
            {selectedNode.year && (
              <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "rgba(255,255,255,0.06)", color: "#cbd5e1" }}>
                Year: {selectedNode.year}
              </span>
            )}
            {selectedNode.department && (
              <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: "rgba(0,242,254,0.1)", color: "#00f2fe" }}>
                {selectedNode.department}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
