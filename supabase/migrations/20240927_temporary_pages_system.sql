-- Create temporary pages system tables
-- Migration for temporary pages and receipts

CREATE TABLE IF NOT EXISTS public.temporary_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_code UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content JSONB NOT NULL,
    content_type TEXT DEFAULT 'report',
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    access_count INTEGER DEFAULT 0,
    max_access_count INTEGER DEFAULT NULL,
    allowed_actions TEXT[] DEFAULT '{read,print}',
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_code UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content JSONB NOT NULL,
    receipt_type TEXT DEFAULT 'payment',
    reference_id TEXT,
    amount NUMERIC(10,2) DEFAULT 0,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    access_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.page_access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID,
    page_type TEXT NOT NULL,
    access_code UUID,
    ip_address INET,
    user_agent TEXT,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    action TEXT DEFAULT 'view',
    success BOOLEAN DEFAULT true
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_temporary_pages_access_code ON public.temporary_pages(access_code);
CREATE INDEX IF NOT EXISTS idx_temporary_pages_expires_at ON public.temporary_pages(expires_at);
CREATE INDEX IF NOT EXISTS idx_temporary_pages_active ON public.temporary_pages(is_active);
CREATE INDEX IF NOT EXISTS idx_receipts_receipt_code ON public.receipts(receipt_code);
CREATE INDEX IF NOT EXISTS idx_receipts_active ON public.receipts(is_active);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_page_id ON public.page_access_logs(page_id);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_access_code ON public.page_access_logs(access_code);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_accessed_at ON public.page_access_logs(accessed_at);
