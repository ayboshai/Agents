'use client';

import { useMemo, useState } from 'react';
import { leadFormContent } from '../data/content';
import { leadSchema, type LeadPayload } from '../lib/lead-schema';

type FieldErrors = Partial<Record<keyof LeadPayload, string>>;

export default function LeadForm() {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [statusMessage, setStatusMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const payload = useMemo(
    () => ({ name: name.trim(), phone: phone.trim(), message: message.trim() }),
    [name, phone, message],
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validation = leadSchema.safeParse(payload);
    if (!validation.success) {
      const errors = validation.error.flatten().fieldErrors;
      setFieldErrors({
        name: errors.name?.[0],
        phone: errors.phone?.[0],
        message: errors.message?.[0],
      });
      setStatusMessage('Проверьте корректность полей: имя, телефон и сообщение.');
      return;
    }

    setFieldErrors({});
    setStatusMessage('');
    setSubmitting(true);

    try {
      const response = await fetch('/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(validation.data),
      });

      const responsePayload = (await response.json()) as {
        errors?: Record<string, string[]>;
      };

      if (!response.ok) {
        setFieldErrors({
          name: responsePayload.errors?.name?.[0],
          phone: responsePayload.errors?.phone?.[0],
          message: responsePayload.errors?.message?.[0],
        });
        setStatusMessage(leadFormContent.genericErrorMessage);
        return;
      }

      setName('');
      setPhone('');
      setMessage('');
      setStatusMessage(leadFormContent.successMessage);
    } catch {
      setStatusMessage(leadFormContent.genericErrorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <h2 className="text-3xl font-bold text-slate-900">{leadFormContent.title}</h2>
      <form className="mt-8 space-y-4" noValidate onSubmit={handleSubmit}>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="name">
            {leadFormContent.fields.nameLabel}
          </label>
          <input
            aria-describedby={fieldErrors.name ? 'name-error' : undefined}
            aria-invalid={fieldErrors.name ? 'true' : 'false'}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="name"
            name="name"
            onChange={(event) => setName(event.target.value)}
            required
            type="text"
            value={name}
          />
          {fieldErrors.name ? (
            <p className="mt-1 text-sm text-red-600" id="name-error">
              {fieldErrors.name}
            </p>
          ) : null}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="phone">
            {leadFormContent.fields.phoneLabel}
          </label>
          <input
            aria-describedby={fieldErrors.phone ? 'phone-error' : undefined}
            aria-invalid={fieldErrors.phone ? 'true' : 'false'}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="phone"
            name="phone"
            onChange={(event) => setPhone(event.target.value)}
            required
            type="tel"
            value={phone}
          />
          {fieldErrors.phone ? (
            <p className="mt-1 text-sm text-red-600" id="phone-error">
              {fieldErrors.phone}
            </p>
          ) : null}
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="message">
            {leadFormContent.fields.messageLabel}
          </label>
          <textarea
            aria-describedby={fieldErrors.message ? 'message-error' : undefined}
            aria-invalid={fieldErrors.message ? 'true' : 'false'}
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="message"
            name="message"
            onChange={(event) => setMessage(event.target.value)}
            required
            rows={5}
            value={message}
          />
          {fieldErrors.message ? (
            <p className="mt-1 text-sm text-red-600" id="message-error">
              {fieldErrors.message}
            </p>
          ) : null}
        </div>

        {statusMessage ? (
          <p aria-live="polite" className="text-sm text-slate-700" role="alert">
            {statusMessage}
          </p>
        ) : null}

        <button
          className="rounded-md bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={submitting}
          type="submit"
        >
          {submitting ? 'Отправка...' : leadFormContent.submitButton}
        </button>
      </form>
    </section>
  );
}
