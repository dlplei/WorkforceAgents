import { useState } from 'react';
import {
  ShieldAlert, ShieldCheck, Ban, CheckCircle2,
  Calendar, FileText, Ticket, Clock,
  Loader2, Edit3, HelpCircle, AlertTriangle
} from 'lucide-react';
import type { HitlActionRequest } from '../types';

interface Props {
  request: HitlActionRequest;
  onApprove: (req: HitlActionRequest) => Promise<void> | void;
  onReject: (req: HitlActionRequest) => Promise<void> | void;
  onEdit?: (req: HitlActionRequest) => void;
  disabled?: boolean;
}

export default function HitlApprovalCard({
  request, onApprove, onReject, onEdit, disabled = false
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [rejecting, setRejecting] = useState(false);

  const getIcon = (cat: string) => {
    if (cat === 'leave') return <Calendar className="w-4 h-4 text-amber-400" />;
    if (cat === 'document') return <FileText className="w-4 h-4 text-blue-400" />;
    if (cat === 'ticket') return <Ticket className="w-4 h-4 text-purple-400" />;
    return <HelpCircle className="w-4 h-4 text-cyan-400" />;
  };

  const getRiskBadge = (risk: string) => {
    if (risk === 'high') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-rose-500/15 text-rose-300 border border-rose-500/40">
          <AlertTriangle className="w-3 h-3 mr-1 text-rose-400" />
          高风险写操作
        </span>
      );
    }
    if (risk === 'low') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-emerald-500/15 text-emerald-300 border border-emerald-500/40">
          <ShieldCheck className="w-3 h-3 mr-1 text-emerald-400" />
          低风险业务
        </span>
      );
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-amber-500/15 text-amber-300 border border-amber-500/40">
        <ShieldAlert className="w-3 h-3 mr-1 text-amber-400" />
        中风险审批
      </span>
    );
  };

  const handleApprove = async () => {
    if (disabled || submitting || request.status !== 'pending') return;
    setSubmitting(true);
    try { await onApprove(request); } finally { setSubmitting(false); }
  };

  const handleReject = async () => {
    if (disabled || rejecting || request.status !== 'pending') return;
    setRejecting(true);
    try { await onReject(request); } finally { setRejecting(false); }
  };

  const isPending = request.status === 'pending';
  const isApproved = request.status === 'approved';
  const isRejected = request.status === 'rejected';

  const cardBorder = isApproved
    ? 'border-emerald-500/50 bg-gradient-to-b from-slate-900/90 to-emerald-950/20'
    : isRejected
    ? 'border-slate-700/60 bg-slate-900/60 opacity-80'
    : 'border-amber-500/40 bg-gradient-to-b from-slate-900/95 to-amber-950/20';

  return (
    <div className={`my-3 w-full rounded-xl border p-4 shadow-xl backdrop-blur transition-all ${cardBorder}`}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-700/50">
        <div className="flex items-center space-x-2.5 min-w-0">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
            isApproved ? 'bg-emerald-500/20 text-emerald-400' : isRejected ? 'bg-slate-800 text-slate-400' : 'bg-amber-500/20 text-amber-400'
          }`}>
            {isApproved ? <CheckCircle2 className="w-4 h-4" /> : isRejected ? <Ban className="w-4 h-4" /> : getIcon(request.category)}
          </div>
          <div className="min-w-0">
            <div className="flex items-center space-x-2">
              <h4 className="text-xs font-semibold text-white truncate">{request.title || '人机协同门禁操作授权'}</h4>
              <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">[{request.tool_name}]</span>
            </div>
            <p className="text-[11px] text-slate-400">
              {isApproved ? '已完成人工授权校验并入库流转' : isRejected ? '用户已取消放弃此次操作' : 'Human-in-the-Loop 门禁已拦截，等待人工授权确认'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {getRiskBadge(request.risk_level)}
          {isApproved && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/50">
              <CheckCircle2 className="w-3 h-3 mr-1" /> 已提交
            </span>
          )}
          {isRejected && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
              <Ban className="w-3 h-3 mr-1" /> 已撤销
            </span>
          )}
        </div>
      </div>

      {/* Details Matrix */}
      <div className="my-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        {Object.entries(request.summary || {}).map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between p-2 rounded-lg bg-slate-800/60 border border-slate-700/40">
            <span className="text-slate-400 shrink-0 mr-2">{k}</span>
            <span className="text-slate-200 font-medium text-right break-words">{String(v)}</span>
          </div>
        ))}
      </div>

      {isApproved && request.resultMessage && (
        <div className="mb-3 p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-xs text-emerald-300 flex items-start space-x-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div className="flex-1">{request.resultMessage}</div>
        </div>
      )}

      {/* Actions */}
      {isPending ? (
        <div className="pt-3 border-t border-slate-700/50 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-1.5 text-[11px] text-amber-300/80">
            <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
            <span>涉及企业生产数据写操作，请核对无误后点击确认</span>
          </div>

          <div className="flex items-center space-x-2 ml-auto">
            {onEdit && (
              <button
                type="button"
                onClick={() => onEdit(request)}
                disabled={disabled || submitting || rejecting}
                className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700/80 transition-colors disabled:opacity-50"
              >
                <Edit3 className="w-3.5 h-3.5 mr-1" />
                <span>修改诉求</span>
              </button>
            )}

            <button
              type="button"
              onClick={handleReject}
              disabled={disabled || submitting || rejecting}
              className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-medium text-rose-300 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 transition-colors disabled:opacity-50"
            >
              {rejecting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Ban className="w-3.5 h-3.5 mr-1" />}
              <span>取消放弃</span>
            </button>

            <button
              type="button"
              onClick={handleApprove}
              disabled={disabled || submitting || rejecting}
              className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-md shadow-emerald-900/30 transition-all disabled:opacity-50 cursor-pointer"
            >
              {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <CheckCircle2 className="w-3.5 h-3.5 mr-1" />}
              <span>确认提交执行</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="pt-2 text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800/80">
          <span className="flex items-center space-x-1 font-mono">
            <Clock className="w-3 h-3 text-slate-500 mr-1" />
            <span>ID: {request.action_id}</span>
          </span>
          <span className="text-slate-400">
            {new Date(request.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </div>
      )}
    </div>
  );
}
