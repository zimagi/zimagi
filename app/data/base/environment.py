from systems.models.index import BaseModelFacade, Model


class EnvironmentBaseFacadeOverride(BaseModelFacade('environment')):

    def get_base_scope(self):
        return { 'environment_id': Model('environment').facade.get_env() }
