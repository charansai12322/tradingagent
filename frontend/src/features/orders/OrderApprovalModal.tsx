"use client";

import React, { useState } from "react";
import { AlertTriangle, Lock, ShieldCheck, CheckCircle2, XCircle } from "lucide-react";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ProposedOrder, OrderExecutionResult } from "@/types/trading";
import { formatCurrency, formatDateTime } from "@/lib/formatters";

export interface OrderApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  proposal: ProposedOrder | null;
  tradingEnabled: boolean;
  onApprove: (proposalId: string) => Promise<OrderExecutionResult>;
}

export const OrderApprovalModal: React.FC<OrderApprovalModalProps> = ({
  isOpen,
  onClose,
  proposal,
  tradingEnabled,
  onApprove,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [approvalResult, setApprovalResult] = useState<OrderExecutionResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [confirmedCheckbox, setConfirmedCheckbox] = useState(false);

  const handleConfirmApproval = async () => {
    if (!proposal) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const result = await onApprove(proposal.proposal_id);
      setApprovalResult(result);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Order approval rejected by server.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setApprovalResult(null);
    setErrorMessage(null);
    setConfirmedCheckbox(false);
    onClose();
  };

  if (!proposal) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Human-in-the-Loop Order Review"
      subtitle={`Proposal ID: ${proposal.proposal_id}`}
      footer={
        approvalResult ? (
          <Button variant="secondary" size="md" onClick={handleClose}>
            Dismiss Review
          </Button>
        ) : (
          <div className="flex items-center gap-3 w-full justify-between">
            <Button variant="ghost" size="sm" onClick={handleClose} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button
              variant="oxide"
              size="md"
              onClick={handleConfirmApproval}
              disabled={!confirmedCheckbox || isSubmitting || !tradingEnabled}
              isLoading={isSubmitting}
            >
              {!tradingEnabled ? "Execution Disabled" : "Authorize & Send"}
            </Button>
          </div>
        )
      }
    >
      {/* If Approval Result is available */}
      {approvalResult ? (
        <div className="space-y-4 py-2">
          <div
            className={`p-4 rounded-sm border ${
              approvalResult.success
                ? "bg-[#357A52]/10 border-positive text-positive"
                : "bg-[#A34F3F]/10 border-oxide text-oxide"
            }`}
          >
            <div className="flex items-center gap-2 font-serif text-base font-normal">
              {approvalResult.success ? (
                <CheckCircle2 className="w-5 h-5 text-positive" />
              ) : (
                <XCircle className="w-5 h-5 text-oxide" />
              )}
              <span>
                {approvalResult.success
                  ? "Paper Order Executed"
                  : "Order Execution Rejected by Risk Engine"}
              </span>
            </div>
            <p className="text-xs text-ink/80 mt-1 font-sans leading-relaxed">
              {approvalResult.message}
            </p>
          </div>

          <div className="border border-stone rounded-sm p-3 bg-bone/40 text-xs font-mono space-y-1.5">
            <div className="flex justify-between">
              <span className="text-muted">Symbol / Side:</span>
              <span className="text-ink font-semibold">
                {approvalResult.symbol} {approvalResult.side?.toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted">Quantity:</span>
              <span className="text-ink">{approvalResult.quantity}</span>
            </div>
            {approvalResult.order_id && (
              <div className="flex justify-between">
                <span className="text-muted">Alpaca Order ID:</span>
                <span className="text-ink">{approvalResult.order_id}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-muted">Status:</span>
              <span className="text-ink font-semibold">{approvalResult.filled_status}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4 text-xs font-sans">
          {/* Execution Policy Notice */}
          {!tradingEnabled && (
            <div className="p-3 bg-[#A34F3F]/10 border border-oxide/40 rounded-sm text-oxide flex items-start gap-2">
              <Lock className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Order Placement Disabled by Server Policy</strong>
                <span className="text-[11px] text-ink/80 leading-relaxed block mt-0.5">
                  <code className="font-mono bg-bone px-1 py-0.5 rounded">TRADING_ENABLED=false</code> is enforced on the backend. Even with user approval, the server risk engine will reject order dispatch to Alpaca.
                </span>
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 bg-[#A34F3F]/10 border border-oxide/40 rounded-sm text-oxide">
              <strong>Server Error:</strong> {errorMessage}
            </div>
          )}

          {proposal.estimated_notional > 100.0 && (
            <div className="p-3 bg-[#A34F3F]/10 border border-oxide/40 rounded-sm text-oxide flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Exceeds Maximum Order Cap ($100.00 Limit)</strong>
                <span className="text-[11px] text-ink/80 leading-relaxed block mt-0.5">
                  This proposal estimated total of <strong>${proposal.estimated_notional?.toFixed(2)}</strong> exceeds the maximum allowable order notional limit ($100.00). The backend risk engine will reject this order upon submission.
                </span>
              </div>
            </div>
          )}

          {/* Proposal Details Table */}
          <div className="border border-stone rounded-sm overflow-hidden">
            <div className="bg-bone px-3 py-2 border-b border-stone flex justify-between items-center text-[10px] font-mono uppercase text-muted tracking-wider">
              <span>Proposal Details</span>
              <Badge variant={proposal.side === "buy" ? "buy" : "sell"} size="sm">
                {proposal.side}
              </Badge>
            </div>
            <div className="p-3 space-y-2 text-xs font-mono bg-chalk">
              <div className="flex justify-between">
                <span className="text-muted font-sans">Security Symbol:</span>
                <span className="font-bold text-ink text-sm">{proposal.symbol}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted font-sans">Action Side:</span>
                <span className="uppercase font-semibold text-ink">{proposal.side}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted font-sans">Shares Quantity:</span>
                <span className="text-ink">{proposal.quantity} share(s)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted font-sans">Estimated Unit Price:</span>
                <span className="text-ink">${proposal.estimated_price?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t border-stone/40 pt-1.5 font-semibold">
                <span className="text-muted font-sans">Estimated Total Value:</span>
                <span className="text-ink">${proposal.estimated_notional?.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-[10px] text-muted pt-1">
                <span className="font-sans">Proposal TTL Expiry:</span>
                <span>{formatDateTime(proposal.expires_at)}</span>
              </div>
            </div>
          </div>

          {/* Explicit User Consent Checkbox */}
          <div className="pt-2">
            <label className="flex items-start gap-2.5 p-3 rounded-sm border border-stone bg-bone/30 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={confirmedCheckbox}
                onChange={(e) => setConfirmedCheckbox(e.target.checked)}
                className="mt-0.5 rounded border-stone text-ink focus:ring-ink"
              />
              <span className="text-xs text-ink/80 leading-snug">
                I acknowledge that I have reviewed the proposed transaction for <strong>{proposal.quantity} share(s) of {proposal.symbol}</strong>, understand that this is a simulated paper trade, and grant explicit authorization to evaluate backend risk controls.
              </span>
            </label>
          </div>
        </div>
      )}
    </Modal>
  );
};
