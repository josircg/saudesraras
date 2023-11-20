from drf_yasg.inspectors import SwaggerAutoSchema as SAS


class SwaggerAutoSchema(SAS):
    """Class to show only GET methods"""

    def get_operation(self, operation_keys):
        operation = super().get_operation(operation_keys)

        if self.method == 'GET':
            return operation
