import React, { useState, useEffect, useCallback } from 'react';
import { X, CheckCircle, XCircle, Clock, Calendar, User, FileText, AlertCircle, RefreshCw, Loader2 } from 'lucide-react';
import type { ApprovalItem, EmployeeProfile } from '../types';

interface PendingApprovalsModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentEmployee: EmployeeProfile;
  backendUrl?: string;
  onApprovalDone?: () => void;
}

export default function PendingApprovalsModal({
  isOpen,
  onClose,
  currentEmployee,
  backendUrl = '',
  onApprovalDone,
}: PendingApprovalsModalProps) {
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [comments, setComments] = useState<Record<string, string>>({});
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

  useEffect(() => {
    if (isOpen) {
      setProcessedRecords({});
      fetchPendingList();
    }
  }, [isOpen, fetchPendingList]);

  if (!isOpen) return null;

  const handleAction = async (approvalId: string, action: 'approve' | 'reject') => {
    // 防重复点击与并发锁定
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

      // 1. 业界最佳实践：立即将当前卡片锁定为已归档终态，彻底替换按钮为审计回执
      setProcessedRecords((prev) => ({
        ...prev,
        [approvalId]: {
          decision,
          message: resultMessage,
          timestamp: Date.now(),
        },
      }));

      // 2. 乐观从待办列表中过滤或更新，并通知全局
      setApprovals((prev) => prev.filter((item) => (item.id || item.approval_id) !== approvalId));

      // 3. 触发父级回调与全局事件广播
      onApprovalDone?.();
      window.dispatchEvent(
        new CustomEvent('workforce:approvals_updated', {
          detail: { approvalId, decision, approver: currentEmployee.name },
        })
      );

      // 4. 静默拉取最新列表强一致校验
      await fetchPendingList();
    } catch (err: any) {
      setErrorMsg(err.message || '提交审批时发生异常');
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700 bg-slate-800/90">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-white">待我审批的事项</h2>
              <p className="text-xs text-slate-400">
                当前审批人：<span className="text-slate-200 font-medium">{currentEmployee.name}</span> ({currentEmployee.id} · {currentEmployee.position})
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={fetchPendingList}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="刷新"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
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
          {loading && approvals.length === 0 ? (
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

              let typeBadge = '请假审批';
              if (rawType.includes('报销')) typeBadge = '报销审批';
              else if (rawType.includes('证明')) typeBadge = '证明审批';
              else if (rawType.includes('年假')) typeBadge = '年假审批';
              else if (rawType.includes('病假')) typeBadge = '病假审批';

              let leaveTypeLabel = '年假';
              if (rawType === 'sick' || rawType.includes('病假')) leaveTypeLabel = '病假';
              else if (rawType === 'personal' || rawType.includes('事假')) leaveTypeLabel = '事假';
              else if (rawType.includes('报销')) leaveTypeLabel = '差旅报销';
              else if (rawType === 'annual' || rawType.includes('年假')) leaveTypeLabel = '年假';
              else leaveTypeLabel = rawType;

              const displaySubmitted = rawDate
                ? rawDate.includes('T')
                  ? new Date(rawDate).toLocaleString('zh-CN', { hour12: false })
                  : rawDate
                : '近期';

              return (
                <div key={approvalId} className="bg-slate-900/70 border border-slate-700/80 rounded-xl p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                        {typeBadge}
                      </span>
                      <span className="text-xs font-mono text-slate-400">{approvalId}</span>
                    </div>
                    <span className="text-[11px] text-slate-500">
                      提交: {displaySubmitted}
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
                      <span className="font-semibold text-white">{leaveTypeLabel}</span>
                      <span className="text-amber-300 font-bold ml-1">{calcDays} 天</span>
                    </div>
                    <div className="col-span-2 flex items-center space-x-1.5 text-slate-300">
                      <Clock className="w-3.5 h-3.5 text-emerald-400" />
                      <span>时间: </span>
                      <span className="font-mono text-slate-200">
                        {startDate || '待定'} ~ {endDate || '待定'}
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
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-slate-700 bg-slate-800/80 flex justify-between items-center text-xs text-slate-400">
          <span>待审批单据数: {approvals.length}</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  );
}
