# babelsdk(jinja2)

import json
from collections import OrderedDict
from bottle import (
    HTTPResponse,
    request,
    response,
    route,
    run,
)

def segmentation_response(*segments):
    """Constructs an HTTP body for a segmentation response."""
    for segment in segments:
        if isinstance(segment, dict):
            serialized_segment = json.dumps(segment, indent=2)
            yield 'j{}\n'.format(len(serialized_segment))
            yield serialized_segment
        if isinstance(segment, list):
            yield 's\n'
            for s in segment:
                if isinstance(s, dict):
                    serialized_segment = json.dumps(s, indent=2)
                    yield 'j{}\n'.format(len(serialized_segment))
                    yield serialized_segment
                elif isinstance(s, str):
                    yield 'b{}\n'.format(len(s))
                    yield s
            yield 'e\n'
        elif isinstance(segment, str):
            yield 'b{}\n'.format(len(segment))
            yield segment

{% for namespace_name, namespace in api.namespaces.items() -%}
    {%- if namespace.operations %}
        {%- for op in namespace.operations %}
@route('/2/{{ namespace_name }}/{{ op.name|lower }}', method='POST')
def {{ namespace_name }}_{{ op.name|pymethod }}():
    return segmentation_response(
                {%- for segment in op.response_segmentation.segments -%}
                    {% if segment.data_type.name == 'Binary' %}
                    {% elif segment.list %}
        [{{ segment.data_type.get_example('default')|pypprint|indent(8) }}],
                    {% elif segment.data_type.has_example('default') %}
        {{ segment.data_type.get_example('default')|pypprint|indent(8) }},
                    {% else %}
        {'no example': 'no example'},
                    {%- endif -%}
                {%- endfor %}
    )
        {%- endfor %}
    {% endif -%}
{% endfor %}

run(host='localhost', port=8080, debug=True, reloader=True)
