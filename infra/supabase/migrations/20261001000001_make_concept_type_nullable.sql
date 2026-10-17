-- Make content_ideas.concept_type nullable
ALTER TABLE content_ideas
ALTER COLUMN concept_type DROP NOT NULL;
