// app/process_complete_plan/route.ts

import { NextResponse } from 'next/server';
import { parse } from 'url';
import fs from 'fs';

export const config = {
  api: {
    bodyParser: false, // Disallow Next.js body parsing, so we can handle it ourselves
  },
};

export async function POST(request: Request) {
    const formdata = await request.json();

    console.log(formdata)
}
