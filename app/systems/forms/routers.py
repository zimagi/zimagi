from django.conf import settings
from django.urls import path

import re

# Path
# Form
# View
# Template
# Params

# urls = get_form_view(data_type -> Form, template)
# data_type - create   {data_type}/create
#             edit     {data_type}/edit/{id}
#             delete   {data_type}/delete/{id}

class FormRouter(object):

    def get_urls(self):
        urls = []

        # Path
        # View
        # urls.append(path(re.sub(r'\s+', '/', name), view))

        return urls
