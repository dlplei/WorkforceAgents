import React, { useState, useEffect, useCallback } from 'react';
import { 
  X, CheckCircle, XCircle, Clock, Calendar, User, FileText, 
  AlertCircle, RefreshCw, Loader2, Copy, Check, History, CheckCheck 
} from 'lucide-react';
import type { ApprovalItem, EmployeeProfile } from '../types';

interface PendingApprovalsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentEmployee: EmployeeProfile;
  backendUrl?: string;
  onApprovalDone?: () => void;
}

interface BadgeConfig {
  badgeText: string;
  badgeClass: string;
  typeLabel: string;
  category: 'leave' | 'travel' | 'transfer' | 'expense' | 'document' | 'other';
}

function getApprovalBadgeConfig(rawType: string = ''): BadgeConfig {
  const t = rawType.toLowerCase();

  // 1. 转岗调动
  if (t.includes('调动') || t.includes('转岗') || t === 'transfer') {
    return {
      badgeText: '转岗审批',
      badgeClass: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
      typeLabel: '转岗调动',
      category: 'transfer',
    };
  }

  // 2. 差旅申请
  if (t.includes('差旅') || t.includes('出差') || t === 'travel') {
    return {
      badgeText: '差旅审批',
      badgeClass: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
      typeLabel: '差旅申请',
      category: 'travel',
    };
  }

  // 3. 费用报销
  if (t.includes('报销') || t === 'expense') {
    return {
      badgeText: '报销审批',
      badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
      typeLabel: '费用报销',
      category: 'expense',
    };
  }

  // 4. 年假
  if (t.includes('年假') || t === 'annual') {
    return {
      badgeText: '年假审批',
      badgeClass: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
      typeLabel: '年假申请',
      category: 'leave',
    };
  }

  // 5. 病假
  if (t.includes('病假') || t === 'sick') {
    return {
      badgeText: '病假审批',
      badgeClass: 'bg-rose-500/20 text-rose-300 border-rose-500/40',
      typeLabel: '病假申请',
      category: 'leave',
    };
  }

  // 6. 证明
  if (t.includes('证明') || t === 'document') {
    return {
      badgeText: '证明审批',
      badgeClass: 'bg-blue-500/20 text-blue-300 border-blue-500/40',
      typeLabel: '人事证明',
      category: 'document',
    };
  }

  // 7. 事假
  if (t.includes('事假') || t === 'personal') {
    return {
      badgeText: '事假审批',
      badgeClass: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
      typeLabel: '事假申请',
      category: 'leave',
    };
  }

  return {
    badgeText: '请假审批',
    badgeClass: 'bg-teal-500/20 text-teal-300 border-teal-500/40',
    typeLabel: rawType || '日常事务',
    category: 'other',
  };
}


