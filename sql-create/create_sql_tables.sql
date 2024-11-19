-- Works table
CREATE TABLE works (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    initial_document_id BYTEA NOT NULL,
    primary_document_hash BYTEA NOT NULL,
    provenance_id INTEGER,
    CONSTRAINT fk_works_initial_document FOREIGN KEY (initial_document_id) 
        REFERENCES documents(hash),
    CONSTRAINT fk_works_primary_document FOREIGN KEY (primary_document_hash) 
        REFERENCES documents(hash),
    CONSTRAINT fk_works_provenance FOREIGN KEY (provenance_id) 
        REFERENCES provenance(id)
);

-- Documents table
CREATE TABLE documents (
    hash BYTEA PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    s3uri TEXT NOT NULL,
    publication_id INTEGER,
    provenance_id INTEGER,
    CONSTRAINT fk_documents_publication FOREIGN KEY (publication_id) 
        REFERENCES publication(id),
    CONSTRAINT fk_documents_provenance FOREIGN KEY (provenance_id) 
        REFERENCES provenance(id)
);

-- RTransparent table
CREATE TABLE rtransparent (
    id SERIAL PRIMARY KEY,
    document_hash BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    version VARCHAR(50),
    provenance_id INTEGER,
    CONSTRAINT fk_rtransparent_document FOREIGN KEY (document_hash) 
        REFERENCES documents(hash),
    CONSTRAINT fk_rtransparent_provenance FOREIGN KEY (provenance_id) 
        REFERENCES provenance(id)
);

-- Provenance table
CREATE TABLE provenance (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(255),
    version VARCHAR(50),
    compute TEXT,
    personnel TEXT,
    comment TEXT
);

-- XML table
CREATE TABLE xml (
    id SERIAL PRIMARY KEY,
    document_hash BYTEA NOT NULL,
    xml TEXT,
    CONSTRAINT fk_xml_document FOREIGN KEY (document_hash) 
        REFERENCES documents(hash)
);

-- Add indexes for foreign keys to improve query performance
CREATE INDEX idx_works_initial_document_id ON works(initial_document_id);
CREATE INDEX idx_works_primary_document_hash ON works(primary_document_hash);
CREATE INDEX idx_works_provenance_id ON works(provenance_id);
CREATE INDEX idx_documents_provenance_id ON documents(provenance_id);
CREATE INDEX idx_rtransparent_document_hash ON rtransparent(document_hash);
CREATE INDEX idx_rtransparent_provenance_id ON rtransparent(provenance_id);
CREATE INDEX idx_xml_document_hash ON xml(document_hash);