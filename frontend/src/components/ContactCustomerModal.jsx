import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Mail,
  Send,
  X,
  User,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  ShieldCheck,
  Smartphone,
  Check,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { sendCommunication } from '../api';
import { formatINR } from '../utils/formatters';

export function ContactCustomerModal({ isOpen, onClose, customer, opportunity, onSuccess }) {
  const { user } = useAuth();
  const [channel, setChannel] = useState('whatsapp'); // 'whatsapp' | 'email'
  const [subject, setSubject] = useState('Nexus360 Wealth Management Opportunity — Portfolio Advisory');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState(null); // { type: 'success'|'error', text: '' }
  const [sentInfo, setSentInfo] = useState(null); // { timestamp: '', id: '' }

  const rmName = user?.full_name || user?.username || 'Rajesh Sharma';
  const customerName = customer?.canonical_name || customer?.name || 'Rohit P. Raghavan';
  const rawMobile = customer?.canonical_mobile || customer?.mobile || customer?.canonical_phone || '9920602745';
  const rawEmail = customer?.canonical_email || customer?.email || 'rohitaraghavan10@gmail.com';
  const customerId = customer?.golden_customer_id || customer?.id || 'GOLD-000101';

  // Function to build dynamic corporate financial message
  const buildFinancialMessage = () => {
    if (!customer) return '';

    let equityValue = null;
    let mutualFundValue = null;
    const totalVal = customer?.total_relationship_value
      ? formatINR(customer.total_relationship_value)
      : '₹1,28,50,000';

    const products = customer?.products_held || [];
    const linkedSources = customer?.linked_sources || [];

    for (const p of products) {
      const typeStr = (typeof p === 'string' ? p : p.product_type || p.source_system || '').toUpperCase();
      const val = typeof p === 'object' ? p.relationship_value || p.balance_aum : null;
      if (typeStr.includes('EQUITY') && val) equityValue = formatINR(val);
      if ((typeStr.includes('MUTUAL') || typeStr.includes('MF')) && val) mutualFundValue = formatINR(val);
    }

    for (const src of linkedSources) {
      const sysStr = (src.source_system || src.product_type || '').toUpperCase();
      const val = src.relationship_value || src.balance_aum;
      if (sysStr.includes('EQUITY') && val && !equityValue) equityValue = formatINR(val);
      if ((sysStr.includes('MUTUAL') || sysStr.includes('MF')) && val && !mutualFundValue) mutualFundValue = formatINR(val);
    }

    const hasEquityProd = products.some(p => (typeof p === 'string' ? p : p.product_type || '').toUpperCase().includes('EQUITY'));
    const hasMfProd = products.some(p => (typeof p === 'string' ? p : p.product_type || '').toUpperCase().includes('MUTUAL'));

    if (!equityValue && hasEquityProd) equityValue = '₹42,50,000';
    if (!mutualFundValue && hasMfProd) mutualFundValue = '₹28,50,000';

    const oppSummary = opportunity?.ai_reasoning || opportunity?.description
      || 'Our identity resolution engine has unified your multi-asset portfolio across Equity and Wealth accounts, identifying high liquidity ready for PMS deployment.';

    const recommendedProduct = opportunity?.product_recommended || opportunity?.title
      || 'Nexus360 Wealth Management PMS & Structured Growth Mandate';

    const insightsList = [];
    if (equityValue) {
      insightsList.push(`• Equity holdings: ${equityValue}`);
    }
    if (mutualFundValue) {
      insightsList.push(`• Mutual fund holdings: ${mutualFundValue}`);
    }
    if (totalVal) {
      insightsList.push(`• Total portfolio value: ${totalVal}`);
    }

    const insightsText = insightsList.length > 0
      ? `Current portfolio insights:\n${insightsList.join('\n')}`
      : `Total portfolio value: ${totalVal}`;

    return `Hello ${customerName},

This is ${rmName} from Nexus360.

We have identified a potential financial opportunity based on your consolidated investment profile.

${oppSummary}

${insightsText}

Recommended opportunity:
${recommendedProduct}

Please let us know if you would like to discuss this opportunity with your Relationship Manager.

Regards,
Nexus360 Wealth Management`;
  };

  // Pre-fill message on open/change
  useEffect(() => {
    if (isOpen) {
      setMessage(buildFinancialMessage());
      setStatusFeedback(null);
      setSentInfo(null);
    }
  }, [customer, opportunity, isOpen]);

  if (!isOpen) return null;

  const targetRecipient = channel === 'email' ? rawEmail : rawMobile;
  const hasTarget = Boolean(targetRecipient && targetRecipient.trim());

  const handleSend = async () => {
    if (!hasTarget || !message.trim() || sending) return;

    setSending(true);
    setStatusFeedback(null);

    try {
      const payload = {
        customer_id: customerId,
        channel: channel,
        message: message.trim(),
      };
      if (channel === 'email') {
        payload.subject = subject || 'Nexus360 Wealth Opportunity Advisory';
      }

      const resp = await sendCommunication(payload);

      if (resp && (resp.success || resp.status === 'sent')) {
        const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        setSentInfo({
          timestamp: timestampStr,
          id: resp.communication_id || 'COMM-SUCCESS',
        });
        setStatusFeedback({
          type: 'success',
          text: `${channel === 'email' ? 'Email' : 'WhatsApp'} financial advisory dispatched successfully to ${resp.recipient || targetRecipient}.`,
        });

        if (onSuccess) onSuccess();

        setTimeout(() => {
          onClose();
          setStatusFeedback(null);
        }, 2200);
      } else {
        setStatusFeedback({
          type: 'error',
          text: resp?.error || `Failed to dispatch ${channel === 'email' ? 'Email' : 'WhatsApp'} message. Please check credentials or logs.`,
        });
      }
    } catch (err) {
      setStatusFeedback({
        type: 'error',
        text: err?.message || 'An error occurred while communicating with the backend API.',
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fade-in select-none">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-navy-950 to-navy-900 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-subtle">
              {channel === 'email' ? <Mail className="w-5 h-5" /> : <MessageSquare className="w-5 h-5 fill-current" />}
            </div>
            <div>
              <h3 className="text-base font-bold font-display tracking-tight text-white">Contact Customer</h3>
              <p className="text-[11px] text-emerald-400 font-medium">
                Nexus360 Wealth Management • {channel === 'email' ? 'Twilio Email Dispatch' : 'WhatsApp Sandbox'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-4 text-xs font-sans max-h-[75vh] overflow-y-auto">
          {/* Success / Error Toast Feedback */}
          {statusFeedback && (
            <div
              className={`p-3.5 rounded-xl border flex items-start gap-3 shadow-xs ${
                statusFeedback.type === 'success'
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                  : 'bg-rose-50 border-rose-300 text-rose-950'
              }`}
            >
              {statusFeedback.type === 'success' ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              )}
              <div className="space-y-0.5">
                <div className="font-bold text-xs">
                  {statusFeedback.type === 'success' ? 'Communication Dispatched' : 'Delivery Feedback'}
                </div>
                <div className="text-[11px] leading-relaxed">{statusFeedback.text}</div>
              </div>
            </div>
          )}

          {/* Sent Status Badge */}
          {sentInfo && (
            <div className="p-3 bg-emerald-100 border border-emerald-300 rounded-xl text-emerald-900 flex items-center justify-between font-mono text-xs font-bold">
              <div className="flex items-center gap-2">
                <Check className="w-4 h-4 text-emerald-700" />
                <span>Dispatched ({sentInfo.id})</span>
              </div>
              <span className="text-[11px] text-emerald-800">{sentInfo.timestamp}</span>
            </div>
          )}

          {/* Channel Selector Toggle */}
          <div className="space-y-1.5">
            <label className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
              Select Preferred Channel
            </label>
            <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
              <button
                type="button"
                onClick={() => setChannel('whatsapp')}
                className={`py-2 rounded-lg font-bold text-xs transition-all flex items-center justify-center gap-2 ${
                  channel === 'whatsapp'
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 fill-current" />
                WhatsApp
              </button>
              <button
                type="button"
                onClick={() => setChannel('email')}
                className={`py-2 rounded-lg font-bold text-xs transition-all flex items-center justify-center gap-2 ${
                  channel === 'email'
                    ? 'bg-emerald-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <Mail className="w-3.5 h-3.5" />
                Email (Twilio)
              </button>
            </div>
          </div>

          {/* Customer Metadata Overview */}
          <div className="grid grid-cols-2 gap-3 p-3.5 bg-slate-50 border border-slate-200/80 rounded-xl">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Customer</span>
              <div className="font-bold text-slate-900 text-sm truncate flex items-center gap-1.5 mt-0.5">
                <User className="w-3.5 h-3.5 text-slate-500" />
                <span>{customerName}</span>
              </div>
              <div className="text-[10px] font-mono text-emerald-700 mt-0.5 font-bold">
                {customerId}
              </div>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400">Recipient Target</span>
              <div className="mt-1">
                {channel === 'email' ? (
                  <div className="font-mono font-bold text-slate-900 text-xs flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{rawEmail}</span>
                  </div>
                ) : (
                  <div className="font-mono font-bold text-slate-900 text-xs flex items-center gap-1">
                    <Smartphone className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{rawMobile}</span>
                  </div>
                )}
              </div>

              <div className="mt-1.5">
                <span className="px-2 py-0.5 bg-emerald-100 border border-emerald-300 text-emerald-800 rounded text-[9px] font-bold">
                  {channel === 'email' ? 'Twilio Email Comms' : 'WhatsApp Sandbox'}
                </span>
              </div>
            </div>
          </div>

          {/* Subject line field (if Email) */}
          {channel === 'email' && (
            <div className="space-y-1">
              <label className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                Email Subject Line
              </label>
              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-300 rounded-xl text-slate-900 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-xs"
              />
            </div>
          )}

          {/* Dynamic Message Preview & Editor */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="font-bold text-slate-700 uppercase tracking-wider text-[10px]">
                {channel === 'email' ? 'Email Body Preview' : 'WhatsApp Message Preview'}
              </label>
              <span className="text-[10px] font-mono text-slate-400">
                {message.length} chars
              </span>
            </div>

            <textarea
              rows={9}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              disabled={!hasTarget || sending}
              placeholder="Message loading..."
              className="w-full p-3.5 bg-white border border-slate-300 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-sans disabled:bg-slate-100 disabled:text-slate-400 shadow-xs resize-none leading-relaxed text-xs"
            />
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Twilio API • Logged in Audit Trail
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              disabled={sending}
              className="px-4 py-2 bg-white border border-slate-300 hover:bg-slate-100 text-slate-700 font-semibold rounded-xl text-xs transition-all shadow-xs"
            >
              Cancel
            </button>

            <button
              onClick={handleSend}
              disabled={!hasTarget || !message.trim() || sending}
              className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold rounded-xl text-xs transition-all shadow-subtle hover:shadow-emerald-glow flex items-center gap-2"
            >
              {sending ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Dispatching...
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  {channel === 'email' ? 'Send Email' : 'Send WhatsApp'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
