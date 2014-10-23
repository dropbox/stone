# babelapi(jinja2)

import json
from collections import OrderedDict
from bottle import (
    HTTPResponse,
    request,
    response,
    route,
    run,
)

from babelapi.data_type import OrderedExample

def segmentation_response(header, body, *segments):
    """Constructs HTTP headers and body for a segmentation response."""
    response_json = []

    for segment in segments:
        response_json.append(segment)

    if len(response_json) == 1:
        response_json = response_json[0]

    if header:
        response.headers['Dropbox-API-Result'] = json.dumps(response_json, indent=2)
        if body:
            return open('v2_server.babelt.py')
    else:
        # Manually convert json to a string because bottle only dumps json for
        # dicts, and not lists.
        response.content_type = 'application/json'
        return json.dumps(response_json)

{% for namespace_name, namespace in api.namespaces.items() -%}
    {%- if namespace.operations %}
        {%- for op in namespace.operations %}
@route('/2/{{ namespace_name }}/{{ op.name|lower }}', method={%- trim -%}
    [{% if op.extras.method == "GET" %}'GET', {% endif %}'POST'])
def {{ namespace_name }}_{{ op.name|method }}():
    return segmentation_response(
        {% if op.extras.host == 'content' %}
        True,
        {% else %}
        False,
        {% endif %}
        {% if op.response_segmentation.segments_by_name.get('data') %}
        True,
        {% else %}
        False,
        {% endif %}
        {% for segment in op.response_segmentation.segments %}
            {% if segment.data_type.name == 'Binary' %}
            {% elif not segment.data_type.has_example('default') %}
        {'no example': 'no example'},
            {% elif segment.list %}
        [{{ segment.data_type.get_example('default')|pprint|indent(8) }}],
            {% elif segment.data_type.has_example('default') %}
        {{ segment.data_type.get_example('default')|pprint|indent(8) }},
            {% endif %}
        {% endfor %}
    )

        {% endfor %}
    {% endif %}
{% endfor %}

run(host='localhost', port=8080, debug=True, reloader=True)
