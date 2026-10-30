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
  const svgWidth = large ? 480 : 320;
  const svgHeight = large ? 530 : 415;
  const scale = large ? 1.3 : 1;

  const nodePositions: Record<string, { x: number; y: number; w: number; h: number }> = {
    __start__: { x: (svgWidth / 2) - (46 * scale), y: 10 * scale, w: 92 * scale, h: 26 * scale },
    guardrail_check: { x: (svgWidth / 2) - (78 * scale), y: 48 * scale, w: 156 * scale, h: 36 * scale },
    knowledge_retrieval: { x: (svgWidth / 2) - (78 * scale), y: 104 * scale, w: 156 * scale, h: 38 * scale },
    reasoning: { x: (svgWidth / 2) - (78 * scale), y: 162 * scale, w: 156 * scale, h: 42 * scale },
    tool_execution: { x: (svgWidth / 2) - (78 * scale), y: 226 * scale, w: 156 * scale, h: 40 * scale },
    hitl_gate: { x: (svgWidth / 2) - (78 * scale), y: 290 * scale, w: 156 * scale, h: 40 * scale },
    __end__: { x: (svgWidth / 2) - (46 * scale), y: 356 * scale, w: 92 * scale, h: 26 * scale },
  };

  const isNodeActive = (id: string) =>
    (activeNode === id ||
      (id === 'reasoning' && activeNode === 'response_generation') ||
      (id === 'guardrail_check' && activeNode === 'guardrail_check') ||
      (id === 'hitl_gate' && (activeNode === 'hitl_gate' || activeNode === 'hitl_request'))) &&
    isRunning;
  const isNodeVisited = (id: string) => Boolean(nodeVisitCounts[id]);

  const isShortCircuitPathActive =
    isNodeActive('guardrail_check') ||
    (!isRunning && Boolean(nodeVisitCounts['guardrail_check']) && !nodeVisitCounts['knowledge_retrieval']);

  const isHitlPathActive =
    isNodeActive('hitl_gate') ||
    Boolean(nodeVisitCounts['hitl_gate']);

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
        <marker id="arrow-rose" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#f43f5e" />
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
        <marker id="arrow-orange" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#f97316" />
        </marker>
        <marker id="arrow-emerald" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">
          <polygon points="0 0, 7 3.5, 0 7" fill="#34d399" />
        </marker>
      </defs>

      {/* 1. START -> guardrail_check */}
      <line
        x1={nodePositions.__start__.x + nodePositions.__start__.w / 2}
        y1={nodePositions.__start__.y + nodePositions.__start__.h}
        x2={nodePositions.guardrail_check.x + nodePositions.guardrail_check.w / 2}
        y2={nodePositions.guardrail_check.y}
        stroke={isNodeActive('guardrail_check') ? '#f43f5e' : '#475569'}
        strokeWidth={isNodeActive('guardrail_check') ? '2.5' : '1.5'}
        markerEnd={isNodeActive('guardrail_check') ? 'url(#arrow-rose)' : 'url(#arrow-default)'}
        strokeDasharray={isNodeActive('guardrail_check') ? '4 2' : 'none'}
      />

      {/* 2. guardrail_check -> knowledge_retrieval (合规流转) */}
      <line
        x1={nodePositions.guardrail_check.x + nodePositions.guardrail_check.w / 2}
        y1={nodePositions.guardrail_check.y + nodePositions.guardrail_check.h}
        x2={nodePositions.knowledge_retrieval.x + nodePositions.knowledge_retrieval.w / 2}
        y2={nodePositions.knowledge_retrieval.y}
        stroke={isNodeActive('knowledge_retrieval') ? '#38bdf8' : '#475569'}
        strokeWidth={isNodeActive('knowledge_retrieval') ? '2.5' : '1.5'}
        markerEnd={isNodeActive('knowledge_retrieval') ? 'url(#arrow-cyan)' : 'url(#arrow-default)'}
        strokeDasharray={isNodeActive('knowledge_retrieval') ? '4 2' : 'none'}
      />
      <text
        x={nodePositions.guardrail_check.x + nodePositions.guardrail_check.w / 2 + 6}
        y={nodePositions.guardrail_check.y + nodePositions.guardrail_check.h + 14 * scale}
        fill="#94a3b8"
        fontSize={8 * scale}
      >
        [合规业务]
      </text>

      {/* 3. guardrail_check -> END (微秒级短路流: 攻击拦截/偏离引导) */}
      <path
        d={`M ${nodePositions.guardrail_check.x} ${nodePositions.guardrail_check.y + 19 * scale}
            C ${10 * scale} ${nodePositions.guardrail_check.y + 19 * scale},
              ${10 * scale} ${nodePositions.__end__.y + 13 * scale},
              ${nodePositions.__end__.x} ${nodePositions.__end__.y + 13 * scale}`}
        fill="none"
        stroke={isShortCircuitPathActive ? '#f43f5e' : '#334155'}
        strokeWidth={isShortCircuitPathActive ? '2.5' : '1.2'}
        strokeDasharray="4 3"
        markerEnd={isShortCircuitPathActive ? 'url(#arrow-rose)' : 'url(#arrow-default)'}
      />
      <text
        x={12 * scale}
        y={nodePositions.guardrail_check.y + 36 * scale}
        fill={isShortCircuitPathActive ? '#f43f5e' : '#64748b'}
        fontSize={8 * scale}
        fontWeight={isShortCircuitPathActive ? 'bold' : 'normal'}
      >
        [快速短路]
      </text>

      {/* 4. knowledge_retrieval -> reasoning */}
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

      {/* 5. reasoning -> tool_execution */}
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
      {/* 6. tool_execution -> reasoning (只读结果回流) */}
      <path
        d={`M ${nodePositions.tool_execution.x + nodePositions.tool_execution.w} ${nodePositions.tool_execution.y + 18 * scale}
            C ${svgWidth - 14} ${nodePositions.tool_execution.y + 18 * scale},
              ${svgWidth - 14} ${nodePositions.reasoning.y + 20 * scale},
              ${nodePositions.reasoning.x + nodePositions.reasoning.w} ${nodePositions.reasoning.y + 20 * scale}`}
        fill="none"
        stroke={isNodeActive('reasoning') && nodeVisitCounts['tool_execution'] ? '#f59e0b' : '#64748b'}
        strokeWidth={isNodeActive('reasoning') && nodeVisitCounts['tool_execution'] ? '2.5' : '1.5'}
        strokeDasharray="3 3"
        markerEnd="url(#arrow-amber)"
      />
      <text
        x={svgWidth - 52 * scale}
        y={nodePositions.reasoning.y + 40 * scale}
        fill="#f59e0b"
        fontSize={8 * scale}
      >
        只读回流
      </text>

      {/* 7. tool_execution -> hitl_gate (写操作门禁挂起卡片) */}
      <line
        x1={nodePositions.tool_execution.x + nodePositions.tool_execution.w / 2}
        y1={nodePositions.tool_execution.y + nodePositions.tool_execution.h}
        x2={nodePositions.hitl_gate.x + nodePositions.hitl_gate.w / 2}
        y2={nodePositions.hitl_gate.y}
        stroke={isHitlPathActive ? '#f97316' : '#475569'}
        strokeWidth={isHitlPathActive ? '2.5' : '1.5'}
        strokeDasharray="4 2"
        markerEnd={isHitlPathActive ? 'url(#arrow-orange)' : 'url(#arrow-default)'}
      />
      <text
        x={nodePositions.tool_execution.x + nodePositions.tool_execution.w / 2 + 6}
        y={nodePositions.tool_execution.y + nodePositions.tool_execution.h + 16 * scale}
        fill={isHitlPathActive ? '#fb923c' : '#94a3b8'}
        fontSize={8 * scale}
        fontWeight={isHitlPathActive ? 'bold' : 'normal'}
      >
        [写操作拦截]
      </text>

      {/* 8. hitl_gate -> tool_execution (人工授权执行回流) */}
      <path
        d={`M ${nodePositions.hitl_gate.x + nodePositions.hitl_gate.w} ${nodePositions.hitl_gate.y + 18 * scale}
            C ${svgWidth - 26} ${nodePositions.hitl_gate.y + 18 * scale},
              ${svgWidth - 26} ${nodePositions.tool_execution.y + 28 * scale},
              ${nodePositions.tool_execution.x + nodePositions.tool_execution.w} ${nodePositions.tool_execution.y + 28 * scale}`}
        fill="none"
        stroke={isNodeActive('tool_execution') && nodeVisitCounts['hitl_gate'] ? '#10b981' : '#334155'}
        strokeWidth="1.5"
        strokeDasharray="2 2"
        markerEnd="url(#arrow-emerald)"
      />
      <text
        x={svgWidth - 44 * scale}
        y={nodePositions.hitl_gate.y - 4 * scale}
        fill="#34d399"
        fontSize={7.5 * scale}
      >
        授权执行
      </text>

      {/* 9. hitl_gate -> END (卡片取消/撤销) */}
      <line
        x1={nodePositions.hitl_gate.x + nodePositions.hitl_gate.w / 2}
        y1={nodePositions.hitl_gate.y + nodePositions.hitl_gate.h}
        x2={nodePositions.__end__.x + nodePositions.__end__.w / 2}
        y2={nodePositions.__end__.y}
        stroke="#475569"
        strokeWidth="1.2"
        strokeDasharray="3 3"
        markerEnd="url(#arrow-default)"
      />
      <text
        x={nodePositions.hitl_gate.x + nodePositions.hitl_gate.w / 2 + 6}
        y={nodePositions.hitl_gate.y + nodePositions.hitl_gate.h + 14 * scale}
        fill="#64748b"
        fontSize={7.5 * scale}
      >
        [取消/归档]
      </text>

      {/* 10. reasoning -> END */}
      <path
        d={`M ${nodePositions.reasoning.x} ${nodePositions.reasoning.y + 20 * scale}
            C ${36 * scale} ${nodePositions.reasoning.y + 20 * scale},
              ${36 * scale} ${nodePositions.__end__.y + 13 * scale},
              ${nodePositions.__end__.x} ${nodePositions.__end__.y + 13 * scale}`}
        fill="none"
        stroke={isNodeActive('__end__') || (!isRunning && Boolean(nodeVisitCounts['reasoning'])) ? '#34d399' : '#475569'}
        strokeWidth={isNodeActive('__end__') ? '2.5' : '1.5'}
        strokeDasharray="4 3"
        markerEnd="url(#arrow-emerald)"
      />
      <text
        x={40 * scale}
        y={nodePositions.reasoning.y + 40 * scale}
        fill="#34d399"
        fontSize={8 * scale}
      >
        [答复完成]
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

      {/* 0. 安全护栏 Guardrails */}
      <NodeBox
        pos={nodePositions.guardrail_check}
        label="🛡️ 安全护栏 (Guardrails)"
        subLabel="前置审查与快速短路"
        isActive={isNodeActive('guardrail_check')}
        isSelected={selectedNode === 'guardrail_check'}
        isVisited={isNodeVisited('guardrail_check')}
        count={nodeVisitCounts['guardrail_check']}
        activeColor="#f43f5e"
        scale={scale}
        onClick={() => onSelectNode('guardrail_check')}
      />

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
        subLabel="自主业务与执行适配"
        isActive={isNodeActive('tool_execution')}
        isSelected={selectedNode === 'tool_execution'}
        isVisited={isNodeVisited('tool_execution')}
        count={nodeVisitCounts['tool_execution']}
        activeColor="#f59e0b"
        scale={scale}
        onClick={() => onSelectNode('tool_execution')}
      />

      {/* 人机协同门禁 HITL */}
      <NodeBox
        pos={nodePositions.hitl_gate}
        label="👤 人机协同 (HITL)"
        subLabel="写操作卡片确认与授权"
        isActive={isNodeActive('hitl_gate')}
        isSelected={selectedNode === 'hitl_gate'}
        isVisited={isNodeVisited('hitl_gate')}
        count={nodeVisitCounts['hitl_gate']}
        activeColor="#f97316"
        scale={scale}
        onClick={() => onSelectNode('hitl_gate')}
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
