from systems.models.index import BaseModelFacade, Model


class EnvironmentBaseFacade(BaseModelFacade('environment')):

    def get_base_scope(self):
        return { 'environment_id': Model('environment').facade.get_env() }
