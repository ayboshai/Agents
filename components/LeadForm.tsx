'use client';

import { useState } from 'react';

interface LeadFormPayload {
  name: string;
  phone: string;
  message: string;
}

interface LeadFormProps {
  onSubmit: (payload: LeadFormPayload) => Promise<void> | void;
}

export default function LeadForm({ onSubmit }: LeadFormProps) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const digitsCount = phone.replace(/\D/g, '').length;
    if (name.trim().length < 2 || name.trim().length > 80) {
      setError('Введите имя от 2 до 80 символов');
      return;
    }

    if (digitsCount < 10) {
      setError('Введите корректный номер телефона');
      return;
    }

    if (message.trim().length < 10 || message.trim().length > 1000) {
      setError('Сообщение должно быть от 10 до 1000 символов');
      return;
    }

    setError('');
    await onSubmit({ name: name.trim(), phone: phone.trim(), message: message.trim() });
  };

  return (
    <section className="mx-auto max-w-3xl px-6 py-16">
      <h2 className="text-3xl font-bold text-slate-900">Обсудим ваш проект</h2>
      <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="name">
            Name
          </label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="name"
            name="name"
            onChange={(event) => setName(event.target.value)}
            required
            type="text"
            value={name}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="phone">
            Phone
          </label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="phone"
            name="phone"
            onChange={(event) => setPhone(event.target.value)}
            required
            type="tel"
            value={phone}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700" htmlFor="message">
            Message
          </label>
          <textarea
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            id="message"
            name="message"
            onChange={(event) => setMessage(event.target.value)}
            required
            rows={5}
            value={message}
          />
        </div>

        {error ? <p className="text-sm text-red-600">{error}</p> : null}

        <button className="rounded-md bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700" type="submit">
          Оставить заявку
        </button>
      </form>
    </section>
  );
}
