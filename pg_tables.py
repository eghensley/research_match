authors = ['DROP TABLE IF EXISTS research_match.authors;',
           'CREATE TABLE research_match.authors \
            (auth_id integer NOT NULL, \
            name text COLLATE pg_catalog."default" NOT NULL, \
            page text COLLATE pg_catalog."default", \
            CONSTRAINT authors_pkey PRIMARY KEY (auth_id)) \
            WITH (OIDS = FALSE) \
            TABLESPACE pg_default;']


publishers = ['DROP TABLE IF EXISTS research_match.publishers;',
              'CREATE TABLE research_match.publishers \
            (pub_id integer NOT NULL, \
            name text COLLATE pg_catalog."default" NOT NULL, \
            page text COLLATE pg_catalog."default", \
            CONSTRAINT publishers_pkey PRIMARY KEY (pub_id)) \
            WITH (OIDS = FALSE)']
            
create_tables = {}
create_tables['authors'] = authors
create_tables['publishers'] = publishers