export default function PendingApprovalsModal({
  isOpen,
  onClose,
  currentEmployee,
  backendUrl = '',
  onApprovalDone,
}: PendingApprovalsModalProps) {
  const [activeTab, setActiveTab] = useState<'pending' | 'history'>('pending');
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [historyApprovals, setHistoryApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyRange, setHistoryRange] = useState<'all' | '7days' | '30days'>('all');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [processedRecords, setProcessedRecords] = useState<Record<string, { decision: 'approved' | 'rejected'; message: string; timestamp: number }>>({});

  const cleanBase = backendUrl.replace(/\/+$/, '');

  const fetchPendingList = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${cleanBase}/api/approvals/pending`, {
        headers: { 'X-Employee-Id': currentEmployee.id },
      });
      if (!res.ok) throw new Error(`获取待办列表失败 (${res.status})`);
      const data = await res.json();
      setApprovals(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setErrorMsg(err.message || '加载待审批列表出错');
    } finally {
      setLoading(false);
    }
  }, [cleanBase, currentEmployee.id]);

  const fetchHistoryList = useCallback(async (range: 'all' | '7days' | '30days' = historyRange) => {
    setHistoryLoading(true);
    setErrorMsg(null);
    try {
      let url = `${cleanBase}/api/approvals/history`;
      const now = new Date();
      if (range === '7days') {
        const d = new Date(now.getTime() - 7 * 86400000);
        const startStr = d.toISOString().split('T')[0];
        url += `?start_date=${startStr}`;
      } else if (range === '30days') {
        const d = new Date(now.getTime() - 30 * 86400000);
        const startStr = d.toISOString().split('T')[0];
        url += `?start_date=${startStr}`;
      }
      const res = await fetch(url, {
        headers: { 'X-Employee-Id': currentEmployee.id },
      });
      if (!res.ok) throw new Error(`获取审批历史失败 (${res.status})`);
      const data = await res.json();
      setHistoryApprovals(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setErrorMsg(err.message || '加载审批历史出错');
    } finally {
      setHistoryLoading(false);
    }
  }, [cleanBase, currentEmployee.id, historyRange]);

  useEffect(() => {
    if (isOpen) {
      setProcessedRecords({});
      fetchPendingList();
      fetchHistoryList(historyRange);
    }
  }, [isOpen, fetchPendingList, fetchHistoryList, historyRange]);

  const handleCopyId = async (id: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.warn('Copy failed', err);
    }
  };

  const handleAction = async (approvalId: string, action: 'approve' | 'reject') => {
    if (processingId || processedRecords[approvalId]) return;
    setProcessingId(approvalId);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const decision = action === 'approve' ? 'approved' : 'rejected';
      const comment = comments[approvalId]?.trim() || (action === 'approve' ? '同意申请' : '予以驳回');
      const res = await fetch(`${cleanBase}/api/approvals/${approvalId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Employee-Id': currentEmployee.id,
        },
        body: JSON.stringify({ decision, action, comment }),
      });
      const resData = await res.json();
      if (!res.ok) throw new Error(resData.detail || '审批操作失败');
      
      const resultMessage = resData.message || `单据 ${approvalId} 已${action === 'approve' ? '审批通过' : '成功驳回'}`;
      setSuccessMsg(resultMessage);

      setProcessedRecords((prev) => ({
        ...prev,
        [approvalId]: {
          decision,
          message: resultMessage,
          timestamp: Date.now(),
        },
      }));

      setApprovals((prev) => prev.filter((item) => (item.id || item.approval_id) !== approvalId));

      onApprovalDone?.();
      window.dispatchEvent(
        new CustomEvent('workforce:approvals_updated', {
          detail: { approvalId, decision, approver: currentEmployee.name },
        })
      );

      await Promise.all([fetchPendingList(), fetchHistoryList()]);
    } catch (err: any) {
      setErrorMsg(err.message || '提交审批时发生异常');
    } finally {
      setProcessingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/90">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <CheckCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-semibold text-white">审批中心</h2>
                <span className="text-[11px] px-2 py-0.2 rounded-full bg-slate-700 text-slate-300 font-mono">
                  Approval Hub
                </span>
              </div>
              <p className="text-xs text-slate-400">
                当前用户：<span className="text-slate-200 font-medium">{currentEmployee.name}</span> ({currentEmployee.id} · {currentEmployee.position})
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => {
                if (activeTab === 'pending') fetchPendingList();
                else fetchHistoryList(historyRange);
              }}
              disabled={loading || historyLoading}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="刷新列表"
            >
              <RefreshCw className={`w-4 h-4 ${(loading || historyLoading) ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="px-6 pt-3 pb-2 border-b border-slate-700/60 bg-slate-800/40 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => setActiveTab('pending')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'pending'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>待我审批</span>
              {approvals.length > 0 && (
                <span className={`px-1.5 py-0.2 text-[10px] font-bold rounded-full ${
                  activeTab === 'pending' ? 'bg-white text-blue-600' : 'bg-amber-500/20 text-amber-300'
                }`}>
                  {approvals.length}
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>审批历史</span>
              {historyApprovals.length > 0 && (
                <span className={`px-1.5 py-0.2 text-[10px] font-bold rounded-full ${
                  activeTab === 'history' ? 'bg-white text-blue-600' : 'bg-slate-700 text-slate-300'
                }`}>
                  {historyApprovals.length}
                </span>
              )}
            </button>
          </div>

          {activeTab === 'history' && (
            <div className="flex items-center space-x-1 text-xs">
              {(['all', '7days', '30days'] as const).map((rng) => (
                <button
                  key={rng}
                  onClick={() => {
                    setHistoryRange(rng);
                    fetchHistoryList(rng);
                  }}
                  className={`px-2 py-1 rounded text-[11px] transition-colors ${
                    historyRange === rng
                      ? 'bg-slate-700 text-white font-medium'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {rng === 'all' ? '全部' : rng === '7days' ? '近7天' : '近30天'}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Error / Success Alert */}
        {errorMsg && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="mx-6 mt-4 p-3 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Content List */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {activeTab === 'pending' ? (
            loading && approvals.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                正在获取待审批清单...
              </div>
            ) : approvals.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <CheckCircle className="w-10 h-10 mx-auto mb-2 text-emerald-400/60" />
                <p className="text-sm font-medium text-slate-300">当前没有待审批事项</p>
                <p className="text-xs text-slate-500 mt-1">下属员工提交请假或审批请求后将在此显示</p>
              </div>
            ) : (
              approvals.map((item) => {
                const approvalId = item.id || item.approval_id || '';
                const isBusy = processingId === approvalId;
                const applicantName = item.applicant || item.employee_name || item.employee_id || '未知';
                const applicantId = item.employee_id || '';
                const rawType = item.approval_type || item.type || item.details?.leave_type || '请假申请';
                const startDate = item.start_date || item.details?.start_date;
                const endDate = item.end_date || item.details?.end_date;
                const reason = item.reason || item.details?.reason;
                const rawDate = item.request_date || item.date || item.submitted_at || '';

                let calcDays = item.days || item.details?.days;
                if (!calcDays && startDate && endDate) {
                  const s = new Date(startDate);
                  const e = new Date(endDate);
                  if (!isNaN(s.getTime()) && !isNaN(e.getTime())) {
                    calcDays = Math.max(1, Math.round((e.getTime() - s.getTime()) / (1000 * 3600 * 24)) + 1);
                  }
                }
                calcDays = calcDays || 1;

                const badgeInfo = getApprovalBadgeConfig(rawType);

                const displaySubmitted = rawDate
                  ? rawDate.includes('T')
                    ? new Date(rawDate).toLocaleString('zh-CN', { hour12: false })
                    : rawDate
                  : '近期';

                return (
                  <div key={approvalId} className="bg-slate-900/70 border border-slate-700/80 rounded-xl p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${badgeInfo.badgeClass}`}>
                          {badgeInfo.badgeText}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => handleCopyId(approvalId, e)}
                          title="点击复制单号"
                          className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 border border-slate-700 transition-colors"
                        >
                          <span>{approvalId}</span>
                          {copiedId === approvalId ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3 text-slate-400" />
                          )}
                        </button>
                      </div>
                      <span className="text-[11px] text-slate-500">
                        提报: {displaySubmitted}
                      </span>
                    </div>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-800/60 rounded-lg p-3 border border-slate-700/40">
                    <div className="flex items-center space-x-1.5 text-slate-300">
                      <User className="w-3.5 h-3.5 text-blue-400" />
                      <span>申请人: </span>
                      <span className="font-semibold text-white">{applicantName}</span>
                      {applicantId && <span className="text-slate-400">({applicantId})</span>}
                    </div>
                    <div className="flex items-center space-x-1.5 text-slate-300">
                      <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                      <span>类型: </span>
                      <span className="font-semibold text-white">{badgeInfo.typeLabel}</span>
                      {badgeInfo.category === 'leave' || badgeInfo.category === 'travel' ? (
                        <span className="text-amber-300 font-bold ml-1">{calcDays} 天</span>
                      ) : (item.amount || item.details?.amount) ? (
                        <span className="text-amber-300 font-bold ml-1">¥{Number(item.amount || item.details?.amount).toFixed(2)}</span>
                      ) : null}
                    </div>
                    <div className="col-span-2 flex items-center space-x-1.5 text-slate-300">
                      <Clock className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{badgeInfo.category === 'transfer' ? '生效日期: ' : '时间周期: '}</span>
                      <span className="font-mono text-slate-200">
                        {badgeInfo.category === 'transfer'
                          ? (startDate || item.details?.effective_date || '即日生效')
                          : `${startDate || '待定'} ~ ${endDate || '待定'}`}
                      </span>
                    </div>
                    {reason && (
                      <div className="col-span-2 flex items-start space-x-1.5 text-slate-300 mt-1">
                        <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5" />
                        <span>事由: </span>
                        <span className="text-slate-200 italic">{reason}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions or Resolved Audit Receipt */}
                  {processedRecords[approvalId] ? (
                    <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-1.5">
                        {processedRecords[approvalId].decision === 'approved' ? (
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-400" />
                        )}
                        <span className={processedRecords[approvalId].decision === 'approved' ? 'text-emerald-300 font-semibold' : 'text-rose-300 font-semibold'}>
                          {processedRecords[approvalId].message}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">
                        {new Date(processedRecords[approvalId].timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                      </span>
                    </div>
                  ) : (
                    <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-2">
                      <input
                        type="text"
                        placeholder="审批批注 (选填，例如：按时交接工作即可)"
                        value={comments[approvalId] || ''}
                        onChange={(e) => setComments((prev) => ({ ...prev, [approvalId]: e.target.value }))}
                        disabled={Boolean(processingId)}
                        className="w-full sm:flex-1 bg-slate-800 text-xs text-white border border-slate-700 rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500 placeholder-slate-500 disabled:opacity-60"
                      />
                      <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
                        <button
                          type="button"
                          onClick={() => handleAction(approvalId, 'reject')}
                          disabled={Boolean(processingId)}
                          className="flex-1 sm:flex-initial flex items-center justify-center space-x-1 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 rounded-lg text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                        >
                          {isBusy && !comments[approvalId] ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <XCircle className="w-3.5 h-3.5 mr-1" />}
                          <span>{isBusy ? '处理中...' : '驳回'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleAction(approvalId, 'approve')}
                          disabled={Boolean(processingId)}
                          className="flex-1 sm:flex-initial flex items-center justify-center space-x-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer shadow-sm"
                        >
                          {isBusy ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <CheckCircle className="w-3.5 h-3.5 mr-1" />}
                          <span>{isBusy ? '处理中...' : '批准同意'}</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )
        ) : (
            /* History Tab Content */
            historyLoading && historyApprovals.length === 0 ? (
              <div className="py-12 text-center text-slate-400 text-sm">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-blue-400" />
                正在加载审批历史记录...
              </div>
            ) : historyApprovals.length === 0 ? (
              <div className="py-12 text-center text-slate-400">
                <History className="w-10 h-10 mx-auto mb-2 text-slate-500" />
                <p className="text-sm font-medium text-slate-300">暂无审批归档记录</p>
                <p className="text-xs text-slate-500 mt-1">已处理的请假或业务申请将展示在此处流水中</p>
              </div>
            ) : (
              historyApprovals.map((item) => {
                const approvalId = item.id || item.approval_id || '';
                const applicantName = item.applicant || item.employee_name || item.employee_id || '未知';
                const isApproved = item.status === 'approved' || item.status === '已批准';
                const rawType = item.approval_type || item.type || '业务申请';
                const actionDate = item.action_date || item.request_date || item.date || '近期';
                const comment = item.comment || (isApproved ? '审批通过' : '予以驳回');

                return (
                  <div key={approvalId} className="bg-slate-900/60 border border-slate-700/60 rounded-xl p-4 space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
                          isApproved 
                            ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' 
                            : 'bg-rose-500/15 text-rose-300 border-rose-500/30'
                        }`}>
                          {isApproved ? '已批准' : '已驳回'}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => handleCopyId(approvalId, e)}
                          title="点击复制单号"
                          className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-xs font-mono text-slate-300 border border-slate-700 transition-colors"
                        >
                          <span>{approvalId}</span>
                          {copiedId === approvalId ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3 text-slate-400" />
                          )}
                        </button>
                        <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getApprovalBadgeConfig(rawType).badgeClass}`}>
                          {getApprovalBadgeConfig(rawType).badgeText}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-500">
                        申请日期: {item.request_date || item.date || '未知'}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs bg-slate-800/40 rounded-lg p-3 border border-slate-700/30">
                      <div className="flex items-center space-x-1.5 text-slate-300">
                        <User className="w-3.5 h-3.5 text-blue-400" />
                        <span>申请人: </span>
                        <span className="font-semibold text-white">{applicantName}</span>
                      </div>
                      <div className="flex items-center space-x-1.5 text-slate-300">
                        <Clock className="w-3.5 h-3.5 text-emerald-400" />
                        <span>周期: </span>
                        <span className="font-mono text-slate-200">
                          {item.start_date || '当日'} ~ {item.end_date || item.start_date || '当日'}
                        </span>
                      </div>
                      {item.reason && (
                        <div className="col-span-2 flex items-start space-x-1.5 text-slate-300 mt-1">
                          <FileText className="w-3.5 h-3.5 text-slate-400 mt-0.5" />
                          <span>事由: </span>
                          <span className="text-slate-300 italic">{item.reason}</span>
                        </div>
                      )}
                    </div>

                    {/* Audit Trail */}
                    <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                      <div className="flex items-center space-x-2">
                        <span className="text-slate-400">审批人: <strong className="text-slate-200">{item.approver || '经办主管'}</strong></span>
                        <span className="text-slate-500">·</span>
                        <span className="text-slate-300">意见: “{comment}”</span>
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono">
                        处理于 {actionDate}
                      </span>
                    </div>
                  </div>
                );
              })
            )
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-700 bg-slate-800/80 flex justify-between items-center text-xs text-slate-400">
          <span>
            {activeTab === 'pending'
              ? `待审批单据数: ${approvals.length}`
              : `历史归档记录数: ${historyApprovals.length}`}
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition-colors cursor-pointer"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
