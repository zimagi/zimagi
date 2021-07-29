from systems.models.index import ModelFacade


class DataSetFacade(ModelFacade('dataset')):

    def get_field_data_display(self, instance, value, short):
        data = instance.provider.load()
        return "\n" + self.notice_color(data) + "\n"
