
class DataChatRegistry:
    _registry = {} # { Model: ConfigDict }

    @classmethod
    def register(cls, model_class, include_fields=None, exclude_fields=None, tags=None):
        """
        Register a model for exposure to Data Chat.
        """
        meta = model_class._meta
        table_name = meta.db_table

        # Calculate allowed fields
        all_fields = [f.name for f in meta.get_fields() if not f.is_relation and not f.many_to_many]

        allowed_fields = []
        if include_fields:
            allowed_fields = include_fields
        else:
            allowed_fields = all_fields

        if exclude_fields:
            allowed_fields = [f for f in allowed_fields if f not in exclude_fields]

        cls._registry[table_name] = {
            "model": model_class,
            "table_name": table_name,
            "fields": allowed_fields,
            "tags": tags or []
        }
        return model_class

    @classmethod
    def get_exposed_tables(cls):
        """
        Return schema information for all exposed tables.
        """
        # 1. Start with Registry
        tables = cls._registry.copy()

        # 2. Merge with Settings (if enabled)
        # TODO: Implement settings merge logic

        return tables

# Decorator shortcut
def register_model(include_fields=None, exclude_fields=None, tags=None):
    def _wrapper(model_class):
        DataChatRegistry.register(model_class, include_fields, exclude_fields, tags)
        return model_class
    return _wrapper
