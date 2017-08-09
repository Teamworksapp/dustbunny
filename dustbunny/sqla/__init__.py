"""
SQLAlchemy Tools
================

"""

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import mapper
from sqlalchemy import event
from sqlparse import format as sql_format
import sys

from functools import partial

def import_upon_configure(Base, here):
    """
    Import ORM models from the given base class into the current namespace.
    """
    def import_models_into_namespace():
        for class_ in Base._decl_class_registry.values():
            if hasattr(class_, '__tablename__'):
                setattr(here, class_.__name__, class_)

    # Listen for the SQLAlchemy event and run setup_schema.
    # Note: This has to be done after Base and session are setup
    event.listen(mapper, 'after_configured', import_models_into_namespace)


def print_sql(db, q, inline=False):
    """
    If you are using Postgres, print the sql used by a query.
    
    :param q (query): an SQLAlchemy query object 
    :param inline (bool): inline parameters? 
    :return: None
    """
    print(render_sql(db, q, inline=inline))

def render_sql(db, q, inline=False):
    """
    Render the sql used by a query (only works for Postgres)
    
    :param q (query): an SQLAlchemy query object 
    :param inline (bool): inline parameters? 
    :return: str
    """
    compiled_statement = q.statement.compile(dialect=postgresql.dialect())
    pretty_statement = sql_format(str(compiled_statement), reindent=True)
    if inline:
        with db.session.connection().connection.connection.cursor() as cur:
            return cur.mogrify(pretty_statement, compiled_statement.params).decode('utf-8')
    else:
        return pretty_statement + ("\nparameters: {}".format(str(compiled_statement.params)) if compiled_statement.params else '')