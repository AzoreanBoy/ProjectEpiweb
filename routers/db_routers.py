class EpidbRouter:
    """
    Router for using the epilepsiae database
    """

    route_app_labels = {'epidb'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "epidb"
        return 'default'

    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the auth or contenttypes apps is
        involved.
        """
        return 'default'

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the auth and contenttypes apps only appear in the
        'epidb' database.
        """
        return 'default'
