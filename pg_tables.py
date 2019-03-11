authors = ['DROP TABLE IF EXISTS research_match.authors;',
           
           'CREATE TABLE research_match.authors \
            (auth_id integer NOT NULL, \
            name text COLLATE pg_catalog."default" NOT NULL, \
            page text COLLATE pg_catalog."default", \
            page_hash bigint NOT NULL, \
            CONSTRAINT authors_pkey PRIMARY KEY (auth_id), \
            CONSTRAINT authors_uq_page UNIQUE (page_hash)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS research_match.auth_page_idx;',
            'CREATE INDEX auth_page_idx \
            ON research_match.authors USING btree \
            (page COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            
            'DROP INDEX IF EXISTS research_match.auth_page_hash_idx;',
            'CREATE INDEX auth_page_hash_idx \
            ON research_match.authors USING btree \
            (page_hash) \
            TABLESPACE pg_default;'
            ]

papers = ['DROP TABLE IF EXISTS research_match.papers;',
           'CREATE TABLE research_match.papers \
            (pap_id integer NOT NULL, \
            mongo_hash varchar NOT NULL, \
            page text COLLATE pg_catalog."default" NOT NULL, \
            page_hash bigint NOT NULL, \
            CONSTRAINT papers_pkey PRIMARY KEY (pap_id), \
            CONSTRAINT papers_uq_page UNIQUE (page_hash), \
            CONSTRAINT papers_uq_mongo UNIQUE (mongo_hash)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;',

            'DROP INDEX IF EXISTS research_match.pap_page_idx;',
            'CREATE INDEX pap_page_idx \
            ON research_match.papers USING btree \
            (page COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            
            'DROP INDEX IF EXISTS research_match.pap_page_hash_idx;',
            'CREATE INDEX pap_page_hash_idx \
            ON research_match.papers USING btree \
            (page_hash) \
            TABLESPACE pg_default;'
            
            'DROP INDEX IF EXISTS research_match.pap_mongo_hash_idx;',
            'CREATE INDEX pap_mongo_hash_idx \
            ON research_match.papers USING btree \
            (mongo_hash COLLATE pg_catalog."default") \
            TABLESPACE pg_default;'
            ]


publishers = ['DROP TABLE IF EXISTS research_match.publishers;',
              'CREATE TABLE research_match.publishers \
            (pub_id integer NOT NULL, \
            name text COLLATE pg_catalog."default" NOT NULL, \
            page text COLLATE pg_catalog."default" NOT NULL, \
            page_hash bigint NOT NULL, \
            CONSTRAINT publishers_pkey PRIMARY KEY (pub_id), \
            CONSTRAINT publishers_uq_page UNIQUE (page_hash)) \
            WITH (OIDS = FALSE)',
            'DROP INDEX  IF EXISTS research_match.pub_name_idx;',
            'CREATE INDEX pub_name_idx \
            ON research_match.publishers USING btree \
            (name COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            'DROP INDEX  IF EXISTS research_match.pub_page_idx;',
            'CREATE INDEX pub_page_idx \
            ON research_match.publishers USING btree \
            (page COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            
            'DROP INDEX IF EXISTS research_match.pub_page_hash_idx;',
            'CREATE INDEX pub_page_hash_idx \
            ON research_match.publishers USING btree \
            (page_hash) \
            TABLESPACE pg_default;'            
            ]


institutions = ['DROP TABLE IF EXISTS research_match.institutions;',
              'CREATE TABLE research_match.institutions \
            (inst_id integer NOT NULL, \
            name text COLLATE pg_catalog."default" NOT NULL, \
            page text COLLATE pg_catalog."default" NOT NULL, \
            page_hash bigint NOT NULL, \
            CONSTRAINT institutions_pkey PRIMARY KEY (inst_id), \
            CONSTRAINT institutions_uq_page UNIQUE (page_hash)) \
            WITH (OIDS = FALSE)',
            'DROP INDEX  IF EXISTS research_match.inst_name_idx;',
            'CREATE INDEX inst_name_idx \
            ON research_match.institutions USING btree \
            (name COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',
            'DROP INDEX  IF EXISTS research_match.inst_page_idx;',
            'CREATE INDEX inst_page_idx \
            ON research_match.institutions USING btree \
            (page COLLATE pg_catalog."default" text_pattern_ops) \
            TABLESPACE pg_default;',

            'DROP INDEX IF EXISTS research_match.inst_page_hash_idx;',
            'CREATE INDEX inst_page_hash_idx \
            ON research_match.institutions USING btree \
            (page_hash) \
            TABLESPACE pg_default;'      
            ]


