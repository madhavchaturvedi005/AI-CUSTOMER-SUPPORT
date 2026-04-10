-- Migration 002: Add knowledge_base table for document storage
-- This table stores uploaded documents and their extracted text content
-- for the AI to use in conversations

CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    file_type VARCHAR(100),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_knowledge_base_active ON knowledge_base(active);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_uploaded_at ON knowledge_base(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_filename ON knowledge_base(filename);

-- Full text search index for content
CREATE INDEX IF NOT EXISTS idx_knowledge_base_content_search ON knowledge_base USING gin(to_tsvector('english', content));

COMMENT ON TABLE knowledge_base IS 'Stores uploaded documents and extracted text for AI knowledge base';
COMMENT ON COLUMN knowledge_base.filename IS 'Original filename of uploaded document';
COMMENT ON COLUMN knowledge_base.content IS 'Extracted text content from document';
COMMENT ON COLUMN knowledge_base.file_type IS 'MIME type of uploaded file';
COMMENT ON COLUMN knowledge_base.active IS 'Whether this document is active in knowledge base';
