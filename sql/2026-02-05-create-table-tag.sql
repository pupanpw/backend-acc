-- tags
CREATE TABLE IF NOT EXISTS tags (
  id           BIGSERIAL PRIMARY KEY,
  user_id_line TEXT NOT NULL,
  name         TEXT NOT NULL,
  slug         TEXT NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_tags_user_slug UNIQUE (user_id_line, slug)
);

-- transaction_tags (join table)
CREATE TABLE IF NOT EXISTS transaction_tags (
  transaction_id BIGINT NOT NULL,
  tag_id         BIGINT NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (transaction_id, tag_id),
  FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tt_tag_id ON transaction_tags(tag_id);


ALTER TABLE transactions
DROP COLUMN IF EXISTS tag;


CREATE INDEX IF NOT EXISTS idx_tx_user_date
  ON transactions(user_id_line, transaction_at);

CREATE INDEX IF NOT EXISTS idx_tt_tx
  ON transaction_tags(transaction_id);

CREATE INDEX IF NOT EXISTS idx_tt_tag
  ON transaction_tags(tag_id);
