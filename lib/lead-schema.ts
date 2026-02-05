import { z } from 'zod';

export const leadSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, 'Введите имя от 2 до 80 символов')
    .max(80, 'Введите имя от 2 до 80 символов'),
  phone: z
    .string()
    .trim()
    .refine((value) => value.replace(/\D/g, '').length >= 10, {
      message: 'Введите корректный номер телефона',
    }),
  message: z
    .string()
    .trim()
    .min(10, 'Сообщение должно быть от 10 до 1000 символов')
    .max(1000, 'Сообщение должно быть от 10 до 1000 символов'),
});

export type LeadPayload = z.infer<typeof leadSchema>;