xref_pap_auth = ['DROP TABLE IF EXISTS research_match.xref_pap_auth;',
              'CREATE TABLE research_match.xref_pap_auth \
            (pap_auth_id integer NOT NULL, \
            pap_id integer NOT NULL, \
            auth_id integer NOT NULL, \
            CONSTRAINT pap_auth_pkey PRIMARY KEY (pap_auth_id), \
            CONSTRAINT pap_auth_pap_fkey FOREIGN KEY (pap_id) \
            REFERENCES research_match.papers (pap_id), \
            CONSTRAINT pap_auth_auth_fkey FOREIGN KEY (auth_id) \
            REFERENCES research_match.authors (auth_id)) \
            WITH (OIDS = FALSE)',
            
            'DROP INDEX  IF EXISTS research_match.pap_auth_id_idx;',
            'CREATE INDEX pap_auth_id_idx \
            ON research_match.xref_pap_auth USING btree \
            (pap_auth_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_auth_pap_idx;',
            'CREATE INDEX pap_auth_pap_idx \
            ON research_match.xref_pap_auth USING btree \
            (pap_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_auth_auth_idx;',
            'CREATE INDEX pap_auth_auth_idx \
            ON research_match.xref_pap_auth USING btree \
            (auth_id) \
            TABLESPACE pg_default;',
            ]

xref_pap_pub = ['DROP TABLE IF EXISTS research_match.xref_pap_pub;',
              'CREATE TABLE research_match.xref_pap_pub \
            (pap_pub_id integer NOT NULL, \
            pap_id integer NOT NULL, \
            pub_id integer NOT NULL, \
            CONSTRAINT pap_pub_pkey PRIMARY KEY (pap_pub_id), \
            CONSTRAINT pap_pub_pap_fkey FOREIGN KEY (pap_id) \
            REFERENCES research_match.papers (pap_id), \
            CONSTRAINT pap_pub_pub_fkey FOREIGN KEY (pub_id) \
            REFERENCES research_match.publishers (pub_id)) \
            WITH (OIDS = FALSE)',
            
            'DROP INDEX  IF EXISTS research_match.pap_pub_id_idx;',
            'CREATE INDEX pap_pub_id_idx \
            ON research_match.xref_pap_pub USING btree \
            (pap_pub_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_pub_pap_idx;',
            'CREATE INDEX pap_pub_pap_idx \
            ON research_match.xref_pap_pub USING btree \
            (pap_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_pub_pub_idx;',
            'CREATE INDEX pap_pub_pub_idx \
            ON research_match.xref_pap_pub USING btree \
            (pub_id) \
            TABLESPACE pg_default;',
            ]

xref_pap_inst = ['DROP TABLE IF EXISTS research_match.xref_pap_inst;',
              'CREATE TABLE research_match.xref_pap_inst \
            (pap_inst_id integer NOT NULL, \
            pap_id integer NOT NULL, \
            inst_id integer NOT NULL, \
            CONSTRAINT pap_inst_pkey PRIMARY KEY (pap_inst_id), \
            CONSTRAINT pap_inst_pap_fkey FOREIGN KEY (pap_id) \
            REFERENCES research_match.papers (pap_id), \
            CONSTRAINT pap_inst_inst_fkey FOREIGN KEY (inst_id) \
            REFERENCES research_match.institutions (inst_id)) \
            WITH (OIDS = FALSE)',
            
            'DROP INDEX  IF EXISTS research_match.pap_inst_id_idx;',
            'CREATE INDEX pap_inst_id_idx \
            ON research_match.xref_pap_inst USING btree \
            (pap_inst_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_inst_pap_idx;',
            'CREATE INDEX pap_inst_pap_idx \
            ON research_match.xref_pap_inst USING btree \
            (pap_id) \
            TABLESPACE pg_default;',

            'DROP INDEX  IF EXISTS research_match.pap_inst_inst_idx;',
            'CREATE INDEX pap_inst_inst_idx \
            ON research_match.xref_pap_inst USING btree \
            (inst_id) \
            TABLESPACE pg_default;',
            ]

references = ['DROP TABLE IF EXISTS research_match.references;',
           'CREATE TABLE research_match.references \
            (ref_id integer NOT NULL, \
            cit_pap_id integer NOT NULL, \
            ref_pap_id integer NOT NULL, \
            CONSTRAINT references_pkey PRIMARY KEY (ref_id), \
            CONSTRAINT references_ref_fkey FOREIGN KEY (ref_pap_id) \
            REFERENCES research_match.papers (pap_id), \
            CONSTRAINT references_cit_fkey FOREIGN KEY (cit_pap_id) \
            REFERENCES research_match.papers (pap_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;',
            
            'DROP INDEX IF EXISTS research_match.ref_ref_id_idx;',
            'CREATE INDEX ref_ref_id_idx \
            ON research_match.references USING btree \
            (ref_id) \
            TABLESPACE pg_default;'

            'DROP INDEX IF EXISTS research_match.ref_cit_pap_idx;',
            'CREATE INDEX ref_cit_pap_idx \
            ON research_match.references USING btree \
            (cit_pap_id) \
            TABLESPACE pg_default;'      
            
            'DROP INDEX IF EXISTS research_match.ref_ref_pap_idx;',
            'CREATE INDEX ref_ref_pap_idx \
            ON research_match.references USING btree \
            (ref_pap_id) \
            TABLESPACE pg_default;'  
            ]

create_tables = {}
create_tables['authors'] = authors
create_tables['publishers'] = publishers
create_tables['institutions'] = institutions
create_tables['papers'] = papers
create_tables['xref_pap_inst'] = xref_pap_inst
create_tables['xref_pap_pub'] = xref_pap_pub
create_tables['xref_pap_auth'] = xref_pap_auth
create_tables['references'] = references