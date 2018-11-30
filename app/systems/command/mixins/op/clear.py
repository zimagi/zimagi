
from utility import query


class ClearMixin(object):

    def exec_clear(self, facade, prompt = True):
        if facade.count():
            if prompt:
                self.confirmation(self.color("Are you sure you want to clear ALL {} instances?".format(facade.name), 'notice'))
        else:
            self.warning("No {} instances exist".format(facade.name))

        if facade.clear():
            self.success(" > Successfully cleared {} instances".format(facade.name))
        else:
            self.error("{} clear failed".format(facade.name.title()))


    def exec_clear_related(self, facade, instance, relation, prompt = True):
        queryset = query.get_queryset(instance, relation)
        instance_name = type(instance).__name__.lower()

        if queryset:
            if prompt:
                self.confirmation(self.color("Are you sure you want to remove ALL {} instances from {}?".format(facade.name, str(instance)), 'notice'))
            try:
                queryset.clear()
            except Exception:
                self.error("{} clear failed".format(facade.name.title()))

            self.success(" > Successfully cleared {} instances from {} {}".format(facade.name, instance_name, str(instance)))
        else:
            self.error("There is no relation {} on {} class".format(relation, instance_name))
