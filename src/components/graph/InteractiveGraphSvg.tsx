import React from 'react';
import NodeBox from './NodeBox';


interface Props {
  activeNode: string;
  isRunning: boolean;
  selectedNode: string;
  onSelectNode: (node: string) => void;
  nodeVisitCounts: Record<string, number>;
  large?: boolean;
}

export default function InteractiveGraphSvg({
  activeNode,
  isRunning,
  selectedNode,
  onSelectNode,
  nodeVisitCounts,
  large = false,
}: Props) {
  const svgWidth = large ? 480 : 310;
  const svgHeight = large ? 430 : 340;
  const scale = large ? 1.3 : 1;

  const nodePositions: Record<string, { x: number; y: number; w: number; h: number }> = {
    __start__: { x: (svgWidth / 2) - (48 * scale), y: 12 * scale, w: 96 * scale, h: 28 * scale },
    knowledge_retrieval: { x: (svgWidth / 2) - (78 * scale), y: 64 * scale, w: 156 * scale, h: 42 * scale },
    reasoning: { x: (svgWidth / 2) - (78 * scale), y: 138 * scale, w: 156 * scale, h: 46 * scale },
    tool_execution: { x: (svgWidth / 2) - (78 * scale), y: 220 * scale, w: 156 * scale, h: 44 * scale },
    __end__: { x: (svgWidth / 2) - (48 * scale), y: 295 * scale, w: 96 * scale, h: 28 * scale },
  };

  const isNodeActive = (id: string) => (activeNode === id || (id === 'reasoning' && activeNode === 'response_generation')) && isRunning;
  const isNodeVisited = (id: string) => Boolean(nodeVisitCounts[id]);

  return (
    <svg
      width={svgWidth}
      height={svgHeight}
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      className="overflow-visible select-none"
    >
      <defs>
        <marker id="arrow-default" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
          <polygon points="0 0, 6 3, 0 6" fill="#64748b" />
        </marker>
        <marker id="arrow-cyan" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#38bdf8" />
        </marker>
        <marker id="arrow-purple" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#c084fc" />
        </marker>
        <marker id="arrow-amber" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#f59e0b" />
        </marker>
        <marker id="arrow-emerald" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#34d399" />
        </marker>
      </defs>

      {/* 1. START -> knowledge_retrieval */}
      <line
        x1={nodePositions.__start__.x + nodePositions.__start__.w / 2}
        y1={nodePositions.__start__.y + nodePositions.__start__.h}
        x2={nodePositions.knowledge_retrieval.x + nodePositions.knowledge_retrieval.w / 2}
        y2={nodePositions.knowledge_retrieval.y}
        stroke={isNodeActive('knowledge_retrieval') ? '#38bdf8' : '#475569'}
        strokeWidth={isNodeActive('knowledge_retrieval') ? '2.5' : '1.5'}
        markerEnd={isNodeActive('knowledge_retrieval') ? 'url(#arrow-cyan)' : 'url(#arrow-default)'}
        strokeDasharray={isNodeActive('knowledge_retrieval') ? '4 2' : 'none'}
      />

      {/* 2. knowledge_retrieval -> reasoning */}
      <line
        x1={nodePositions.knowledge_retrieval.x + nodePositions.knowledge_retrieval.w / 2}
        y1={nodePositions.knowledge_retrieval.y + nodePositions.knowledge_retrieval.h}
        x2={nodePositions.reasoning.x + nodePositions.reasoning.w / 2}
        y2={nodePositions.reasoning.y}
        stroke={isNodeActive('reasoning') ? '#c084fc' : '#475569'}
        strokeWidth={isNodeActive('reasoning') ? '2.5' : '1.5'}
        markerEnd={isNodeActive('reasoning') ? 'url(#arrow-purple)' : 'url(#arrow-default)'}
        strokeDasharray={isNodeActive('reasoning') ? '4 2' : 'none'}
      />

      {/* 3. reasoning -> tool_execution */}
      <line
        x1={nodePositions.reasoning.x + nodePositions.reasoning.w / 2}
        y1={nodePositions.reasoning.y + nodePositions.reasoning.h}
        x2={nodePositions.tool_execution.x + nodePositions.tool_execution.w / 2}
        y2={nodePositions.tool_execution.y}
        stroke={isNodeActive('tool_execution') ? '#f59e0b' : '#475569'}
        strokeWidth={isNodeActive('tool_execution') ? '2.5' : '1.5'}
        strokeDasharray="4 3"
        markerEnd={isNodeActive('tool_execution') ? 'url(#arrow-amber)' : 'url(#arrow-default)'}
      />
      <text
        x={nodePositions.reasoning.x + nodePositions.reasoning.w / 2 + 6}
        y={nodePositions.reasoning.y + nodePositions.reasoning.h + 16 * scale}
        fill="#94a3b8"
        fontSize={8.5 * scale}
      >
        [调用工具]
      </text>
      {/* 4. tool_execution -> reasoning (循环回流) */}
      <path
        d={`M ${nodePositions.tool_execution.x + nodePositions.tool_execution.w} ${nodePositions.tool_execution.y + 20 * scale}
            C ${svgWidth - 14} ${nodePositions.tool_execution.y + 20 * scale},
              ${svgWidth - 14} ${nodePositions.reasoning.y + 22 * scale},
              ${nodePositions.reasoning.x + nodePositions.reasoning.w} ${nodePositions.reasoning.y + 22 * scale}`}
        fill="none"
        stroke={isNodeActive('reasoning') && nodeVisitCounts['tool_execution'] ? '#f59e0b' : '#64748b'}
        strokeWidth={isNodeActive('reasoning') && nodeVisitCounts['tool_execution'] ? '2.5' : '1.5'}
        strokeDasharray="3 3"
        markerEnd="url(#arrow-amber)"
      />
      <text
        x={svgWidth - 52 * scale}
        y={nodePositions.reasoning.y + 44 * scale}
        fill="#f59e0b"
        fontSize={8.5 * scale}
      >
        回流反馈
      </text>

      {/* 5. reasoning -> END */}
      <path
        d={`M ${nodePositions.reasoning.x} ${nodePositions.reasoning.y + 22 * scale}
            C ${16 * scale} ${nodePositions.reasoning.y + 22 * scale},
              ${16 * scale} ${nodePositions.__end__.y + 14 * scale},
              ${nodePositions.__end__.x} ${nodePositions.__end__.y + 14 * scale}`}
        fill="none"
        stroke={isNodeActive('__end__') || (!isRunning && nodeVisitCounts['reasoning']) ? '#34d399' : '#475569'}
        strokeWidth={isNodeActive('__end__') ? '2.5' : '1.5'}
        strokeDasharray="4 3"
        markerEnd="url(#arrow-emerald)"
      />
      <text
        x={18 * scale}
        y={nodePositions.reasoning.y + 56 * scale}
        fill="#34d399"
        fontSize={8.5 * scale}
      >
        [答复/结束]
      </text>
      {/* START 节点 */}
      <g className="cursor-pointer" onClick={() => onSelectNode('__start__')}>
        <rect
          x={nodePositions.__start__.x}
          y={nodePositions.__start__.y}
          width={nodePositions.__start__.w}
          height={nodePositions.__start__.h}
          rx={nodePositions.__start__.h / 2}
          fill="#064e3b"
          stroke={selectedNode === '__start__' ? '#34d399' : '#059669'}
          strokeWidth={selectedNode === '__start__' ? '2' : '1'}
        />
        <text
          x={nodePositions.__start__.x + nodePositions.__start__.w / 2}
          y={nodePositions.__start__.y + 18 * scale}
          textAnchor="middle"
          fill="#a7f3d0"
          fontSize={11 * scale}
          fontWeight="bold"
        >
          START 起点
        </text>
      </g>

      {/* 知识检索 RAG */}
      <NodeBox
        pos={nodePositions.knowledge_retrieval}
        label="📚 知识检索 (RAG)"
        subLabel="向量/关键词混合"
        isActive={isNodeActive('knowledge_retrieval')}
        isSelected={selectedNode === 'knowledge_retrieval'}
        isVisited={isNodeVisited('knowledge_retrieval')}
        count={nodeVisitCounts['knowledge_retrieval']}
        activeColor="#38bdf8"
        scale={scale}
        onClick={() => onSelectNode('knowledge_retrieval')}
      />

      {/* 决策推理 Reasoning */}
      <NodeBox
        pos={nodePositions.reasoning}
        label="🧠 决策推理 (LLM)"
        subLabel="ReAct 规划与工具决策"
        isActive={isNodeActive('reasoning')}
        isSelected={selectedNode === 'reasoning'}
        isVisited={isNodeVisited('reasoning')}
        count={nodeVisitCounts['reasoning']}
        activeColor="#c084fc"
        scale={scale}
        onClick={() => onSelectNode('reasoning')}
      />

      {/* 工具执行 Tool Execution */}
      <NodeBox
        pos={nodePositions.tool_execution}
        label="🔧 工具执行 (Tools)"
        subLabel="9项运维自主/确认工具"
        isActive={isNodeActive('tool_execution')}
        isSelected={selectedNode === 'tool_execution'}
        isVisited={isNodeVisited('tool_execution')}
        count={nodeVisitCounts['tool_execution']}
        activeColor="#f59e0b"
        scale={scale}
        onClick={() => onSelectNode('tool_execution')}
      />

      {/* END 节点 */}
      <g className="cursor-pointer" onClick={() => onSelectNode('__end__')}>
        <rect
          x={nodePositions.__end__.x}
          y={nodePositions.__end__.y}
          width={nodePositions.__end__.w}
          height={nodePositions.__end__.h}
          rx={nodePositions.__end__.h / 2}
          fill="#134e4a"
          stroke={selectedNode === '__end__' ? '#2dd4bf' : '#0d9488'}
          strokeWidth={selectedNode === '__end__' ? '2' : '1'}
        />
        <text
          x={nodePositions.__end__.x + nodePositions.__end__.w / 2}
          y={nodePositions.__end__.y + 18 * scale}
          textAnchor="middle"
          fill="#99f6e4"
          fontSize={11 * scale}
          fontWeight="bold"
        >
          END 终点
        </text>
      </g>


    </svg>
  );
}
