import { NextResponse } from 'next/server';
import { leadSchema } from '../../../lib/lead-schema';

export async function POST(request: Request) {
  let json: unknown;

  try {
    json = await request.json();
  } catch {
    return NextResponse.json({ ok: false, errors: { form: ['Некорректный JSON payload'] } }, { status: 400 });
  }

  const result = leadSchema.safeParse(json);

  if (!result.success) {
    return NextResponse.json(
      {
        ok: false,
        errors: result.error.flatten().fieldErrors,
      },
      { status: 400 },
    );
  }

  return NextResponse.json({ ok: true }, { status: 200 });
}
