import { NextResponse } from 'next/server';
import { kv } from '@vercel/kv';

export const dynamic = 'force-dynamic';


// Fallback memory store in case KV is not configured locally
let fallbackStore = {
    status: 'idle',
    message: 'Bot is initializing...',
    reelId: null,
    sender: null,
    updatedAt: new Date().toISOString()
};

const KV_KEY = 'bot_state';

// GET request to fetch the current bot status
export async function GET() {
    try {
        if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
            const state = await kv.get(KV_KEY);
            return NextResponse.json(state || fallbackStore);
        }
        // If no KV credentials (local dev testing), use memory
        return NextResponse.json(fallbackStore);
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(fallbackStore);
    }
}

// POST request for the Python bot to push status updates
export async function POST(request: Request) {
    try {
        const body = await request.json();

        const newState = {
            status: body.status || 'idle',
            message: body.message || '',
            reelId: body.reelId || null,
            sender: body.sender || null,
            updatedAt: new Date().toISOString()
        };

        if (process.env.KV_REST_API_URL && process.env.KV_REST_API_TOKEN) {
            await kv.set(KV_KEY, newState);
        } else {
            // Memory fallback for local testing without Vercel DB
            fallbackStore = newState;
        }

        return NextResponse.json({ success: true, state: newState });
    } catch (error) {
        console.error('POST Error:', error);
        return NextResponse.json({ success: false, error: 'Invalid payload' }, { status: 400 });
    }
}
