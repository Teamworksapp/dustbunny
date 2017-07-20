"""
SQLAlchemy
==========
"""

from sqlalchemy import event
from sqlalchemy.orm import mapper
from functools import partial

def import_upon_configure(Base, here):
    def import_models_into_namespace():
        for class_ in Base._decl_class_registry.values():
            if hasattr(class_, '__tablename__'):
                setattr(here, class_.__name__, class_)

    # Listen for the SQLAlchemy event and run setup_schema.
    # Note: This has to be done after Base and session are setup
    event.listen(mapper, 'after_configured', import_models_into_namespace)

