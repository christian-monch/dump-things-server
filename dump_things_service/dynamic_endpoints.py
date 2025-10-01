import logging
from itertools import count

from fastapi import FastAPI

from dump_things_service.config import InstanceConfig

logger = logging.getLogger('dump_things_service')


_endpoint_template = """
async def {name}(
        data: {model_var_name}.{class_name} | Annotated[str, Body(media_type='text/plain')],
        api_key: str = Depends(api_key_header_scheme),
        format: Format = Format.json,
) -> JSONResponse | PlainTextResponse:
    logger.info('{name}(%s, %s, %s, %s)', repr(data), repr('{class_name}'), repr({model_var_name}), repr(format))
    return {handler}('{collection}', data, '{class_name}', {model_var_name}, format, api_key)
"""


def create_store_endpoints(
    app: FastAPI,
    instance_config: InstanceConfig,
    global_dict: dict,
):
    # Create endpoints for all classes in all collections
    logger.info('Creating dynamic store_record endpoints...')
    serial_number = count()

    for collection, (
        model,
        classes,
        model_var_name,
    ) in instance_config.model_info.items():
        global_dict[model_var_name] = model
        for class_name in classes:
            # Create an endpoint to dump data of type `class_name` in version
            # `version` of schema `application`.
            endpoint_name = f'_endpoint_{next(serial_number)}'

            endpoint_source = _endpoint_template.format(
                name=endpoint_name,
                model_var_name=model_var_name,
                class_name=class_name,
                collection=collection,
                info=f"'store {collection}/{class_name} objects'",
                handler='store_record',
            )
            exec(endpoint_source, global_dict)  # noqa S102

            # Create an API route for the endpoint
            app.add_api_route(
                path=f'/{collection}/record/{class_name}',
                endpoint=global_dict[endpoint_name],
                methods=['POST'],
                name=f'handle "{class_name}" of schema "{model.linkml_meta["id"]}" objects',
                response_model=None,
                tags=[f'Write records to "{collection}"']
            )

    logger.info('Creation of %d endpoints completed.', next(serial_number))


def create_validate_endpoints(
        app: FastAPI,
        instance_config: InstanceConfig,
        global_dict: dict,
):
    # Create endpoints for all classes in all collections
    logger.info('Creating dynamic validate_record endpoints...')
    serial_number = count()

    for collection, (
            model,
            classes,
            model_var_name,
    ) in instance_config.model_info.items():
        global_dict[model_var_name] = model
        for class_name in classes:
            # Create an endpoint to dump data of type `class_name` in version
            # `version` of schema `application`.
            endpoint_name = f'_endpoint_validate_{next(serial_number)}'

            endpoint_source = _endpoint_template.format(
                name=endpoint_name,
                model_var_name=model_var_name,
                class_name=class_name,
                collection=collection,
                info=f"'validate {collection}/{class_name} objects'",
                handler='validate_record',
            )
            exec(endpoint_source, global_dict)  # noqa S102

            # Create an API route for the endpoint
            app.add_api_route(
                path=f'/{collection}/validate/record/{class_name}',
                endpoint=global_dict[endpoint_name],
                methods=['POST'],
                name=f'validate "{class_name}" of schema "{model.linkml_meta["id"]}" objects',
                response_model=None,
                tags=[f'Validate records for "{collection}"']
            )

    logger.info('Creation of %d endpoints completed.', next(serial_number))
