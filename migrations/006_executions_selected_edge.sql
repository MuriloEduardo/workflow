ALTER TABLE executions
    ADD COLUMN selected_edge_id UUID REFERENCES edges(id) NULL;
